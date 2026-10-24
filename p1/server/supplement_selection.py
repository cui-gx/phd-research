"""S2 supplement B: fixed 800-frame LOF audit and bounded matched CPU updates."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
import time
import numpy as np

from .science import sha256_file
from .supplement_coverage import local_path, load_trajectory, ca_measures, distance_features, drmsd

SEEDS=(2026102411,2026102412,2026102413)
INFER_SEED=2026102404


def score_order(rows):
    if len(rows)!=800 or any(not np.isfinite(float(r["lof"])) for r in rows):
        raise ValueError("LOF scores must be finite for all 800 candidates")
    return sorted(rows,key=lambda r:(float(r["lof"]),str(r["result_id"]),int(r["frame"])))


def compare(a,b):
    from scipy.stats import spearmanr
    ka=[(r["result_id"],int(r["frame"])) for r in a]
    kb=[(r["result_id"],int(r["frame"])) for r in b]
    if ka!=kb: raise ValueError("Candidate order/identity mismatch")
    aa,bb=score_order(a),score_order(b)
    top={}
    for k in (1,10,100):
        sa={(r["result_id"],int(r["frame"])) for r in aa[:k]}
        sb={(r["result_id"],int(r["frame"])) for r in bb[:k]}
        top[str(k)]={"intersection":len(sa&sb),"jaccard":len(sa&sb)/len(sa|sb),"overlap_fraction":len(sa&sb)/k}
    sp=spearmanr([r["lof"] for r in a],[r["lof"] for r in b]).statistic
    return {"top_k":top,"spearman_800":None if not np.isfinite(sp) else float(sp),
            "top1_changed":(aa[0]["result_id"],aa[0]["frame"])!=(bb[0]["result_id"],bb[0]["frame"]),
            "top1_a":{"result_id":aa[0]["result_id"],"frame_id_0based":int(aa[0]["frame"])},
            "top1_b":{"result_id":bb[0]["result_id"],"frame_id_0based":int(bb[0]["frame"])}}


def snapshot_contacts(run):
    snapshot=json.loads((run/"tasks/infer-frozen-r0/science/snapshot.json").read_text())
    for name in ("infer-frozen-r1","infer-updated-r0","infer-updated-r1"):
        if json.loads((run/"tasks"/name/"science/snapshot.json").read_text())!=snapshot:
            raise ValueError("Inference snapshots differ")
    if [m["frames"] for m in snapshot["results"]]!=[400,400]: raise ValueError("Expected 400+400 pool")
    contacts=[]; ids=[]; sha=[]
    for member in snapshot["results"]:
        p=local_path(run,member["contact_map_path"])
        if sha256_file(p)!=member["contact_map_path_sha256"]: raise ValueError("Contact input mismatch")
        arr=np.load(p,allow_pickle=True)
        if len(arr)!=400: raise ValueError("Contact count mismatch")
        contacts.extend(arr)
        task=p.parents[1].name
        rr=json.loads((run/"tasks"/task/"result.json").read_text())
        ids.extend([{"run_id":"s2-pilot-02","task_id":task,"seed":rr["seed"],
                     "result_id":member["result_id"],"frame":i,"frame_id_0based":i,
                     "physical_time_ps":(i+1)*0.5,"input_sha256":member["contact_map_path_sha256"]}
                    for i in range(400)])
        sha.append(sha256_file(p))
    obj=np.empty(800,dtype=object)
    for i,v in enumerate(contacts): obj[i]=v
    return snapshot,obj,ids,sha


def physical_top1(run,a,b):
    lookup={}
    for task in ("md-200ps-r0","md-200ps-r1"):
        result,xyz,_=load_trajectory(run,task)
        lookup[result["result_id"]]=xyz
    x=lookup[a["result_id"]][a["frame_id_0based"]]
    y=lookup[b["result_id"]][b["frame_id_0based"]]
    f=lambda z:{"Rg_CA_A":float(ca_measures(z)[0]),"Q_long_8A":float(ca_measures(z)[1]),
                "R_ee_A":float(ca_measures(z)[2])}
    return {"a":f(x),"b":f(y),"CA_dRMSD_A":float(drmsd(distance_features(x),distance_features(y)))}


def old_scores(run,model):
    return json.loads((run/"tasks"/f"infer-{model}-r0"/"science/candidate-scores.json").read_text())


def seed_rng(torch,seed):
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)


def tensor_digest(torch,state):
    h=hashlib.sha256()
    for k,v in sorted(state.items()):
        h.update(k.encode());h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def optimizer_digest(torch,value):
    h=hashlib.sha256()
    def visit(v):
        if isinstance(v,dict):
            h.update(b"dict")
            for k in sorted(v,key=lambda x:str(x)):
                visit(str(k));visit(v[k])
        elif isinstance(v,(list,tuple)):
            h.update(b"sequence");h.update(str(len(v)).encode())
            for x in v:visit(x)
        elif isinstance(v,torch.Tensor):
            h.update(b"tensor");h.update(str(v.dtype).encode());h.update(str(tuple(v.shape)).encode())
            h.update(v.detach().cpu().numpy().tobytes())
        else:
            h.update(repr(v).encode())
    visit(value)
    return h.hexdigest()


def analyze(run,out,plan_commit,analysis_commit):
    import torch
    from sklearn.neighbors import LocalOutlierFactor
    from torch.utils.data import DataLoader
    from mdlearn.data.datasets.contact_map import ContactMapDataset
    from mdlearn.nn.models.vae.symmetric_conv2d_vae import SymmetricConv2dVAETrainer
    run,out=Path(run),Path(out)
    out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    torch.set_num_threads(2)
    snapshot,contacts,ids,input_hashes=snapshot_contacts(run)
    before=old_scores(run,"frozen"); updated=old_scores(run,"updated")
    if [(r["result_id"],r["frame"]) for r in before] != [(r["result_id"],r["frame"]) for r in ids]:
        raise ValueError("Historical scores not same fixed pool")
    historical=compare(before,updated)
    historical["top1_physical"]=physical_top1(run,historical["top1_a"],historical["top1_b"])
    historical["same_seed_repeated_exact"]={name:
        old_scores(run,name)==json.loads((run/"tasks"/f"infer-{name}-r1"/"science/candidate-scores.json").read_text())
        for name in ("frozen","updated")}
    (out/"historical-lof-only.json").write_text(json.dumps(historical,indent=2))
    config=json.loads(Path("configs/p1_server_science.json").read_text())["cvae"]
    config.update(device="cpu",num_data_workers=0,prefetch_factor=None,verbose=False)
    checkpoint_path=local_path(run,json.loads((run/"tasks/train-before/result.json").read_text())["model_weight_path"])
    expected=json.loads((run/"tasks/train-before/result.json").read_text())["model_weight_sha256"]
    if sha256_file(checkpoint_path)!=expected:raise ValueError("Common checkpoint SHA mismatch")
    checkpoint=torch.load(checkpoint_path,map_location="cpu",weights_only=True)
    if not {"model_state_dict","optimizer_state_dict"}<=set(checkpoint):
        raise ValueError("Cannot prove complete model+optimizer restoration")
    if "scheduler_state_dict" in checkpoint and config.get("scheduler_name") is None:
        raise ValueError("Checkpoint scheduler mismatch")
    initial_digest=tensor_digest(torch,checkpoint["model_state_dict"])
    initial_optimizer_digest=optimizer_digest(torch,checkpoint["optimizer_state_dict"])
    def trainer_loaded(seed):
        seed_rng(torch,seed)
        trainer=SymmetricConv2dVAETrainer(**config)
        trainer.model.load_state_dict(copy.deepcopy(checkpoint["model_state_dict"]))
        trainer.optimizer.load_state_dict(copy.deepcopy(checkpoint["optimizer_state_dict"]))
        if trainer.scheduler is not None:
            trainer.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        if tensor_digest(torch,trainer.model.state_dict())!=initial_digest:raise ValueError("Model restore digest failed")
        if optimizer_digest(torch,trainer.optimizer.state_dict())!=initial_optimizer_digest:
            raise ValueError("Optimizer restore digest failed")
        seed_rng(torch,seed)  # initialization consumed RNG; re-establish pair state
        return trainer
    def infer(trainer,label):
        seed_rng(torch,INFER_SEED)
        inference_start=time.monotonic()
        embedding,*_=trainer.predict(X=contacts,inference_batch_size=64)
        if embedding.shape[0]!=800 or not np.isfinite(embedding).all():raise ValueError("Nonfinite embedding")
        lof=LocalOutlierFactor(n_neighbors=20,metric="minkowski",p=2,novelty=False,n_jobs=2)
        lof.fit(embedding)
        rows=[{**ident,"lof":float(value),"analysis_commit":analysis_commit,"plan_commit":plan_commit,
               "parameter_id":"LOF-k20-minkowski-p2-noveltyFalse"}
              for ident,value in zip(ids,lof.negative_outlier_factor_)]
        if any(not np.isfinite(r["lof"]) for r in rows):raise ValueError("Nonfinite LOF")
        (out/f"scores-{label}.json").write_text(json.dumps(rows,indent=2))
        np.save(out/f"embeddings-{label}.npy",embedding,allow_pickle=False)
        return rows,time.monotonic()-inference_start
    f0=trainer_loaded(INFER_SEED)
    f0_scores,f0_time=infer(f0,"F0")
    f0_repeat,f0_repeat_time=infer(f0,"F0-repeat")
    repeat_exact=f0_scores==f0_repeat
    if not repeat_exact:raise ValueError("F0 CPU repeated inference failed")
    comparisons=[]; arms=[]; failures=[]
    for pair_index,seed in enumerate(SEEDS):
        rng=np.random.default_rng(seed)
        order=rng.permutation(800)
        old_indices=np.r_[np.arange(400),np.arange(400)]
        mixed_indices=np.arange(800)
        pair=[]
        for arm,index_base in (("F1-old",old_indices),("F2-mix",mixed_indices)):
            arm_start=time.monotonic()
            try:
                exposure=index_base[order]
                if len(exposure)!=800 or len(exposure.reshape(200,4))!=200:
                    raise ValueError("Exposure shape mismatch")
                if arm=="F1-old" and not np.all(np.bincount(exposure,minlength=800)[:400]==2):
                    raise ValueError("Old exposures not twice each")
                if arm=="F2-mix" and not np.all(np.bincount(exposure,minlength=800)==1):
                    raise ValueError("Mixed exposures not once each")
                trainer=trainer_loaded(seed)
                trainer.model.train()
                ds=ContactMapDataset(contacts[exposure],trainer.input_shape)
                loader=DataLoader(ds,batch_size=4,shuffle=False,num_workers=0,drop_last=False)
                # Vendor _train supplies its original loss, gradient clipping and RMSprop step.
                step_count=0
                original_step=trainer.optimizer.step
                def counted_step(*args,**kwargs):
                    nonlocal step_count
                    if time.monotonic()-arm_start>90:
                        raise TimeoutError(f"{arm}: exceeded 90s before optimizer step {step_count+1}")
                    if time.monotonic()-start>900:
                        raise TimeoutError(f"B exceeded 900s before optimizer step {step_count+1}")
                    step_count+=1
                    return original_step(*args,**kwargs)
                trainer.optimizer.step=counted_step
                loss=trainer._train(loader)
                trainer.optimizer.step=original_step
                elapsed=time.monotonic()-arm_start
                if step_count!=200 or elapsed>90 or time.monotonic()-start>900:
                    raise TimeoutError(f"{arm}: steps={step_count}, train_s={elapsed:.3f}")
                digest=tensor_digest(torch,trainer.model.state_dict())
                torch.save({"model_state_dict":trainer.model.state_dict(),"optimizer_state_dict":trainer.optimizer.state_dict()},
                           out/f"checkpoint-{arm}-seed-{seed}.pt")
                score,infertime=infer(trainer,f"{arm}-seed-{seed}")
                batch_hash=hashlib.sha256(exposure.astype("<i8").tobytes()).hexdigest()
                row={"arm":arm,"seed":seed,"pair_index":pair_index,"initial_model_digest":initial_digest,
                     "initial_optimizer_digest":initial_optimizer_digest,
                     "initial_checkpoint_sha256":expected,"exposure_count":800,"batch_size":4,
                     "optimizer_steps":step_count,"batch_index_sha256":batch_hash,
                     "exposure_frame_ids_0based":exposure.tolist(),"loss_tuple":list(map(float,loss)),
                     "train_s":elapsed,"inference_s":infertime,"final_model_digest":digest,
                     "final_checkpoint_sha256":sha256_file(out/f"checkpoint-{arm}-seed-{seed}.pt"),
                     "selection_top1":score_order(score)[0]}
                arms.append(row)
                pair.append((arm,score))
            except Exception as e:
                failures.append({"seed":seed,"arm":arm,"error":repr(e),"elapsed_B_s":time.monotonic()-start})
                break
        if failures:break
        if optimizer_digest(torch,checkpoint["optimizer_state_dict"])!=initial_optimizer_digest:
            raise ValueError("In-memory common checkpoint optimizer was modified")
        old,mix=pair[0][1],pair[1][1]
        for label,a,b in (("F1_vs_F0",f0_scores,old),("F2_vs_F0",f0_scores,mix),("F2_vs_F1",old,mix)):
            result=compare(a,b)
            result["top1_physical"]=physical_top1(run,result["top1_a"],result["top1_b"])
            comparisons.append({"seed":seed,"comparison":label,**result})
        if time.monotonic()-start>900:break
    (out/"matched-arms.json").write_text(json.dumps(arms,indent=2,allow_nan=False))
    (out/"selection-comparison.json").write_text(json.dumps(comparisons,indent=2,allow_nan=False))
    (out/"selection-manifest.json").write_text(json.dumps({"status":"MEASURED" if len(arms)==6 else "INCOMPLETE",
        "historical_cuda_comparison":"separate", "f0_cpu_repeat_exact":repeat_exact,
        "f0_cpu_inference_s":[f0_time,f0_repeat_time],"plan_commit":plan_commit,"analysis_commit":analysis_commit,
        "common_checkpoint_sha256":expected,"common_model_digest":initial_digest,
        "common_optimizer_digest":initial_optimizer_digest,
        "snapshot_id":snapshot["snapshot_id"],"contact_input_sha256":input_hashes,
        "elapsed_B_s":time.monotonic()-start,"failures":failures},indent=2,allow_nan=False))
