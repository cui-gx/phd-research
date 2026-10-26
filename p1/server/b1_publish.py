"""B1の完了した証拠を照合し、小規模な公開用資料を整理する。"""
from pathlib import Path
import importlib.metadata as meta
import json
import platform
import shutil
import subprocess
from .science import ROOT
from .gq_r2 import sha,dump


def publish():
    project=ROOT.parent;root=project/'runs/b1-pilot-20261026';art=project/'artifacts/b1-pilot-20261026'
    out=art/'analysis-v1';public=art/'public-v1';public.mkdir(exist_ok=False)
    def redacted(v):
        if isinstance(v,dict):return {k:redacted(w) for k,w in v.items() if k not in ['gpu_uuid','GPU_uuid']}
        if isinstance(v,list):return [redacted(w) for w in v]
        if isinstance(v,str):return v.replace(str(project),'<PROJECT>')
        return v
    for p in out.iterdir():
        if p.suffix in ('.json','.csv','.png'):shutil.copy2(p,public/p.name)
    import numpy as np
    enhanced=json.loads((out/'discrete.json').read_text())
    for row in enhanced:
        feature=root/'tasks'/f"prepare-md-{row['arm']}-b{row['block']}"/'science/features.npz'
        with np.load(feature) as z:
            times=z['time_ps']
            row['representative_time_ps']=times[row['representative_frame_ids']].tolist()
            row['confirmation_time_ps']=times[row['confirmation_frame_ids']].tolist()
    dump(public/'discrete-with-times.json',enhanced)
    for name in ['state-freeze.json','selection-freeze.json','attempt-map.json','source-amendment-01.json','source-amendment-02.json']:
        dump(public/name,redacted(json.loads((root/name).read_text())))
    events=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
    dump(public/'events.json',redacted(events))
    import torch
    from .supplement_selection import tensor_digest,optimizer_digest
    models=[];inputs=[];failures=[]
    manifest={}
    for task in sorted((root/'tasks').iterdir()):
        req=json.loads((task/'request.json').read_text());inputs.append(redacted(req))
        science=task/'science'
        result=json.loads((science/'result.json').read_text()) if (science/'result.json').exists() else None
        if result:
            for n,h in result['artifacts'].items():
                if sha(science/n)!=h:raise RuntimeError('原タスクのSHAが変化しています。')
        else:
            failures.append(dict(task=task.name,error=json.loads((science/'failure.json').read_text()),
                            execution=json.loads((task/'execution.json').read_text())))
            (public/(task.name+'-failure.txt')).write_text((science/'failure.txt').read_text().replace(str(project),'<PROJECT>'))
        if req['kind']=='ai' and req['operation']=='train' and result:
            saved=torch.load(science/'checkpoint.pt',map_location='cpu',weights_only=True)
            if tensor_digest(torch,saved['model_state_dict'])!=result['final_model_digest']:raise RuntimeError('保存モデル内容が不一致です。')
            if optimizer_digest(torch,saved['optimizer_state_dict'])!=result['final_optimizer_digest']:raise RuntimeError('保存optimizer内容が不一致です。')
            models.append(dict(task=task.name,result=result,optimizer_param_groups=saved['optimizer_state_dict']['param_groups'],
                saved_rng_digest=optimizer_digest(torch,saved['rng']),saved_checkpoint_verified=True,
                loss=json.loads((science/'loss.json').read_text()),exposure=json.loads((science/'exposure.json').read_text())))
        for p in task.rglob('*'):
            if p.is_file() and 'runtime-cache' not in p.parts:manifest[str(p.relative_to(root))]=sha(p)
    dump(public/'model-provenance.json',models);dump(public/'task-requests.json',inputs);dump(public/'failures.json',failures)
    dump(public/'raw-artifact-sha256.json',manifest)
    shutil.copy2(root/'tasks/decision-pool/science/indices.json',public/'data-indices.json')
    for p in art.glob('unit*.txt'):shutil.copy2(p,public/p.name)
    lock=(art/'requirements.lock.txt').read_text()
    lock='\n'.join('mdlearn==0.0.10a1 # 固定vendor 938cb80' if line.startswith('mdlearn @') else line for line in lock.splitlines())+'\n'
    (public/'requirements.lock.txt').write_text(lock)
    versions={n:meta.version(n) for n in ['numpy','scipy','torch','openmm','MDAnalysis','scikit-learn','mdlearn','parsl']}
    import torch
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.total','--format=csv,noheader'],text=True).strip()
    cpu_model=next(v.split(':',1)[1].strip() for v in Path('/proc/cpuinfo').read_text().splitlines() if v.startswith('model name'))
    dump(public/'environment.json',dict(python=platform.python_version(),OS=platform.platform(),CPU_model=cpu_model,
        GPU_without_private_identifiers=gpu,versions=versions,torch_build_CUDA=torch.version.cuda,
        controller_CPU=[0],worker_CPU=[1,2],numeric_threads=2))
    original=json.loads((project/'artifacts/gq-r1-20261026/original-evidence-before.json').read_text());n=0
    for name,items in original.items():
        for rel,h in items.items():
            if sha(project/'runs'/name/rel)!=h:raise RuntimeError('S1/S2原証拠が変化しています。')
            n+=1
    gq=json.loads((ROOT/'docs/执行证据/2026-10-26-gq/raw-artifact-sha256.json').read_text()) if (ROOT/'docs/执行证据/2026-10-26-gq/raw-artifact-sha256.json').exists() else json.loads((project/'artifacts/gq-r2-20261026/r1-raw-sha256.json').read_text())
    for rel,h in gq.items():
        if sha(project/'runs/gq-r1-20261026'/rel)!=h:raise RuntimeError('GQ原証拠が変化しています。')
    r2=json.loads((project/'artifacts/gq-r2-20261026/cleanup-verification.json').read_text())
    for rel,h in r2['derived_array_sha256'].items():
        if sha(project/'artifacts/gq-r2-20261026'/rel)!=h:raise RuntimeError('R2原配列が変化しています。')
    if sha(project/'artifacts/gq-r2-evidence-20261026.tar.gz')!=r2['archive_sha256']:raise RuntimeError('R2アーカイブが変化しています。')
    dump(public/'legacy-preservation.json',dict(S1_S2_files=n,GQ_files=len(gq),R2_arrays=len(r2['derived_array_sha256']),R2_archive_unchanged=True,all_unchanged=True))
    sources={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'p1/server'/n for n in ['b1_science.py','b1_run.py','b1_analysis.py','b1_publish.py','gq_science.py','gq_r2.py','science.py','supplement_coverage.py','supplement_selection.py']]}
    dump(public/'executed-source-sha256.json',sources)
    dump(public/'public-sha256.json',{p.name:sha(p) for p in public.iterdir() if p.is_file()})
    print(json.dumps(json.loads((public/'validation.json').read_text()),indent=2))


if __name__=='__main__':publish()
