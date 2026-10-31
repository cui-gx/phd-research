"""272固定軌跡の独立batch制御。予算・成功証拠を跨batchで保持する。"""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
os.environ['CUDA_VISIBLE_DEVICES']='-1'
import argparse,csv,fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
from nmr34_v2_execute import append_event,canonical_keys,exclusive_json,limit_reason,pdb_keys,stage


def checkpoint(path,data):
    """予算状態のみ原子的に更新。科学成果を変更しない。"""
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data));tmp.replace(path)


def supervise(project,bundle,out,resume_approval=None):
    """明示承認なしの再開と未確定budgetのリセットを拒否する。"""
    import psutil
    out.mkdir(parents=True,exist_ok=True)
    lock=(project/'artifacts/nmr34-full-global.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    config=json.loads((bundle/'config.json').read_text());fp=hashlib.sha256((bundle/'config.json').read_bytes()).hexdigest()
    ledger=out/'budget-state.json';used=0.;segment=0
    if ledger.exists():
        prior=json.loads(ledger.read_text())
        if not resume_approval or prior['segment_open'] or prior['fingerprint']!=fp:raise ValueError('再開承認/確定台帳/fingerprintが必要')
        used=prior['spent_s'];segment=prior['segment']+1
    elif resume_approval:raise ValueError('初回を再開扱いにしない')
    if used>=config['limits']['wall_s']:raise ValueError('累積予算を消費済み')
    os.environ['MPLCONFIGDIR']=str(out/'mpl-cache')
    start=time.monotonic();stage(out,'startup');checkpoint(ledger,dict(fingerprint=fp,spent_s=used,segment=segment,segment_open=True))
    append_event(out/'budget-events.jsonl',dict(event='START',segment=segment,used_s=used,resume_approval=resume_approval))
    peak=0;threads=0;reason=None
    with (out/f'stdout-{segment}.log').open('x') as stdout,(out/f'stderr-{segment}.log').open('x') as stderr:
        command=[sys.executable,__file__,'worker',str(project),str(bundle),str(out)]
        if resume_approval:command+=['--resume-approval',resume_approval]
        process=subprocess.Popen(command,stdout=stdout,stderr=stderr)
        try:
            while True:
                now=time.monotonic();rss=0
                for p in [psutil.Process()]+psutil.Process().children(recursive=True):
                    try:
                        rss+=p.memory_info().rss
                        if p.pid==process.pid:threads=max(threads,p.num_threads())
                    except psutil.NoSuchProcess:pass
                peak=max(peak,rss);disk=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
                ss=json.loads((out/'stage.json').read_text());elapsed=used+now-start
                reason=limit_reason(elapsed,now-ss['started'],rss,disk,config['limits'])
                append_event(out/'budget-events.jsonl',dict(event='SAMPLE',spent_s=elapsed,stage=ss['name'],RSS_bytes=rss,output_bytes=disk))
                checkpoint(ledger,dict(fingerprint=fp,spent_s=elapsed,segment=segment,segment_open=True))
                if reason or process.poll() is not None:break
                time.sleep(.2)
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait()
    spent=used+time.monotonic()-start
    checkpoint(ledger,dict(fingerprint=fp,spent_s=spent,segment=segment,segment_open=False))
    result=dict(status='PASS' if not reason and process.returncode==0 else 'STOPPED',spent_s=spent,
                returncode=process.returncode,reason=reason,peak_RSS_bytes=peak,max_worker_threads=threads)
    exclusive_json(out/f'supervisor-{segment}.json',result)
    append_event(out/'budget-events.jsonl',dict(event='END',**result))
    if result['status']!='PASS':raise RuntimeError('保護停止/失敗。自動再開しない。')


def preserve_partial(out,dest,approval):
    """明示再開時だけ部分成果を別attemptへ保持する。"""
    if not approval:raise ValueError('部分成果の再実行には明示承認が必要')
    archive=out/'failed-attempts';archive.mkdir(exist_ok=True)
    target=archive/(dest.name+'-'+str(time.time_ns()));dest.rename(target)
    append_event(out/'recovery.jsonl',dict(approval=approval,preserved=str(target.relative_to(out))))


def worker(project,bundle,out,resume_approval=None):
    """1科学workerで固定順に処理。完了単位は全SHA検査後にだけskipする。"""
    import numpy as np
    import MDAnalysis as mda
    from nmr34_v2 import References,Run,Timer,archive_metadata,dcd_chunks,evaluate_chunks,export_references,load_ca_once,proper_rmsd,require,save_json,sha256,summarize,verify_inputs
    config=json.loads((bundle/'config.json').read_text());manifest=json.loads((bundle/'manifest.json').read_text())
    require(sha256(bundle/'manifest.json')==config['manifest_sha256'],'manifest不一致')
    require(len(manifest)==272 and len({x['task_id'] for x in manifest})==272,'行列不正')
    for name,h in config['code_sha256'].items():require(sha256(Path(__file__).with_name(name))==h,'code SHA不一致')
    stage(out,'all_input_preflight');before=verify_inputs({project/p:h for x in manifest for p,h in x['inputs'].items()})
    verify_inputs({project/p:h for p,h in config['references'].items()})
    verify_inputs({bundle/p:h for p,h in config['analysis_inputs_sha256'].items()})
    freeze=json.loads((bundle/'freeze.json').read_text());keys=canonical_keys(freeze['CA_keys'])
    rp=project/'source/inputs/p1-fsd-ey/1FME-folded.pdb';require(pdb_keys(rp)==keys,'参照対応不一致')
    u=mda.Universe(str(rp));ca=u.select_atoms('name CA');refs=References(np.array([ca.positions.copy().astype(float) for _ in u.trajectory]))
    if not (out/'reference-map.json').exists():export_references(refs,out)
    units=out/'units';units.mkdir(exist_ok=True);completed=0
    for entry in manifest:
        tid=entry['task_id'];dest=units/tid;stage(out,tid)
        if (dest/'receipt.json').exists():
            receipt=json.loads((dest/'receipt.json').read_text());require(receipt['status']=='PASS','失敗単位の上書き禁止')
            for name,h in receipt['outputs'].items():require(sha256(dest/name)==h,'成功成果SHA不一致')
            require(json.loads((dest/'success.json').read_text())['status']=='PASS','成功marker不足')
            completed+=1;continue
        if dest.exists():preserve_partial(out,dest,resume_approval)
        t0=time.monotonic();c0=time.process_time();timer=Timer()
        with Run(dest,config['manifest_sha256']):
            science=project/'runs/b1-expansion-20261026/tasks'/tid/'science';prep=science.parent.parent/(tid+'-prep')/'science'
            old=project/'artifacts/n1-cpu-20261030-v1/output/units'/tid
            with timer.measure('CA_cache_metadata'):
                require(pdb_keys(science/'initial.pdb')==[keys[0]],'原子順不一致')
                cached=load_ca_once(prep/'features.npz',16*1024**2)
                with np.load(prep/'features.npz',allow_pickle=False) as z:valid=z['valid'];reasons=z['reasons'];times=z['time_ps']
                prior=np.load(old/'frames.npz',allow_pickle=False)
                require(len(cached)==entry['frames'] and np.array_equal(valid,prior['valid']) and np.array_equal(times,prior['time_ps']),'metadata不一致')
                require(np.array_equal(times,np.genfromtxt(science/'sim.csv',delimiter=',',skip_header=1)[:,1]),'sim時刻不一致')
                archive_metadata(dest,prior['frame_id'],prior['global_frame_id'],times,prior['local_time_ps'],valid,reasons)
                oldrows=list(csv.DictReader((old/'windows.csv').open()))
                windows=[(int(r['burn_ps']),float(r['prefix_ns']),float(r['sampling_ps'])) for r in oldrows]
                statuses={f'{b}_{p}_{s}':r['window_status'] for (b,p,s),r in zip(windows,oldrows)}
            chunks,compute=evaluate_chunks(dcd_chunks(science/'initial.pdb',science/'sim.dcd',cached,keys[0]),refs,dest,qualify=False)
            rows=summarize(dest,chunks,prior['local_time_ps'],valid,windows,compute,statuses)
            with timer.measure('M1_and_fixed_scalar_audit'):
                maxerr=0.;dt=0.;origin=None
                for item in chunks:
                    i=item['start'];j=i+item['frames'];sl=slice(i,j)
                    with np.load(dest/item['path'],allow_pickle=False) as z:
                        require(np.array_equal(z['frame_id'],prior['frame_id'][sl]),'frame ID不一致')
                        e=float(np.max(abs(z['RMSD_A'][:,0]-prior['RMSD_A'][sl])));maxerr=max(maxerr,e);require(e<=1e-8,'M1不一致')
                        require(np.array_equal(z['contact_count'][:,0],np.rint(prior['Q'][sl]*refs.den[0]).astype(int)),'Q1 count不一致')
                        if origin is None:origin=z['dcd_time_ps'][0]-times[0]
                        dt=max(dt,float(np.max(abs(z['dcd_time_ps']-origin-times[sl]))));require(dt<.001,'時刻不一致')
                scalar_error=0.
                for i in entry['scalar_frames']:
                    selected=next(v for v in chunks if v['start']<=i<v['start']+v['frames'])
                    with np.load(dest/selected['path'],allow_pickle=False) as zz:rr=zz['RMSD_A'][i-selected['start']]
                    scalar_error=max(scalar_error,max(abs(rr[k]-proper_rmsd(cached[i],ref)) for k,ref in enumerate(refs.native)))
                require(scalar_error<=1e-8,'事前指定scalar抽査不一致')
                for row in rows:
                    if row['model']!=1:continue
                    b,p,s=map(float,row['window'].split('_'));oldrow=next(r for r in oldrows if float(r['burn_ps'])==b and float(r['prefix_ns'])==p and float(r['sampling_ps'])==s)
                    for key in ('min_RMSD_A','mean_RMSD_A','median_RMSD_A','p10_RMSD_A','final_RMSD_A','mean_Q','median_Q','max_Q','Q_at_argmin','argmin_frame'):
                        require(abs(row[key]-float(oldrow[key]))<=1e-8,'M1窓不一致 '+key)
            with timer.measure('input_SHA_after'):
                verify_inputs({project/p:h for p,h in entry['inputs'].items()})
            prior.close()
            outputs={str(p.relative_to(dest)):sha256(p) for p in dest.rglob('*') if p.is_file() and p.name!='run.lock'}
            save_json(dest/'receipt.json',dict(status='PASS',task_id=tid,frames=entry['frames'],M1_max_error_A=maxerr,scalar_sample_max_error_A=scalar_error,
                scalar_frames=entry['scalar_frames'],DCD_time_error_ps=dt,wall_s=time.monotonic()-t0,CPU_s=time.process_time()-c0,
                timing={**timer.records,**compute.records},outputs=outputs))
        completed+=1
        checkpoint(out/'status.json',dict(completed=completed,total=272,last=tid))
    stage(out,'global_final_SHA');verify_inputs(before)
    if not (out/'compute-complete.json').exists():save_json(out/'compute-complete.json',dict(status='PASS',completed=completed,frames=sum(e['frames'] for e in manifest),input_SHA_unchanged=True))
    if not (out/'analysis-complete.json').exists():
        from nmr34_full_analyze import analyze
        if (out/'analysis').exists():preserve_partial(out,out/'analysis',resume_approval)
        analyze(out,bundle)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['supervise','worker'])
    for name in ('project','bundle','output'):p.add_argument(name,type=Path)
    p.add_argument('--resume-approval');a=p.parse_args()
    if a.mode=='worker':worker(a.project,a.bundle,a.output,a.resume_approval)
    else:supervise(a.project,a.bundle,a.output,a.resume_approval)
