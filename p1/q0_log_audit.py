"""既存ログだけを読む単一CPUの資格監査。モデルと軌道を実行しない。"""
import argparse,csv,hashlib,json,math,os,resource,statistics,time,sys
from pathlib import Path

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def table(p,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
def avg(x):return statistics.fmean(x)
def main(project,out,bundle):
    start=time.monotonic();cpu=time.process_time()
    assert os.environ['CUDA_VISIBLE_DEVICES']=='-1'
    assert all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU,(7200,7200))
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
    assert project.stat().st_uid==os.getuid() and project in out.parents
    out.mkdir(exist_ok=False)
    raw=project/'runs/b1-expansion-20261026';summary=project/'artifacts/b1-expansion-20261026/summary-v1'
    expected=read(bundle/'raw-artifact-sha256.json');models=read(bundle/'models.json');tasks=read(bundle/'task-manifest.json')
    verified={};failure=[]
    def guard():
        if time.monotonic()-start>=7200:raise RuntimeError('2時間の資源復核点で停止')
        if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>1024**3:raise RuntimeError('出力予算超過')
    def check(p):
        guard();rel=str(p.relative_to(raw));actual=digest(p)
        if rel not in expected or actual!=expected[rel]:raise RuntimeError('入力SHA不一致: '+rel)
        verified[rel]=actual
        return p
    def load(p):return read(check(p))
    curves=[];mr=[];recipes=[];lineage=[]
    byid={r['state_id']+'-'+r['label']:r for r in models}
    for tid,known in byid.items():
        t=raw/'tasks'/tid;req=load(t/'request.json');result=load(t/'science/result.json')
        recipe=load(t/'science/recipe.json');exp=load(t/'science/exposure.json');loss=load(t/'science/loss.json')
        ck=check(t/'science/checkpoint.pt');assert digest(ck)==known['checkpoint_sha256']==result['checkpoint_sha256']
        assert result['seed']==known['seed']==req['seed']
        assert exp['steps']==result['optimizer_steps']==known['optimizer_steps']==200
        assert exp['batch_size']==4 and len(exp['frame_ids_0based'])==len(set(exp['frame_ids_0based']))==800
        assert sorted(exp['permutation_positions'])==list(range(800))
        pool=Path(req['pool']);indices=load(pool/'indices.json');ids=indices['old'] if known['arm']=='M0' else indices[known['arm']]
        assert exp['frame_ids_0based']==[ids[i] for i in exp['permutation_positions']]
        assert not set(ids)&set(indices['validation']) and len(indices['validation'])==200
        for k in ['initial_model_digest','initial_optimizer_digest','initial_rng_digest','final_model_digest','final_optimizer_digest','parent_checkpoint_sha256']:
            assert result[k]==known[k]
        parent=byid[known['state_id']+'-M0']
        if known['arm']!='M0':
            assert result['parent_checkpoint_sha256']==parent['checkpoint_sha256']
            assert result['initial_model_digest']==parent['final_model_digest']
            assert result['initial_optimizer_digest']==parent['final_optimizer_digest']
        vals=loss['per_step'];tr,br,kr=loss['mean_loss'];va,bv,kv=loss['validation_loss']
        assert len(vals)==200 and all(math.isfinite(v) for v in vals+[tr,br,kr,va,bv,kv])
        assert math.isclose(avg(vals),tr,rel_tol=1e-6,abs_tol=1e-5)
        common=dict(task_id=tid,root_id=known['root_id'],state_id=known['state_id'],arm=known['arm'],seed=req['seed'])
        for i,v in enumerate(vals,1):curves.append(dict(**common,step=i,total=v,BCE='NOT_SAVED',KL='NOT_SAVED'))
        mr.append(dict(**common,steps=200,unique_frames=800,train_total=tr,train_BCE_batchsum_mean=br,train_KL_batchmean_mean=kr,
            train_BCE_per_frame=br/4,train_BCE_per_element=br/(4*784),validation_total=va,validation_BCE_batchsum_mean=bv,
            validation_BCE_per_frame=bv/50,validation_BCE_per_element=bv/(50*784),validation_KL_batchmean_mean=kv,
            validation_KL_sample_weighted='NOT_RECOVERABLE',first20_total_mean=avg(vals[:20]),last20_total_mean=avg(vals[-20:]),maximum_step_total=max(vals),
            per_step_mean_error=avg(vals)-tr,parent_checkpoint_sha256=result['parent_checkpoint_sha256'],optimizer=recipe['cvae']['optimizer_name']))
        recipes.append(dict(task_id=tid,recipe=recipe))
        lineage.append(dict(**common,parent_checkpoint_sha256=result['parent_checkpoint_sha256'],initial_model_digest=result['initial_model_digest'],initial_optimizer_digest=result['initial_optimizer_digest'],initial_rng_digest=result['initial_rng_digest'],final_model_digest=result['final_model_digest'],final_optimizer_digest=result['final_optimizer_digest'],exposure_sha256=digest(t/'science/exposure.json'),temporal_split_ID_disjoint=True))
    assert len(mr)==80
    for state in sorted({r['state_id'] for r in models}):
        for block in [1,2]:
            a,b=[byid[state+'-'+arm+'-t'+str(block)] for arm in ['F1','F2']]
            for k in ['seed','initial_model_digest','initial_optimizer_digest','initial_rng_digest']:assert a[k]==b[k]
    table(out/'model-loss-summary.csv',mr);table(out/'model-loss-per-step.csv',curves);table(out/'model-lineage.csv',lineage);write(out/'model-recipes.json',recipes)
    mdrows=[];windows=[];blocks=[];continuity=[]
    md=[t for t in tasks if t['request']['kind']=='md'];assert len(md)==272
    for task in md:
        tid=task['task_id'];t=raw/'tasks'/tid;req=load(t/'request.json');res=load(t/'science/result.json')
        p=check(t/'science/sim.csv')
        with p.open() as f:
            rd=csv.DictReader(f);arr=[{k.lstrip('#').strip('"'):float(v) for k,v in r.items()} for r in rd]
        n=len(arr);assert n==int(req['length_ns']*2000)
        keys=['Temperature (K)','Potential Energy (kJ/mole)'];times=[r['Time (ps)'] for r in arr];steps=[r['Step'] for r in arr]
        assert all(math.isfinite(v) for r in arr for v in r.values())
        terr=max(abs((times[i]-times[i-1])-.5) for i in range(1,n));assert terr<1e-5
        assert all(steps[i]-steps[i-1]==250 for i in range(1,n))
        assert abs(times[0]-res['initial_time_ps']-.5)<1e-5 and abs(times[-1]-res['final_time_ps'])<1e-5
        base=dict(task_id=tid,root_id=tid[:3],kind='history' if '-h' in tid else 'downstream',seed=req['seed'],restart=res['restart'])
        row=dict(**base,rows=n,initial_time_ps=res['initial_time_ps'],final_time_ps=res['final_time_ps'],step_first=steps[0],step_last=steps[-1],max_report_interval_error_ps=terr)
        for k,short in zip(keys,['temperature_K','potential_kJ_mol']):
            v=[r[k] for r in arr];row[short+'_mean']=avg(v);row[short+'_sd']=statistics.stdev(v);row[short+'_min']=min(v);row[short+'_max']=max(v)
        mdrows.append(row)
        # 既登録の窓と10ps表示集約。平衡判定の新閾値は設けない。
        for lo,hi in [(0,100),(100,200),(200,500),(500,req['length_ns']*1000)]:
            a=[r for i,r in enumerate(arr,1) if lo<i*0.5<=hi]
            z=dict(**base,local_start_ps=lo,local_end_ps=hi,rows=len(a))
            for k,short in zip(keys,['temperature_K','potential_kJ_mol']):z[short+'_mean']=avg([r[k] for r in a]) if a else ''
            windows.append(z)
        for offset in range(0,n,20):
            a=arr[offset:offset+20];z=dict(task_id=tid,local_end_ps=(offset+len(a))*.5,rows=len(a))
            for k,short in zip(keys,['temperature_K','potential_kJ_mol']):z[short+'_mean']=avg([r[k] for r in a])
            blocks.append(z)
    for root in ['r%02d'%i for i in range(1,9)]:
        hist=sorted([r for r in mdrows if r['root_id']==root and r['kind']=='history'],key=lambda r:r['initial_time_ps']);assert len(hist)==4
        for a,b in zip(hist,hist[1:]):
            delta=b['initial_time_ps']-a['final_time_ps'];assert abs(delta)<1e-5
            continuity.append(dict(root_id=root,previous_task=a['task_id'],next_task=b['task_id'],checkpoint_time_gap_ps=delta,step_gap=b['step_first']-a['step_last']))
    table(out/'md-task-diagnostics.csv',mdrows);table(out/'md-window-diagnostics.csv',windows);table(out/'md-timeseries-10ps.csv',blocks);table(out/'history-continuity.csv',continuity)
    quality=read(summary/'quality.json');assert len(quality)==240
    qrows=[]
    for q in quality:
        tid=q['branch']['branch_id']+'-evaluate'
        # quality.jsonは既存評価結果の索引。DCDや特徴配列は開かない。
        qrows.append(dict(branch_id=q['branch']['branch_id'],frames=q['frames'],qualified_frames=q['qualified_frames'],status=q['status'],selected_coordinates_exact=q['selected_coordinates_exact']))
    table(out/'existing-quality.csv',qrows)
    for rel,old in verified.items():assert digest(raw/rel)==old
    table(out/'input-sha256.csv',[dict(path=k,sha256=v,post_readback_matches=True) for k,v in sorted(verified.items())])
    write(out/'failures.json',[{'type':'inspection_path_error','detail':'初回の読取りでtask直下result.jsonを想定し欠落。science/result.jsonへ訂正。さらに窓境界の浮動小数点重複を防ぐため、検証済み0.5ps報告indexで排他的分類へ変更。最初のQ0出力はoutput-before-boundary-fixに保持。原B1/R1変更なし。'}])
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    write(out/'status.json',dict(status='COMPLETE',models=80,MD_tasks=272,history_MD=32,downstream_MD=240,MD_log_rows=sum(r['rows'] for r in mdrows),raw_SHA_checked=len(verified),raw_unmodified=True,per_step_BCE_KL='NOT_SAVED',model_loading=False,DCD_read=False,scientific_acceptance='PENDING'))
    write(out/'costs.json',dict(wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,peak_RSS_MiB=peak,affinity_count=len(os.sched_getaffinity(0)),CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],output_bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),review_point_s=7200,code_sha256=digest(Path(__file__)),python=sys.version,platform=sys.platform))
    write(out/'output-sha256.json',{p.name:digest(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps(read(out/'status.json')))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('output',type=Path);p.add_argument('bundle',type=Path);a=p.parse_args()
    main(a.project.resolve(),a.output.resolve(),a.bundle.resolve())
