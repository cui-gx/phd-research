"""GQ-R2のCPU限定監督。本人が起動したプロセス群のみ停止できる。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import psutil


def main():
    p=argparse.ArgumentParser(description='CPU解析の有界実行')
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--phase',required=True)
    p.add_argument('--analysis-id',default='analysis-v1')
    p.add_argument('--attempt',default='')
    args=p.parse_args();root=args.project;art=root/'artifacts/gq-r2-20261026'
    out=art/args.analysis_id;out.mkdir(exist_ok=True)
    label=args.phase+args.attempt
    if (art/(label+'-execution.json')).exists():
        raise RuntimeError('実行記録が既に存在します。上書きしません。')
    cores=psutil.cpu_percent(interval=1,percpu=True)
    available=psutil.virtual_memory().available
    gpu=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True)
    occupancy=dict(time_UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        CPU_0_1_2_percent=cores[:3],available_memory_bytes=available,
        GPU_process_count=len(gpu.stdout.strip().splitlines()) if gpu.stdout.strip() else 0,
        GPU_query_returncode=gpu.returncode,kind='CPU限定。GPUの使用権を主張しない。')
    (art/(label+'-resources.json')).write_text(json.dumps(occupancy,indent=2))
    if available<20*1024**3 or max(cores[:3])>60:
        raise RuntimeError('共有CPU/メモリ境界が不明瞭なため計算を停止します。')
    env=os.environ.copy()
    env.update(CUDA_VISIBLE_DEVICES='-1',OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',
               MPLCONFIGDIR=str(art/'mpl-cache'),PYTHONDONTWRITEBYTECODE='1')
    cmd=['taskset','-c','0,1,2',str(root/'source/.runtime/gq-r2-20261026/bin/python'),'-B','-m','p1.server.gq_r2',
         '--phase',args.phase,'--out',str(out),'--root',str(root/'runs/gq-r1-20261026'),
         '--prior',str(root/'artifacts/gq-r1-20261026/analysis-final-v2'),
         '--manifest',str(art/'r1-raw-sha256.json')]
    started=time.monotonic();rss=0;reason=None
    with open(art/(label+'-stdout.txt'),'x') as stdout,open(art/(label+'-stderr.txt'),'x') as stderr:
        proc=subprocess.Popen(cmd,cwd=root/'source',env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        while proc.poll() is None:
            try:
                parent=psutil.Process(proc.pid)
                current=sum(q.memory_info().rss for q in [parent,*parent.children(recursive=True)] if q.is_running())
                rss=max(rss,current)
            except psutil.NoSuchProcess:
                pass
            if rss>16*1024**3:reason='RSS16GiB超過'
            if time.monotonic()-started>2400:reason='2400秒超過'
            if reason:
                os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL)
                break
            time.sleep(.5)
        rc=proc.wait()
    record=dict(phase=args.phase,returncode=rc,wall_s=time.monotonic()-started,
                sampled_peak_process_tree_RSS_bytes=rss,stop_reason=reason,GPU_compute=False,
                command=[s.replace(str(root),'<PROJECT>') for s in cmd],
                environment={k:env[k].replace(str(root),'<PROJECT>') for k in ['CUDA_VISIBLE_DEVICES','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MPLCONFIGDIR']})
    (art/(label+'-execution.json')).write_text(json.dumps(record,indent=2,ensure_ascii=False))
    print(json.dumps(record,ensure_ascii=False),flush=True)
    raise SystemExit(rc)


if __name__=='__main__':main()
