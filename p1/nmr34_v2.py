"""NMR34 v2の独立CPU adapter。実データ実行には別途承認・入力凍結が必要。"""
import os
for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import contextlib
import csv
import fcntl
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from n1_native_metrics import native_contact_mask, proper_rmsd


def require(condition, message):
    """最適化実行でも省略されない入力・数値検査。"""
    if not condition:
        raise ValueError(message)


def sha256(path):
    """読み取り専用のbyte SHA。"""
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify_inputs(expected):
    """指定された全入力のSHAを照合する。"""
    actual = {str(p): sha256(p) for p in expected}
    require(actual == {str(p): h for p, h in expected.items()}, '入力SHA不一致')
    return actual


def save_json(path, value):
    """既存証拠を上書きしない。"""
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


class Timer:
    """重複しないwall/process CPU区間を記録する。"""
    def __init__(self):
        self.records = {}
        self.active = False

    @contextlib.contextmanager
    def measure(self, name):
        require(not self.active, '計時区間の重複')
        self.active = True
        start, cpu = time.monotonic(), time.process_time()
        try:
            yield
        finally:
            row = self.records.setdefault(name, {'wall_s': 0., 'CPU_s': 0., 'calls': 0})
            row['wall_s'] += time.monotonic() - start
            row['CPU_s'] += time.process_time() - cpu
            row['calls'] += 1
            self.active = False


class Run:
    """排他lock、再実行拒否、不変receiptと協調的資源停止。"""
    def __init__(self, output, fingerprint, check=lambda: None):
        self.output, self.fingerprint, self.check = Path(output), fingerprint, check

    def __enter__(self):
        self.output.mkdir(parents=True, exist_ok=True)
        self.lock = (self.output / 'run.lock').open('a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            require(not (self.output / 'start.json').exists(), '既存実行は再利用しない')
            self.check()
            save_json(self.output / 'start.json', {'fingerprint': self.fingerprint})
        except BaseException:
            self.lock.close()
            raise
        return self

    def __exit__(self, kind, value, tb):
        try:
            save_json(self.output / ('failure.json' if kind else 'success.json'),
                      {'status': 'STOPPED' if kind else 'PASS',
                       'fingerprint': self.fingerprint, 'error': str(value) if kind else None})
        finally:
            self.lock.close()


class References:
    """対応済みÅ座標と固定native maskを一度だけ構築する。"""
    def __init__(self, coordinates):
        self.native = np.array(coordinates, dtype=np.float64, copy=True)
        require(self.native.ndim == 3 and self.native.shape[1:] == (28, 3)
                and len(self.native) == 34 and np.isfinite(self.native).all(), '参照座標不正')
        self.centered = self.native - self.native.mean(axis=1, keepdims=True)
        self.masks = np.array([native_contact_mask(x) for x in self.native])
        self.den = self.masks.sum(axis=(1, 2))
        self.integer_masks = self.masks.astype(np.int16)
        self.eligible = np.triu(np.ones((28, 28), dtype=bool), 3)
        for value in (self.native, self.centered, self.masks, self.den, self.integer_masks):
            value.flags.writeable = False

    def rmsd(self, coordinates):
        """全参照のproper Kabsch。float64と直接残差を維持する。"""
        x = np.asarray(coordinates, dtype=np.float64)
        require(x.ndim == 3 and x.shape[1:] == (28, 3) and np.isfinite(x).all(), '入力座標不正')
        x = x - x.mean(axis=1, keepdims=True)
        u, _, vt = np.linalg.svd(np.einsum('bni,knj->bkij', x, self.centered))
        u[:, :, :, -1] *= np.where(np.linalg.det(u @ vt) >= 0, 1., -1.)[:, :, None]
        residual = np.einsum('bni,bkij->bknj', x, u @ vt) - self.centered[None]
        return np.sqrt(np.mean(np.sum(residual * residual, axis=-1), axis=-1))

    def contacts(self, coordinates):
        """固定分母のQと8Åからの符号付きmargin [Å]。"""
        x = np.asarray(coordinates, dtype=np.float64)
        distances = np.linalg.norm(x[:, :, None] - x[:, None, :], axis=-1)
        count = np.einsum('bij,kij->bk', (distances < 8.).astype(np.int16), self.integer_masks)
        return count, count / self.den, distances - 8.


def ensemble(rmsd, q):
    """同じRMSD argminの参照Qを選ぶ。同値は小番号優先。"""
    require(rmsd.shape == q.shape and rmsd.ndim == 2 and rmsd.shape[1] > 0
            and np.isfinite(rmsd).all() and np.isfinite(q).all(), 'ensemble入力不正')
    arg = rmsd.argmin(axis=1)
    row = np.arange(len(arg))
    return rmsd[row, arg], arg + 1, q[row, arg]


def window_ids(local_time_ps, valid, burn_ps, prefix_ns, sampling_ps):
    """旧時刻比較→窓内stride→品質の順序と位相を保存する。"""
    t, valid = np.asarray(local_time_ps), np.asarray(valid)
    require(t.ndim == 1 and valid.shape == t.shape and valid.dtype == np.bool_
            and np.isfinite(t).all() and np.all(np.diff(t) > 0), '時刻/品質不正')
    require(sampling_ps in (.5, 2.), '未登録sampling')
    sampled = np.flatnonzero((t > burn_ps) & (t <= prefix_ns * 1000 + 1e-5))[::int(sampling_ps / .5)]
    return sampled, sampled[valid[sampled]]


def load_ca_once(features_npz, maximum_bytes):
    """圧縮NPZのCAを一度だけ解凍。zipヘッダで事前容量を制限する。"""
    import zipfile
    with zipfile.ZipFile(features_npz) as archive:
        require(archive.getinfo('ca.npy').file_size <= maximum_bytes, 'CA容量の事前上限超過')
    with np.load(features_npz, allow_pickle=False) as z:
        ca = z['ca']
    require(ca.ndim == 3 and ca.shape[1:] == (28, 3) and np.isfinite(ca).all(), 'CA配列不正')
    return ca


def dcd_chunks(topology, dcd, expected_ca, atom_keys, chunk_size=512):
    """将来の承認用reader。実行時のみMDAnalysisをimportする。"""
    import MDAnalysis as mda
    require(1 <= chunk_size <= 512, 'chunk上限超過')
    universe = mda.Universe(str(topology), str(dcd), convert_units=True)
    with universe.trajectory as trajectory:
        # Universeを保持し、選択の対応キーを外部で凍結したものと照合する。
        ca = universe.select_atoms('name CA')
        keys = [tuple(str(v).strip() for v in (a.chainID, a.resid, a.icode, a.resname, a.altLoc)) for a in ca]
        require(keys == atom_keys and len(trajectory) == len(expected_ca), 'CA対応/frame数不一致')
        block, times = [], []
        for i, ts in enumerate(trajectory):
            x = ca.positions.copy().astype(np.float64)
            require(ts.frame == i and np.array_equal(x, expected_ca[i]), 'DCD座標/順序不一致')
            block.append(x); times.append(float(ts.time))
            if len(block) == chunk_size or i == len(expected_ca) - 1:
                yield np.array(block), np.array(times)
                block, times = [], []


def evaluate_chunks(chunks, references, output, qualify=False, margin_A=1e-6,
                    check=lambda: None):
    """上限512点の独立圧縮chunkを保存。実DCD入口の自動呼出しは持たない。"""
    output = Path(output)
    require(output.is_dir() and np.isfinite(margin_A) and margin_A >= 0, '出力/診断幅不正')
    timer, manifest, offset = Timer(), [], 0
    scalar_error = 0.
    iterator = iter(chunks)
    while True:
        check()
        with timer.measure('read_and_coordinate_validation'):
            item = next(iterator, None)
        if item is None:
            break
        x, times = item
        require(0 < len(x) <= 512 and np.asarray(times).shape == (len(x),), 'chunk形式不正')
        with timer.measure('Kabsch'):
            r = references.rmsd(x)
        with timer.measure('Q_and_margin'):
            count, q, margin = references.contacts(x)
            near = np.argwhere((abs(margin) <= margin_A) & references.eligible[None])
            # 全eligible pairが対象。native所属は固定maskから再構成できる。
            near_margin = margin[tuple(near.T)] if len(near) else np.empty(0)
        with timer.measure('scalar_qualification'):
            if qualify:
                scalar = np.array([[proper_rmsd(v, ref) for ref in references.native] for v in x])
                scalar_error = max(scalar_error, float(np.max(abs(r - scalar))))
                require(scalar_error <= 1e-8, 'scalar/chunk不一致')
        with timer.measure('ensemble_and_validation'):
            minimum, arg, same_q = ensemble(r, q)
            require(np.isfinite(q).all() and ((q >= 0) & (q <= 1)).all(), 'Q範囲不正')
        check()
        path = output / f'chunk-{offset:09d}.npz'
        with timer.measure('compression_save'):
            with path.open('xb') as stream:
                np.savez_compressed(stream, RMSD_A=r, Q=q, contact_count=count,
                    ensemble_min_RMSD_A=minimum, argmin_model=arg,
                    Q_at_RMSD_argmin=same_q, M1_minus_min_A=r[:, 0]-minimum,
                    frame_id=np.arange(offset, offset+len(x)), dcd_time_ps=times,
                    near_pair=near, near_margin_A=near_margin)
        with timer.measure('output_SHA'):
            manifest.append({'path': path.name, 'start': offset, 'frames': len(x), 'sha256': sha256(path)})
        offset += len(x)
    require(offset > 0, '入力frameなし')
    save_json(output / 'chunks.json', {'chunks': manifest, 'frames': offset,
              'qualify': qualify, 'scalar_max_error_A': scalar_error if qualify else None,
              'near_margin_A': margin_A, 'timing': timer.records})
    return manifest, timer


def summarize(output, manifest, local_time_ps, valid, windows, timer, window_status=None):
    """列ごとにchunkを読み、exact quantileを保つ。全R/Q行列を複製しない。"""
    output = Path(output)
    with timer.measure('window_ID'):
        ids = {}
        for burn, prefix, sampling in windows:
            sampled, eligible = window_ids(local_time_ps, valid, burn, prefix, sampling)
            ids[f'{burn}_{prefix}_{sampling}'] = {'sampled': sampled.tolist(), 'valid': eligible.tolist()}
        save_json(output / 'window-ids.json', ids)
    rows = []
    # 最大1軌跡×2列。長さ上限は将来の実行カードで固定する。
    for model in range(1, 36):
        rparts, qparts = [], []
        with timer.measure('window_chunk_read'):
            for item in manifest:
                with np.load(output/item['path'], allow_pickle=False) as z:
                    rparts.append((z['ensemble_min_RMSD_A'] if model == 35 else z['RMSD_A'][:, model-1]).copy())
                    qparts.append((z['Q_at_RMSD_argmin'] if model == 35 else z['Q'][:, model-1]).copy())
        with timer.measure('window_aggregation'):
            r, q = np.concatenate(rparts), np.concatenate(qparts)
            require(len(r) == len(local_time_ps), 'frame/窓時刻数不一致')
            for key, selected in ids.items():
                ii = np.asarray(selected['valid'], dtype=int)
                row = {'model': 'NMR34_MIN' if model == 35 else model, 'window': key,
                       'total': len(selected['sampled']), 'valid': len(ii),
                       'window_status': (window_status or {}).get(key, 'UNVERIFIED_WINDOW_STATUS')}
                if len(ii):
                    rr, qq = r[ii], q[ii]; arg = ii[rr.argmin()]
                    row.update(min_RMSD_A=float(rr.min()), mean_RMSD_A=float(rr.mean()),
                        median_RMSD_A=float(np.median(rr)), p10_RMSD_A=float(np.quantile(rr,.1)),
                        final_RMSD_A=float(rr[-1]), mean_Q=float(qq.mean()), median_Q=float(np.median(qq)),
                        max_Q=float(qq.max()), Q_at_argmin=float(q[arg]), argmin_frame=int(arg))
                else:
                    row['status'] = 'NO_VALID_FRAMES'
                rows.append(row)
    with timer.measure('summary_save'):
        save_json(output/'windows.json', rows)
    return rows


def archive_metadata(output, frame_id, global_frame_id, time_ps, local_time_ps, valid, reasons):
    """原ID/品質/時刻を独立保存する。実軌跡との照合は将来資格の必須門。"""
    arrays = [np.asarray(x) for x in (frame_id, global_frame_id, time_ps, local_time_ps, valid)]
    n = len(arrays[0])
    require(all(x.shape == (n,) for x in arrays) and np.array_equal(arrays[0], np.arange(n)), 'ID対応不正')
    require(arrays[4].dtype == np.bool_ and np.asarray(reasons).shape[0] == n
            and np.array_equal(arrays[4], ~np.asarray(reasons, dtype=bool).any(axis=1)), '品質対応不正')
    require(np.isfinite(arrays[2]).all() and np.isfinite(arrays[3]).all()
            and np.all(np.diff(arrays[2]) > 0) and np.all(np.diff(arrays[3]) > 0), '保存時刻不正')
    with (Path(output)/'frame-metadata.npz').open('xb') as stream:
        np.savez_compressed(stream, frame_id=arrays[0], global_frame_id=arrays[1],
            time_ps=arrays[2], local_time_ps=arrays[3], valid=arrays[4], reasons=reasons)


def resource_check(output, start, wall_limit, rss_limit, disk_limit):
    """将来の単worker保護callback。OS設定/affinityを変更しない。"""
    import psutil
    process = psutil.Process()
    rss = process.memory_info().rss + sum(p.memory_info().rss for p in process.children(recursive=True))
    disk = sum(p.stat().st_size for p in Path(output).rglob('*') if p.is_file())
    require(time.monotonic() - start < wall_limit and rss <= rss_limit and disk <= disk_limit,
            '時間/RSS/出力保護停止')
    return {'RSS_bytes': rss, 'output_bytes': disk}


def fingerprint(config, inputs, code_paths):
    """設定、入力SHA、実装SHAから再現可能な識別子を作る。"""
    payload = {'config': config, 'inputs': inputs,
               'code': {str(p): sha256(p) for p in code_paths}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def export_references(references, output):
    """34参照の固定分母/pairとM1対応を独立保存する。"""
    save_json(Path(output)/'reference-map.json', [
        {'model': k+1, 'denominator': int(references.den[k]),
         'pairs_zero_based': np.argwhere(references.masks[k]).tolist(),
         'coordinate_float64_sha256': hashlib.sha256(references.native[k].tobytes()).hexdigest(),
         'RMSD_to_M1_A': proper_rmsd(references.native[k], references.native[0])}
        for k in range(34)])
