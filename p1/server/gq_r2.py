"""局所構造領域の探索的評価。MD、学習、GPU Context は実行しない。"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
from pathlib import Path
import resource
import time

import numpy as np
from scipy.spatial.distance import cdist

EPSILONS = (.5, 1., 1.5, 2., 3., 4.)
BURNS = (0, 100, 200, 500)
STRIDES = (1, 2, 4, 10)
TAUS = (0, 2, 5, 10)
PAIRS = np.array([(i, j) for i in range(28) for j in range(i+3, 28)])


def dump(path, obj):
    """非有限JSONを禁止し、途中ファイルから原子的に公開する。"""
    path = Path(path)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def table(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def descriptors(x):
    """Cα座標[Å]から非局所325距離[Å]を計算する。"""
    x = np.asarray(x, dtype=np.float64)
    return np.linalg.norm(x[..., PAIRS[:, 0], :] - x[..., PAIRS[:, 1], :], axis=-1)


def distances(a, b):
    """特徴次元で規格化した dRMSD [Å]。"""
    return cdist(np.atleast_2d(a), np.atleast_2d(b))/np.sqrt(np.shape(a)[-1])


def nearest(a, b, block=64):
    """小ブロックごとに最近傍を求め、全フレーム間行列を避ける。"""
    if not len(b):
        return np.full(len(a), np.inf), np.full(len(a), -1, dtype=int)
    ds, ids = [], []
    for start in range(0, len(a), block):
        mat = distances(a[start:start+block], b)
        ii = mat.argmin(axis=1)
        ds.extend(mat[np.arange(len(ii)), ii])
        ids.extend(ii)
    return np.array(ds), np.array(ids)


def regions(features, times, epsilon, tau=0, valid=None, history=None,
            published=None, cutoff=None, max_gap=None):
    """固定仮代表への連続支持で新領域を登録する。既往集合は圧縮しない。

    times は物理時刻[ps]、published と cutoff は同じ時計の公開時刻。
    支持フレームの公開が期限を超える場合、そのフレームは利用しない。
    返り値は元配列の代表位置と、支持確認時の位置である。
    """
    f = np.asarray(features, dtype=float)
    t = np.asarray(times, dtype=float)
    if not len(f):
        return [], []
    if not np.isfinite(f).all() or not np.isfinite(t).all() or epsilon <= 0 or tau < 0:
        raise ValueError('距離、時刻、閾値が不正です。')
    if np.any(np.diff(t) < 0):
        raise ValueError('持続条件には非減少の物理時刻が必要です。')
    v = np.ones(len(f), dtype=bool) if valid is None else np.asarray(valid, dtype=bool).copy()
    if published is not None and cutoff is not None:
        v &= np.asarray(published) <= cutoff
    base_d = nearest(f, history)[0] if history is not None and len(history) else np.full(len(f), np.inf)
    reps, confirmations = [], []
    centers = np.empty_like(f)
    pending = None
    last = None
    if max_gap is None:
        positive = np.diff(t)[np.diff(t) > 0]
        max_gap = 1.01*float(np.median(positive)) if len(positive) else 0
    for i, x in enumerate(f):
        if not v[i]:
            pending = None
            last = None
            continue
        if last is not None and t[i]-t[last] > max_gap+1e-9:
            pending = None
        last = i
        d = base_d[i]
        if reps:
            d = min(d, distances(x, centers[:len(reps)]).min())
        if d <= epsilon+1e-10:
            pending = None
            continue
        if not reps and history is None:
            reps.append(i)
            confirmations.append(i)
            centers[0] = x
            pending = None
            continue
        if tau == 0:
            centers[len(reps)] = x
            reps.append(i)
            confirmations.append(i)
            continue
        if pending is None or distances(x, f[pending])[0, 0] > epsilon+1e-10:
            pending = i
        if t[i]-t[pending] >= tau-1e-9:
            centers[len(reps)] = f[pending]
            reps.append(pending)
            confirmations.append(i)
            pending = None
    return reps, confirmations


def farthest_cover(f, epsilon):
    """先頭ID固定の最遠点被覆。512点以下の参照用。"""
    selected = [0]
    minimum = distances(f, f[:1])[:, 0]
    while minimum.max() > epsilon+1e-10:
        i = int(minimum.argmax())
        selected.append(i)
        minimum = np.minimum(minimum, distances(f, f[i:i+1])[:, 0])
    return selected


def quantiles(x):
    if not np.size(x):
        return None
    return [float(v) for v in np.quantile(x, [0, .5, .9, .95, 1])]


def circular(a, b):
    return np.sqrt(np.mean(np.angle(np.exp(1j*(a-b)))**2, axis=-1))*180/np.pi


def geometry(x, spec):
    """全原子の保守的な異常検出。物理モデルの妥当性を認証しない。"""
    ca = x[spec['ca']]
    adj = np.linalg.norm(np.diff(ca, axis=0), axis=1)
    cn = np.linalg.norm(x[spec['cn'][:, 0]]-x[spec['cn'][:, 1]], axis=1)
    ce = np.abs(np.linalg.norm(x[spec['ci']]-x[spec['cj']], axis=1)-spec['length'])
    heavy = np.linalg.norm(x[spec['hi']]-x[spec['hj']], axis=1).min()
    q = x[spec['chiral']]
    volume = np.einsum('ij,ij->i', np.cross(q[:, 0]-q[:, 1], q[:, 2]-q[:, 1]), q[:, 3]-q[:, 1])
    flips = np.count_nonzero(np.sign(volume) != spec['sign'])
    values = np.array([adj.min(), adj.max(), cn.min(), cn.max(), ce.max(), heavy, flips])
    reasons = [not np.isfinite(x).all(), adj.min() < 2.5 or adj.max() > 5,
               cn.min() < .8 or cn.max() > 2, ce.max() > .01, heavy < .8,
               flips > 0 or np.any(np.abs(volume) < 1e-6)]
    return values, np.array(reasons, dtype=bool)


def quality(root, prior, out, manifest):
    import MDAnalysis as mda
    from MDAnalysis.lib.distances import calc_dihedrals
    import openmm as mm
    from openmm import unit
    expected = json.loads(Path(manifest).read_text())
    inputs, summaries, source_spec = [], [], None
    topology_hash = None
    for seed in (11, 12, 13, 14):
        chunks = []
        for name in (f'root-{seed}-1ns', f'extend-{seed}-to4ns'):
            task = root/'tasks'/name/'science'
            for filename in ('initial.pdb', 'sim.dcd', 'sim.csv', 'system.xml', 'result.json'):
                rel = f'tasks/{name}/science/{filename}'
                actual = sha(task/filename)
                if expected[rel] != actual:
                    raise RuntimeError('原データSHAが一致しません：'+rel)
                inputs.append(dict(artifact=rel, sha256=actual))
            feature_path = prior/(name+'-features.npz')
            inputs.append(dict(artifact='R1-derived/'+feature_path.name, sha256=sha(feature_path)))
            cached = dict(np.load(feature_path))
            u = mda.Universe(str(task/'initial.pdb'), str(task/'sim.dcd'))
            identity = [(int(a.index), int(a.resid), a.resname, a.name) for a in u.atoms]
            digest = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
            if topology_hash is not None and digest != topology_hash:
                raise RuntimeError('原子順序が一致しません。')
            topology_hash = digest
            if len(u.atoms) != 504 or len(u.residues) != 28:
                raise RuntimeError('原子数または残基数が不正です。')
            system = mm.XmlSerializer.deserialize((task/'system.xml').read_text())
            constraints = [system.getConstraintParameters(i) for i in range(system.getNumConstraints())]
            ci = np.array([int(v[0]) for v in constraints]); cj = np.array([int(v[1]) for v in constraints])
            lengths = np.array([v[2].value_in_unit(unit.angstrom) for v in constraints])
            ca = u.select_atoms('protein and name CA').indices
            if len(ca) != 28:
                raise RuntimeError('Cα数が不正です。')
            cn = np.array([(a.atoms.select_atoms('name C')[0].index, b.atoms.select_atoms('name N')[0].index)
                           for a, b in zip(u.residues[:-1], u.residues[1:])])
            heavy = u.select_atoms('not name H* and not name D*')
            hi, hj = np.triu_indices(len(heavy), 1)
            mask = np.abs(heavy.resindices[hi]-heavy.resindices[hj]) > 1
            hi, hj = heavy.indices[hi[mask]], heavy.indices[hj[mask]]
            chiral = np.array([[r.atoms.select_atoms('name '+n)[0].index for n in ('N','CA','C','CB')]
                              for r in u.residues if len(r.atoms.select_atoms('name CB')) == 1])
            xyz0 = u.atoms.positions.copy().astype(float)
            if source_spec is None:
                q = xyz0[chiral]
                sign = np.sign(np.einsum('ij,ij->i', np.cross(q[:,0]-q[:,1],q[:,2]-q[:,1]),q[:,3]-q[:,1]))
                source_spec = dict(ca=ca, cn=cn, ci=ci, cj=cj, length=lengths, hi=hi, hj=hj,
                                   chiral=chiral, sign=sign)
                np.savez_compressed(out/'synthetic-source.npz', xyz=xyz0, **source_spec)
            angles = np.array([g.indices for r in u.residues for sel in (r.phi_selection, r.psi_selection)
                               if (g := sel()) is not None])
            vals, bad, acheck, fcheck = [], [], 0., 0.
            for j, ts in enumerate(u.trajectory):
                xyz = u.atoms.positions.astype(float)
                value, reasons = geometry(xyz, source_spec)
                ang = calc_dihedrals(*[xyz[angles[:, k]] for k in range(4)])
                reasons[0] |= not np.isfinite(ang).all()
                if j % 200 == 0:
                    fcheck = max(fcheck, float(np.max(np.abs(descriptors(xyz[ca])-cached['distances_A'][j]))))
                    acheck = max(acheck, float(np.max(np.abs(np.angle(np.exp(1j*(ang-cached['angles_rad'][j])))))))
                vals.append(value); bad.append(reasons)
            values = np.array(vals); reasons = np.array(bad)
            if fcheck > 1e-6 or acheck > 1e-4:
                raise RuntimeError('既存特徴量の再計算照合に失敗しました。')
            if len(values) != len(cached['ca']) or len(values) != len(cached['state']):
                raise RuntimeError('フレーム対応が一致しません。')
            summary = dict(task=name, frames=len(values), qualified=int((~reasons.any(axis=1)).sum()),
                           reasons=dict(zip(['nonfinite','CA_adjacent','peptide_CN','constraint','heavy_clash','chirality'], reasons.sum(axis=0).tolist())),
                           minima=values.min(axis=0).tolist(), maxima=values.max(axis=0).tolist(),
                           feature_recheck_max_A=fcheck, angle_recheck_max_rad=acheck)
            summaries.append(summary)
            chunks.append((cached, values, reasons))
        joined = {key: np.concatenate([c[0][key] for c in chunks]) for key in chunks[0][0]}
        joined['quality_values'] = np.concatenate([c[1] for c in chunks])
        joined['valid'] = ~np.concatenate([c[2] for c in chunks]).any(axis=1)
        joined['reasons'] = np.concatenate([c[2] for c in chunks])
        joined['time_ps'] = np.arange(1, len(joined['ca'])+1)*.5
        if len(joined['ca']) != 8000 or np.any(np.abs(joined['state'][:,1]-joined['time_ps']) > 1e-5):
            raise RuntimeError('連続時間またはフレーム総数が一致しません。')
        np.savez_compressed(out/f'root-{seed}.npz', **joined)
        potential = joined['state'][:,2]
        med = np.median(potential); mad = np.median(np.abs(potential-med))
        energies = np.flatnonzero(np.abs(potential-med)>10*max(mad,1e-10))
        dump(out/f'root-{seed}-quality.json',dict(seed=seed, qualified=int(joined['valid'].sum()),
             exclusions_by_burn=[dict(burn_ps=b, qualified=int(np.sum(joined['valid'] & (joined['time_ps']>b))),
                                     retained_sample_duration_ns=float(np.sum(joined['valid'] & (joined['time_ps']>b))*.0005)) for b in BURNS],
             energy_warning_frame_ids=energies.tolist(), energy_median_kJ_mol=float(med), energy_MAD_kJ_mol=float(mad)))
    dump(out/'input-verification.json', dict(topology_identity_sha256=topology_hash, files=inputs,
         checked_feature_interval_ps=100, raw_checks_all_frames=True, feature_recheck_scope='全点ではなく100 ps間隔'))
    dump(out/'quality-summary.json', summaries)


def load(out):
    return {s: dict(np.load(out/f'root-{s}.npz')) for s in (11,12,13,14)}


def calibration(out):
    data = load(out)
    rows = []
    for seed in (11,12):
        a = data[seed]
        f, g, t = a['distances_A'], a['angles_rad'], a['time_ps']
        for window, mask in [('post100',t>100), ('early100',t<=100)]:
            for lag in (1,2,4,10,20,40,100,200):
                valid = mask[lag:] & mask[:-lag] & a['valid'][lag:] & a['valid'][:-lag]
                dd = np.sqrt(np.mean((f[lag:]-f[:-lag])**2,axis=1))[valid]
                angle = circular(g[lag:], g[:-lag])[valid]
                rows.append(dict(seed=seed,window=window,lag_ps=lag*.5,pairs=len(dd),
                     dRMSD_q0_q50_q90_q95_q100_A=quantiles(dd), angle_RMS_q0_q50_q90_q95_q100_deg=quantiles(angle)))
    dump(out/'calibration.json',rows)
    pair_rows=[]
    for left,right in itertools.combinations(data,2):
        ia=np.flatnonzero((data[left]['time_ps']>100)&data[left]['valid'])[::20]
        ib=np.flatnonzero((data[right]['time_ps']>100)&data[right]['valid'])[::20]
        dd=distances(data[left]['distances_A'][ia],data[right]['distances_A'][ib])
        pair_rows.append(dict(left=left,right=right,stride_ps=10,dRMSD_A=quantiles(dd)))
    dump(out/'cross-stream.json',pair_rows)
    correlations=[]
    for seed,a in data.items():
        v=a['rg_A'][a['time_ps']>100];v=v-v.mean()
        corr=np.correlate(v,v,mode='full')[len(v)-1:]/np.dot(v,v)
        first=np.flatnonzero(corr<=0)
        end=int(first[0]) if len(first) else len(corr)
        correlations.append(dict(seed=seed,Rg_lag0p5ps=float(corr[1]),first_nonpositive_ps=end*.5,
              truncated_integrated_time_ps=float(.5*(.5+corr[1:end].sum())),
              caution='非定常性のある有限系列の記述。ESSや平衡性の認証ではない。'))
    dump(out/'correlation.json',correlations)


def evaluate(out):
    data=load(out);rows=[];primary=[]
    for seed,a in data.items():
        for burn,stride,eps,tau in itertools.product(BURNS,STRIDES,EPSILONS,TAUS):
            start=time.monotonic()
            ii=np.flatnonzero(a['time_ps']>burn)[::stride]
            f=a['distances_A'][ii];t=a['time_ps'][ii]
            reps,confirmed=regions(f,t,eps,tau,valid=a['valid'][ii])
            row=dict(seed=seed,burn_ps=burn,interval_ps=stride*.5,epsilon_A=eps,tau_ps=tau,
                     total_regions=len(reps),added_regions=max(0,len(reps)-1),frames=len(ii),
                     wall_s=time.monotonic()-start)
            rows.append(row)
            if burn==100 and stride==4 and tau==5:
                base=ii[reps[0]] if reps else None
                repids=ii[reps]
                info=dict(**row,representative_frame_ids=repids.tolist(),confirmation_frame_ids=ii[confirmed].tolist(),
                     representative_time_ps=a['time_ps'][repids].tolist(),confirmation_time_ps=a['time_ps'][ii[confirmed]].tolist(),
                     angles_from_seed_deg=quantiles(circular(a['angles_rad'][repids],a['angles_rad'][base])) if len(reps) else [],
                     angles_between_representatives_deg=quantiles(circular(a['angles_rad'][repids[1:]],a['angles_rad'][repids[:-1]])) if len(reps)>1 else [],
                     increments_by_ns=[int(np.sum((a['time_ps'][ii[confirmed]]>k*1000)&(a['time_ps'][ii[confirmed]]<=(k+1)*1000))) for k in range(4)],
                     Rg_range_A=quantiles(a['rg_A'][repids]) if len(reps) else [],
                     Q8_range=quantiles(a['q'][repids]) if len(reps) else [])
                primary.append(info)
        table(out/'sensitivity.csv',rows)
        dump(out/'primary-regions.json',primary)
        print('評価系列完了',seed,flush=True)
    libraries=[]
    for eps in EPSILONS:
        cal=np.concatenate([a['distances_A'][(a['time_ps']>100)&a['valid']][::4] for s,a in data.items() if s in (11,12)])
        rep,_=regions(cal,np.arange(len(cal)),eps,0)
        lib=cal[rep]
        np.savez_compressed(out/f'library-{eps}.npz',centers=lib)
        for seed,a in data.items():
            ii=np.flatnonzero((a['time_ps']>100)&a['valid'])[::4]
            dd,ids=nearest(a['distances_A'][ii],lib)
            inside=dd<=eps+1e-10
            libraries.append(dict(seed=seed,epsilon_A=eps,library_centers=len(lib),frames=len(ii),
                    visited_centers=int(len(np.unique(ids[inside]))),outside_frames=int((~inside).sum()),
                    outside_fraction=float((~inside).mean()),nearest_dRMSD_A=quantiles(dd),
                    dataset_role='校正・構庫' if seed in (11,12) else '既知の探索的別系列'))
    dump(out/'fixed-library.json',libraries)


def controls(out):
    data=load(out);rng=np.random.default_rng(20261026);report=[];order=[];reference=[]
    for seed,a in data.items():
        ii=np.flatnonzero((a['time_ps']>100)&a['valid'])[::4]
        f=a['distances_A'][ii]
        for eps in EPSILONS:
            for label,idx in [('forward',np.arange(len(f))),('reverse',np.arange(len(f))[::-1]),('shuffle',rng.permutation(len(f)))]:
                reps,_=regions(f[idx],np.arange(len(f)),eps)
                order.append(dict(seed=seed,epsilon_A=eps,order=label,regions=len(reps)))
            ix=np.linspace(0,len(f)-1,min(512,len(f)),dtype=int)
            sample=f[ix]
            rep=farthest_cover(sample,eps)
            exact=distances(sample,sample)
            blocked,ids=nearest(sample,sample[rep],block=13)
            ref=exact[:,rep].min(axis=1)
            reference.append(dict(seed=seed,epsilon_A=eps,sample_frames=len(sample),centers=len(rep),
                 exact_block_max_abs_A=float(np.max(np.abs(blocked-ref))),cover_radius_A=float(blocked.max())))
    a=data[11];ii=np.flatnonzero((a['time_ps']>100)&a['valid'])[::4][:512]
    f=a['distances_A'][ii];t=a['time_ps'][ii]
    for eps in EPSILONS:
        rep,_=regions(f,t,eps,5)
        dup,_=regions(np.repeat(f,2,axis=0),np.repeat(t,2),eps,5)
        report.append(dict(control='同一時刻の反復',epsilon_A=eps,original=len(rep),duplicated=len(dup),passed=len(rep)==len(dup)))
    xyz=a['ca'][ii[0]];theta=.31
    rot=np.array([[np.cos(theta),-np.sin(theta),0],[np.sin(theta),np.cos(theta),0],[0,0,1]])
    err=float(distances(descriptors(xyz),descriptors(xyz@rot+np.array([20,-7,3])))[0,0])
    mirror=float(distances(descriptors(xyz),descriptors(xyz*np.array([-1,1,1])))[0,0])
    report.append(dict(control='剛体変換',max_dRMSD_A=err,passed=err<1e-10))
    report.append(dict(control='鏡像距離の既知の盲点',dRMSD_A=mirror,passed=mirror<1e-10))
    for sigma in (1e-6,.01,.05,.1):
        x=xyz+rng.normal(0,sigma,size=(100,*xyz.shape))
        dd=distances(descriptors(x),descriptors(xyz))[:,0]
        reps,_=regions(descriptors(x),np.arange(100),.5)
        report.append(dict(control='人工Cαガウス摂動（MDではない）',sigma_A=sigma,dRMSD_A=quantiles(dd),epsilon0p5_regions=len(reps)))
    synth=dict(np.load(out/'synthetic-source.npz'));x=synth.pop('xyz')
    normal,reasons=geometry(x,synth)
    mirrored=x*np.array([-1,1,1]);mv,mr=geometry(mirrored,synth)
    broken=x.copy();broken[int(synth['cn'][0,1])]+=np.array([10,0,0]);bv,br=geometry(broken,synth)
    report.extend([dict(control='全原子鏡像',chirality_flips=int(mv[-1]),rejected=bool(mr.any())),
                   dict(control='ペプチドNの人工10Å移動',rejected=bool(br.any()),reasons=br.tolist())])
    single=np.repeat(f[:1],100,axis=0)
    sr,_=regions(single,np.arange(100),.5,5)
    report.append(dict(control='同一構造100回',regions=len(sr),passed=len(sr)==1))
    dump(out/'negative-controls.json',report)
    table(out/'order-sensitivity.csv',order)
    dump(out/'exact-reference.json',reference)


def figures(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family']='Noto Sans CJK JP'
    data=load(out)
    fig,axs=plt.subplots(3,1,figsize=(9,8),sharex=True)
    for seed,a in data.items():
        ii=np.arange(0,len(a['time_ps']),20);t=a['time_ps'][ii]/1000
        axs[0].plot(t,a['rg_A'][ii],label=str(seed),linewidth=.7)
        axs[1].plot(t,a['state'][ii,2],linewidth=.7)
        axs[2].plot(t,a['quality_values'][ii,5],linewidth=.7)
    axs[0].set_ylabel('Cα回転半径 [Å]');axs[1].set_ylabel('ポテンシャルエネルギー [kJ/mol]')
    axs[2].set_ylabel('非局所重原子の最短距離 [Å]');axs[2].set_xlabel('物理時間 [ns]')
    axs[0].legend(title='乱数系列');fig.tight_layout();fig.savefig(out/'quality-timeseries.png',dpi=150);plt.close(fig)
    primary=json.loads((out/'primary-regions.json').read_text())
    lib=json.loads((out/'fixed-library.json').read_text())
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for seed in data:
        rows=[r for r in primary if r['seed']==seed]
        axs[0].plot([r['epsilon_A'] for r in rows],[r['added_regions'] for r in rows],'o-',label=str(seed))
        rows=[r for r in lib if r['seed']==seed]
        axs[1].plot([r['epsilon_A'] for r in rows],[r['outside_fraction'] for r in rows],'o-')
    axs[0].set_ylabel('追加領域数（A）');axs[1].set_ylabel('参照庫外率（B）')
    for ax in axs:ax.set_xlabel('ε [Å]');ax.grid(alpha=.2)
    axs[0].legend(title='乱数系列');fig.tight_layout();fig.savefig(out/'regions-and-library.png',dpi=150);plt.close(fig)
    cal=json.loads((out/'calibration.json').read_text())
    fig,ax=plt.subplots(figsize=(7,4))
    for seed in (11,12):
        rows=[r for r in cal if r['seed']==seed and r['window']=='post100']
        ax.plot([r['lag_ps'] for r in rows],[r['dRMSD_q0_q50_q90_q95_q100_A'][1] for r in rows],'o-',label=f'{seed}: 中央値')
        ax.plot([r['lag_ps'] for r in rows],[r['dRMSD_q0_q50_q90_q95_q100_A'][3] for r in rows],'--',label=f'{seed}: 95百分位')
    ax.set_xscale('log');ax.set_xlabel('時間差 [ps]');ax.set_ylabel('dRMSD [Å]');ax.legend();ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(out/'lag-calibration.png',dpi=150);plt.close(fig)


def main():
    p=argparse.ArgumentParser(description='GQ-R2 CPU限定の局所構造評価')
    p.add_argument('--phase',choices=['quality','calibration','evaluate','controls','figures'],required=True)
    p.add_argument('--root',type=Path);p.add_argument('--prior',type=Path)
    p.add_argument('--manifest',type=Path);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
        raise RuntimeError('CUDA_VISIBLE_DEVICES=-1 を指定してください。')
    resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3))
    args.out.mkdir(exist_ok=True,parents=True)
    receipt=args.out/(args.phase+'-runtime.json')
    if receipt.exists():
        raise RuntimeError('完了済み段階を上書きできません。新しい出力先を使用してください。')
    started=time.monotonic();cpu=time.process_time()
    try:
        if args.phase=='quality':quality(args.root,args.prior,args.out,args.manifest)
        else:globals()[args.phase](args.out)
    except Exception as e:
        dump(args.out/(args.phase+'-failure.json'),dict(type=type(e).__name__,message=str(e)))
        raise
    finally:
        usage=resource.getrusage(resource.RUSAGE_SELF)
        dump(receipt,dict(phase=args.phase,wall_s=time.monotonic()-started,cpu_s=time.process_time()-cpu,
          peak_RSS_KiB=usage.ru_maxrss,affinity=sorted(os.sched_getaffinity(0)),GPU_compute=False,
          source_sha256=sha(__file__),plan_commit='94d96bc24c8c35dca7f08452809b2a35239a9da3'))


if __name__=='__main__':
    main()
