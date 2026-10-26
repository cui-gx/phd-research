"""B1拡張のデータ適応と決定前状態。既存の科学関数を再利用する。"""
from __future__ import annotations
import json
import resource
import sys
import time
import traceback
from pathlib import Path
import numpy as np
from . import b1_science as core
from .gq_r2 import dump,sha,nearest,distances,circular


def combine_pool(req,out):
    """公開済み履歴だけを連結し、相対窓の学習IDを固定する。"""
    dirs=[Path(p) for p in req['prepared']]
    data=[dict(np.load(p/'features.npz')) for p in dirs]
    a={k:np.concatenate([d[k] for d in data]) for k in data[0]}
    x=np.concatenate([np.load(p/'contacts.npy',allow_pickle=True) for p in dirs])
    b=req['boundary_ps'];old=core.indices(a['time_ps'],a['valid'],b-1900,b-400+1e-5,800)
    val=core.indices(a['time_ps'],a['valid'],b-300,b+1e-5,200)
    final=req['pool_stage']=='decision'
    if not final and a['time_ps'].max()>b+1e-5:raise ValueError('M0用poolに未来データがあります。')
    new=core.indices(a['time_ps'],a['valid'],b,b+1600+1e-5,400) if final else np.array([],int)
    for ids in (old,val,new):
        if len({np.ascontiguousarray(a['ca'][i]).tobytes() for i in ids})!=len(ids):raise ValueError('同一座標で容量を補充できません。')
    candidate=np.flatnonzero((a['time_ps']>100)&a['valid'])
    if set(old)&set(new) or set(old)&set(val):raise ValueError('時間splitが重複しています。')
    sets=dict(old=old.tolist(),new=new.tolist(),validation=val.tolist(),candidate=candidate.tolist(),
              F1=old.tolist(),F2=np.r_[old[::2],new].tolist() if final else [])
    dump(out/'indices.json',sets);np.save(out/'contacts.npy',x,allow_pickle=True);np.savez_compressed(out/'features.npz',**a)
    return dict(root_id=req['root_id'],state_id=req['state_id'],boundary_ps=b,old_unique=len(old),new_unique=len(new),
                validation=len(val),candidates=len(candidate),pool_stage=req['pool_stage'],frames=len(x),
                old_max_ps=float(a['time_ps'][old].max()),new_min_ps=float(a['time_ps'][new].min()) if final else None)


def grid_cells(rg,q):
    """原点0・0.5Å×0.05の固定物理セル。クリップしない。"""
    return [tuple(v) for v in np.column_stack((np.floor(np.asarray(rg)/.5),np.floor(np.asarray(q)/.05))).astype(int)]


def js_bits(a,b):
    """経験分布のJS。空集合をゼロへ置換しない。"""
    from collections import Counter
    if not a or not b:return None
    ca,cb=Counter(a),Counter(b);keys=sorted(set(ca)|set(cb))
    p=np.array([ca[k]/len(a) for k in keys]);q=np.array([cb[k]/len(b) for k in keys]);m=(p+q)/2
    pi=p>0;qi=q>0
    return float((np.sum(p[pi]*np.log2(p[pi]/m[pi]))+np.sum(q[qi]*np.log2(q[qi]/m[qi])))/2)


def state_features(req,out):
    """更新を実行する前に履歴だけからX/Z/Wを公開する。"""
    start=time.monotonic()
    if req['inputs_available_monotonic']>start:raise ValueError('未公開入力を特徴へ使用できません。')
    pool=Path(req['pool']);a=dict(np.load(pool/'features.npz'));sets=json.loads((pool/'indices.json').read_text())
    old=np.array(sets['old']);new=np.array(sets['new']);b=req['boundary_ps']
    dd,_=nearest(a['distances_A'][new],a['distances_A'][old])
    cells=grid_cells(a['rg_A'],a['q']);o=[cells[i] for i in old];n=[cells[i] for i in new]
    ii=np.flatnonzero(a['time_ps']>100)[::4];ii=ii[a['valid'][ii]]
    earlier=ii[a['time_ps'][ii]<=b+1e-5];recent=ii[a['time_ps'][ii]>b]
    previous=set(cells[i] for i in earlier);current=set(cells[i] for i in ii);recent_cells=[cells[i] for i in recent]
    X=dict(new_nonrepeat_fraction_eps2=float(np.mean(dd>2+1e-10)),new_to_old_distance_mean_A=float(dd.mean()),
           Rg_Q_JS_bits=js_bits(o,n),recent_grid_increment_per_ns=(len(current)-len(previous))/2,
           recent_repeat_fraction=float(np.mean([c in previous for c in recent_cells])) if recent_cells else None)
    W=dict(grid_cells_total=len(current),grid_cells_recent=len(set(recent_cells)),recent_repeat_fraction=X['recent_repeat_fraction'])
    for name in ('rg_A','q'):
        v=a[name][ii];W.update({name+'_mean':float(v.mean()),name+'_std':float(v.std()),name+'_min':float(v.min()),name+'_max':float(v.max())})
    Z=dict(completed_MD_ns=req['milestone_ns'],decision_milestone_ns=req['milestone_ns'],candidate_count=len(sets['candidate']),
           old_training_count=800,new_training_count=400,validation_count=200,M0_optimizer_steps=200,model_data_age_ns=2,
           model_publication_age_s=start-req['M0_available_monotonic'],estimated_update_s=4.,estimated_inference_s=3.5,
           estimated_MD4ns_s=208.,cost_profile_source='B1-Pilot-670fac9',remaining_wall_horizon_s=None,
           horizon_reason='not_applicable_equal_MD',recipe_id='CVAE-938cb80-200steps-batch4')
    snapshot=dict(root_id=req['root_id'],state_id=req['state_id'],X=X,Z=Z,W=W,
                  input_hashes=req['input_hashes'],inputs_available_monotonic=req['inputs_available_monotonic'],
                  feature_start_monotonic=start,feature_end_monotonic=time.monotonic(),
                  outcome_information_used=False,role='predecision_diagnostic')
    if snapshot['inputs_available_monotonic']>start:raise ValueError('未公開入力を特徴へ使用できません。')
    dump(out/'state-features.json',snapshot)
    return snapshot


def selection(req,out):
    """候補順位の一致性・対応条件を検査し、原DCDから起点を取り出す。"""
    import MDAnalysis as mda
    pool=Path(req['pool']);a=dict(np.load(pool/'features.npz'));sets=json.loads((pool/'indices.json').read_text())
    candidates=np.array(sets['candidate']);ranks={};selected={};models={}
    for label,path in req['inferences'].items():
        p=Path(path);v=dict(np.load(p/'ranking.npz'))
        if not np.array_equal(v['frame_ids'],candidates):raise ValueError('候補集合が一致しません。')
        ranks[label]=v;models[label]=json.loads((p/'result.json').read_text())['checkpoint_sha256']
    if any(not np.array_equal(ranks['F0'][k],ranks['F0-repeat'][k]) for k in ranks['F0']):raise ValueError('F0反復推論が一致しません。')
    for t in (1,2):
        rr=[json.loads((Path(req['training'][f'{arm}-t{t}'])/'result.json').read_text()) for arm in ('F1','F2')]
        for k in ('initial_model_digest','initial_optimizer_digest','initial_rng_digest','optimizer_steps','exposures'):
            if rr[0][k]!=rr[1][k]:raise ValueError('対応学習条件が不一致です：'+k)
        if any(v['optimizer_steps']!=200 or v['exposures']!=800 for v in rr):raise ValueError('学習量が不正です。')
    for label,v in ranks.items():
        if label=='F0-repeat':continue
        frame=int(v['frame_ids'][v['order'][0]]);segment,local=divmod(frame,4000)
        source=Path(req['history_tasks'][segment]);u=mda.Universe(str(source/'initial.pdb'),str(source/'sim.dcd'))
        u.trajectory[local];xyz=u.atoms.positions.copy();np.save(out/(label+'.npy'),xyz,allow_pickle=False)
        selected[label]=dict(frame_id=frame,time_ps=float(a['time_ps'][frame]),segment=segment,local_frame=local,
            selected_sha256=sha(out/(label+'.npy')),DCD_sha256=sha(source/'sim.dcd'),checkpoint_sha256=models[label])
    comparisons=[]
    from scipy.stats import spearmanr
    for t in (1,2):
        for high,low in [('F2','F1'),('F2','F0'),('F1','F0')]:
            x=high+f'-t{t}';y=low+f'-t{t}' if low!='F0' else 'F0'
            ia,ib=selected[x]['frame_id'],selected[y]['frame_id'];ra,rba=ranks[x],ranks[y]
            aa=ra['frame_ids'][ra['order']];bb=rba['frame_ids'][rba['order']]
            rho=float(spearmanr(ra['lof'],rba['lof']).statistic)
            comparisons.append(dict(training_block=t,comparison=high+'-'+low,selected_high=ia,selected_low=ib,
                selected_dRMSD_A=float(distances(a['distances_A'][ia],a['distances_A'][ib])[0,0]),
                selected_angle_RMS_deg=float(circular(a['angles_rad'][ia],a['angles_rad'][ib])),
                score_spearman=rho if np.isfinite(rho) else None,
                overlaps={str(k):len(set(aa[:k])&set(bb[:k])) for k in (1,10,100)}))
    dump(out/'selected.json',selected);dump(out/'selection-comparisons.json',comparisons)
    return dict(selected=selected,comparisons=comparisons,F0_repeat_exact=True,matched_training=True)


def branch_analysis(req,out):
    """大きな軌跡を一枝ずつ評価する。"""
    from .expansion_analysis import analyze_branch
    return analyze_branch(req,out)


def main():
    req=json.loads(Path(sys.argv[1]).read_text());out=Path(req['output_dir']);out.mkdir(parents=True,exist_ok=False)
    for p,h in req.get('input_hashes',{}).items():core.require_hash(p,h)
    start=time.perf_counter();cpu=time.process_time()
    handlers=dict(md=core.md,prepare=core.prepare,ai=core.ai,pool=combine_pool,features=state_features,selection=selection,analysis=branch_analysis)
    try:
        result=handlers[req['kind']](req,out);result.update(status='success')
    except BaseException as e:
        (out/'failure.txt').write_text(traceback.format_exc());dump(out/'failure.json',dict(error=repr(e)));raise
    finally:dump(out/'timing.json',dict(worker_wall_s=time.perf_counter()-start,cpu_s=time.process_time()-cpu,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,source_sha256=sha(__file__)))
    result.update(artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()});dump(out/'result.json',result)


if __name__=='__main__':main()
