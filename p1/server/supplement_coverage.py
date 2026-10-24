"""Frozen S2 supplement A: CPU-only, read-only trajectory analysis.

All coordinates and distances are in angstrom. No model or native reference is read.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
import time
import numpy as np

from .science import sha256_file

RG_WIDTHS = (0.5, 1.0, 2.0)
Q_WIDTHS = (0.02, 0.05, 0.10)
REE_WIDTHS = (1.0, 2.0, 4.0)
CONTACT_RADII = (7.0, 8.0, 9.0)
EPSILONS = (1.0, 2.0, 4.0)
STRIDES = (1, 2, 4, 10)


def ca_measures(xyz, radius=8.0):
    x = np.asarray(xyz, dtype=np.float64)
    if x.shape[-2:] != (28, 3) or not np.isfinite(x).all():
        raise ValueError("Expected finite C-alpha coordinates (...,28,3)")
    center = x.mean(axis=-2, keepdims=True)
    rg = np.sqrt(np.mean(np.sum((x-center)**2, axis=-1), axis=-1))
    ree = np.linalg.norm(x[..., -1, :]-x[..., 0, :], axis=-1)
    i, j = np.triu_indices(28, k=4)
    assert len(i) == 300
    d = np.linalg.norm(x[..., i, :]-x[..., j, :], axis=-1)
    contacts = np.sum(d < radius, axis=-1)
    q = contacts / 300.0
    return rg, q, ree, contacts


def distance_features(xyz):
    x = np.asarray(xyz, dtype=np.float64)
    i, j = np.triu_indices(28, k=3)
    assert len(i) == 325
    return np.linalg.norm(x[..., i, :]-x[..., j, :], axis=-1)


def drmsd(a, b):
    return np.sqrt(np.mean((np.asarray(a)-np.asarray(b))**2, axis=-1))


def q_bin_indices(contact_counts, width, shifted=False):
    """Evaluate floor((c/300-o)/width) using exact integer arithmetic."""
    counts=np.asarray(contact_counts,dtype=np.int64)
    if (counts<0).any() or (counts>300).any():
        raise ValueError("Q contact count outside 0..300")
    fraction=Fraction(str(width))
    if shifted:
        return (2*counts*fraction.denominator-300*fraction.numerator)//(600*fraction.numerator)
    return (counts*fraction.denominator)//(300*fraction.numerator)


def bins(x, y, wx, wy, shifted=False, q_contact_counts=None):
    x, y = np.asarray(x), np.asarray(y)
    if (not np.isfinite(x).all() or not np.isfinite(y).all() or
            (x < 0).any() or (y < 0).any()):
        raise ValueError("Invalid physical coordinate")
    ox, oy = (wx/2, wy/2) if shifted else (0, 0)
    y_bins=np.floor((y-oy)/wy)
    if q_contact_counts is not None:
        if not np.allclose(y,np.asarray(q_contact_counts)/300.0,rtol=0,atol=1e-15):
            raise ValueError("Q ratio/count mismatch")
        y_bins=q_bin_indices(q_contact_counts,wy,shifted)
    return np.stack((np.floor((x-ox)/wx), y_bins), axis=-1).astype(np.int64)


def occupancy(labels):
    keys = [tuple(map(int, row)) for row in labels]
    n = len(keys)
    if n == 0:
        return {"N": 0, "U": 0}
    counts = {}
    run_lengths = []
    run = 1
    cumulative = []
    for i, key in enumerate(keys):
        counts[key] = counts.get(key, 0)+1
        cumulative.append(len(counts))
        if i:
            if key == keys[i-1]:
                run += 1
            else:
                run_lengths.append(run)
                run = 1
    run_lengths.append(run)
    u = len(counts)
    return {"N": n, "U": u, "U_over_N": u/n,
            "visit_frequencies": [{"bin": list(k), "visits": v} for k,v in sorted(counts.items())],
            "singleton_fraction_of_occupied_bins": sum(v == 1 for v in counts.values())/u,
            "transition_rate": sum(keys[i] != keys[i-1] for i in range(1,n))/(n-1) if n > 1 else None,
            "dwell_run_frames_median": float(np.median(run_lengths)),
            "dwell_run_frames_min_max": [min(run_lengths), max(run_lengths)],
            "dwell_observed_span_ps_median": float(np.median(run_lengths)-1)*0.5,
            "cumulative_U": cumulative}


def autocorrelation(x):
    x = np.asarray(x, dtype=np.float64)
    y = x-x.mean()
    den = float(np.dot(y,y))
    if den == 0:
        return None
    return [float(np.dot(y[:-k],y[k:])/den) for k in range(1,min(200,len(x)//4)+1)]


def centers(calibration, epsilon):
    idx = []
    for frame in range(0, min(len(calibration),2000),10):
        f = calibration[frame]
        if not idx or np.min(drmsd(calibration[idx],f)) > epsilon:
            idx.append(frame)
    return idx


def center_visits(features, library, center_ids, epsilon):
    # Block distances to avoid an N x K x 325 temporary above the RSS cap.
    nearest, nearest_id = [], []
    for start in range(0,len(features),64):
        block = features[start:start+64]
        ds = np.sqrt(np.mean((block[:,None,:]-library[None,:,:])**2,axis=-1))
        arg = np.argmin(ds,axis=1)  # center_ids are sorted, so first tie wins
        nearest.extend(ds[np.arange(len(arg)),arg].tolist())
        nearest_id.extend([center_ids[i] for i in arg])
    d = np.asarray(nearest)
    visited = sorted({f for f,v in zip(nearest_id,d) if v <= epsilon})
    return {"K":len(center_ids),"visited_centers":visited,
            "visited":len(visited),"visited_over_K":len(visited)/len(center_ids),
            "out_of_library_frames":int(np.count_nonzero(d > epsilon)),
            "out_of_library_fraction":float(np.mean(d > epsilon)),
            "nearest_D_A_median_p90_max":[float(v) for v in (np.median(d),np.percentile(d,90),np.max(d))],
            "nearest_center_frame_id_0based":nearest_id,"nearest_D_A":nearest}


def local_path(run, remote):
    marker = "/runs/s2-pilot-02/"
    if marker not in remote:
        raise ValueError("Unexpected remote artifact path")
    return run / remote.split(marker,1)[1]


def load_trajectory(run, task):
    import MDAnalysis as mda
    result_path = run/"tasks"/task/"result.json"
    result = json.loads(result_path.read_text())
    pdb = local_path(run,result["pdb_path"])
    dcd = local_path(run,result["dcd_path"])
    for kind,path in (("pdb_path",pdb),("dcd_path",dcd)):
        if sha256_file(path) != result["artifact_sha256"][kind]:
            raise ValueError(f"Input SHA mismatch: {path}")
    u = mda.Universe(str(pdb),str(dcd))
    if u.atoms.n_atoms != 504:
        raise ValueError("Topology is not 504 atoms")
    ca = u.select_atoms("protein and name CA")
    if len(ca) != 28:
        raise ValueError("Topology is not 28 CA atoms")
    xyz = np.array([ca.positions.copy() for _ in u.trajectory],dtype=np.float64)
    if len(xyz) != result["frames"] or not np.isfinite(xyz).all():
        raise ValueError("Trajectory frames invalid")
    mapping = [{"sequence_index_1based":i+1,"atom_index_0based":int(atom.index),
                "atom_name":str(atom.name),"resid":int(atom.resid),"resname":str(atom.resname),
                "segid":str(atom.segid)} for i,atom in enumerate(ca)]
    return result,xyz,mapping


def prefix_diagnostic(a,b):
    n=min(len(a),len(b))
    raw=np.all(a[:n] == b[:n],axis=(1,2))
    d=drmsd(distance_features(a[:n]),distance_features(b[:n]))
    drift=np.linalg.norm(a[:n].mean(axis=1)-b[:n].mean(axis=1),axis=1)
    return {"overlap_frames":n,"raw_coordinate_exact_equal_fraction":float(np.mean(raw)),
            "CA_dRMSD_A_min_median_max":[float(v) for v in (d.min(),np.median(d),d.max())],
            "CA_dRMSD_le_1e-6_fraction":float(np.mean(d<=1e-6)),
            "CA_dRMSD_le_1e-3_fraction":float(np.mean(d<=1e-3)),
            "centroid_displacement_A_median":float(np.median(drift))}


def analyze(run, out, plan_commit, analysis_commit):
    t0=time.monotonic()
    run,out=Path(run),Path(out)
    out.mkdir(parents=True,exist_ok=False)
    checks=json.loads((run/"checksums.json").read_text())
    failures=[]
    for rel,expected in checks.items():
        path=run/rel
        if not path.is_file() or sha256_file(path)!=expected:
            failures.append(rel)
    if failures or len(checks)!=203:
        raise ValueError(f"Raw archive validation failed: {len(checks)} files, mismatches {failures}")
    tasks=[f"md-{length}ps-r{rep}" for rep in (0,1) for length in (20,200,1000)]
    data={task:load_trajectory(run,task) for task in tasks}
    mapping=data["md-1000ps-r0"][2]
    if any(v[2]!=mapping for v in data.values()):
        raise ValueError("CA atom mapping differs across tasks")
    (out/"ca-mapping.json").write_text(json.dumps(mapping,indent=2))
    prefixes={}
    for rep in (0,1):
        longest=data[f"md-1000ps-r{rep}"][1]
        for length in (20,200):
            prefixes[f"r{rep}-{length}vs1000"]=prefix_diagnostic(data[f"md-{length}ps-r{rep}"][1],longest)
    prefixes["r0-vs-r1-1000"]=prefix_diagnostic(data["md-1000ps-r0"][1],data["md-1000ps-r1"][1])
    (out/"prefix-diagnostics.json").write_text(json.dumps(prefixes,indent=2))
    allrows=[]; curves=[]; negatives=[]; ac={}; mixing=[]; perframe=[]
    for task in tasks:
        result,xyz,_=data[task]
        frame_ids=np.arange(len(xyz))
        rg,_,ree,_=ca_measures(xyz)
        q_by_radius={radius:ca_measures(xyz,radius)[1] for radius in CONTACT_RADII}
        for frame in range(len(xyz)):
            perframe.append({"run_id":"s2-pilot-02","task_id":task,"result_id":result["result_id"],
                "seed":result["seed"],"frame_id_0based":frame,"physical_time_ps":(frame+1)*0.5,
                "input_sha256":result["artifact_sha256"]["dcd_path"],
                "analysis_commit":analysis_commit,"plan_commit":plan_commit,"parameter_id":"A1-physical-features",
                "Rg_CA_A":float(rg[frame]),"R_ee_A":float(ree[frame]),
                **{f"Q_long_{radius:g}A":float(q_by_radius[radius][frame]) for radius in CONTACT_RADII}})
        ac[task]={"Rg_CA":autocorrelation(rg),"R_ee":autocorrelation(ree)} if "1000ps" in task else None
        features=distance_features(xyz)
        for radius in CONTACT_RADII:
            _,q,_,counts=ca_measures(xyz,radius)
            if "1000ps" in task:
                ac[task][f"Q_long_r{radius:g}"]=autocorrelation(q)
            for representation in ("Rg_Q","Rg_Ree"):
                if representation=="Rg_Ree" and radius!=8.0: continue
                y=q if representation=="Rg_Q" else ree
                widths=Q_WIDTHS if representation=="Rg_Q" else REE_WIDTHS
                for wx in RG_WIDTHS:
                    for wy in widths:
                        for shifted in (False,True):
                            label=bins(rg,y,wx,wy,shifted,
                                       q_contact_counts=counts if representation=="Rg_Q" else None)
                            summary=occupancy(label)
                            base={"run_id":"s2-pilot-02","task_id":task,"seed":result["seed"],"result_id":result["result_id"],
                                  "frame_id_0based":[0,len(xyz)-1],"physical_time_ps":[0.5,len(xyz)*0.5],
                                  "input_sha256":result["artifact_sha256"]["dcd_path"],
                                  "analysis_commit":analysis_commit,"plan_commit":plan_commit,
                                  "representation":representation,"contact_radius_A":radius if representation=="Rg_Q" else None,
                                  "rg_bin_A":wx,"second_bin":wy,"origin_half_bin":shifted,
                                  "parameter_id":f"{representation}-r{radius:g}-wx{wx:g}-wy{wy:g}-half{int(shifted)}"}
                            flags={"one_frame_one_state":summary["U_over_N"]>=0.8,
                                   "collapse":summary["U"]<=1,
                                   "jitter":summary["transition_rate"]>=0.8 and summary["dwell_run_frames_median"]==1}
                            stride_counts={}
                            for stride in STRIDES:
                                sub=occupancy(label[::stride])["U"]
                                if sub>summary["U"]: raise AssertionError("Subsample increased U")
                                stride_counts[str(stride)]=sub
                            flags["sampling_sensitive"]=stride_counts["10"]/summary["U"]<0.5
                            trim={}
                            if "1000ps" in task:
                                for cutoff in (20,100):
                                    trim[str(cutoff)]={"N":int(np.sum((frame_ids+1)*0.5>cutoff)),
                                        "U":occupancy(label[(frame_ids+1)*0.5>cutoff])["U"]}
                            allrows.append({**base,"N":summary["N"],"U":summary["U"],
                                            "U_over_N":summary["U_over_N"],"transition_rate":summary["transition_rate"],
                                            "singleton_fraction":summary["singleton_fraction_of_occupied_bins"],
                                            "dwell_run_frames_median":summary["dwell_run_frames_median"],
                                            "stride_U":stride_counts,"trim_time_gt_ps":trim,"flags":flags})
                            if "1000ps" in task:
                                curves.append({**base,"physical_time_ps":((frame_ids+1)*0.5).tolist(),
                                               "frame_id_0based":frame_ids.tolist(),"cumulative_U":summary["cumulative_U"],
                                               "visit_frequencies":summary["visit_frequencies"],
                                               "dwell_observed_span_ps_median":summary["dwell_observed_span_ps_median"]})
                                # Exact duplicate and permutation final-set controls.
                                repeat=occupancy(np.concatenate((label,label)))["U"]
                                perm=occupancy(label[::-1])["U"]
                                if repeat!=summary["U"] or perm!=summary["U"]: raise AssertionError("Set invariant failed")
                                transform=xyz.copy(); transform=transform @ np.array([[0,1,0],[-1,0,0],[0,0,1]])+np.array([10,-7,3])
                                r2,q2,e2,c2=ca_measures(transform,radius)
                                if max(np.max(np.abs(rg-r2)),np.max(np.abs(q-q2)),np.max(np.abs(ree-e2)))>1e-6:
                                    raise AssertionError("Rigid invariance of measures failed")
                                label2=bins(r2,q2 if representation=="Rg_Q" else e2,wx,wy,shifted,
                                            q_contact_counts=c2 if representation=="Rg_Q" else None)
                                changed=np.any(label2!=label,axis=1)
                                ox,oy=(wx/2,wy/2) if shifted else (0,0)
                                xb=np.abs((rg-ox)/wx-np.round((rg-ox)/wx))*wx <=1e-6
                                yb=np.abs((y-oy)/wy-np.round((y-oy)/wy))*wy <=1e-6
                                if np.any(changed & ~(xb|yb)): raise AssertionError("Nonboundary rigid bin flip")
                                negatives.append({**base,"repeat_U":repeat,"permuted_U":perm,
                                                  "rigid_changed_boundary_frames":int(np.sum(changed)),
                                                  "rigid_changed_nonboundary_frames":0})
        if "1000ps" in task:
            # Diagnostic only: distance to each cell's first observed frame.
            # This does not adapt bin widths or redefine the held-out library.
            for representation,y,width in (("Rg_Q",q_by_radius[8.0],0.05),("Rg_Ree",ree,2.0)):
                label=bins(rg,y,1.0,width,
                           q_contact_counts=ca_measures(xyz,8.0)[3] if representation=="Rg_Q" else None)
                groups={}
                for i,key in enumerate(map(tuple,label)):
                    groups.setdefault(key,[]).append(i)
                for key,frames in sorted(groups.items()):
                    ds=drmsd(features[frames],features[frames[0]])
                    mixing.append({"task_id":task,"seed":result["seed"],"result_id":result["result_id"],
                        "input_sha256":result["artifact_sha256"]["dcd_path"],"analysis_commit":analysis_commit,
                        "plan_commit":plan_commit,"parameter_id":f"{representation}-baseline-within-cell",
                        "representation":representation,"bin":list(key),"frames":len(frames),
                        "first_frame_id_0based":frames[0],"to_first_dRMSD_A_median_p90_max":
                        [float(np.median(ds)),float(np.percentile(ds,90)),float(np.max(ds))]})
    (out/"coverage-sensitivity.json").write_text(json.dumps(allrows,indent=2,allow_nan=False))
    (out/"physical-features.json").write_text(json.dumps(perframe,indent=2,allow_nan=False))
    (out/"coverage-curves.json").write_text(json.dumps(curves,indent=2,allow_nan=False))
    (out/"coverage-negative-controls.json").write_text(json.dumps(negatives,indent=2))
    (out/"autocorrelation.json").write_text(json.dumps(ac,indent=2,allow_nan=False))
    (out/"within-cell-drmsd.json").write_text(json.dumps(mixing,indent=2,allow_nan=False))
    cal=distance_features(data["md-1000ps-r0"][1]); hold=distance_features(data["md-1000ps-r1"][1])
    a2=[]
    for eps in EPSILONS:
        ids=centers(cal,eps)
        lib=cal[ids]
        source_xyz=data["md-1000ps-r0"][1]
        rotated=source_xyz @ np.array([[0,1,0],[-1,0,0],[0,0,1]])+np.array([10,-7,3])
        if not np.allclose(distance_features(rotated),cal,atol=1e-6,rtol=0):
            raise AssertionError("A2 rigid distance invariance failed")
        frozen=out/f"centers-eps-{eps:g}.npy"
        np.save(frozen,lib,allow_pickle=False)
        for task,feats in (("md-1000ps-r0",cal),("md-1000ps-r1",hold)):
            visit=center_visits(feats,lib,ids,eps)
            repeated=center_visits(np.concatenate((feats,feats)),lib,ids,eps)
            permuted=center_visits(feats[::-1],lib,ids,eps)
            stride_visits={str(stride):center_visits(feats[::stride],lib,ids,eps)["visited_centers"]
                           for stride in STRIDES}
            if (repeated["visited_centers"]!=visit["visited_centers"] or
                    permuted["visited_centers"]!=visit["visited_centers"] or
                    any(not set(v)<=set(visit["visited_centers"]) for v in stride_visits.values())):
                raise AssertionError("Center-library negative control failed")
            rr=data[task][0]
            a2.append({"run_id":"s2-pilot-02","task_id":task,"result_id":rr["result_id"],
                       "seed":rr["seed"],"frame_id_0based":[0,len(feats)-1],
                       "physical_time_ps":[0.5,len(feats)*0.5],
                       "input_sha256":rr["artifact_sha256"]["dcd_path"],
                       "analysis_commit":analysis_commit,"plan_commit":plan_commit,
                       "parameter_id":f"A2-eps-{eps:g}","epsilon_A":eps,"center_frame_ids_0based":ids,
                       "center_sha256":sha256_file(frozen),**visit,
                       "negative_controls":{"duplicate_same_visited":True,"permuted_same_visited":True,
                                            "stride_visited_centers":stride_visits},
                       "flags":{"center_collapse":len(ids)==1,"center_too_fine":len(ids)/200>=0.8,
                                "library_unrepresentative":visit["out_of_library_fraction"]>0.5}})
    (out/"center-library-results.json").write_text(json.dumps(a2,indent=2,allow_nan=False))
    # Task completion is a worker-end proxy, not frame production or verified publication.
    finished=sorted(((name,v[0]["started_unix_s"],v[0]["ended_unix_s"]) for name,v in data.items()),key=lambda x:x[2])
    origin=min(start for _,start,_ in finished)
    unions={"Rg_Q":set(),"Rg_Ree":set()};steps=[]
    for name,started,ended in finished:
        xyz=data[name][1]
        rg,q,ree,counts=ca_measures(xyz)
        unions["Rg_Q"].update(map(tuple,bins(rg,q,1.0,0.05,q_contact_counts=counts)))
        unions["Rg_Ree"].update(map(tuple,bins(rg,ree,1.0,2.0)))
        steps.append({"task_id":name,"worker_start_unix_s":started,"worker_end_unix_s":ended,
                      "worker_end_since_first_worker_start_s":ended-origin,
                      "union_U_Rg_Q":len(unions["Rg_Q"]),"union_U_Rg_Ree":len(unions["Rg_Ree"])})
    (out/"time-axis-worker-proxy.json").write_text(json.dumps({"status":"DERIVED_PROXY_NOT_MEASURED_PUBLICATION",
        "origin":"earliest worker start, excludes controller startup","total_controller_run_s_from_summary":
        json.loads((run/"summary.json").read_text())["end_to_end_s"],
        "warning":"Worker end excludes final serialization/return; no per-frame wall time, no verified batch publication event",
        "steps":steps},indent=2))
    (out/"coverage-manifest.json").write_text(json.dumps({"status":"DERIVED","raw_checked":len(checks),
        "plan_commit":plan_commit,"analysis_commit":analysis_commit,"elapsed_s":time.monotonic()-t0,
        "tasks":{k:{"seed":v[0]["seed"],"frames":len(v[1]),"dcd_sha256":v[0]["artifact_sha256"]["dcd_path"],
                    "pdb_sha256":v[0]["artifact_sha256"]["pdb_path"]} for k,v in data.items()},
        "sampling_interval_ps":0.5,"independent_seed_groups":2,"calibration_seed":2026102401,
        "internal_holdout_seed":2026102402,"time_boundary":"physical MD time only; no measured per-frame wall time"},indent=2))
