"""承認された二軌跡だけのNMR参照資格。原入力・旧実装は読み取り専用。"""
import os
for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
os.environ['CUDA_VISIBLE_DEVICES']='-1'
import argparse,csv,fcntl,hashlib,json,signal,sys,time,threading
from pathlib import Path
import numpy as np
import MDAnalysis as mda
import psutil
from n1_native_metrics import proper_rmsd,native_contact_mask
IDS=['r01-h1-md','r01-s4-F0-t0-m2-md']
REF_SHA=['a5276b2752cd95555f7ca078c512c68f89b50893519e99347a1986fa63c82dc8','f9c5de680c00ee2629634fb6c7f621e2e1e2664e92b2e4b51b236d5e483b436b']
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def table(p,rows):
    with p.open('x') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def batch(x,refs):
    x=x-x.mean(axis=-2,keepdims=True);y=refs-refs.mean(axis=-2,keepdims=True)
    h=np.einsum('bni,knj->bkij',x,y);u,_,v=np.linalg.svd(h)
    u[:,:,:,-1]*=np.where(np.linalg.det(u@v)>=0,1.,-1.)[:,:,None]
    rot=u@v;dif=np.einsum('bni,bkij->bknj',x,rot)-y[None]
    return np.sqrt(np.mean(np.sum(dif*dif,axis=-1),axis=-1))
def keys(p):
    groups=[];current=[]
    for l in p.read_text().splitlines():
        if l.startswith('ENDMDL'):
            groups.append(current);current=[]
        elif l.startswith(('ATOM  ','HETATM')) and l[12:16].strip()=='CA':current.append([l[21],l[22:26],l[26],l[17:20],l[16]])
    if current:groups.append(current)
    return groups

def main(a):
    start=time.monotonic();cpu=time.process_time();a.out.mkdir(parents=True,exist_ok=True)
    lock=(a.out/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not (a.out/'failure.json').exists(),'失敗後は自動再実行しない')
    old=a.project/'artifacts/n1-cpu-20261030-v1';run=a.project/'runs/b1-expansion-20261026'
    refs=[a.project/'source/inputs/p1-fsd-ey'/n for n in ['1FME-folded-model1.pdb','1FME-folded.pdb']]
    audit=json.loads((a.bundle/'unit-audit.json').read_text());sel=[next(x for x in audit if x['task_id']==tid) for tid in IDS]
    expected={str((run/p).relative_to(a.project)):h for x in sel for p,h in x['source_SHA256'].items()}
    for p,h in zip(refs,REF_SHA):expected[str(p.relative_to(a.project))]=h
    for x in sel:
        for n,h in x['outputs'].items():expected[str((old/'output/units'/x['task_id']/n).relative_to(a.project))]=h
    prior=json.loads((a.out/'freeze.json').read_text()) if a.mode=='run' else None
    spent=prior['wall_s'] if prior else 0.;stage=start;peak=0;stop=threading.Event();viol=[]
    def guard():
        nonlocal peak
        while not stop.wait(.1):
            proc=psutil.Process();rss=proc.memory_info().rss+sum(p.memory_info().rss for p in proc.children(recursive=True));peak=max(peak,rss)
            size=sum(p.stat().st_size for p in a.out.rglob('*') if p.is_file())
            if rss>2*1024**3 or size>256*1024**2 or time.monotonic()-start+spent>=900 or time.monotonic()-stage>=300:
                viol.append({'rss':rss,'output_bytes':size,'wall_s':time.monotonic()-start+spent});os.kill(os.getpid(),signal.SIGTERM);return
    def terminated(*_):raise RuntimeError('資源・時間保護停止')
    signal.signal(signal.SIGTERM,terminated);threading.Thread(target=guard,daemon=True).start()
    try:
        before={p:sha(a.project/p) for p in expected};require(before==expected,'原入力SHA不一致')
        kk=keys(refs[1]);require(len(kk)==34 and all(k==keys(refs[0])[0] for k in kk),'参照原子対応不一致')
        fp=hashlib.sha256(json.dumps({'inputs':expected,'code':sha(Path(__file__)),'pure_functions':sha(Path(__file__).with_name('n1_native_metrics.py')),'ids':IDS,'limits':[900,300,2*1024**3,256*1024**2]},sort_keys=True).encode()).hexdigest()
        if a.mode=='freeze':
            rng=np.random.default_rng(34);x=rng.normal(size=(5,28,3));y=rng.normal(size=(3,28,3))
            rr=batch(x,y);err=max(abs(rr[i,j]-proper_rmsd(x[i],y[j])) for i in range(5) for j in range(3));require(err<1e-12,'人工scalar/chunk不一致')
            rot=np.array([[0.,-1,0],[1,0,0],[0,0,1]]);require(proper_rmsd(x[0]@rot+3,x[0])<1e-12,'回転不変性');require(proper_rmsd(x[0]*[-1,1,1],x[0])>1e-3,'鏡映禁止')
            require(proper_rmsd(x[0]/10*10,x[0])<1e-12,'nm/Å変換')
            save(a.out/'freeze.json',dict(status='PASS',inputs=before,config_fingerprint=fp,CA_keys=kk,python=sys.version,numpy=np.__version__,MDAnalysis=mda.__version__,psutil=psutil.__version__,synthetic_error=err,wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,peak_RSS_bytes=peak))
            return
        require(prior['config_fingerprint']==fp,'凍結fingerprint不一致');require(not (a.out/'run-start.json').exists(),'既存実行は上書きしない')
        save(a.out/'run-start.json',{'fingerprint':fp,'budget_already_spent_s':spent})
        u=mda.Universe(str(refs[1]));ca=u.select_atoms('name CA');native=np.array([ca.positions.copy().astype(float) for _ in u.trajectory]);require(native.shape==(34,28,3),'34×28CA不一致')
        m1=mda.Universe(str(refs[0])).select_atoms('name CA').positions.astype(float);require(np.array_equal(native[0],m1),'model1座標不一致')
        masks=np.array([native_contact_mask(n) for n in native]);den=masks.sum(axis=(1,2));geo=batch(native,native)
        require(np.max(np.abs(np.diag(geo)))<=1e-8,'自己RMSD不一致')
        for k,ref in enumerate(native):
            require(np.all((np.linalg.norm(ref[:,None]-ref[None,:],axis=-1)<8)[masks[k]]),'参照Q自己不一致')
            rot=np.array([[0.,-1,0],[1,0,0],[0,0,1]])
            require(proper_rmsd(ref@rot+3,ref)<=1e-8,'参照回転不変性')
            require(proper_rmsd(ref*[-1,1,1],ref)>1e-5,'参照鏡映禁止')
        pairs=[dict(model=k+1,count=int(den[k]),pairs=np.argwhere(masks[k]).tolist(),self_RMSD_A=float(geo[k,k]),self_Q=1) for k in range(34)]
        table(a.out/'reference-geometry.csv',[dict(model_i=i+1,model_j=j+1,RMSD_A=float(geo[i,j])) for i in range(34) for j in range(34)]);save(a.out/'reference-contacts.json',pairs)
        receipts=[]
        for tid,n in zip(IDS,[4000,8000]):
            stage=time.monotonic();c0=time.process_time();dest=a.out/tid;dest.mkdir();s=run/'tasks'/tid/'science';prep=run/'tasks'/(tid+'-prep')/'science'
            require(keys(s/'initial.pdb')[0]==kk[0],'MD原子順不一致')
            oldz=np.load(old/'output/units'/tid/'frames.npz');features=np.load(prep/'features.npz');times=features['time_ps'];valid=features['valid']
            require(np.array_equal(valid,oldz['valid']) and np.array_equal(times,oldz['time_ps']),'時刻/valid不一致')
            require(np.array_equal(valid,~features['reasons'].any(axis=1)),'品質理由不一致')
            require(np.array_equal(times,np.genfromtxt(s/'sim.csv',delimiter=',',skip_header=1)[:,1]),'sim.csv時刻不一致')
            uu=mda.Universe(str(s/'initial.pdb'),str(s/'sim.dcd'),convert_units=True);c=uu.select_atoms('name CA');require(len(uu.trajectory)==n and len(c)==28,'frame/原子数不一致')
            R=np.empty((n,34));Q=np.empty_like(R);counts=np.empty((n,34),dtype=np.int16);buf=[];maxerr=0.;origin=None;maxdt=0.
            for i,ts in enumerate(uu.trajectory):
                require(ts.frame==i,'frame ID不一致');x=c.positions.astype(float);require(np.array_equal(x,features['ca'][i]),'座標/単位不一致')
                if origin is None:origin=ts.time-times[0]
                maxdt=max(maxdt,abs(ts.time-origin-times[i]));require(maxdt<.001,'DCD時刻不一致');buf.append(x)
                if len(buf)==512 or i==n-1:
                    xx=np.array(buf);offset=i-len(buf)+1;rr=batch(xx,native)
                    scalar=np.array([[proper_rmsd(v,ref) for ref in native] for v in xx]);maxerr=max(maxerr,float(np.max(abs(rr-scalar))));require(maxerr<=1e-8,'scalar/chunk不一致')
                    ds=np.linalg.norm(xx[:,:,None,:]-xx[:,None,:,:],axis=-1);cc=np.einsum('bij,kij->bk',(ds<8).astype(np.int16),masks.astype(np.int16))
                    R[offset:i+1]=rr;counts[offset:i+1]=cc;Q[offset:i+1]=cc/den;buf=[]
            err=float(np.max(abs(R[:,0]-oldz['RMSD_A'])));require(err<=1e-8,'原N1 RMSD不一致');require(np.array_equal(counts[:,0],np.rint(oldz['Q']*den[0]).astype(int)),'原Q count不一致')
            require(np.isfinite(R).all() and np.isfinite(Q).all() and (Q>=0).all() and (Q<=1).all(),'数値範囲不一致')
            arg=R.argmin(axis=1);minimum=R[np.arange(n),arg];require(np.all(minimum<=R[:,0]+1e-8),'ensemble min不一致')
            np.savez_compressed(dest/'frames.npz',RMSD_A=R,Q=Q,contact_count=counts,ensemble_min_RMSD_A=minimum,argmin_model=arg+1,frame_id=oldz['frame_id'],global_frame_id=oldz['global_frame_id'],time_ps=times,local_time_ps=oldz['local_time_ps'],valid=valid)
            orig=list(csv.DictReader((old/'output/units'/tid/'windows.csv').open()));ws=[];ids={}
            for row in orig:
                burn=int(row['burn_ps']);prefix=float(row['prefix_ns'])*1000;stride=int(float(row['sampling_ps'])/.5);key=f'{burn}_{prefix}_{stride}'
                sampled=np.flatnonzero((oldz['local_time_ps']>burn)&(oldz['local_time_ps']<=prefix+1e-5))[::stride];ii=sampled[valid[sampled]];ids[key]=ii.tolist()
                require(len(sampled)==int(row['total']) and len(ii)==int(row['valid']),'窓ID/件数不一致')
                for k in range(34):
                    r=R[ii,k];q=Q[ii,k];imin=int(ii[r.argmin()]);d=dict(task_id=tid,model=k+1,burn_ps=burn,prefix_ns=prefix/1000,sampling_ps=.5*stride,window_status=row['window_status'],total=len(sampled),valid=len(ii),min_RMSD_A=float(r.min()),mean_RMSD_A=float(r.mean()),median_RMSD_A=float(np.median(r)),p10_RMSD_A=float(np.quantile(r,.1)),final_RMSD_A=float(r[-1]),mean_Q=float(q.mean()),median_Q=float(np.median(q)),max_Q=float(q.max()),Q_at_argmin=float(Q[imin,k]),argmin_frame=imin)
                    if k==0:
                        for name in ['min_RMSD_A','mean_RMSD_A','median_RMSD_A','p10_RMSD_A','final_RMSD_A','mean_Q','median_Q','max_Q','Q_at_argmin','argmin_frame']:require(abs(d[name]-float(row[name]))<=1e-8,'原窓要約不一致 '+name)
                    ws.append(d)
            save(dest/'window-ids.json',ids);table(dest/'windows.csv',ws)
            receipt=dict(status='PASS',task_id=tid,frames=n,model1_max_error_A=err,scalar_chunk_max_error_A=maxerr,Q1_count_exact=True,window_ID_reproduction=True,DCD_max_time_error_ps=maxdt,wall_s=time.monotonic()-stage,CPU_s=time.process_time()-c0,peak_RSS_bytes=peak,outputs={p.name:sha(p) for p in dest.iterdir()})
            save(dest/'receipt.json',receipt);receipts.append(receipt);print(tid,'PASS',flush=True)
        after={p:sha(a.project/p) for p in expected};require(after==before,'入力事後SHA不一致')
        save(a.out/'final.json',dict(status='PASS',units=receipts,inputs_unchanged=True,inputs_sha256=after,wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,cumulative_science_wall_s=time.monotonic()-start+spent,peak_RSS_bytes=peak,output_bytes=sum(p.stat().st_size for p in a.out.rglob('*') if p.is_file()),full_272_executed=False))
    except BaseException as e:
        save(a.out/'failure.json',dict(status='STOPPED',error=repr(e),wall_s=time.monotonic()-start,cumulative_science_wall_s=time.monotonic()-start+spent,guard=viol));raise
    finally:stop.set()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','run']);p.add_argument('project',type=Path);p.add_argument('bundle',type=Path);p.add_argument('out',type=Path);main(p.parse_args())
