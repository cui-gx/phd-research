"""承認済みB1拡張の復元可能な単GPU制御器。科学関数は再実装しない。"""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from .science import ROOT
from .gq_r2 import dump,sha
from .expansion_contract import RUN_ID,experiment_matrix,M0_SEED,INFERENCE_SEED
from .b1_run import execute_b1

PLAN_COMMIT='060c72e981234a652deae7f3d8db2f4f2dfd4724'


class Campaign:
    """成功出力はハッシュを照合し、失敗を黙って上書きしない。"""
    def __init__(self):
        from .support import inspect_host
        from .runner import controller_affinity
        from parsl.concurrent import ParslPoolExecutor
        from parsl.config import Config
        from parsl.executors.threads import ThreadPoolExecutor
        self.root=ROOT.parent/'runs'/RUN_ID;self.art=ROOT.parent/'artifacts'/RUN_ID
        self.root.mkdir(exist_ok=True);self.art.mkdir(exist_ok=True)
        self.lock=(self.root/'run.lock').open('a');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        matrix_path=ROOT/'docs/P1-B1-Expansion/experiment-matrix.json'
        self.matrix=json.loads(matrix_path.read_text())
        if self.matrix!=experiment_matrix():raise ValueError('事前行列の再生成結果が一致しません。')
        verified=json.loads((self.art/'preregistration-verified.json').read_text())
        if verified['plan_commit']!=PLAN_COMMIT or verified['matrix_sha256']!=sha(matrix_path):raise ValueError('事前登録の遠隔確認が不一致です。')
        self.attempts=json.loads((self.root/'attempt-map.json').read_text()) if (self.root/'attempt-map.json').exists() else {}
        sources={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'p1/server').glob('*.py') if not p.name.startswith('._')}
        if not (self.root/'manifest.json').exists():
            inspection=inspect_host();dump(self.root/'environment-private.json',inspection)
            uuid=subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
            if '\n' in uuid:raise ValueError('単GPU条件に一致しません。')
            dump(self.root/'manifest.json',dict(approval='P1-B1-EXPANSION-20261026',plan_commit=PLAN_COMMIT,
                implementation_commit=verified['implementation_commit'],matrix_sha256=sha(matrix_path),GPU_uuid=uuid,
                monotonic_origin=time.monotonic(),source_sha256=sources,input_sha256=sha(ROOT/'inputs/p1-fsd-ey/1FME-unfolded.pdb')))
            saved=self.art/'executed-source';saved.mkdir()
            for rel in sources:
                target=saved/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
            shutil.copytree(ROOT/'docs/P1-B1-Expansion',self.art/'preregistered-documents',ignore=shutil.ignore_patterns('._*'))
        self.manifest=json.loads((self.root/'manifest.json').read_text())
        expected=dict(self.manifest['source_sha256'])
        for p in sorted(self.root.glob('source-amendment-*.json')):expected.update(json.loads(p.read_text())['source_sha256'])
        if any(sha(ROOT/n)!=h for n,h in expected.items()):raise ValueError('実行ソースが変わっています。修正記録が必要です。')
        self.expected_sources=expected
        self.origin=self.manifest['monotonic_origin'];self.log=(self.root/'events.jsonl').open('a',buffering=1)
        self.previous=controller_affinity([0]);self.executor=ParslPoolExecutor(config=Config(executors=[ThreadPoolExecutor(label='expansion-one',max_threads=1)],run_dir=str(self.root/f'parsl-{time.time_ns()}'),usage_tracking=0,app_cache=False))
        self.completed=set();self.emit('controller_started',pid=os.getpid());self.progress('RUNNING')

    def emit(self,kind,**values):
        self.log.write(json.dumps(dict(kind=kind,at_s=time.monotonic()-self.origin,UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**values))+'\n')

    def science(self,name):return self.root/'tasks'/self.attempts.get(name,name)/'science'

    def available(self,name):
        p=self.science(name).parent/'availability.json'
        if not p.exists():
            dump(p,dict(monotonic=time.monotonic(),UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),recovery_publication=True))
        return json.loads(p.read_text())['monotonic']

    def progress(self,status,error=None):
        expected=[v['branch_id'] for v in self.matrix['branches']]
        evaluated=[n for n in expected if (self.science(n+'-analysis')/'result.json').exists()]
        md=[n for n in expected if (self.science(n+'-md')/'result.json').exists()]
        dump(self.root/'status.json',dict(status=status,completed_downstream_MD=len(md),evaluated_branches=len(evaluated),expected_downstream_MD=240,
             completed_task_count=len(self.completed),last_completed=getattr(self,'last',None),error=error,
             updated_UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),S3='NOT APPROVED',B2_and_C_predictor='NOT APPROVED'))

    def task(self,name,kind,files=(),**kwargs):
        from .qualification import occupancy
        if any(sha(ROOT/n)!=h for n,h in self.expected_sources.items()):raise ValueError('タスク開始前のソース照合が不一致です。')
        actual=self.attempts.get(name,name);target=self.root/'tasks'/actual
        req=dict(kind=kind,task_id=actual,output_dir=str(target/'science'),gpu_uuid=self.manifest['GPU_uuid'],
            worker_module='p1.server.expansion_science',supervision_interval_s=1.,GPU_diagnostics=True,
            minimum_free_bytes=100*1024**3,timeout_s=1800 if kind=='md' else (600 if kind=='ai' else 2400),
            input_hashes={str(p):sha(p) for p in files},**kwargs)
        if (target/'science/result.json').exists():
            if json.loads((target/'request.json').read_text())!=req:raise ValueError('再開時の入力が変化しています：'+name)
            result=json.loads((target/'science/result.json').read_text())
            if result['status']!='success' or any(sha(target/'science'/n)!=h for n,h in result['artifacts'].items()):raise ValueError('完成済み出力が変化しています。')
            self.completed.add(name);self.available(name);return result
        if target.exists():raise RuntimeError('未完/失敗attemptを保存して新attemptを登録してください：'+name)
        if (self.root/'STOP').exists():raise RuntimeError('研究者または実行端のSTOPを検出しました。')
        snap=occupancy()
        paths=[self.root,self.art,Path(sys.prefix)]
        size=sum(int(subprocess.check_output(['du','-sb',str(p)],text=True).split()[0]) for p in paths)
        if size>120*1024**3-256*1024**2 or shutil.disk_usage(self.root).free<100*1024**3:raise RuntimeError('容量保護のため停止します。')
        target.mkdir(parents=True);dump(target/'occupancy-private.json',snap);dump(target/'request.json',req)
        self.emit('task_dispatched',task=name,actual_task=actual,kind_task=kind,request_sha256=sha(target/'request.json'))
        result=self.executor.submit(execute_b1,str(target/'request.json')).result()
        dump(target/'availability.json',dict(monotonic=time.monotonic(),UTC=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
        self.emit('task_output_available',task=name,actual_task=actual,result_sha256=sha(target/'science/result.json'),qualified=kind=='prepare')
        self.completed.add(name);self.last=name;self.progress('RUNNING');print('完了',name,flush=True)
        return result

    def prepare(self,name,contacts):
        p=self.science(name);r=json.loads((p/'result.json').read_text())
        return self.task(name+'-prep','prepare',files=[p/'sim.dcd',p/'initial.pdb'],md_dir=str(p),dcd_sha256=sha(p/'sim.dcd'),length_ns=r['length_ns'],contacts=contacts)

    def pool(self,name,prepared,state,stage):
        files=[p/n for p in prepared for n in ('features.npz','contacts.npy')]
        return self.task(name,'pool',files=files,prepared=list(map(str,prepared)),root_id=state['root_id'],state_id=state['state_id'],boundary_ps=state['boundary_ps'],pool_stage=stage)

    def ai(self,name,pool,seed,operation,arm=None,cp=None):
        files=[pool/n for n in ('contacts.npy','indices.json')]
        kw=dict(pool=str(pool),seed=seed,operation=operation,contacts_sha256=sha(pool/'contacts.npy'),indices_sha256=sha(pool/'indices.json'))
        if arm:kw['arm']=arm
        if cp:files.append(cp);kw.update(checkpoint=str(cp),checkpoint_sha256=sha(cp))
        return self.task(name,'ai',files=files,**kw)

    def prepare_root(self,root):
        rid=root['root_id'];prepared=[];previous=None
        for segment in range(1,5):
            name=f'{rid}-h{segment}-md';kw=dict(seed=root['history_seed'],length_ns=2,expected_initial_time_ps=(segment-1)*2000)
            files=[]
            if previous:
                files=[previous];kw.update(checkpoint=str(previous),checkpoint_sha256=sha(previous))
            self.task(name,'md',files=files,**kw);self.prepare(name,True);prepared.append(self.science(name+'-prep'));previous=self.science(name)/'final.chk'
            milestone=4 if segment<=2 else 8;state=next(v for v in self.matrix['states'] if v['root_id']==rid and v['milestone_ns']==milestone);sid=state['state_id']
            if segment in (1,3):
                self.pool(sid+'-old-pool',prepared,state,'old_only_M0')
                self.ai(sid+'-M0',self.science(sid+'-old-pool'),M0_SEED,'train','M0')
                r=json.loads((self.science(sid+'-M0')/'result.json').read_text())
                baseline=self.root/'common-M0-initial-digests.json';value={k:r[k] for k in ('initial_model_digest','initial_optimizer_digest')}
                if baseline.exists() and json.loads(baseline.read_text())!=value:raise ValueError('未学習M0の共通初期値が不一致です。')
                if not baseline.exists():dump(baseline,value)
            else:
                self.pool(sid+'-decision-pool',prepared,state,'decision');pool=self.science(sid+'-decision-pool')
                self.task(sid+'-features','features',files=[pool/'features.npz',pool/'indices.json',self.science(sid+'-M0')/'checkpoint.pt'],
                    pool=str(pool),root_id=rid,state_id=sid,milestone_ns=milestone,boundary_ps=state['boundary_ps'],
                    M0_available_monotonic=self.available(sid+'-M0'),inputs_available_monotonic=self.available(sid+'-decision-pool'))
                m0=json.loads((self.science(sid+'-M0')/'result.json').read_text())
                frozen=dict(state=state,M0_checkpoint_sha256=sha(self.science(sid+'-M0')/'checkpoint.pt'),
                    M0_model_digest=m0['final_model_digest'],M0_optimizer_digest=m0['final_optimizer_digest'],
                    last_history_checkpoint_sha256=sha(self.science(name)/'final.chk'),
                    history_DCD_sha256=[sha(self.science(f'{rid}-h{i}-md')/'sim.dcd') for i in range(1,segment+1)],
                    pool_indices_sha256=sha(pool/'indices.json'),pool_features_sha256=sha(pool/'features.npz'),
                    features_sha256=sha(self.science(sid+'-features')/'state-features.json'),
                    frozen_monotonic=self.available(sid+'-features'),history_tasks=[f'{rid}-h{i}-md' for i in range(1,segment+1)])
                p=self.root/'states'/(sid+'.json');p.parent.mkdir(exist_ok=True)
                if p.exists() and json.loads(p.read_text())!=frozen:raise ValueError('凍結状態が変化しています。')
                if not p.exists():dump(p,frozen);self.emit('decision_state_frozen',state=sid,sha256=sha(p))

    def models(self,state):
        sid=state['state_id'];frozen=json.loads((self.root/'states'/(sid+'.json')).read_text());pool=self.science(sid+'-decision-pool');cp=self.science(sid+'-M0')/'checkpoint.pt'
        if sha(cp)!=frozen['M0_checkpoint_sha256'] or sha(pool/'indices.json')!=frozen['pool_indices_sha256']:raise ValueError('状態のモデル/poolが変化しています。')
        training={};inferences={};models={'F0':cp}
        for t in (1,2):
            arms=['F1','F2'] if (int(state['root_id'][1:])+state['milestone_ns']+t)%2 else ['F2','F1']
            for arm in arms:
                label=f'{arm}-t{t}';name=sid+'-'+label
                self.ai(name,pool,state['training_seeds'][str(t)],'train',arm,cp)
                training[label]=str(self.science(name));models[label]=self.science(name)/'checkpoint.pt'
        for label,model in list(models.items())+[('F0-repeat',cp)]:
            name=sid+'-infer-'+label;self.ai(name,pool,INFERENCE_SEED,'infer',cp=model);inferences[label]=str(self.science(name))
        self.task(sid+'-selection','selection',files=[pool/'features.npz',pool/'indices.json']+[Path(p)/'result.json' for p in training.values()]+[Path(p)/'ranking.npz' for p in inferences.values()],
            pool=str(pool),training=training,inferences=inferences,history_tasks=[str(self.science(n)) for n in frozen['history_tasks']])

    def branch(self,b):
        sid=b['state_id'];bid=b['branch_id'];selected=self.science(sid+'-selection');label='F0' if b['arm']=='F0' else b['arm']+f"-t{b['training_block']}"
        point=json.loads((selected/'selected.json').read_text())[label];freeze=self.root/'states'/(sid+'.json')
        self.task(bid+'-md','md',files=[selected/(label+'.npy'),selected/'selected.json',freeze],seed=b['MD_seed'],length_ns=4,
            selected=str(selected/(label+'.npy')),selected_sha256=point['selected_sha256'],source_global_frame=point['frame_id'],
            source_DCD_sha256=point['DCD_sha256'],model_sha256=point['checkpoint_sha256'],branch=b,state_freeze_sha256=sha(freeze))
        self.prepare(bid+'-md',False);p=self.science(bid+'-md-prep');pool=self.science(sid+'-decision-pool')
        self.task(bid+'-analysis','analysis',files=[p/'features.npz',pool/'features.npz',self.science(bid+'-md')/'initial-coordinates-A.npy',selected/(label+'.npy')],
            branch=b,prepared=str(p),pool=str(pool),selected=str(selected/(label+'.npy')),md_dir=str(self.science(bid+'-md')))

    def close(self,status,error=None):
        from .runner import restore_affinity
        self.progress(status,error);self.executor.shutdown(wait=True);restore_affinity(self.previous);self.log.close();self.lock.close()


def main():
    p=argparse.ArgumentParser(description='承認済み240枝だけを復元可能に実行する。');p.add_argument('--phase',choices=['all','first','remaining','final'],default='all');a=p.parse_args()
    campaign=Campaign();status='STOPPED';error=None
    try:
        if a.phase in ('all','first'):
            campaign.prepare_root(campaign.matrix['roots'][0])
            for s in campaign.matrix['states']:
                if s['root_id']=='r01':campaign.models(s)
            campaign.branch(campaign.matrix['branches'][0]);campaign.emit('first_registered_branch_engineering_complete')
        if a.phase in ('all','remaining'):
            for root in campaign.matrix['roots']:campaign.prepare_root(root)
            for state in campaign.matrix['states']:campaign.models(state)
            for branch in campaign.matrix['branches']:campaign.branch(branch)
            campaign.emit('fixed_matrix_complete',downstream_MD_ns=960)
        if a.phase in ('all','remaining','final'):
            from .expansion_analysis import finalize_campaign
            started=time.perf_counter();cpu=time.process_time()
            try:finalize_campaign(campaign.root,campaign.art,campaign.matrix)
            finally:dump(campaign.art/'finalization-runtime.json',dict(wall_s=time.perf_counter()-started,CPU_s=time.process_time()-cpu,GPU_compute=False))
            from .expansion_publish import publish,archive
            publish(campaign.root,campaign.art,campaign.matrix)
            archive(campaign.root,campaign.art,campaign.matrix)
            status='ANALYSIS_ARCHIVED_AWAITING_LOCAL_BACKUP'
        else:status='FIRST_BRANCH_VERIFIED'
    except BaseException as e:error=repr(e);status='STOPPED_REQUIRES_INSPECTION';raise
    finally:campaign.close(status,error)


if __name__=='__main__':main()
