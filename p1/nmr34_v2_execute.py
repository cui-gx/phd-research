"""固定二軌跡だけの実行制御。全量への自動拡張・自動再開を持たない。"""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
os.environ['CUDA_VISIBLE_DEVICES']='-1'
import argparse
import csv
import fcntl
import hashlib
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

IDS = ['r01-h1-md','r01-s4-F0-t0-m2-md']


def exclusive_json(path, value):
    """確定証拠の上書きを拒否する。"""
    with Path(path).open('x') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)


def append_event(path, value):
    """累積費用台帳を追記し、ディスクへ確定する。"""
    with Path(path).open('a') as f:
        f.write(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())


def stage(output, name):
    """watchdogへ工程の開始時刻を原子的に通知する。"""
    tmp=output/'stage.tmp';tmp.write_text(json.dumps({'name':name,'started':time.monotonic()}))
    tmp.replace(output/'stage.json')


def limit_reason(elapsed, stage_elapsed, rss, disk, limits):
    """人工試験可能な資源門。すべての上限を同時に守る。"""
    return next((name for name,bad in [
        ('wall',elapsed>=limits['wall_s']),('stage',stage_elapsed>=limits['stage_s']),
        ('RSS',rss>limits['RSS_bytes']),('disk',disk>limits['output_bytes'])] if bad),None)


def canonical_keys(groups):
    """PDB固定欄の空白だけを正規化する。原子の並べ替えは禁止。"""
    return [[tuple(str(v).strip() for v in key) for key in group] for group in groups]


def pdb_keys(path):
    """原PDBのCAキーをmodel順に抽出する。"""
    groups=[];current=[]
    for line in Path(path).read_text().splitlines():
        if line.startswith('ENDMDL'):
            groups.append(current);current=[]
        elif line.startswith(('ATOM  ','HETATM')) and line[12:16].strip()=='CA':
            current.append([line[21],line[22:26],line[26],line[17:20],line[16]])
    if current:groups.append(current)
    return canonical_keys(groups)


def supervise(project,bundle,output,worker_command=None):
    """単科学processを外部監視し、例外時にも台帳とログを保持する。"""
    import psutil
    output.mkdir(parents=True,exist_ok=True)
    (project/'artifacts').mkdir(exist_ok=True)
    lock=(project/'artifacts/nmr34-v2-qualification-global.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (output/'start.json').exists():
        lock.close();raise ValueError('既存実行は再起動しない')
    config=json.loads((bundle/'config.json').read_text());limits=config['limits']
    start=time.monotonic();stage(output,'startup')
    exclusive_json(output/'start.json',{'start_monotonic':start,'config':config})
    process=None;peak=0;threads=0;reason=None
    with (output/'stdout.log').open('x') as stdout,(output/'stderr.log').open('x') as stderr:
        command=worker_command or [sys.executable,__file__,'worker',str(project),str(bundle),str(output)]
        process=subprocess.Popen(command,stdout=stdout,stderr=stderr)
        append_event(output/'budget.jsonl',{'event':'START','worker_pid':process.pid,'elapsed_s':time.monotonic()-start})
        try:
            while True:
                snapshot=json.loads((output/'stage.json').read_text());now=time.monotonic()
                tree=[psutil.Process()]+psutil.Process().children(recursive=True)
                rss=0
                for p in tree:
                    try:
                        rss+=p.memory_info().rss
                        if p.pid==process.pid:threads=max(threads,p.num_threads())
                    except psutil.NoSuchProcess:pass
                peak=max(peak,rss)
                disk=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
                reason=limit_reason(now-start,now-snapshot['started'],rss,disk,limits)
                append_event(output/'budget.jsonl',{'event':'SAMPLE','elapsed_s':now-start,'stage':snapshot['name'],
                            'RSS_bytes':rss,'output_bytes':disk,'worker_threads':threads})
                if reason or process.poll() is not None:break
                time.sleep(.1)
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait()
    elapsed=time.monotonic()-start
    result={'status':'PASS' if process.returncode==0 and not reason else 'STOPPED',
            'returncode':process.returncode,'protection_reason':reason,'cumulative_wall_s':elapsed,
            'peak_process_tree_RSS_bytes':peak,'max_worker_threads_observed':threads,
            'output_bytes':sum(p.stat().st_size for p in output.rglob('*') if p.is_file())}
    append_event(output/'budget.jsonl',{'event':'END',**result})
    exclusive_json(output/'supervisor-final.json',result)
    lock.close()
    if result['status']!='PASS':raise RuntimeError('限定実行は停止した。証拠を保全して審査する。')


def worker(project,bundle,output):
    """SHA検査後、固定入力の二単位を一回ずつ評価する。"""
    import numpy as np
    import MDAnalysis as mda
    from nmr34_v2 import (References,Run,Timer,archive_metadata,dcd_chunks,evaluate_chunks,
        export_references,fingerprint,load_ca_once,proper_rmsd,require,save_json,sha256,summarize,verify_inputs)
    start=time.monotonic();cpu=time.process_time();total=Timer()
    config=json.loads((bundle/'config.json').read_text());require(config['ids']==IDS,'行列変更禁止')
    frozen=json.loads((bundle/'freeze.json').read_text())
    with total.measure('input_SHA_before'):
        before=verify_inputs({project/p:h for p,h in config['inputs'].items()})
        for name,h in config['code_sha256'].items():require(sha256(Path(__file__).with_name(name))==h,'実装SHA不一致')
        fp=fingerprint(config,config['inputs'],[Path(__file__).with_name(n) for n in config['code_sha256']])
        save_json(output/'execution-fingerprint.json',{'fingerprint':fp,'config':config,
            'Python':sys.version,'numpy':np.__version__,'MDAnalysis':mda.__version__,
            'environment':{n:os.environ.get(n) for n in ('CUDA_VISIBLE_DEVICES','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}})
    stage(output,'reference')
    with total.measure('references_and_self_tests'):
        refs_path=project/'source/inputs/p1-fsd-ey/1FME-folded.pdb'
        keys=canonical_keys(frozen['CA_keys']);require(pdb_keys(refs_path)==keys,'参照キー不一致')
        u=mda.Universe(str(refs_path));ca=u.select_atoms('name CA')
        refs=References(np.array([ca.positions.copy().astype(float) for _ in u.trajectory]))
        for native in refs.native:
            require(proper_rmsd(native,native)<=1e-8,'参照自己不一致')
            require(proper_rmsd(native*[-1,1,1],native)>1e-5,'鏡映禁止不一致')
        export_references(refs,output)
    receipts=[]
    old=project/'artifacts/n1-cpu-20261030-v1/output/units'
    v1=project/'artifacts/nmr34-qa-20261030-v1/output'
    for tid,n in zip(IDS,[4000,8000]):
        stage(output,tid);t0=time.monotonic();c0=time.process_time();unit_timer=Timer()
        dest=output/tid
        with Run(dest,fp):
            science=project/'runs/b1-expansion-20261026/tasks'/tid/'science'
            prep=science.parent.parent/(tid+'-prep')/'science'
            with unit_timer.measure('CA_cache_and_metadata'):
                require(pdb_keys(science/'initial.pdb')==[keys[0]],'初期原子順不一致')
                cached=load_ca_once(prep/'features.npz',16*1024**2)
                with np.load(prep/'features.npz',allow_pickle=False) as z:
                    valid=z['valid'];reasons=z['reasons'];time_ps=z['time_ps']
                previous=np.load(old/tid/'frames.npz',allow_pickle=False)
                original=np.load(v1/tid/'frames.npz',allow_pickle=False)
                for field in ('frame_id','global_frame_id','time_ps','local_time_ps','valid'):
                    require(np.array_equal(original[field],previous[field]),'v1/N1 metadata不一致 '+field)
                require(len(cached)==n and np.array_equal(valid,previous['valid']) and
                        np.array_equal(time_ps,previous['time_ps']),'元metadata不一致')
                require(np.array_equal(time_ps,np.genfromtxt(science/'sim.csv',delimiter=',',skip_header=1)[:,1]),'sim時刻不一致')
                archive_metadata(dest,previous['frame_id'],previous['global_frame_id'],time_ps,previous['local_time_ps'],valid,reasons)
                orig=list(csv.DictReader((old/tid/'windows.csv').open()))
                windows=[(int(r['burn_ps']),float(r['prefix_ns']),float(r['sampling_ps'])) for r in orig]
                statuses={f'{b}_{p}_{s}':r['window_status'] for (b,p,s),r in zip(windows,orig)}
            chunks=dcd_chunks(science/'initial.pdb',science/'sim.dcd',cached,keys[0])
            manifest,timer=evaluate_chunks(chunks,refs,dest,qualify=True,margin_A=config['near_margin_A'])
            rows=summarize(dest,manifest,previous['local_time_ps'],valid,windows,timer,statuses)
            with unit_timer.measure('v1_N1_and_window_equivalence'):
                err=0.;time_error=0.;origin=None;near_count=0
                for item in manifest:
                    i=item['start'];j=i+item['frames'];sl=slice(i,j)
                    with np.load(dest/item['path'],allow_pickle=False) as z:
                        r=z['RMSD_A'];q=z['Q'];count=z['contact_count']
                        e=float(np.max(abs(r-original['RMSD_A'][sl])));err=max(err,e)
                        require(e<=1e-8,'全34 v1/v2 RMSD不一致')
                        require(np.max(abs(r[:,0]-previous['RMSD_A'][sl]))<=1e-8,'N1不一致')
                        require(np.array_equal(count,original['contact_count'][sl]) and np.array_equal(q,original['Q'][sl]),'Q/count不一致')
                        if not np.array_equal(z['argmin_model'],original['argmin_model'][sl]):
                            save_json(dest/'argmin-disagreement.json',{'frame_start':i,'v2':z['argmin_model'].tolist(),'v1':original['argmin_model'][sl].tolist()})
                            raise ValueError('argmin不一致')
                        require(np.max(abs(z['ensemble_min_RMSD_A']-original['ensemble_min_RMSD_A'][sl]))<=1e-8,'ensemble不一致')
                        require(np.array_equal(z['frame_id'],previous['frame_id'][sl]),'frame ID不一致')
                        arg=z['argmin_model']-1;require(np.array_equal(z['Q_at_RMSD_argmin'],original['Q'][sl][np.arange(j-i),arg]),'同参照Q不一致')
                        if origin is None:origin=z['dcd_time_ps'][0]-time_ps[0]
                        time_error=max(time_error,float(np.max(abs(z['dcd_time_ps']-origin-time_ps[sl]))))
                        require(time_error<.001,'DCD時刻不一致')
                        # near表の全件を元cache座標へ戻して確認する。
                        near=z['near_pair'];near_count+=len(near)
                        for (frame,a,b),margin in zip(near,z['near_margin_A']):
                            distance=np.linalg.norm(cached[i+frame,a].astype(float)-cached[i+frame,b].astype(float))
                            require(abs((distance-8)-margin)<=1e-12,'near margin不一致')
                ids=json.loads((dest/'window-ids.json').read_text());oldids=json.loads((v1/tid/'window-ids.json').read_text())
                expected=list(csv.DictReader((v1/tid/'windows.csv').open()))
                for row in rows:
                    b,p,s=map(float,row['window'].split('_'));prior_key=f'{int(b)}_{p*1000}_{int(s/.5)}'
                    require(ids[row['window']]['valid']==oldids[prior_key],'旧窓ID不一致')
                    require(row['valid']==len(ids[row['window']]['valid']),'窓件数不一致')
                    if row['model']!='NMR34_MIN':
                        prior=next(v for v in expected if int(v['model'])==row['model'] and float(v['burn_ps'])==b and float(v['prefix_ns'])==p and float(v['sampling_ps'])==s)
                        for key in ('min_RMSD_A','mean_RMSD_A','median_RMSD_A','p10_RMSD_A','final_RMSD_A','mean_Q','median_Q','max_Q','Q_at_argmin','argmin_frame'):
                            require(abs(row[key]-float(prior[key]))<=1e-8,'窓要約不一致 '+key)
                    else:
                        ii=np.asarray(ids[row['window']]['valid']);rr=original['ensemble_min_RMSD_A'][ii]
                        aa=original['argmin_model'][ii]-1;qq=original['Q'][ii,aa];mi=int(rr.argmin())
                        truth=dict(min_RMSD_A=rr.min(),mean_RMSD_A=rr.mean(),median_RMSD_A=np.median(rr),
                            p10_RMSD_A=np.quantile(rr,.1),final_RMSD_A=rr[-1],mean_Q=qq.mean(),median_Q=np.median(qq),
                            max_Q=qq.max(),Q_at_argmin=qq[mi],argmin_frame=ii[mi])
                        for key,value in truth.items():require(abs(row[key]-float(value))<=1e-8,'ensemble窓不一致 '+key)
                require(len(rows)==840,'全窓行数不一致')
            receipt={'task_id':tid,'status':'PASS','frames':n,'v1_v2_max_RMSD_error_A':err,'Q_count_exact':True,
                     'argmin_exact':True,'window_equivalence':True,'DCD_time_error_ps':time_error,'near_pairs':near_count,
                     'wall_s':time.monotonic()-t0,'CPU_s':time.process_time()-c0,'timing':{**unit_timer.records,**timer.records}}
            save_json(dest/'qualification.json',receipt);receipts.append(receipt)
            previous.close();original.close()
    stage(output,'final_SHA')
    with total.measure('input_SHA_after'):
        require(verify_inputs({project/p:h for p,h in config['inputs'].items()})==before,'事後入力SHA不一致')
    save_json(output/'worker-final.json',{'status':'PASS','units':receipts,'input_SHA_unchanged':True,
        'wall_s':time.monotonic()-start,'CPU_s':time.process_time()-cpu,'timing':total.records,'full_272_executed':False})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['supervise','worker'])
    for key in ('project','bundle','output'):parser.add_argument(key,type=Path)
    args=parser.parse_args()
    if args.mode=='supervise':supervise(args.project,args.bundle,args.output)
    else:worker(args.project,args.bundle,args.output)
