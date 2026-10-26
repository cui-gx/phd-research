"""Server-side exploratory trajectory diagnostics; never a policy result."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import time
import numpy as np
from .supplement_coverage import (ca_measures, distance_features, drmsd, bins,
                                  center_visits, autocorrelation)


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False))


def summarize(values):
    a = np.asarray(values)
    return [float(a.min()), float(np.median(a)), float(a.max())]


def trajectory(task):
    import MDAnalysis as mda
    from MDAnalysis.lib.distances import calc_dihedrals
    out = task/"science"
    result = json.loads((out/"result.json").read_text())
    u = mda.Universe(str(out/"initial.pdb"), str(out/"sim.dcd"))
    ca = u.select_atoms("protein and name CA")
    if len(ca) != 28 or len(u.atoms) != 504:
        raise RuntimeError("Unexpected atom mapping")
    groups, angle_names = [], []
    for residue in u.residues:
        for name, selector in (("phi", residue.phi_selection), ("psi", residue.psi_selection)):
            group = selector()
            if group is not None:
                groups.append(group.indices)
                angle_names.append(f"{residue.resid}-{residue.resname}-{name}")
    groups = np.asarray(groups)
    all_xyz, dihedrals, ca_adj = [], [], []
    cn_pairs = []
    for left, right in zip(u.residues[:-1], u.residues[1:]):
        c = left.atoms.select_atoms("name C")[0].index
        n = right.atoms.select_atoms("name N")[0].index
        cn_pairs.append((c, n))
    cn_pairs = np.asarray(cn_pairs)
    cn_max, heavy_min, chirality_flip = [], [], []
    heavy = u.select_atoms("not name H* and not name D*")
    hi, hj = np.triu_indices(len(heavy), 1)
    # Exclude same-residue and adjacent-residue pairs: clash check is conservative,
    # not a complete all-atom validation or a forcefield certification.
    mask = np.abs(heavy.resindices[hi]-heavy.resindices[hj]) > 1
    hi, hj = hi[mask], hj[mask]
    chiral = []
    for res in u.residues:
        ids = [res.atoms.select_atoms("name "+name) for name in ("N", "CA", "C", "CB")]
        if all(len(x) == 1 for x in ids): chiral.append([x[0].index for x in ids])
    chiral = np.asarray(chiral)
    first_sign = None
    for frame, ts in enumerate(u.trajectory):
        xyz = u.atoms.positions
        if not np.isfinite(xyz).all(): raise RuntimeError("Nonfinite coordinates")
        x = ca.positions.copy()
        all_xyz.append(x)
        ca_adj.append(float(np.max(np.linalg.norm(np.diff(x, axis=0), axis=1))))
        cn_max.append(float(np.max(np.linalg.norm(xyz[cn_pairs[:, 0]]-xyz[cn_pairs[:, 1]], axis=1))))
        dihedrals.append(calc_dihedrals(*[xyz[groups[:, k]] for k in range(4)]))
        if frame % 10 == 0:
            heavy_xyz = heavy.positions
            heavy_min.append(float(np.min(np.linalg.norm(heavy_xyz[hi]-heavy_xyz[hj], axis=1))))
            q = xyz[chiral]
            sign = np.sign(np.einsum('ij,ij->i', np.cross(q[:,0]-q[:,1],q[:,2]-q[:,1]),q[:,3]-q[:,1]))
            if first_sign is None: first_sign = sign.copy()
            chirality_flip.append(int(np.sum(sign != first_sign)))
    xyz = np.asarray(all_xyz, dtype=np.float64)
    angles = np.asarray(dihedrals)
    state = np.genfromtxt(out/"sim.csv", delimiter=",", skip_header=1)
    if len(xyz) != result["expected_frames"] or not np.isfinite(state).all():
        raise RuntimeError("Incomplete trajectory/state data")
    # StateDataReporter emits Step,Time,Potential,Kinetic,Total,Temperature.
    temp = state[:, -1]
    quality = {"frames": len(xyz), "temperature_K_min_median_max": summarize(temp),
               "temperature_K_mean": float(temp.mean()), "potential_kJ_mol_min_median_max": summarize(state[:, 2]),
               "CA_adjacent_max_A": float(max(ca_adj)), "peptide_CN_max_A": float(max(cn_max)),
               "nonlocal_heavy_min_A_sampled_5ps": float(min(heavy_min)),
               "sidechain_chirality_flips_max_sampled_5ps": max(chirality_flip),
               "angle_columns": angle_names, "angle_nonfinite_count": int(np.count_nonzero(~np.isfinite(angles)))}
    quality["hard_geometry_warning"] = quality["CA_adjacent_max_A"] > 5 or quality["peptide_CN_max_A"] > 2 or quality["nonlocal_heavy_min_A_sampled_5ps"] < .8
    quality["soft_warning"] = not 200 < float(temp.mean()) < 400 or max(chirality_flip) > 0
    return result, xyz, angles, state, quality


def analyze(root, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    physics_dir = root/"tasks/physics-01/science"
    if (physics_dir/"evaluations.json").exists():
        evaluations = json.loads((physics_dir/"evaluations.json").read_text())
        forces = np.load(physics_dir/"forces.npz")["forces"]
        comparisons = []
        for source in sorted({v["source"] for v in evaluations}):
            for group in (-1,0,1,2):
                batches = {}
                for method in ("cutoff_1nm","cutoff_2nm","no_cutoff"):
                    indices = [i for i,v in enumerate(evaluations) if v["source"]==source and v["group"]==group and v["method"]==method and not v["warmup"]]
                    e=np.array([evaluations[i]["energy_kJ_mol"] for i in indices]); f=forces[indices]
                    batches[method]=(e,f)
                e0,f0=batches["no_cutoff"];reference=f0.mean(axis=0)
                for method,(e,f) in batches.items():
                    delta=f.mean(axis=0)-reference
                    den=np.sum(reference**2)
                    comparisons.append(dict(source=source,group=group,method=method,
                      energy_mean_kJ_mol=float(e.mean()),energy_range_kJ_mol=float(np.ptp(e)),
                      delta_energy_mean_vs_NC_kJ_mol=float(e.mean()-e0.mean()),
                      force_rms_delta_kJ_mol_nm=float(np.sqrt(np.mean(np.sum(delta**2,axis=1)))),
                      force_relative_l2_delta=float(np.sqrt(np.sum(delta**2)/den)) if den else None,
                      technical_force_max_repeat_delta=float(np.max(np.abs(f-f[0])))))
        dump(output/"physics-comparisons.json",comparisons)
    items, feature_arrays = [], {}
    for task in sorted((root/"tasks").iterdir()):
        req = json.loads((task/"request.json").read_text())
        if req["kind"] != "md" or not (task/"science/result.json").exists(): continue
        result, xyz, angles, state, quality = trajectory(task)
        rg, q, ree, contact = ca_measures(xyz)
        features = distance_features(xyz)
        np.savez_compressed(output/(task.name+"-features.npz"), ca=xyz, distances_A=features,
                            rg_A=rg, q=q, ree_A=ree, angles_rad=angles, state=state)
        time_ps = result["initial_ns"]*1000+(np.arange(len(xyz))+1)*.5
        indices = np.arange(len(xyz))[time_ps > 100]
        row = dict(task=task.name, **result, quality=quality)
        row["post100ps_frames"] = len(indices)
        row["Rg_A_min_median_max"] = summarize(rg[indices]) if len(indices) else None
        row["Q8_min_median_max"] = summarize(q[indices]) if len(indices) else None
        row["dRMSD_to_first_A_min_median_max"] = summarize(drmsd(features, features[0]))
        row["Rg_lag1"] = (autocorrelation(rg[indices]) or [None])[0] if len(indices) > 8 else None
        row["Q_lag1"] = (autocorrelation(q[indices]) or [None])[0] if len(indices) > 8 else None
        row["dihedral_circular_change_from_first_abs_deg_median_p95"] = [float(v) for v in np.percentile(np.abs(np.angle(np.exp(1j*(angles-angles[0]))))*180/np.pi, [50,95])]
        row["block_100ps"] = [{"start_ps": float(time_ps[i]), "Rg_mean_A": float(rg[i:i+200].mean()),
                                 "Q8_mean": float(q[i:i+200].mean()), "potential_mean_kJ_mol": float(state[i:i+200,2].mean()),
                                 "temperature_mean_K": float(state[i:i+200,-1].mean())} for i in range(0,len(xyz),200)]
        items.append(row)
        if task.name.startswith(("root", "extend")):
            feature_arrays[task.name] = (result, xyz, features, time_ps)
    dump(output/"trajectory-summary.json", items)
    sensitivity, libraries, alias = [], [], []
    # Analyze each physical stream as a time-ordered concatenation. Checkpoint
    # continuations are one root, not new independent replicates.
    roots = {}
    for name, (result, xyz, features, time_ps) in feature_arrays.items():
        roots.setdefault(result["seed"], []).append((result["initial_ns"], xyz, features, time_ps))
    joined = {}
    for seed, segments in sorted(roots.items()):
        segments.sort(key=lambda v:v[0])
        x = np.concatenate([s[1] for s in segments]); f = np.concatenate([s[2] for s in segments]); t = np.concatenate([s[3] for s in segments])
        joined[seed] = (x, f, t)
        for burn in (0, 100, 200):
            for stride in (1,2,4,10):
                idx = np.flatnonzero(t > burn)[::stride]
                if not len(idx): continue
                rg, _, _, _ = ca_measures(x[idx])
                for radius in (7.,8.,9.):
                    _, q, _, count = ca_measures(x[idx],radius)
                    for wr in (.5,1.,2.):
                        for wq in (.02,.05,.10):
                            for shifted in (False,True):
                                labels = bins(rg,q,wr,wq,shifted,q_contact_counts=count)
                                keys, counts = np.unique(labels,axis=0,return_counts=True)
                                sensitivity.append(dict(seed=seed,total_ns=float(t[-1]/1000),burn_ps=burn,stride=stride,radius_A=radius,
                                  rg_width_A=wr,q_width=wq,shifted=shifted,N=len(idx),U=len(keys),U_over_N=len(keys)/len(idx),
                                  max_bin_fraction=float(counts.max()/len(idx))))
        idx = np.flatnonzero(t > 100)[::10]
        rg,q,_,count = ca_measures(x[idx]); labels = bins(rg,q,1.,.05,q_contact_counts=count)
        max_d, pair = 0., None
        for key in np.unique(labels,axis=0):
            positions = idx[np.all(labels == key,axis=1)]
            for n,a in enumerate(positions[:-1]):
                distances = drmsd(f[positions[n+1:]],f[a]); k=int(np.argmax(distances))
                if distances[k] > max_d: max_d=float(distances[k]);pair=[int(a),int(positions[n+1+k])]
        alias.append(dict(seed=seed,max_same_grid_drmsd_A=max_d,frames=pair,subsample_ps=5))
    seeds = sorted(joined)
    if len(seeds) >= 4:
        for horizon in (1.,5.):
            if horizon == 5. and not any(v[2][-1] >= 4999 for v in joined.values()): continue
            calibration=[]
            for seed in seeds[:2]:
                x,f,t=joined[seed]; calibration.append(f[(t>100)&(t<=horizon*1000)][::10])
            calibration=np.concatenate(calibration)
            for epsilon in (1.,2.,4.):
                centers=[]
                for i,feature in enumerate(calibration):
                    if not centers or np.min(drmsd(calibration[centers],feature)) > epsilon:centers.append(i)
                lib=calibration[centers]
                for seed in seeds[2:]:
                    x,f,t=joined[seed]
                    for validation_horizon in sorted({min(horizon,float(t[-1]/1000)),float(t[-1]/1000)}):
                        use=f[(t>100)&(t<=validation_horizon*1000)]
                        if not len(use): continue
                        v=center_visits(use,lib,list(range(len(lib))),epsilon)
                        # Long per-frame diagnostics stay server/local, not in the compact JSON.
                        np.savez_compressed(output/f'library-{horizon}-{validation_horizon}-{epsilon}-{seed}.npz',nearest_A=v.pop('nearest_D_A'),center_id=v.pop('nearest_center_frame_id_0based'))
                        libraries.append(dict(calibration_horizon_ns=horizon,validation_horizon_ns=validation_horizon,validation_seed=seed,epsilon_A=epsilon,**v))
    dump(output/"grid-sensitivity.json", sensitivity)
    dump(output/"library-validation.json", libraries)
    dump(output/"shape-alias.json", alias)
    # Verify invariance for each observed root, independently of CVAE/native.
    invariance=[]
    for seed,(x,f,t) in joined.items():
        rotated=x[:20] @ np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])+[10.,-3.,2.]
        invariance.append(dict(seed=seed,rigid_distance_max_error_A=float(np.max(np.abs(distance_features(rotated)-f[:20]))),
                              repeat_distance_max_error_A=float(np.max(np.abs(distance_features(x[:20])-f[:20])))))
    dump(output/"invariance.json", invariance)
    fig,axes=plt.subplots(2,2,figsize=(10,7))
    for seed,(x,f,t) in joined.items():
        rg,q,_,c=ca_measures(x);labels=bins(rg,q,1.,.05,q_contact_counts=c);seen=set();curve=[]
        for key in labels:
            seen.add(tuple(key));curve.append(len(seen))
        axes[0,0].plot(t/1000,rg,label=str(seed)[-2:],lw=.6)
        axes[0,1].plot(t/1000,q,lw=.6)
        axes[1,0].plot(t/1000,curve,lw=1)
        axes[1,1].scatter(rg[::10],q[::10],s=2)
    for ax in axes.ravel():ax.grid(alpha=.2)
    axes[0,0].legend(title='stream seed suffix');axes[0,0].set(ylabel='CA geometric Rg (A)',xlabel='MD time (ns)')
    axes[0,1].set(ylabel='Nonlocal contact fraction',xlabel='MD time (ns)')
    axes[1,0].set(ylabel='Visited projection cells (diagnostic)',xlabel='MD time (ns)')
    axes[1,1].set(xlabel='Rg (A)',ylabel='Q at 8 A')
    fig.suptitle('GQ exploratory streams; no CVAE/policy comparison')
    fig.tight_layout();fig.savefig(output/'trajectory-diagnostics.png',dpi=160);plt.close(fig)
    dump(output/"analysis-runtime.json", {"cpu_wall_s":time.monotonic()-started,"roots":len(joined),"scientific_evaluation_ready":False})
    print(json.dumps({'output':str(output),'trajectories':len(items),'roots':len(joined),'grid_rows':len(sensitivity),'library_rows':len(libraries)}),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.root,a.output)
