"""L2終了後の只読監査・集計・作図を単CPUで順次実行し費用を測る。"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from p1.l2_engineering import read,sha,write


def main(a):
    assert os.environ['CUDA_VISIBLE_DEVICES']=='-1'
    assert all(os.environ[x]=='1' for x in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'])
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
    assert read(a.output/'status.json')['status']=='SCIENTIFIC_UNITS_COMPLETE'
    locks=[]
    for name in ['controller.run.lock','training.run.lock','cpu.run.lock','postprocess.run.lock']:
        f=(a.output/name).open('a');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
    release=read(a.output/'postprocess-release.json');assert release['status']=='PASS'
    for rel,h in release['source_sha256'].items():assert sha(Path(__file__).parent.parent/rel)==h
    events=[json.loads(x) for x in (a.output/'events.jsonl').read_text().splitlines()]
    costs=read(a.output/'cost-ledger.json')
    first=[r for r in costs if r.get('chain_id')=='r01-s4-i1-M0' or r.get('checkpoint')=='r01-s4-i1-M0-step0000']
    base=sum(e.get('process_wall_s',0) for e in events)+sum(r['wall_s'] for r in first)
    base+=sum(read(a.output/'engineering'/name)['wall_s'] for name in ['freeze-cost.json','synthetic-cost.json'])
    ledger=[]
    stages=[('audit','p1.l2_audit',[a.project,a.plan,a.output]),('aggregate','p1.l2_aggregate',[a.project,a.plan,a.output]),('review-summary','p1.l2_review_summary',[a.plan,a.output]),('figures','p1.l2_figures',[a.output])]
    try:
        for label,module,args in stages:
            assert base+sum(r['wall_s'] for r in ledger)<7140,'2時間復核点（未計時初期化への60秒余裕を含む）'
            assert int(Path('/proc/meminfo').read_text().split('MemAvailable:')[1].split()[0])*1024>4*1024**3,'共用RAM不足'
            write(a.output/'postprocess-status.json',dict(status='RUNNING',phase=label))
            before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic();peak=0;violation=None
            with (a.output/(label+'.stdout')).open('x') as stdout,(a.output/(label+'.stderr')).open('x') as stderr:
                p=subprocess.Popen([sys.executable,'-m',module,*map(str,args)],stdout=stdout,stderr=stderr)
                while p.poll() is None:
                    stat=Path('/proc')/str(p.pid)/'status'
                    try:
                        content=stat.read_text()
                        if 'VmRSS:' in content:peak=max(peak,int(content.split('VmRSS:')[1].split()[0])*1024)
                    except FileNotFoundError:pass
                    elapsed=time.monotonic()-start
                    if peak>2*1024**3:violation='RSS2GiB超過'
                    if elapsed>300:violation='単工程300秒復核点'
                    if base+sum(r['wall_s'] for r in ledger)+elapsed>=7140:violation='累計時間復核点'
                    if violation:
                        p.terminate()
                        try:p.wait(timeout=5)
                        except subprocess.TimeoutExpired:p.kill();p.wait()
                        break
                    time.sleep(.25)
            after=resource.getrusage(resource.RUSAGE_CHILDREN)
            row=dict(phase=label,wall_s=time.monotonic()-start,CPU_s=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,peak_RSS_sampled_MiB=peak/2**20,return_code=p.returncode,source_sha256=sha(Path(__file__).parent/(module.split('.')[-1]+'.py')))
            ledger.append(row);write(a.output/'postprocess-costs.json',dict(observed_prior_wall_s=base,initial_process_startup_not_fully_measured=True,phases=ledger))
            assert not violation,violation
            assert p.returncode==0,'後処理失敗: '+label
            size=sum(x.stat().st_size for x in a.output.rglob('*') if x.is_file());assert size<=2*1024**3,'出力2GiB超過'
        write(a.output/'postprocess-status.json',dict(status='COMPLETE',phase='ALL',new_MD=0,new_training=0,new_forward=0))
    except BaseException as e:
        write(a.output/'postprocess-status.json',dict(status='STOPPED',reason=str(e)));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path);main(p.parse_args())
