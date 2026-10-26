"""承認済みB1 Pilotの科学タスク。既存OpenMM/mdlearn関数を再利用する。"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import random
import resource
import sys
import time
import traceback
import numpy as np
from .gq_r2 import descriptors, geometry, sha, dump
from .science import ROOT


def require_hash(path, expected):
    if sha(path)!=expected:raise ValueError('入力SHAが一致しません。')


def indices(times, valid, lo, hi, n):
    """指定時間区間から異なるフレームIDを等間隔に抽出する。"""
    eligible=np.flatnonzero((times>lo)&(times<=hi)&valid)
    if len(eligible)<n:raise ValueError('適格フレームが不足しています。重複で補充しません。')
    result=eligible[np.linspace(0,len(eligible)-1,n,dtype=int)]
    if len(set(result.tolist()))!=n:raise ValueError('抽出IDが重複しています。')
    return result


def md(req,out):
    import openmm as mm
    from openmm import app,unit as u
    from .gq_science import build,system_record
    begin=time.perf_counter();sim,pdb,details=build('no_cutoff',req['seed'])
    system=system_record(sim,details,out)
    expected=ROOT.parent/'runs/gq-r1-20261026/tasks/root-11-1ns/science/system.xml'
    if sha(out/'system.xml')!=sha(expected):raise ValueError('登録済みNoCutoff Systemが変化しています。')
    if req.get('checkpoint'):
        require_hash(req['checkpoint'],req['checkpoint_sha256']);sim.loadCheckpoint(req['checkpoint'])
        initial=float(sim.context.getState().getTime().value_in_unit(u.picosecond))
        if abs(initial-2000)>1e-5:raise ValueError('継続の時間境界が不正です。')
        mode='full_checkpoint_continuation'
    else:
        xyz=np.array(pdb.positions.value_in_unit(u.angstrom),dtype=float)
        if req.get('selected'):
            require_hash(req['selected'],req['selected_sha256']);xyz=np.load(req['selected'])
        np.save(out/'initial-coordinates-A.npy',xyz,allow_pickle=False)
        sim.context.setPositions(xyz*u.angstrom)
        with (out/'initial.pdb').open('x') as f:app.PDBFile.writeFile(pdb.topology,xyz*u.angstrom,f)
        sim.minimizeEnergy(tolerance=10*u.kilojoule_per_mole/u.nanometer,maxIterations=1000)
        sim.context.setVelocitiesToTemperature(300*u.kelvin,req['seed'])
        initial=0.;mode='coordinate_minimization_velocity_reseed'
    if not (out/'initial.pdb').exists():
        with (out/'initial.pdb').open('x') as f:app.PDBFile.writeFile(pdb.topology,sim.context.getState(getPositions=True).getPositions(),f)
    init_s=time.perf_counter()-begin
    dcd=app.DCDReporter(str(out/'sim.dcd'),250)
    log=app.StateDataReporter(str(out/'sim.csv'),250,step=True,time=True,potentialEnergy=True,kineticEnergy=True,totalEnergy=True,temperature=True)
    sim.reporters.extend([dcd,log]);start=time.perf_counter()
    sim.step(int(req['length_ns']*500000));integrate_s=time.perf_counter()-start
    start=time.perf_counter();sim.saveCheckpoint(str(out/'final.chk'))
    state=sim.context.getState(getPositions=True,getEnergy=True)
    if not np.isfinite(state.getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)):raise ValueError('MDエネルギーが非有限です。')
    with (out/'final.pdb').open('x') as f:app.PDBFile.writeFile(pdb.topology,state.getPositions(),f)
    sim.reporters.clear();dcd._out.close();log._out.close()
    end=float(state.getTime().value_in_unit(u.picosecond));del sim
    return dict(initial_time_ps=initial,final_time_ps=end,length_ns=req['length_ns'],seed=req['seed'],restart=mode,
                initialization_s=init_s,integration_with_reporter_s=integrate_s,checkpoint_final_IO_s=time.perf_counter()-start,
                system=system,internal_s=time.perf_counter()-begin)


def prepare(req,out):
    import MDAnalysis as mda
    from MDAnalysis.lib.distances import calc_dihedrals
    from MDAnalysis.analysis.distances import contact_matrix
    from .supplement_coverage import ca_measures
    task=Path(req['md_dir']);require_hash(task/'sim.dcd',req['dcd_sha256'])
    spec_path=ROOT.parent/'artifacts/gq-r2-20261026/analysis-v2/synthetic-source.npz'
    require_hash(spec_path,'53bd1ca4f33765a9382a605edacec9c6ce4e8dcd660b7848e0ca85bef6dd3d50')
    spec=dict(np.load(spec_path));spec.pop('xyz')
    u=mda.Universe(str(task/'initial.pdb'),str(task/'sim.dcd'))
    if len(u.atoms)!=504 or len(u.residues)!=28:raise ValueError('原子対応が不正です。')
    if not np.array_equal(u.select_atoms('name CA').indices,spec['ca']):raise ValueError('Cα順序が不正です。')
    groups=np.array([g.indices for r in u.residues for sel in (r.phi_selection,r.psi_selection) if (g:=sel()) is not None])
    arrays=[];values=[];reasons=[];angles=[];contacts=[]
    for ts in u.trajectory:
        xyz=u.atoms.positions.astype(float);v,b=geometry(xyz,spec)
        angle=calc_dihedrals(*[xyz[groups[:,k]] for k in range(4)])
        b[0]|=not np.isfinite(angle).all()
        values.append(v);reasons.append(b);angles.append(angle);x=xyz[spec['ca']];arrays.append(x)
        if req.get('contacts'):
            coo=contact_matrix(x.astype(np.float32),8.,box=None,returntype='sparse').tocoo()
            contacts.append(np.r_[coo.row,coo.col].astype(np.int16))
    ca=np.array(arrays);valid=~np.array(reasons).any(axis=1)
    state=np.genfromtxt(task/'sim.csv',delimiter=',',skip_header=1)
    times=state[:,1]
    if len(state)!=len(ca) or len(ca)!=int(req['length_ns']*2000):raise ValueError('MD出力数が不一致です。')
    rg,q,ree,count=ca_measures(ca)
    np.savez_compressed(out/'features.npz',ca=ca,distances_A=descriptors(ca),angles_rad=angles,valid=valid,time_ps=times,
                        rg_A=rg,q=q,state=state,quality_values=values,reasons=reasons)
    if contacts:
        x=np.empty(len(contacts),dtype=object)
        for i,c in enumerate(contacts):x[i]=c
        np.save(out/'contacts.npy',x,allow_pickle=True)
    quality=dict(frames=len(ca),valid=int(valid.sum()),reasons=np.array(reasons).sum(axis=0).tolist(),
        geometry_min=np.array(values).min(axis=0).tolist(),geometry_max=np.array(values).max(axis=0).tolist(),
        temperature_mean_K=float(state[:,-1].mean()),time_ps=[float(times[0]),float(times[-1])])
    dump(out/'quality.json',quality)
    return quality


def pools(req,out):
    dirs=[Path(v) for v in req['prepared']]
    data=[dict(np.load(v/'features.npz')) for v in dirs]
    a={k:np.concatenate([d[k] for d in data]) for k in data[0]}
    x=np.concatenate([np.load(v/'contacts.npy',allow_pickle=True) for v in dirs])
    old=indices(a['time_ps'],a['valid'],100,1600,800)
    val=indices(a['time_ps'],a['valid'],1700,2000,200)
    new=indices(a['time_ps'],a['valid'],2000,3600,400) if len(dirs)==2 else np.array([],dtype=int)
    pool=np.flatnonzero((a['time_ps']>100)&a['valid'])
    for ids in [old,val,new]:
        if len(ids) and len({np.ascontiguousarray(a['ca'][i]).tobytes() for i in ids})!=len(ids):
            raise ValueError('学習/検証に同一座標フレームが重複しています。')
    np.save(out/'contacts.npy',x,allow_pickle=True)
    np.savez_compressed(out/'features.npz',**a)
    sets=dict(old=old.tolist(),validation=val.tolist(),new=new.tolist(),candidate=pool.tolist(),
              F1=old.tolist(),F2=np.r_[old[::2],new].tolist() if len(new) else [])
    dump(out/'indices.json',sets)
    return dict(old_unique=len(old),new_unique=len(new),validation=len(val),candidates=len(pool),
                old_max_ps=float(a['time_ps'][old].max()),new_min_ps=float(a['time_ps'][new].min()) if len(new) else None,
                data_stage='final_decision' if len(dirs)==2 else 'old_only_M0')


def rng_seed(torch,seed):
    from .science import _seed_all
    _seed_all(seed,torch)


def ai(req,out):
    import torch
    from torch.utils.data import DataLoader
    from mdlearn.data.datasets.contact_map import ContactMapDataset
    from sklearn.neighbors import LocalOutlierFactor
    from .science import _trainer,load_config
    from .supplement_selection import tensor_digest,optimizer_digest
    begin=time.perf_counter();pool=Path(req['pool'])
    require_hash(pool/'contacts.npy',req['contacts_sha256']);require_hash(pool/'indices.json',req['indices_sha256'])
    x=np.load(pool/'contacts.npy',allow_pickle=True);sets=json.loads((pool/'indices.json').read_text())
    cfg=load_config();dump(out/'recipe.json',dict(cvae=cfg['cvae'],effective_split='事前時間split、fit既定splitは不使用',normalization='binary_contact_no_learned_scaling'));trainer,torch=_trainer(dict(science_config=cfg,device='cuda',seed=req['seed'],cpu_threads=2))
    parent_sha=None
    if req.get('checkpoint'):
        require_hash(req['checkpoint'],req['checkpoint_sha256'])
        saved=torch.load(req['checkpoint'],map_location='cpu',weights_only=True)
        trainer.model.load_state_dict(copy.deepcopy(saved['model_state_dict']))
        trainer.optimizer.load_state_dict(copy.deepcopy(saved['optimizer_state_dict']))
        if trainer.scheduler is not None:trainer.scheduler.load_state_dict(copy.deepcopy(saved['scheduler_state_dict']))
        parent_sha=req['checkpoint_sha256']
        if tensor_digest(torch,trainer.model.state_dict())!=saved['model_digest']:raise ValueError('モデル復元に失敗しました。')
        if optimizer_digest(torch,trainer.optimizer.state_dict())!=saved['optimizer_digest']:raise ValueError('Optimizer復元に失敗しました。')
    initial_model=tensor_digest(torch,trainer.model.state_dict());initial_optimizer=optimizer_digest(torch,trainer.optimizer.state_dict())
    rng_seed(torch,req['seed']);torch.cuda.synchronize();setup_s=time.perf_counter()-begin
    initial_rng=dict(torch_cpu=torch.get_rng_state(),torch_cuda=torch.cuda.get_rng_state_all(),python=random.getstate(),numpy=(str(np.random.get_state()[0]),np.random.get_state()[1].tolist(),int(np.random.get_state()[2]),int(np.random.get_state()[3]),float(np.random.get_state()[4])))
    initial_rng_digest=optimizer_digest(torch,initial_rng)
    if req['operation']=='train':
        arm=req['arm'];ids=np.array(sets['old'] if arm=='M0' else sets[arm],dtype=int)
        if len(ids)!=800 or len(set(ids.tolist()))!=800:raise ValueError('学習用の相異なる800個のIDという条件を満たしません。')
        order=np.random.default_rng(req['seed']).permutation(800);exposure=ids[order]
        dataset=ContactMapDataset(x[exposure],trainer.input_shape)
        loader=DataLoader(dataset,batch_size=4,shuffle=False,num_workers=0,drop_last=False)
        trainer.model.train();count=0;losses=[];stash={}
        step=trainer.optimizer.step;recon=trainer.model.recon_loss;kld=trainer.model.kld_loss
        def tracked_recon(*args,**kwargs):
            value=recon(*args,**kwargs);stash['rec']=value.detach();return value
        def tracked_kld(*args,**kwargs):
            value=kld(*args,**kwargs);stash['kld']=value.detach();return value
        def counted(*args,**kwargs):
            nonlocal count
            step(*args,**kwargs);count+=1
            losses.append(float((trainer.lambda_rec*stash['rec']+stash['kld']).cpu()))
        trainer.optimizer.step=counted;trainer.model.recon_loss=tracked_recon;trainer.model.kld_loss=tracked_kld
        start=time.perf_counter()
        try:loss=trainer._train(loader)
        finally:
            trainer.optimizer.step=step;trainer.model.recon_loss=recon;trainer.model.kld_loss=kld
        torch.cuda.synchronize();fit_s=time.perf_counter()-start
        if count!=200 or not np.isfinite(loss).all() or not np.isfinite(losses).all() or len(losses)!=200:raise ValueError('200歩またはlossが不正です。')
        if not all(bool(torch.isfinite(v).all()) for v in trainer.model.state_dict().values()):raise ValueError('モデルに非有限値があります。')
        digest=tensor_digest(torch,trainer.model.state_dict());opt_digest=optimizer_digest(torch,trainer.optimizer.state_dict())
        start=time.perf_counter()
        saved=dict(epoch=1 if arm=='M0' else 2,model_state_dict=trainer.model.state_dict(),optimizer_state_dict=trainer.optimizer.state_dict(),
                   model_digest=digest,optimizer_digest=opt_digest,optimizer_steps_this_task=count,
                   rng=dict(torch_cpu=torch.get_rng_state(),torch_cuda=torch.cuda.get_rng_state_all(),python=random.getstate(),
                            numpy=(str(np.random.get_state()[0]),np.random.get_state()[1].tolist(),int(np.random.get_state()[2]),int(np.random.get_state()[3]),float(np.random.get_state()[4]))))
        if trainer.scheduler is not None:saved['scheduler_state_dict']=trainer.scheduler.state_dict()
        torch.save(saved,out/'checkpoint.pt');checkpoint_s=time.perf_counter()-start
        rng_seed(torch,2026102671);start=time.perf_counter()
        _,vl,vr,vk=trainer.predict(X=x[np.array(sets['validation'])],inference_batch_size=64)
        torch.cuda.synchronize();val_s=time.perf_counter()-start
        dump(out/'loss.json',dict(per_step=losses,mean_loss=list(map(float,loss)),validation_loss=[float(vl),float(vr),float(vk)]))
        dump(out/'exposure.json',dict(frame_ids_0based=exposure.tolist(),batch_size=4,steps=200,permutation_positions=order.tolist()))
        return dict(arm=arm,seed=req['seed'],initial_model_digest=initial_model,initial_optimizer_digest=initial_optimizer,
            parent_checkpoint_sha256=parent_sha,initial_rng_digest=initial_rng_digest,final_model_digest=digest,final_optimizer_digest=opt_digest,
            checkpoint_sha256=sha(out/'checkpoint.pt'),optimizer_steps=count,exposures=len(exposure),training_unique=len(set(exposure.tolist())),
            setup_and_data_s=setup_s,fit_s=fit_s,checkpoint_s=checkpoint_s,validation_s=val_s,
            internal_s=time.perf_counter()-begin)
    ids=np.array(sets['candidate'],dtype=int);rng_seed(torch,2026102671);start=time.perf_counter()
    embedding,*_=trainer.predict(X=x[ids],inference_batch_size=64);torch.cuda.synchronize();embed_s=time.perf_counter()-start
    start=time.perf_counter();lof=LocalOutlierFactor(n_neighbors=20,metric='minkowski',p=2,novelty=False,n_jobs=2).fit(embedding)
    scores=lof.negative_outlier_factor_;order=np.lexsort((ids,scores))
    if not np.isfinite(embedding).all() or not np.isfinite(scores).all():raise ValueError('推論値が非有限です。')
    np.savez_compressed(out/'ranking.npz',frame_ids=ids,embedding=embedding,lof=scores,order=order)
    dump(out/'ranking.json',dict(checkpoint_sha256=parent_sha,candidate_frame_ids=ids.tolist(),ranking_frame_ids=ids[order].tolist(),
                               selected_frame=int(ids[order[0]]),top10=ids[order[:10]].tolist(),top100=ids[order[:100]].tolist(),native_reference_used=False))
    return dict(selected_frame=int(ids[order[0]]),model_digest=initial_model,checkpoint_sha256=parent_sha,candidates=len(ids),
                setup_and_load_s=setup_s,embedding_s=embed_s,LOF_and_output_s=time.perf_counter()-start,internal_s=time.perf_counter()-begin)


def main():
    req=json.loads(Path(sys.argv[1]).read_text());out=Path(req['output_dir']);out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();cpu=time.process_time()
    try:
        result=globals()[req['kind']](req,out);result.update(status='success')
    except BaseException as e:
        (out/'failure.txt').write_text(traceback.format_exc());dump(out/'failure.json',dict(error=repr(e)));raise
    finally:
        dump(out/'timing.json',dict(worker_wall_s=time.perf_counter()-start,cpu_s=time.process_time()-cpu,
              peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_sha256=sha(__file__)))
    result.update(artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    dump(out/'result.json',result)


if __name__=='__main__':main()
