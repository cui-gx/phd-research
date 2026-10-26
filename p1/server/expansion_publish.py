"""B1拡張の小規模証拠公開と根別バックアップ。科学結果を再計算しない。"""
from __future__ import annotations
import json
import re
import shutil
import tarfile
import time
from pathlib import Path
from .gq_r2 import dump,sha


def sanitized(value,project):
    """公開物から不要な個人パスとGPU識別子を除く。"""
    if isinstance(value,str):return re.sub(r'GPU-[0-9a-fA-F-]{36}','GPU_REDACTED',value.replace(str(project),'<PROJECT>'))
    if isinstance(value,list):return [sanitized(v,project) for v in value]
    if isinstance(value,dict):return {sanitized(str(k),project):sanitized(v,project) for k,v in value.items()}
    return value


def publish(run,art,matrix):
    """解析済みの表とSHAだけを公開用領域へ複写する。"""
    begin=time.perf_counter();cpu=time.process_time();out=art/'public-v1';out.mkdir(exist_ok=False);source=art/'summary-v1'
    for p in source.iterdir():
        if p.suffix in ('.csv','.png'):shutil.copy2(p,out/p.name)
        elif p.suffix=='.json':dump(out/p.name,sanitized(json.loads(p.read_text()),run.parent.parent))
    for name in ['preflight.json','preflight-final.json','preflight-final-02.json','requirements.lock.txt','unit-b1.txt','unit-b1-full-matrix.txt','unit-b1-final.txt','unit-r2.txt','finalization-runtime.json']:
        p=art/name
        if p.exists():
            if p.suffix=='.json':dump(out/name,sanitized(json.loads(p.read_text()),run.parent.parent))
            else:(out/name).write_text(sanitized(p.read_text(),run.parent.parent))
    tasks=[]
    for folder in sorted((run/'tasks').iterdir()):
        request=folder/'request.json';result=folder/'science/result.json'
        tasks.append(dict(task_id=folder.name,raw_request_sha256=sha(request),request=sanitized(json.loads(request.read_text()),run.parent.parent),
            raw_result_sha256=sha(result) if result.exists() else None,status='success' if result.exists() else 'failure_or_unfinished'))
    dump(out/'task-manifest.json',tasks)
    events=[json.loads(line) for line in (run/'events.jsonl').read_text().splitlines()]
    dump(out/'events.json',events)
    env=json.loads((run/'environment-private.json').read_text())
    dump(out/'environment.json',dict(python=env['python'],packages=env['packages'],GPU_inventory=sanitized(env['gpu_inventory']['stdout'],run.parent.parent),CPU_quota=[0,1,2],numeric_threads=2,supervision_interval_target_s=1.,private_identifiers_removed=True))
    import torch
    from .supplement_selection import tensor_digest,optimizer_digest
    attempts=json.loads((run/'attempt-map.json').read_text()) if (run/'attempt-map.json').exists() else {}
    groups=[]
    for state in matrix['states']:
        sid=state['state_id']
        for label in ['M0','F1-t1','F1-t2','F2-t1','F2-t2']:
            logical=sid+'-'+label;p=run/'tasks'/attempts.get(logical,logical)/'science/checkpoint.pt'
            if not p.exists():continue
            saved=torch.load(p,map_location='cpu',weights_only=True)
            if tensor_digest(torch,saved['model_state_dict'])!=saved['model_digest'] or optimizer_digest(torch,saved['optimizer_state_dict'])!=saved['optimizer_digest']:raise ValueError('保存checkpointの内容digestが一致しません。')
            groups.append(dict(state_id=sid,label=label,checkpoint_sha256=sha(p),model_digest=saved['model_digest'],optimizer_digest=saved['optimizer_digest'],
                optimizer_param_groups=[{k:v for k,v in g.items() if k!='params'} for g in saved['optimizer_state_dict']['param_groups']],steps=saved['optimizer_steps_this_task']))
    dump(out/'checkpoint-readback.json',groups)
    dump(out/'executed-source-sha256.json',json.loads((run/'manifest.json').read_text())['source_sha256'])
    dump(out/'publication-runtime.json',dict(wall_s=time.perf_counter()-begin,CPU_s=time.process_time()-cpu,GPU_compute=False,checkpoint_readback_device='CPU'))
    dump(out/'public-sha256.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()})
    return out


def archive(run,art,matrix):
    """原データを削除せず、8根と共通メタデータを別々に圧縮する。"""
    begin=time.perf_counter();cpu=time.process_time();out=art/'archives';out.mkdir(exist_ok=True)
    manifest_path=out/'archive-manifest.json';manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    project=run.parent.parent
    def make(name,paths):
        target=out/(name+'.tar.gz')
        if target.name in manifest:
            if sha(target)!=manifest[target.name]['sha256']:raise ValueError('既存バックアップが変化しています。')
            return
        if target.exists():raise ValueError('未確認archiveを上書きできません。別attemptが必要です。')
        if shutil.disk_usage(out).free<100*1024**3:raise RuntimeError('バックアップ用空き容量が不足しています。')
        with tarfile.open(target,'x:gz',compresslevel=1) as f:
            for p in paths:f.add(p,arcname=str(p.relative_to(project)),filter=lambda item:None if Path(item.name).name.startswith('._') else item)
        manifest[target.name]=dict(sha256=sha(target),bytes=target.stat().st_size,roots=[name] if name.startswith('r') else [],state='server_archive_verified_local_copy_pending')
        dump(manifest_path,manifest)
    for root in matrix['roots']:
        rid=root['root_id'];paths=sorted(p for p in (run/'tasks').iterdir() if p.name.startswith(rid+'-'))
        paths += sorted((run/'states').glob(rid+'-*.json'))
        make(rid,paths)
    paths=[p for p in run.iterdir() if p.is_file() and p.name not in ('run.lock','status.json')]
    paths += [p for p in art.iterdir() if p.name not in ('archives','pip-cache','mpl-cache','mdlearn-build') and not p.name.endswith('.whl')]
    make('metadata',paths)
    dump(art/'archive-runtime.json',dict(wall_s=time.perf_counter()-begin,CPU_s=time.process_time()-cpu,GPU_compute=False,local_backup_verified=False))
    return manifest
