"""既存Parsl単一worker構成を使う、範囲固定のB1 Pilot制御。"""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import shutil


def execute_b1(request_path):
    """本人のタスクだけを監督し、完了後に完全回収する。"""
    import psutil
    from p1.server.support import ROOT,_terminate_owned_group
    from p1.server.gq_r2 import dump,sha
    p=Path(request_path);req=json.loads(p.read_text());task=p.parent
    gpu=req['kind'] in ('md','ai')
    env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES=req['gpu_uuid'] if gpu else '-1',
        OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENMM_CPU_THREADS='2',
        PYTHONDONTWRITEBYTECODE='1',WANDB_MODE='disabled',MPLBACKEND='Agg',
        MPLCONFIGDIR=str(task/'runtime-cache/mpl'),CUDA_CACHE_PATH=str(task/'runtime-cache/cuda'))
    (task/'runtime-cache').mkdir(exist_ok=False)
    start=time.monotonic();child=None;peak=0;reason=None
    with (task/'stdout.txt').open('x') as stdout,(task/'stderr.txt').open('x') as stderr,(task/'telemetry.jsonl').open('x') as telemetry:
        try:
            module=req.get('worker_module','p1.server.b1_science')
            if module not in ('p1.server.b1_science','p1.server.expansion_science'):
                raise ValueError('未承認の科学workerです。')
            child=subprocess.Popen(['taskset','-c','1,2',sys.executable,'-B','-m',module,str(p)],
                                   cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            dump(task/'process.json',dict(owned_pid=child.pid,GPU=gpu))
            while child.poll() is None:
                try:
                    procs=[psutil.Process(child.pid),*psutil.Process(child.pid).children(recursive=True)]
                    current=sum(q.memory_info().rss for q in procs if q.is_running());peak=max(peak,current)
                    ids=[q.pid for q in procs]
                except psutil.NoSuchProcess:ids=[child.pid]
                if gpu:
                    query=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
                    if query.returncode:raise RuntimeError('GPU共有状態を確認できません。')
                    listed=[int(v.strip()) for v in query.stdout.splitlines() if v.strip()]
                    if any(v not in ids for v in listed):reason='他利用者のGPUプロセスを検出'
                diagnostic=None
                if gpu and req.get('GPU_diagnostics'):
                    sample=subprocess.run(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
                    diagnostic=dict(query_returncode=sample.returncode,utilization_memory_power=sample.stdout.strip())
                if req.get('minimum_free_bytes') and shutil.disk_usage(task).free<req['minimum_free_bytes']:
                    reason='保存先の空き容量保護に達しました。'
                telemetry.write(json.dumps(dict(elapsed_s=time.monotonic()-start,RSS_bytes=peak,GPU_diagnostic=diagnostic))+'\n');telemetry.flush()
                if time.monotonic()-start>req['timeout_s']:reason='単体異常監視時間超過'
                if peak>16*1024**3:reason='RSS上限超過'
                if (task.parents[1]/'STOP').exists():reason='研究者または実行端STOP'
                if reason:_terminate_owned_group(child);break
                time.sleep(req.get('supervision_interval_s',.2))
            child.wait()
        except BaseException as e:
            reason=repr(e)
            if child is not None:_terminate_owned_group(child)
            raise
        finally:
            if child is not None and child.poll() is None:_terminate_owned_group(child)
            elapsed=time.monotonic()-start
            dump(task/'execution.json',dict(task=req['task_id'],kind=req['kind'],GPU=gpu,
                 GPU_occupation_s=elapsed if gpu else 0,elapsed_s=elapsed,peak_RSS_bytes=peak,
                 returncode=child.returncode if child else None,stop_reason=reason,request_sha256=sha(p)))
            shutil.rmtree(task/'runtime-cache')
    if child.returncode or reason:raise RuntimeError('科学タスクが失敗しました：'+req['task_id'])
    result=json.loads((task/'science/result.json').read_text())
    if result['status']!='success':raise RuntimeError('未完了の科学出力です。')
    return result


def main():
    from .science import ROOT
    from .gq_r2 import dump,sha
    from .qualification import occupancy
    from .support import inspect_host
    from .runner import controller_affinity,restore_affinity
    from parsl.concurrent import ParslPoolExecutor
    from parsl.config import Config
    from parsl.executors.threads import ThreadPoolExecutor
    p=argparse.ArgumentParser(description='承認済みB1 Pilotのみを順番に実行')
    p.add_argument('--stage',choices=['history','branches'],required=True)
    a=p.parse_args();root=ROOT.parent/'runs/b1-pilot-20261026';root.mkdir(exist_ok=True)
    lock=(root/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not (root/'manifest.json').exists():
        inspection=inspect_host();dump(root/'environment-private.json',inspection)
        uuid=subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
        if '\n' in uuid:raise RuntimeError('単一GPU条件を満たしません。')
        dump(root/'manifest.json',dict(approval='P1-B1-PILOT-20261026',plan_commit='0c92f6025bcde7a971994d9c515a1184abe83fbe',
             monotonic_origin=time.monotonic(),GPU_uuid=uuid,GPU_total_cap_s=None,
             source_sha256={str(v.relative_to(ROOT)):sha(v) for v in (ROOT/'p1/server').glob('*.py')},
             input_sha256=sha(ROOT/'inputs/p1-fsd-ey/1FME-unfolded.pdb'),scope_history_ns=4,scope_downstream_ns=24))
    manifest=json.loads((root/'manifest.json').read_text());origin=manifest['monotonic_origin']
    active_sources=dict(manifest['source_sha256'])
    for amendment in sorted(root.glob('source-amendment-*.json')):
        active_sources.update(json.loads(amendment.read_text())['source_sha256'])
    for rel,d in active_sources.items():
        if sha(ROOT/rel)!=d:raise RuntimeError('実行ソースが変化しています。修訂を記録してください。')
    log=(root/'events.jsonl').open('a',buffering=1)
    def emit(kind,**values):log.write(json.dumps(dict(kind=kind,at_s=time.monotonic()-origin,UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**values))+'\n')
    previous=controller_affinity([0])
    executor=ParslPoolExecutor(config=Config(executors=[ThreadPoolExecutor(label='b1-single',max_threads=1)],
                run_dir=str(root/('parsl-'+a.stage)),usage_tracking=0,app_cache=False))
    attempts=json.loads((root/'attempt-map.json').read_text()) if (root/'attempt-map.json').exists() else {}
    def task(name,kind,**kwargs):
        actual=attempts.get(name,name)
        target=root/'tasks'/actual
        req=dict(kind=kind,task_id=actual,output_dir=str(target/'science'),gpu_uuid=manifest['GPU_uuid'],
                 timeout_s=1800 if kind=='md' else (600 if kind=='ai' else 2400),**kwargs)
        if (target/'science/result.json').exists():
            if json.loads((target/'request.json').read_text())!=req:raise RuntimeError('再開時の入力が変化しています。')
            result=json.loads((target/'science/result.json').read_text())
            for n,d in result['artifacts'].items():
                if sha(target/'science'/n)!=d:raise RuntimeError('完成済み出力が変化しています。')
            return result
        if target.exists():raise RuntimeError('失敗/未完タスクを上書きできません：'+name)
        snap=occupancy();target.mkdir(parents=True);dump(target/'occupancy-private.json',snap)
        if sum(v.stat().st_size for v in root.rglob('*') if v.is_file())>10*1024**3:raise RuntimeError('結果保存量が保護上限を超えました。')
        dump(target/'request.json',req);emit('task_dispatched',task=name,kind_task=kind,input_sha256=sha(target/'request.json'))
        result=executor.submit(execute_b1,str(target/'request.json')).result()
        emit('task_output_available',task=name,result_sha256=sha(target/'science/result.json'),qualified=kind=='prepare')
        return result
    def science(name):return root/'tasks'/attempts.get(name,name)/'science'
    def prep(mdname,contacts):
        r=json.loads((science(mdname)/'result.json').read_text())
        return task('prepare-'+mdname,'prepare',md_dir=str(science(mdname)),dcd_sha256=sha(science(mdname)/'sim.dcd'),length_ns=r['length_ns'],contacts=contacts)
    def train(name,arm,seed,pool,cp=None):
        kw=dict(operation='train',arm=arm,seed=seed,pool=str(pool),contacts_sha256=sha(pool/'contacts.npy'),indices_sha256=sha(pool/'indices.json'))
        if cp:kw.update(checkpoint=str(cp),checkpoint_sha256=sha(cp))
        return task(name,'ai',**kw)
    try:
        if a.stage=='history':
            task('history-old','md',seed=2026102660,length_ns=2)
            prep('history-old',True)
            task('old-pool','pools',prepared=[str(science('prepare-history-old'))])
            train('M0','M0',2026102670,science('old-pool'))
            cp=science('history-old')/'final.chk'
            task('history-new','md',seed=2026102660,length_ns=2,checkpoint=str(cp),checkpoint_sha256=sha(cp))
            prep('history-new',True)
            task('decision-pool','pools',prepared=[str(science('prepare-history-old')),str(science('prepare-history-new'))])
            frozen=dict(M0_checkpoint_sha256=sha(science('M0')/'checkpoint.pt'),old_pool_sha256=sha(science('old-pool')/'indices.json'),
              decision_pool_sha256=sha(science('decision-pool')/'indices.json'),history_DCD_sha256=[sha(science(n)/'sim.dcd') for n in ['history-old','history-new']],
              data_legality='M0完了後にhistory-newを生成・公開',recipe_compatible=True,K=200,batch=4,exposures=800)
            dump(root/'state-freeze.json',frozen);emit('decision_state_frozen',sha256=sha(root/'state-freeze.json'))
        else:
            frozen=json.loads((root/'state-freeze.json').read_text())
            cp=science('M0')/'checkpoint.pt';require=sha(cp)==frozen['M0_checkpoint_sha256']
            if not require:raise RuntimeError('共通M0が変化しています。')
            pool=science('decision-pool');models={}
            models['F0']=cp
            for block in (1,2):
                for arm in (['F1','F2'] if block==1 else ['F2','F1']):
                    train(f'{arm}-b{block}',arm,2026102680+block,pool,cp)
                    models[f'{arm}-b{block}']=science(f'{arm}-b{block}')/'checkpoint.pt'
            ranks={}
            for label,model in list(models.items())+[('F0-repeat',cp)]:
                r=task('infer-'+label,'ai',operation='infer',seed=2026102671,pool=str(pool),contacts_sha256=sha(pool/'contacts.npy'),
                       indices_sha256=sha(pool/'indices.json'),checkpoint=str(model),checkpoint_sha256=sha(model))
                ranks[label]=r['selected_frame']
            import numpy as np
            f0=np.load(science('infer-F0')/'ranking.npz');fr=np.load(science('infer-F0-repeat')/'ranking.npz')
            if any(not np.array_equal(f0[k],fr[k]) for k in f0.files):raise RuntimeError('F0推論反復が不一致です。')
            for block in (1,2):
                r1=json.loads((science(f'F1-b{block}')/'result.json').read_text());r2=json.loads((science(f'F2-b{block}')/'result.json').read_text())
                for k in ['initial_model_digest','initial_optimizer_digest','initial_rng_digest','optimizer_steps','exposures']:
                    if r1[k]!=r2[k]:raise RuntimeError('配対更新条件が不一致です：'+k)
            dump(root/'selection-freeze.json',dict(selected_frames=ranks,F0_repeat_exact=True))
            import MDAnalysis as mda
            for block in (1,2):
                for arm in (['F0','F1','F2'] if block==1 else ['F2','F1','F0']):
                    label=arm if arm=='F0' else f'{arm}-b{block}';frame=ranks[label]
                    source='history-old' if frame<4000 else 'history-new';local=frame%4000
                    u=mda.Universe(str(science(source)/'initial.pdb'),str(science(source)/'sim.dcd'));u.trajectory[local]
                    target=root/f'selected-{arm}-b{block}.npy'
                    if not target.exists():np.save(target,u.atoms.positions.copy(),allow_pickle=False)
                    task(f'md-{arm}-b{block}','md',seed=2026102690+block,length_ns=4,selected=str(target),selected_sha256=sha(target),
                         source_global_frame=frame,source_DCD_sha256=sha(science(source)/'sim.dcd'),model_sha256=sha(models[label]))
                    prep(f'md-{arm}-b{block}',False)
            emit('six_downstream_completed',MD_ns=24)
    finally:
        executor.shutdown(wait=True);restore_affinity(previous);log.close();lock.close()


if __name__=='__main__':main()
