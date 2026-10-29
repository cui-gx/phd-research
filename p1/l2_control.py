"""承認済みL2行列を一つの制御器で実行し、復核点で安全に停止する。"""
import argparse
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from p1.l2_engineering import read, rows, sha, write

def main(a):
    lock=(a.output/'controller.run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    release=read(a.output/'execution-release.json')
    assert release['remote_readback']=='PASS'
    for name,h in release['plan_sha256'].items():assert sha(a.plan/name)==h
    for name,h in release['adapter_sha256'].items():assert sha(Path(__file__).parent/name)==h
    events=(a.output/'events.jsonl').open('a',buffering=1)
    def event(kind,**kw):events.write(json.dumps(dict(event=kind,time_unix=time.time(),**kw),ensure_ascii=False)+'\n')
    def status(state,unit=None):
        chains=list((a.output/'chains').glob('*/result.json'));points=list((a.output/'evaluations').glob('*/result.json'))
        write(a.output/'status.json',dict(status=state,current=unit,controller_pid=os.getpid(),chains_complete=len(chains),expected_chains=36,evaluations_complete=len(points),expected_evaluations=156,scientific_optimizer_steps=sum(read(p)['steps'] for p in chains)))
    def run(kind,unit):
        destination=a.output/('chains' if kind=='train' else 'evaluations')/unit
        if (destination/'result.json').exists():
            assert read(destination/'result.json')['status']=='COMPLETE'
            event('SKIP_EXISTING_SUCCESS',kind=kind,unit=unit);return
        assert not destination.exists(),'不完全単位あり。自動再試行せず停止。'
        for name,h in release['plan_sha256'].items():assert sha(a.plan/name)==h
        ledger=read(a.output/'cost-ledger.json')
        assert sum(x['wall_s'] for x in ledger)<7200,'2時間復核点'
        available=int(Path('/proc/meminfo').read_text().split('MemAvailable:')[1].split()[0])*1024
        assert available>=4*1024**3,'共用RAM不足'
        assert __import__('shutil').disk_usage(a.output).free>=4*1024**3,'disk余裕不足'
        gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip()
        if kind=='train':assert not gpu,'GPU使用中'
        event('RESOURCE_CHECK',unit=unit,available_RAM_bytes=available,GPU_idle=not bool(gpu))
        process_start=time.monotonic();status('RUNNING',unit);env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if kind=='train' else '-1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',CUBLAS_WORKSPACE_CONFIG=':4096:8')
        with (a.output/(unit+'.stdout')).open('x') as out,(a.output/(unit+'.stderr')).open('x') as err:
            result=subprocess.run([sys.executable,'-m','p1.l2_'+('train' if kind=='train' else 'evaluate'),str(a.project),str(a.plan),str(a.output),unit],env=env,stdout=out,stderr=err)
        assert result.returncode==0, '子単位失敗: '+unit
        assert read(destination/'result.json')['status']=='COMPLETE'
        event('UNIT_COMPLETE',kind=kind,unit=unit,process_wall_s=time.monotonic()-process_start);status('RUNNING')
    try:
        matrix=rows(a.plan/'experiment-matrix.csv');ordered=[]
        for si,state in enumerate(['r01-s4','r01-s8','r02-s4','r02-s8']):
            for ii in range(3):
                prefix=state+f'-i{ii+1}-'
                ordered += [prefix+'M0']+[prefix+x for x in (['F1','F2'] if (si+ii)%2==0 else ['F2','F1'])]
        assert set(ordered)=={r['chain_id'] for r in matrix}
        for chain in ordered:run('train',chain)
        for cp in rows(a.plan/'checkpoint-matrix.csv'):run('evaluate',cp['checkpoint_id'])
        status('SCIENTIFIC_UNITS_COMPLETE');event('ALL_UNITS_COMPLETE')
    except BaseException as e:
        status('STOPPED');event('STOPPED',reason=str(e));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path);main(p.parse_args())
