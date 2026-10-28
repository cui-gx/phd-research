"""B1-R1の固定軌道CPU再評価。MD・モデル学習・モデル推論を呼び出さない。"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import fcntl
import functools
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np
from scipy.stats import spearmanr

PLAN = '59f97821ae6ffe283c371f710546abf84f691642'
MODES = ('ORIGINAL_HISTORY', 'COMMON_A4', 'COMMON_A2', 'MATCHED_COUNT')
CONT = ('distance_mean_A', 'distance_median_A', 'distance_p90_A',
        'Rg_mean_A', 'Q8_mean', 'angle_to_geometric_neighbor_median_deg')
COMPS = (('F2', 'F1'), ('F2', 'F0'), ('F1', 'F0'))
BURNS = (0, 100, 200, 500)
PREFIXES = (1., 2., 4.)
LABELS = ('F0', 'F1-t1', 'F1-t2', 'F2-t1', 'F2-t2')
ROOTS = tuple(f'r{i:02d}' for i in range(1, 9))
GIB = 1024**3


def read_json(path):
    """保存済みJSONを読み、呼出側で版とSHAを検査する。"""
    return json.loads(Path(path).read_text())


def sha(path):
    """ファイル全体のSHA-256を求める。"""
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(2**20), b''):
            h.update(chunk)
    return h.hexdigest()


def array_sha(a):
    """dtypeとshapeも含む配列識別子。元ファイルSHAとは区別する。"""
    a = np.ascontiguousarray(a)
    h = hashlib.sha256((str(a.dtype)+str(a.shape)).encode())
    h.update(a.tobytes())
    return h.hexdigest()


def dump(path, value):
    """新出力だけを原子的に保存する。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def write_table(path, rows):
    """列順を保持し、欠測を空欄にしたUTF-8 CSVを書く。"""
    rows = list(rows)
    if not rows:
        raise ValueError('空の結果表を成功として保存できません。')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def close_value(actual, expected, atol=1e-8, rtol=1e-10):
    """計算再現の許容。科学的等価性の幅ではない。"""
    return bool(np.allclose(actual, expected, atol=atol, rtol=rtol, equal_nan=False))


def matched_ids(ids, k):
    """結果に依存しない、登録済みfloor規則の等点数間引き。"""
    ids = np.asarray(ids, dtype=np.int64)
    if k < 2 or k > len(ids) or len(np.unique(ids)) != len(ids):
        raise ValueError('間引き点数または候補IDが不正です。')
    positions = np.arange(k, dtype=np.int64)*(len(ids)-1)//(k-1)
    return ids[positions]


def metric_keys():
    """全144指標・時間・尺度条件を省略せず返す。"""
    keys = [(b, p, m, None, None) for b, p, m in itertools.product(BURNS, PREFIXES, CONT)]
    keys += [(b, p, 'added_regions', e, t) for b, p, e, t in
             itertools.product(BURNS, PREFIXES, (1.5, 2., 3.), (0, 5))]
    return keys


def key_spec(key):
    return dict(zip(('burn_ps', 'prefix_ns', 'metric', 'epsilon_A', 'tau_ps'), key))


def correlation(x, y):
    """有限非定常系列の記述。独立標本数を推定しない。"""
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return None
    value = float(np.corrcoef(x, y)[0, 1])
    return value if np.isfinite(value) else None


def randomness(values):
    """2×3の加法記述。純分散成分とは解釈しない。"""
    x = np.asarray(values, float).reshape(2, 3)
    row, col, grand = x.mean(1), x.mean(0), x.mean()
    residual = x-row[:, None]-col[None, :]+grand
    return dict(mean=float(grand), training_means=row.tolist(),
                training_mean_difference=float(row[1]-row[0]),
                training_mean_SD=float(row.std(ddof=1)),
                MD_SD_by_training=x.std(1, ddof=1).tolist(),
                MD_column_means=col.tolist(),
                additive_residual_RMS=float(np.sqrt(np.mean(residual**2))),
                pure_interaction_variance_identified=False)


def root_statistics(values, draws):
    """8根の同じ再標本化インデックスを全結果で共有する。"""
    v = np.asarray(values, float)
    if v.shape != (8,) or not np.isfinite(v).all():
        raise ValueError('完全な8根が必要です。')
    ci = np.quantile(v[draws].mean(1), [.025, .975])
    loo = [(float(v.sum())-float(x))/7 for x in v]
    return dict(roots=8, mean=float(v.mean()), median=float(np.median(v)),
                minimum=float(v.min()), maximum=float(v.max()), root_SD=float(v.std(ddof=1)),
                bootstrap95_low=float(ci[0]), bootstrap95_high=float(ci[1]),
                positive_roots=int((v > 0).sum()), negative_roots=int((v < 0).sum()),
                zero_roots=int((v == 0).sum()),
                leave_one_root_out_means=json.dumps(loo),
                scope='同一準備条件・8根・有限seedの探索的区間。同時被覆やCを認定しない。')


def atom_identity(path):
    """PDBの原子順を座標と切り離して検査する。"""
    rows = []
    for line in Path(path).read_text().splitlines():
        if line.startswith(('ATOM  ', 'HETATM')):
            rows.append((line[12:16].strip(), line[16], line[17:20], line[21],
                         line[22:26], line[26], line[76:78].strip()))
    if len(rows) != 504 or sum(r[0] == 'CA' for r in rows) != 28:
        raise ValueError('固定トポロジーの原子数に一致しません。')
    return rows


class Review:
    """新出力だけを持つ一プロセスのCPU復核器。"""

    def __init__(self, project, output, bundle):
        self.project, self.out, self.bundle = map(lambda p: Path(p).resolve(), (project, output, bundle))
        if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
            raise RuntimeError('CUDA_VISIBLE_DEVICES=-1が必須です。')
        for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
            if os.environ.get(name) != '1':
                raise RuntimeError(name+'=1が必須です。')
        if self.project.stat().st_uid != os.getuid() or self.project not in self.out.parents:
            raise RuntimeError('本人プロジェクトの新出力先に限定します。')
        self.run = self.project/'runs/b1-expansion-20261026'
        self.art = self.project/'artifacts/b1-expansion-20261026'
        self.out.mkdir(parents=True, exist_ok=True)
        self.lock = (self.out/'run.lock').open('a')
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.started, self.cpu_started = time.perf_counter(), time.process_time()
        self.matrix = read_json(self.bundle/'experiment-matrix.json')
        self.expected = read_json(self.bundle/'raw-artifact-sha256.json')
        self.legacy_source = self.art/'executed-source/p1/server/gq_r2.py'
        expected_source = read_json(self.bundle/'expected-frozen-source.json')
        if sha(self.legacy_source) != expected_source['p1/server/gq_r2.py']:
            raise ValueError('固定評価ソースのSHAが不一致です。')
        spec = importlib.util.spec_from_file_location('frozen_r1_gq', self.legacy_source)
        self.gq = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.gq)
        allowed = sorted(os.sched_getaffinity(0))
        os.sched_setaffinity(0, {allowed[0]})
        os.nice(10)
        previous_events = [json.loads(line) for line in (self.out/'events.jsonl').read_text().splitlines()] if (self.out/'events.jsonl').exists() else []
        self.previous_wall = sum(e['wall_s'] for e in previous_events if e['event'] == 'stage_complete')
        self.emit('session_started', pid=os.getpid(), affinity_count=1)
        self.gate('session')
        manifest = dict(plan_commit=PLAN, code_sha256=sha(__file__),
                        input_matrix_sha256=sha(self.bundle/'experiment-matrix.json'),
                        expected_raw_manifest_sha256=sha(self.bundle/'raw-artifact-sha256.json'),
                        frozen_gq_source_sha256=sha(self.legacy_source),
                        modes=list(MODES), worker_count=1, numeric_threads=1,
                        GPU_visible=False, MD=0, training=0, model_inference=0)
        p = self.out/'execution-manifest.json'
        if p.exists() and read_json(p) != manifest:
            raise RuntimeError('既存R1出力の実行版が一致しません。')
        if not p.exists():
            dump(p, manifest)

    def emit(self, kind, **fields):
        row = dict(event=kind, UTC=dt.datetime.now(dt.timezone.utc).isoformat(), **fields)
        with (self.out/'events.jsonl').open('a') as f:
            f.write(json.dumps(row, ensure_ascii=False)+'\n')
        print(json.dumps(row, ensure_ascii=False), flush=True)

    def gate(self, stage):
        """各工程前の共有資源・RSS・保存量の停止ゲート。"""
        mem = {}
        for line in Path('/proc/meminfo').read_text().splitlines():
            k, v = line.split(':', 1)
            mem[k] = int(v.split()[0])*1024
        free = shutil.disk_usage(self.out).free
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        total = sum(p.stat().st_size for p in self.out.rglob('*') if p.is_file())
        load = os.getloadavg()[0]
        cpus = os.cpu_count()
        if mem['MemAvailable'] < 4*GIB or free < 100*GIB or rss > 2*GIB or total > 2*GIB:
            raise RuntimeError('RAM/RSS/保存容量の保護ゲートで停止します。')
        if load > max(2, cpus*.75):
            raise RuntimeError('共有CPU高負荷のため停止します。')
        if self.previous_wall+time.perf_counter()-self.started > 6*3600:
            raise RuntimeError('CPU運用6時間の再審査点に達しました。')
        self.emit('resource_gate', stage=stage, memory_available_bytes=mem['MemAvailable'],
                  free_disk_bytes=free, peak_RSS_bytes=rss, output_bytes=total,
                  load1=load, cpu_count=cpus)

    def science(self, task):
        return self.run/'tasks'/task/'science'

    @functools.lru_cache(maxsize=2)
    def pool(self, sid):
        p = self.science(sid+'-decision-pool')
        with np.load(p/'features.npz', allow_pickle=False) as z:
            arrays = {k: z[k] for k in z.files}
        return arrays, read_json(p/'indices.json')

    def references(self, sid):
        rid = sid[:3]
        four, _ = self.pool(rid+'-s4')
        current, sets = self.pool(sid)
        h4 = np.flatnonzero((four['time_ps'] > 100) & four['valid'])
        hs = np.asarray(sets['candidate'], dtype=np.int64)
        h2 = h4[h4//4000 == 0]
        return {MODES[0]: hs, MODES[1]: h4, MODES[2]: h2,
                MODES[3]: hs if sid.endswith('s4') else matched_ids(hs, len(h4))}

    def audit(self):
        """全raw SHAと形・原子・選点・履歴の時間系譜を読取り専用で検査する。"""
        if (self.out/'input-audit.json').exists():
            raise RuntimeError('入力監査は既に存在します。成功監査を上書きしません。')
        self.gate('input_audit')
        rows = []
        for i, (relative, expected) in enumerate(self.expected.items()):
            p = self.run/relative
            if self.run not in p.resolve().parents or p.is_symlink() or not p.is_file():
                raise ValueError('raw入力の欠損または経路異常：'+relative)
            actual = sha(p)
            rows.append(dict(path=relative, expected_sha256=expected, actual_sha256=actual,
                             bytes=p.stat().st_size, matches=actual == expected))
            if actual != expected:
                write_table(self.out/'input-file-sha256.csv', rows)
                raise ValueError('raw SHA不一致：'+relative)
            if (i+1) % 1000 == 0:
                self.emit('input_SHA_progress', completed=i+1, expected=len(self.expected))
        write_table(self.out/'input-file-sha256.csv', rows)
        if len(self.matrix['roots']) != 8 or len(self.matrix['states']) != 16 or len(self.matrix['branches']) != 240:
            raise ValueError('固定行列が不完全です。')
        live = read_json(self.run/'manifest.json')
        if live['matrix_sha256'] != sha(self.bundle/'experiment-matrix.json'):
            raise ValueError('原バッチ行列のSHAが一致しません。')
        identities = None
        pools = []
        refs = []
        for state in self.matrix['states']:
            sid, rid = state['state_id'], state['root_id']
            a, sets = self.pool(sid)
            n = state['milestone_ns']*2000
            self.check_features(a, n)
            segments = [self.science(f'{rid}-h{i}-md-prep') for i in range(1, state['milestone_ns']//2+1)]
            for k in a:
                combined = np.concatenate([np.load(p/'features.npz', allow_pickle=False)[k] for p in segments])
                if not np.array_equal(a[k], combined):
                    raise ValueError('履歴区間とpoolが一致しません：'+sid+'/'+k)
            four, _ = self.pool(rid+'-s4')
            if not all(np.array_equal(a[k][:8000], four[k]) for k in a):
                raise ValueError('H4のprefix一致に失敗しました。')
            ids = np.asarray(sets['candidate'])
            expected_ids = np.flatnonzero((a['time_ps'] > 100) & a['valid'])
            if not np.array_equal(ids, expected_ids) or len(ids) != (7800 if sid.endswith('s4') else 15800):
                raise ValueError('候補ID/点数が一致しません。')
            frozen = read_json(self.run/'states'/(sid+'.json'))
            if sha(self.science(sid+'-decision-pool')/'features.npz') != frozen['pool_features_sha256']:
                raise ValueError('凍結pool SHA不一致。')
            if sha(self.science(sid+'-decision-pool')/'indices.json') != frozen['pool_indices_sha256']:
                raise ValueError('凍結ID SHA不一致。')
            published = read_json(self.science(sid+'-decision-pool').parent/'availability.json')['monotonic']
            features = read_json(self.science(sid+'-features')/'state-features.json')
            if not (published <= features['feature_start_monotonic'] <= features['feature_end_monotonic'] <= frozen['frozen_monotonic']):
                raise ValueError('凍結前公開の時刻順序が不正です。')
            selected = read_json(self.science(sid+'-selection')/'selected.json')
            for label in LABELS:
                row = selected[label]
                fid = row['frame_id']
                if fid not in set(ids.tolist()) or divmod(fid, 4000) != (row['segment'], row['local_frame']):
                    raise ValueError('選点のID系譜不一致。')
                ident = atom_identity(self.science(f"{rid}-h{row['segment']+1}-md")/'initial.pdb')
                if identities is None:
                    identities = ident
                if ident != identities:
                    raise ValueError('履歴原子順が変わっています。')
                selected_array = np.load(self.science(sid+'-selection')/(label+'.npy'), allow_pickle=False)
                mask = np.array([r[0] == 'CA' for r in ident])
                if not np.array_equal(selected_array[mask], a['ca'][fid]):
                    raise ValueError('選点座標とpool Cαの対応が不一致です。')
                if abs(row['time_ps']-a['time_ps'][fid]) > 1e-8:
                    raise ValueError('選点時刻が不一致です。')
            for mode, ii in self.references(sid).items():
                refs.append(dict(root_id=rid, state_id=sid, reference_mode=mode,
                                 IDs=ii.tolist(), IDs_sha256=array_sha(ii), points=len(ii),
                                 latest_time_ps=float(a['time_ps'][ii].max()),
                                 future_downstream_used=False))
            pools.append(dict(state_id=sid, candidate_points=len(ids), history_points=n,
                              prefix_H4_exact=True, publication_before_freeze=True))
        branch_rows = []
        for branch in self.matrix['branches']:
            bid, sid = branch['branch_id'], branch['state_id']
            label = 'F0' if branch['arm'] == 'F0' else branch['arm']+f"-t{branch['training_block']}"
            p = self.science(bid+'-md')
            if atom_identity(p/'initial.pdb') != identities:
                raise ValueError('下流原子順が一致しません。')
            if not np.array_equal(np.load(p/'initial-coordinates-A.npy', allow_pickle=False),
                                  np.load(self.science(sid+'-selection')/(label+'.npy'), allow_pickle=False)):
                raise ValueError('実MD投入座標が一致しません。')
            a = dict(np.load(self.science(bid+'-md-prep')/'features.npz', allow_pickle=False))
            self.check_features(a, 8000)
            req = read_json(p.parent/'request.json')
            freeze = read_json(self.run/'states'/(sid+'.json'))
            if req['state_freeze_sha256'] != sha(self.run/'states'/(sid+'.json')) or req['seed'] != branch['MD_seed']:
                raise ValueError('下流seed/凍結入力が不一致です。')
            if read_json(p.parent/'availability.json')['monotonic'] < freeze['frozen_monotonic']:
                raise ValueError('下流公開が凍結より前です。')
            branch_rows.append(dict(branch_id=bid, atom_order_exact=True, selected_coordinates_exact=True,
                                    frames=8000, finite=True, ordered=True))
        archives = read_json(self.art/'archives/archive-manifest.json')
        archive_rows = []
        for name, v in archives.items():
            p = self.art/'archives'/name
            expected = v['sha256']
            actual = sha(p)
            if actual != expected:
                raise ValueError('archive SHAが一致しません：'+name)
            archive_rows.append(dict(name=name, bytes=p.stat().st_size, sha256=actual, matches=True))
        write_table(self.out/'branch-input-audit.csv', branch_rows)
        dump(self.out/'reference-manifest.json', refs)
        dump(self.out/'input-audit.json', dict(status='PASS', raw_files=len(rows),
             roots=8, states=pools, branches=240, atom_order_atoms=504, C_alpha_atoms=28,
             archives=archive_rows, raw_modified=False, server_raw_retained=True))
        self.emit('input_audit_complete', files=len(rows), branches=240)

    def check_features(self, a, n):
        shapes = dict(ca=(n, 28, 3), distances_A=(n, 325), angles_rad=(n, 54),
                      valid=(n,), time_ps=(n,), rg_A=(n,), q=(n,))
        for key, shape in shapes.items():
            if a[key].shape != shape or not np.isfinite(a[key]).all():
                raise ValueError('特徴shape/有限性の不一致：'+key)
        if not np.all(np.diff(a['time_ps']) > 0):
            raise ValueError('フレームの時間順序が不正です。')
        # 保存座標から特徴を小区間で再照合し、原子対応の単位誤りを検出する。
        if not close_value(self.gq.descriptors(a['ca'][::1000]), a['distances_A'][::1000], atol=1e-12, rtol=1e-12):
            raise ValueError('Cαと距離特徴の対応が不一致です。')

    def metrics(self, a, ref_a, ids):
        """固定参照から元と同じ全窓・全尺度を計算する。"""
        dd, nn = self.gq.nearest(a['distances_A'], ref_a['distances_A'][ids], block=64)
        angular = self.gq.circular(a['angles_rad'], ref_a['angles_rad'][ids][nn])
        t, valid = a['time_ps'], a['valid']
        continuous, discrete, windows, ac = [], [], [], []
        for burn, prefix in itertools.product(BURNS, PREFIXES):
            mask = (t > burn) & (t <= prefix*1000+1e-5) & valid
            if not mask.any():
                raise ValueError('適格下流フレームがありません。')
            continuous.append(dict(burn_ps=burn, prefix_ns=prefix, frames=int(mask.sum()),
                distance_mean_A=float(dd[mask].mean()), distance_median_A=float(np.median(dd[mask])),
                distance_p90_A=float(np.quantile(dd[mask], .9)), Rg_mean_A=float(a['rg_A'][mask].mean()),
                Q8_mean=float(a['q'][mask].mean()), angle_to_geometric_neighbor_median_deg=float(np.median(angular[mask]))))
            ii = np.flatnonzero((t > burn) & (t <= prefix*1000+1e-5))[::4]
            for epsilon, tau in itertools.product((1.5, 2., 3.), (0, 5)):
                reps, conf = self.gq.regions(a['distances_A'][ii], t[ii], epsilon, tau,
                                           valid=valid[ii], history_min_distance=dd[ii])
                rr, cc = ii[reps], ii[conf]
                discrete.append(dict(burn_ps=burn, prefix_ns=prefix, epsilon_A=epsilon, tau_ps=tau,
                    added_regions=len(reps), representative_frame_ids=rr.tolist(), confirmation_frame_ids=cc.tolist(),
                    representative_time_ps=t[rr].tolist(), confirmation_time_ps=t[cc].tolist()))
        for lo in range(0, 4000, 100):
            mask = (t > lo) & (t <= lo+100+1e-5) & valid
            if mask.any():
                windows.append(dict(start_ps=lo, frames=int(mask.sum()), distance_mean_A=float(dd[mask].mean()),
                                     Rg_mean_A=float(a['rg_A'][mask].mean()), Q8_mean=float(a['q'][mask].mean())))
        for name, value in [('Rg', a['rg_A']), ('Q8', a['q']), ('distance', dd)]:
            for lag in (1, 4, 20, 200):
                mask = valid[:-lag] & valid[lag:] & (t[:-lag] > 100)
                ac.append(dict(observable=name, lag_ps=lag*.5, eligible_pairs=int(mask.sum()),
                               correlation=correlation(value[:-lag][mask], value[lag:][mask])))
        return dict(continuous=continuous, discrete=discrete, windows=windows, autocorrelation=ac), dd, nn

    def result_path(self, bid, mode):
        return self.out/'branches'/bid/(mode+'.json')

    def read_result(self, bid, mode):
        r = read_json(self.result_path(bid, mode))
        if 'alias' in r:
            return read_json(self.result_path(bid, r['alias']))
        return r

    def evaluate(self, branch, mode):
        """成功した新出力を上書きせず、元再現が通るまで追加参照を禁止する。"""
        bid, sid = branch['branch_id'], branch['state_id']
        target = self.result_path(bid, mode)
        if target.exists():
            return
        self.gate(mode+'/'+bid)
        arrays, _ = self.pool(sid)
        ids = self.references(sid)[mode]
        original_ids = self.references(sid)[MODES[0]]
        start, cpu = time.perf_counter(), time.process_time()
        if mode != MODES[0] and np.array_equal(ids, original_ids):
            if not self.result_path(bid, MODES[0]).exists():
                raise ValueError('元再現が未完了です。')
            dump(target, dict(alias=MODES[0], reason='同一参照ID・同一軌道'))
            self.emit('branch_alias', branch=bid, reference_mode=mode)
            return
        a = dict(np.load(self.science(bid+'-md-prep')/'features.npz', allow_pickle=False))
        result, dd, nn = self.metrics(a, arrays, ids)
        if mode == MODES[0]:
            old = self.science(bid+'-analysis')
            for label, filename in [('continuous', 'continuous.json'), ('discrete', 'discrete.json')]:
                expected = read_json(old/filename)
                if len(expected) != len(result[label]):
                    raise ValueError('原結果の件数が不一致です。')
                for got, wanted in zip(result[label], expected):
                    for key, val in wanted.items():
                        equal = (got[key] == val) if key.endswith('_ids') or isinstance(val, int) else close_value(got[key], val)
                        if not equal:
                            dump(self.out/'reproduction-failure.json', dict(branch=bid, table=label, column=key,
                                 actual=got[key], expected=val))
                            raise ValueError('ORIGINAL_HISTORY再現失敗：'+bid+'/'+key)
            with np.load(old/'distances.npz') as z:
                if not close_value(dd, z['d_min_A']) or not np.array_equal(nn, z['nearest_A0_id']):
                    raise ValueError('原最小距離/最近傍IDが不一致です。')
            with (old/'time-windows.csv').open() as f:
                old_windows = list(csv.DictReader(f))
            for got, expected in zip(result['windows'], old_windows):
                if any(not close_value(got[k], float(v)) for k, v in expected.items()):
                    raise ValueError('原100ps窓が不一致です。')
            for got, expected in zip(result['autocorrelation'], read_json(old/'autocorrelation.json')):
                if expected['correlation'] is None:
                    same = got['correlation'] is None
                else:
                    same = close_value(got['correlation'], expected['correlation'])
                if not same or got['eligible_pairs'] != expected['eligible_pairs']:
                    raise ValueError('原相関診断が不一致です。')
            result['original_reproduction'] = 'PASS'
        else:
            original = self.read_result(bid, MODES[0])
            for got, expected in zip(result['continuous'], original['continuous']):
                if any(got[k] != expected[k] for k in ('Rg_mean_A', 'Q8_mean', 'frames')):
                    raise ValueError('参照不変対照が変化しています。')
            if mode == 'COMMON_A4' and sid.endswith('s8'):
                old_dist = np.load(self.out/'distances'/bid/(MODES[0]+'.npz'))['d_min_A']
                if np.any(old_dist > dd+1e-10):
                    raise ValueError('入れ子参照の単調性が破れています。')
        distance_path = self.out/'distances'/bid/(mode+'.npz')
        distance_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(distance_path, d_min_A=dd, nearest_reference_frame_id=ids[nn],
                            reference_frame_ids=ids, time_ps=a['time_ps'], valid=a['valid'])
        result['reference_IDs_sha256'] = array_sha(ids)
        result['cost'] = dict(wall_s=time.perf_counter()-start, CPU_s=time.process_time()-cpu,
                              peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        dump(target, result)
        self.emit('branch_complete', branch=bid, reference_mode=mode, **result['cost'])

    def original(self):
        if read_json(self.out/'input-audit.json')['status'] != 'PASS':
            raise ValueError('入力監査が未完了です。')
        first = self.matrix['branches'][0]
        self.evaluate(first, MODES[0])
        wall = self.read_result(first['branch_id'], MODES[0])['cost']['wall_s']
        projected = wall*720+3600
        dump(self.out/'cost-checkpoint.json', dict(first_branch=first['branch_id'], wall_s=wall,
             estimated_total_scientific_CPU_wall_s=projected, estimate_not_measurement=True,
             rule='720実参照評価＋補助60分という保守的投影', continue_within_6h=projected <= 21600))
        if projected > 21600:
            raise RuntimeError('最初の枝の投影が6時間を超えます。再審査が必要です。')
        for branch in self.matrix['branches'][1:]:
            self.evaluate(branch, MODES[0])
        dump(self.out/'original-reproduction.json', dict(status='PASS', branches=240,
             continuous_rows=2880, discrete_rows=17280, all_scales=True, nearest_ID_exact=True))

    def remaining_references(self):
        if read_json(self.out/'original-reproduction.json')['status'] != 'PASS':
            raise ValueError('全ORIGINAL_HISTORY再現を先に完了してください。')
        for branch in self.matrix['branches']:
            for mode in MODES[1:]:
                self.evaluate(branch, mode)

    def selection_diagnostics(self):
        """保存embeddingだけでLOFを診断する。新しい選点の下流Yを作らない。"""
        from sklearn.neighbors import LocalOutlierFactor
        self.gate('LOF')
        origin_rows, diagnostics, full_checks = [], [], []
        started, cpu = time.perf_counter(), time.process_time()
        for state in self.matrix['states']:
            sid, rid = state['state_id'], state['root_id']
            self.gate('LOF/'+sid)
            a, sets = self.pool(sid)
            candidates = np.asarray(sets['candidate'], dtype=np.int64)
            four_ids = self.references(sid)['COMMON_A4']
            selected = read_json(self.science(sid+'-selection')/'selected.json')
            repeated = dict(np.load(self.science(sid+'-infer-F0-repeat')/'ranking.npz', allow_pickle=False))
            for label in LABELS:
                path = self.science(sid+'-infer-'+label)/'ranking.npz'
                ranking = dict(np.load(path, allow_pickle=False))
                ids, embedding, scores = ranking['frame_ids'], ranking['embedding'], ranking['lof']
                if not np.array_equal(ids, candidates) or not np.array_equal(np.lexsort((ids, scores)), ranking['order']):
                    raise ValueError('保存候補ID/順位が不一致です。')
                if label == 'F0' and any(not np.array_equal(ranking[k], repeated[k]) for k in ranking):
                    raise ValueError('保存F0-repeatが一致しません。')
                full = LocalOutlierFactor(n_neighbors=20, metric='minkowski', p=2,
                                          novelty=False, n_jobs=1).fit(embedding)
                recalculated = full.negative_outlier_factor_
                order = np.lexsort((ids, recalculated))
                equal = close_value(recalculated, scores, atol=1e-10, rtol=1e-10)
                rank_equal = np.array_equal(order, ranking['order'])
                full_checks.append(dict(state_id=sid, label=label,
                    score_max_absolute_error=float(np.max(np.abs(recalculated-scores))),
                    score_within_tolerance=equal, full_order_exact=rank_equal,
                    original_dtype=str(embedding.dtype), score_dtype=str(scores.dtype)))
                if not equal or not rank_equal:
                    dump(self.out/'LOF-reproduction-failure.json', full_checks[-1])
                    raise ValueError('FULL LOFの再現が不一致です：'+sid+'/'+label)
                original_id = int(ids[order[0]])
                if original_id != selected[label]['frame_id']:
                    raise ValueError('Top1と元選点JSONが不一致です。')
                one = a['distances_A'][original_id:original_id+1]
                d4 = float(self.gq.nearest(one, a['distances_A'][four_ids])[0][0])
                ds = float(self.gq.nearest(one, a['distances_A'][candidates])[0][0])
                origin = dict(root_id=rid, state_id=sid, milestone_ns=state['milestone_ns'],
                    label=label, frame_id=original_id, time_ps=float(a['time_ps'][original_id]),
                    segment=int(original_id//4000), local_frame=int(original_id % 4000),
                    source_interval_ns=f'{2*(original_id//4000)}-{2*(original_id//4000)+2}',
                    in_P4=original_id in set(four_ids.tolist()),
                    in_old800=original_id in set(sets['old']),
                    in_retained_old400=original_id in set(sets['old'][::2]),
                    in_new400=original_id in set(sets['new']),
                    in_validation200=original_id in set(sets['validation']),
                    candidate_count=len(ids), selected_m_H4_A=d4, selected_m_Hs_A=ds,
                    checkpoint_sha256=selected[label]['checkpoint_sha256'],
                    selected_coordinates_sha256=selected[label]['selected_sha256'],
                    downstream_status='OBSERVED_ORIGINAL_ONLY')
                origin_rows.append(origin)
                pools = {'FULL': ids}
                if state['milestone_ns'] == 8:
                    pools.update(PREFIX4=four_ids, COUNT_MATCH=matched_ids(ids, len(four_ids)))
                for pool_mode, subset_ids in pools.items():
                    keep = np.flatnonzero(np.isin(ids, subset_ids))
                    if not np.array_equal(ids[keep], subset_ids):
                        raise ValueError('subsetのID順序が一致しません。')
                    if pool_mode == 'FULL':
                        variants = [('FULL_REFIT', recalculated)]
                    else:
                        variants = [('FIXED_FULL_SCORE', scores[keep])]
                        fit = LocalOutlierFactor(n_neighbors=20, metric='minkowski', p=2,
                                                novelty=False, n_jobs=1).fit(embedding[keep])
                        variants.append(('SUBSET_REFIT', fit.negative_outlier_factor_))
                    for scoring, subscore in variants:
                        sorted_positions = np.lexsort((ids[keep], subscore))
                        ranked_ids = ids[keep][sorted_positions]
                        top = int(ranked_ids[0])
                        original_retained = original_id in set(subset_ids.tolist())
                        full_restricted = scores[keep]
                        rho = float(spearmanr(full_restricted, subscore).statistic)
                        if not np.isfinite(rho):
                            rho = None
                        sorted_full = ids[keep][np.lexsort((ids[keep], full_restricted))]
                        row = dict(root_id=rid, state_id=sid, milestone_ns=state['milestone_ns'],
                            label=label, pool_mode=pool_mode, scoring_mode=scoring, candidate_count=len(keep),
                            checkpoint_sha256=selected[label]['checkpoint_sha256'],
                            embedding_sha256=array_sha(embedding), ranking_file_sha256=sha(path),
                            candidate_ids_sha256=array_sha(ids[keep]), selected_frame_id=top,
                            selected_time_ps=float(a['time_ps'][top]), original_selected_frame_id=original_id,
                            original_selected_retained=original_retained, selected_same_as_original=top == original_id,
                            top10=json.dumps(ranked_ids[:10].tolist()), top100=json.dumps(ranked_ids[:100].tolist()),
                            restricted_score_rank_spearman=rho,
                            top10_overlap_fixed_score=len(set(ranked_ids[:10]) & set(sorted_full[:10])),
                            top100_overlap_fixed_score=len(set(ranked_ids[:100]) & set(sorted_full[:100])),
                            selected_structure_change_dRMSD_A=float(self.gq.distances(a['distances_A'][top], one)[0, 0]),
                            selected_structure_change_angle_deg=float(self.gq.circular(a['angles_rad'][top], a['angles_rad'][original_id])),
                            downstream_status='OBSERVED_ORIGINAL_ONLY' if top == original_id else 'NOT_OBSERVED')
                        diagnostics.append(row)
            self.emit('LOF_state_complete', state=sid)
        write_table(self.out/'selected-origins.csv', origin_rows)
        write_table(self.out/'pool-selection-diagnostic.csv', diagnostics)
        write_table(self.out/'LOF-full-reproduction.csv', full_checks)
        if len(origin_rows) != 80 or len(diagnostics) != 240 or len(full_checks) != 80:
            raise ValueError('候補診断の予定件数が不一致です。')
        dump(self.out/'LOF-audit.json', dict(status='PASS', full_fits=80, subset_fits=80,
             diagnostic_rows=len(diagnostics), original_selections=80, original_repeats_checked=16,
             CPU_s=time.process_time()-cpu, wall_s=time.perf_counter()-started,
             no_model_inference=True, no_counterfactual_MD_outcome_imputed=True))

    def summarize(self):
        """全尺度の同根比較と参照寄与を保存し、X予測器を作らない。"""
        self.gate('summary')
        keys = metric_keys()
        outcomes, all_cont, all_disc, all_windows, all_ac, cost_rows = {}, [], [], [], [], []
        for mode, b in itertools.product(MODES, self.matrix['branches']):
            result = self.read_result(b['branch_id'], mode)
            spec = dict(reference_mode=mode, **b)
            for r in result['continuous']:
                all_cont.append(dict(**spec, **r))
                for metric in CONT:
                    key = (r['burn_ps'], r['prefix_ns'], metric, None, None)
                    outcomes[(mode, b['state_id'], b['arm'], b['training_block'], b['MD_block'], key)] = r[metric]
            for r in result['discrete']:
                all_disc.append(dict(**spec, **{k: v for k, v in r.items() if not isinstance(v, list)}))
                key = (r['burn_ps'], r['prefix_ns'], 'added_regions', r['epsilon_A'], r['tau_ps'])
                outcomes[(mode, b['state_id'], b['arm'], b['training_block'], b['MD_block'], key)] = r['added_regions']
            all_windows.extend(dict(**spec, **r) for r in result['windows'])
            all_ac.extend(dict(**spec, **r) for r in result['autocorrelation'])
            logical = read_json(self.result_path(b['branch_id'], mode))
            if 'alias' not in logical:
                cost_rows.append(dict(reference_mode=mode, branch_id=b['branch_id'], **result['cost']))
        write_table(self.out/'continuous.csv', all_cont)
        write_table(self.out/'discrete-counts.csv', all_disc)
        write_table(self.out/'time-windows.csv', all_windows)
        write_table(self.out/'autocorrelation.csv', all_ac)
        write_table(self.out/'evaluation-costs.csv', cost_rows)
        paired, states, random_rows = [], [], []
        state_lookup = {}
        for mode, state, key in itertools.product(MODES, self.matrix['states'], keys):
            sid, rid = state['state_id'], state['root_id']
            spec = dict(reference_mode=mode, root_id=rid, state_id=sid,
                        milestone_ns=state['milestone_ns'], **key_spec(key))
            def value(arm, t, m):
                return outcomes[(mode, sid, arm, 0 if arm == 'F0' else t, m, key)]
            for high, low in COMPS:
                cells = []
                for t, m in itertools.product((1, 2), (1, 2, 3)):
                    hv, lv = value(high, t, m), value(low, t, m)
                    cells.append(hv-lv)
                    paired.append(dict(**spec, comparison=high+'-'+low, training_block=t, MD_block=m,
                                       high=hv, low=lv, difference=hv-lv,
                                       shared_F0_branch_id=f'{sid}-F0-t0-m{m}' if low == 'F0' else None))
                avg = float(np.mean(cells))
                states.append(dict(**spec, comparison=high+'-'+low, mean_difference=avg,
                                   complete_pairs=6, shared_F0_unique_observations=3 if low == 'F0' else 0))
                state_lookup[(mode, rid, state['milestone_ns'], high+'-'+low, key)] = avg
            for quantity in ('F1', 'F2', 'paired_F2-F1'):
                vals = [value('F2', t, m)-value('F1', t, m) if quantity == 'paired_F2-F1'
                        else value(quantity, t, m) for t, m in itertools.product((1, 2), (1, 2, 3))]
                random_rows.append(dict(**spec, quantity=quantity, **randomness(vals)))
            f0 = [value('F0', 0, m) for m in (1, 2, 3)]
            random_rows.append(dict(**spec, quantity='F0', mean=float(np.mean(f0)),
                                    MD_SD=float(np.std(f0, ddof=1)), unique_observations=3))
        draws = np.random.default_rng(1604000001).integers(0, 8, (10000, 8))
        dump(self.out/'bootstrap-design.json', dict(seed=1604000001, draws=10000, units=8,
             resampling_indices_sha256=array_sha(draws), same_draws_for_all_results=True,
             lower_level_resampled=False, independent_frames_used=False))
        root_rows, summary = [], []
        for mode, (high, low), key in itertools.product(MODES, COMPS, keys):
            comp = high+'-'+low
            vectors = {k: [] for k in ('S4', 'S8', 'ROOT_MEAN', 'STAGE_DIFFERENCE')}
            for rid in ROOTS:
                four = state_lookup[(mode, rid, 4, comp, key)]
                eight = state_lookup[(mode, rid, 8, comp, key)]
                root_rows.append(dict(reference_mode=mode, root_id=rid, comparison=comp, **key_spec(key),
                                      S4=four, S8=eight, root_mean=(four+eight)/2, S8_minus_S4=eight-four))
                for name, val in zip(vectors, (four, eight, (four+eight)/2, eight-four)):
                    vectors[name].append(val)
            for scope, vector in vectors.items():
                summary.append(dict(reference_mode=mode, comparison=comp, **key_spec(key),
                                    estimand=scope, **root_statistics(vector, draws)))
        decomposition, decomposition_summary = [], []
        for (high, low), key in itertools.product(COMPS, keys):
            comp = high+'-'+low
            vectors = {k: [] for k in ('Gamma_original', 'Gamma_common_A4', 'reference_contribution')}
            for rid in ROOTS:
                def d(mode, stage):
                    return state_lookup[(mode, rid, stage, comp, key)]
                gn = d(MODES[0], 8)-d(MODES[0], 4)
                gc = d(MODES[1], 8)-d(MODES[1], 4)
                contribution = d(MODES[0], 8)-d(MODES[1], 8)
                if not close_value(gn-gc, contribution, atol=1e-12, rtol=1e-12):
                    raise ValueError('参照寄与の恒等式が一致しません。')
                decomposition.append(dict(root_id=rid, comparison=comp, **key_spec(key),
                    Gamma_original=gn, Gamma_common_A4=gc, reference_contribution=contribution,
                    identity_residual=(gn-gc)-contribution))
                for name, val in zip(vectors, (gn, gc, contribution)):
                    vectors[name].append(val)
            for name, vector in vectors.items():
                decomposition_summary.append(dict(comparison=comp, **key_spec(key), estimand=name,
                                                   **root_statistics(vector, draws)))
        # 元の公開集計も再現し、共有F0と根集計の実装誤りを検出する。
        expected = read_json(self.bundle/'root-summary-expected.json')
        for got, old in zip([r for r in summary if r['reference_mode'] == MODES[0] and r['estimand'] == 'ROOT_MEAN'], expected):
            for k in ('mean', 'median', 'minimum', 'maximum', 'root_SD', 'bootstrap95_low', 'bootstrap95_high'):
                if not close_value(got[k], float(old[k])):
                    raise ValueError('元の根集計が不一致です：'+k)
        write_table(self.out/'paired-effects.csv', paired)
        write_table(self.out/'state-effects.csv', states)
        write_table(self.out/'root-stage-effects.csv', root_rows)
        write_table(self.out/'root-summary.csv', summary)
        write_table(self.out/'reference-decomposition.csv', decomposition)
        write_table(self.out/'reference-decomposition-summary.csv', decomposition_summary)
        dump(self.out/'randomness-decomposition.json', random_rows)
        counts = dict(continuous=len(all_cont), discrete=len(all_disc), paired=len(paired),
                      states=len(states), root_stage=len(root_rows), summary=len(summary),
                      reference_decomposition=len(decomposition), randomness=len(random_rows))
        expected_counts = dict(continuous=11520, discrete=69120, paired=165888,
                               states=27648, root_stage=13824, summary=6912,
                               reference_decomposition=3456, randomness=36864)
        if counts != expected_counts:
            raise ValueError('全条件の予定件数が不一致です。')
        dump(self.out/'result-audit.json', dict(status='PASS', counts=counts,
             all_preregistered_metrics=True, all_roots=True, original_root_summary='PASS',
             shared_F0_preserved=True, reference_identity='PASS', missing=0,
             independent_scientific_review='PENDING', researcher_acceptance='PENDING'))
        self.emit('summary_complete', **counts)

    def finish(self):
        """元入力を再照合し、新出力のSHA索引と実費用を確定する。"""
        self.gate('final_integrity')
        for relative, expected in self.expected.items():
            if sha(self.run/relative) != expected:
                raise ValueError('処理後の原入力SHAが変化しました：'+relative)
        for row in read_json(self.out/'input-audit.json')['archives']:
            if sha(self.art/'archives'/row['name']) != row['sha256']:
                raise ValueError('原archiveの処理後SHAが不一致です。')
        dump(self.out/'final-integrity.json', dict(status='PASS', raw_files=len(self.expected),
             raw_SHA_unchanged=True, archive_SHA_unchanged=True, archive_count=9,
             raw_transfer_to_Mac=False, GPU_jobs=0, MD_jobs=0, training_jobs=0, model_inference_jobs=0))
        import scipy, sklearn
        dump(self.out/'environment.json', dict(python=sys.version, numpy=np.__version__,
             scipy=scipy.__version__, sklearn=sklearn.__version__, platform=platform.platform(),
             GPU_visible=False, torch_imported='torch' in sys.modules,
             OpenMM_imported='openmm' in sys.modules, numeric_threads=1, worker_count=1,
             thread_environment={k: os.environ.get(k) for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}))
        dump(self.out/'costs.json', dict(session_wall_s=time.perf_counter()-self.started,
             session_CPU_s=time.process_time()-self.cpu_started,
             peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
             GPU_s=0, counterfactual_MD_cost_measured=False))
        dump(self.out/'status.json', dict(status='COMPLETE', independent_scientific_review='PENDING',
             original_branches=240, logical_branch_reference_conditions=960,
             new_MD=0, training=0, model_inference=0, B2_C_S3='NOT_APPROVED'))
        hashes = {str(p.relative_to(self.out)): sha(p) for p in sorted(self.out.rglob('*'))
                  if p.is_file() and p.name not in ('output-sha256.json', 'run.lock', 'events.jsonl')}
        dump(self.out/'output-sha256.json', hashes)
        self.emit('review_complete')


def main():
    """段階を明示して起動し、失敗時には証拠を保全する。"""
    p = argparse.ArgumentParser(description='承認されたB1-R1 CPU復核')
    p.add_argument('--project', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--bundle', required=True)
    p.add_argument('--stage', choices=('audit', 'original', 'references', 'lof', 'summary', 'finish', 'all'), required=True)
    args = p.parse_args()
    review = None
    try:
        review = Review(args.project, args.output, args.bundle)
        stages = ('audit', 'original', 'references', 'lof', 'summary', 'finish') if args.stage == 'all' else (args.stage,)
        functions = dict(audit=review.audit, original=review.original,
                         references=review.remaining_references, lof=review.selection_diagnostics,
                         summary=review.summarize, finish=review.finish)
        for stage in stages:
            review.emit('stage_started', stage=stage)
            start, cpu = time.perf_counter(), time.process_time()
            functions[stage]()
            review.emit('stage_complete', stage=stage, wall_s=time.perf_counter()-start,
                        CPU_s=time.process_time()-cpu)
    except Exception as exc:
        if review is not None:
            failure = dict(status='STOPPED', stage=args.stage, error_type=type(exc).__name__,
                           reason=str(exc), UTC=dt.datetime.now(dt.timezone.utc).isoformat(),
                           no_raw_correction=True, no_new_scientific_conditions=True,
                           session_wall_s=time.perf_counter()-review.started,
                           session_CPU_s=time.process_time()-review.cpu_started)
            dump(review.out/('failure-'+str(time.time_ns())+'.json'), failure)
            dump(review.out/'status.json', failure)
            review.emit('stopped', error_type=type(exc).__name__, reason=str(exc))
        traceback.print_exc()
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
