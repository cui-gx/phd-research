"""既存B1を読取り専用で評価するN1単CPU実行器。新しい科学タスクは生成しない。"""
import argparse,csv,hashlib,json,os,resource,time,sys
from pathlib import Path
import numpy as np
import MDAnalysis as mda
from n1_native_metrics import proper_rmsd,native_contact_mask,q_from_mask,best_so_far
from n1_metadata_audit import ca_keys

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(1048576):h.update(b)
    return h.hexdigest()

def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(p,rows):
    with p.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def main(a):
    assert os.environ['CUDA_VISIBLE_DEVICES']=='-1'
    for v in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']:assert os.environ[v]=='1'
    start=time.monotonic();cpu=time.process_time();a.out.mkdir(parents=True,exist_ok=True)
    raw=json.loads((a.bundle/'raw-artifact-sha256.json').read_text());run=a.project/'runs/b1-expansion-20261026'
    rows=list(csv.DictReader((a.bundle/'MD-file-audit.csv').open()));branches=list(csv.DictReader((a.bundle/'branch-index.csv').open()));bmap={b['md_task_id']:b for b in branches}
    first=['r01-h1-md','r01-s4-F0-t0-m2-md'];rows.sort(key=lambda r:(first.index(r['task_id']) if r['task_id'] in first else 2, r['task_id']))
    if a.phase=='first':rows=rows[:2]
    else:assert json.loads((a.out/'first-unit-gate.json').read_text())['status']=='PASS'
    def check():
        elapsed=sum(json.loads(p.read_text())['wall_s'] for p in a.out.glob('units/*/receipt.json'))+time.monotonic()-start
        assert elapsed<7200,'科学2時間復核点'
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<2*1024**2,'RSS保護'
        assert sum(p.stat().st_size for p in a.out.rglob('*') if p.is_file())<2*1024**3,'出力保護'
    ref=a.project/'source/inputs/p1-fsd-ey/1FME-folded-model1.pdb';assert sha(ref)=='a5276b2752cd95555f7ca078c512c68f89b50893519e99347a1986fa63c82dc8'
    native=mda.Universe(str(ref)).select_atoms('name CA').positions.astype(float);mask=native_contact_mask(native)
    assert proper_rmsd(native,native)<1e-10 and q_from_mask(native,mask)==1
    rot=np.array([[0.,-1,0],[1,0,0],[0,0,1]]);assert proper_rmsd(native@rot+3,native)<1e-10
    mirror=native.copy();mirror[:,0]*=-1;assert proper_rmsd(mirror,native)>1e-5
    dump(a.out/'reference-test.json',dict(native_contacts=int(mask.sum()),self_RMSD_A=proper_rmsd(native,native),self_Q=1,mirror_RMSD_A=proper_rmsd(mirror,native),reference_sha256=sha(ref),unit='Angstrom',conversion='MDAnalysis DCD reader convert_units=True; nm values would require explicit x10',phase=a.phase))
    for r in rows:
        check();tid=r['task_id'];out=a.out/'units'/tid
        if out.exists():
            assert a.phase=='full' and (out/'receipt.json').exists(),'未完了単位あり、停止'
            continue
        out.mkdir(parents=True);begin=time.monotonic();c0=time.process_time();s=run/'tasks'/tid/'science';prep=run/'tasks'/(tid+'-prep')/'science'
        files=[s/'sim.dcd',s/'initial.pdb',s/'sim.csv',prep/'features.npz',prep/'quality.json',s/'result.json',prep/'result.json']
        before={str(p.relative_to(run)):sha(p) for p in files}
        for p,h in before.items():assert raw[p]==h,('原SHA不一致',p)
        assert ca_keys(s/'initial.pdb')==ca_keys(ref)
        with np.load(prep/'features.npz',allow_pickle=False) as z:old={k:z[k] for k in ['ca','valid','reasons','time_ps']}
        valid=old['valid'];assert np.array_equal(valid,~old['reasons'].any(axis=1))
        assert int(valid.sum())==json.loads((prep/'quality.json').read_text())['valid']
        state=np.genfromtxt(s/'sim.csv',delimiter=',',skip_header=1);times=state[:,1];assert np.array_equal(times,old['time_ps'])
        n=int(r['header_frames']);assert len(valid)==len(times)==n and np.all(np.diff(times)>0)
        u=mda.Universe(str(s/'initial.pdb'),str(s/'sim.dcd'),convert_units=True);ca=u.select_atoms('name CA');assert len(ca)==28 and len(u.trajectory)==n and len(u.atoms)==504
        rr=np.empty(n);qq=np.empty(n);maxdt=0.;dcd_origin=None
        for i,ts in enumerate(u.trajectory):
            if i%256==0:check()
            assert ts.frame==i
            x=ca.positions.astype(float);assert np.array_equal(x,old['ca'][i]),'CA座標/順序/単位不一致'
            if dcd_origin is None:dcd_origin=ts.time-times[0]
            maxdt=max(maxdt,abs(ts.time-dcd_origin-times[i]));assert maxdt<.001
            rr[i]=proper_rmsd(x,native);qq[i]=q_from_mask(x,mask)
        assert np.isfinite(rr).all() and np.isfinite(qq).all() and (rr>=0).all() and ((qq>=0)&(qq<=1)).all()
        global_offset=(int(tid.split('-h')[1].split('-')[0])-1)*4000 if '-h' in tid else 0
        ids=np.arange(n);elapsed=(ids+1)*.5
        # 原時刻を窓へ使う。継続historyではglobal時刻をsegment localへ分離する。
        local_t=times-float(r['initial_time_ps']);assert np.max(abs(local_t-elapsed))<1e-5
        np.savez_compressed(out/'frames.npz',frame_id=ids,global_frame_id=ids+global_offset,time_ps=times,local_time_ps=local_t,RMSD_A=rr,Q=qq,valid=valid,best_RMSD_A=best_so_far(rr,valid))
        summaries=[]
        for burn in [0,100,200,500]:
            for prefix in [1000,2000,4000]:
                base=np.flatnonzero((local_t>burn)&(local_t<=prefix+1e-5))
                for stride in [1,4]:
                    sampled=base[::stride];ii=sampled[valid[sampled]]
                    d=dict(task_id=tid,root_id=tid[:3],kind=r['kind'],state_id=bmap.get(tid,{}).get('state_id',''),arm=bmap.get(tid,{}).get('arm','HISTORY'),training_block=bmap.get(tid,{}).get('training_block',''),MD_block=bmap.get(tid,{}).get('MD_block',''),burn_ps=burn,prefix_ns=prefix/1000,sampling_ps=.5*stride,total=len(sampled),valid=len(ii),excluded=len(sampled)-len(ii),window_status='COMPLETE' if prefix<=float(r['length_ns'])*1000 else 'INCOMPLETE_WINDOW')
                    if not len(ii):raise ValueError('適格点なし')
                    k=int(ii[np.argmin(rr[ii])]);d.update(min_RMSD_A=float(rr[k]),mean_RMSD_A=float(rr[ii].mean()),median_RMSD_A=float(np.median(rr[ii])),p10_RMSD_A=float(np.quantile(rr[ii],.1)),final_RMSD_A=float(rr[ii[-1]]),mean_Q=float(qq[ii].mean()),median_Q=float(np.median(qq[ii])),min_Q=float(qq[ii].min()),max_Q=float(qq[ii].max()),Q_at_argmin=float(qq[k]),argmin_frame=k,argmin_global_frame=k+global_offset,argmin_time_ps=float(times[k]),argmin_local_ps=float(local_t[k]))
                    assert d['min_RMSD_A']==min(rr[ii]) and d['total']==d['valid']+d['excluded'];summaries.append(d)
        for j in range(0,24,2):assert summaries[j]['min_RMSD_A']<=summaries[j+1]['min_RMSD_A']+1e-12
        table(out/'windows.csv',summaries)
        after={str(p.relative_to(run)):sha(p) for p in files};assert before==after
        dump(out/'receipt.json',dict(task_id=tid,status='PASS',frames=n,qualified=int(valid.sum()),DCD_max_time_error_ps=maxdt,CA_exact_match=True,source_SHA256=before,outputs={p.name:sha(p) for p in out.iterdir() if p.is_file()},wall_s=time.monotonic()-begin,CPU_s=time.process_time()-c0,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
        print(tid,'PASS',round(time.monotonic()-begin,3),flush=True)
    count=len(list(a.out.glob('units/*/receipt.json')))
    dump(a.out/('first-unit-gate.json' if a.phase=='first' else 'execution-status.json'),dict(status='PASS' if a.phase=='first' or count==272 else 'PARTIAL',completed_units=count,expected=2 if a.phase=='first' else 272,wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,scope='POST_HOC_EXPLORATORY',GPU_visible=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('bundle',type=Path);p.add_argument('out',type=Path);p.add_argument('--phase',choices=['first','full'],required=True);a=p.parse_args()
    try:main(a)
    except BaseException as e:
        a.out.mkdir(exist_ok=True,parents=True);dump(a.out/('failure-'+a.phase+'.json'),dict(status='STOPPED',error=repr(e)));raise
