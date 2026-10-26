"""サーバ側で小規模公開証拠と要約を作る。科学実験の追加は行わない。"""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import time
import numpy as np
from .gq_r2 import dump, sha, table, nearest, descriptors


def publish(project):
    art=project/'artifacts/gq-r2-20261026';out=art/'analysis-v2'
    public=art/'public';public.mkdir(exist_ok=False)
    for p in out.iterdir():
        if p.suffix in ('.json','.csv','.png'):
            shutil.copy2(p,public/p.name)
    for p in art.iterdir():
        if p.suffix in ('.json','.txt') and p.name!='r1-raw-sha256.json':
            shutil.copy2(p,public/p.name)
    raw=project/'runs/gq-r1-20261026'
    expected=json.loads((art/'r1-raw-sha256.json').read_text())
    comparisons=[dict(artifact=p,sha256=d,unchanged=(sha(raw/p)==d)) for p,d in expected.items()]
    if not all(x['unchanged'] for x in comparisons):
        raise RuntimeError('R1の原資料が変化しています。')
    dump(public/'r1-preservation.json',dict(files=len(comparisons),all_unchanged=True,artifacts=comparisons))
    inputs=json.loads((out/'input-verification.json').read_text())
    for row in inputs['files']:
        if row['artifact'].startswith('R1-derived/'):
            p=project/'artifacts/gq-r1-20261026/analysis-final-v2'/Path(row['artifact']).name
            if sha(p)!=row['sha256']:raise RuntimeError('R1特徴量が変化しています。')
    primary=json.loads((out/'primary-regions.json').read_text())
    library=json.loads((out/'fixed-library.json').read_text())
    sensitivity=list(csv.DictReader((out/'sensitivity.csv').open()))
    order=list(csv.DictReader((out/'order-sensitivity.csv').open()))
    roots={s:dict(np.load(out/f'root-{s}.npz')) for s in (11,12,13,14)}
    summary=[];blocks=[];bench=[]
    for seed,a in roots.items():
        r=dict(seed=seed,qualified_frames=int(a['valid'].sum()),temperature_K=[float(v) for v in np.quantile(a['state'][:,-1],[0,.5,1])],
               temperature_mean_K=float(a['state'][:,-1].mean()))
        r['primary_by_epsilon']=[dict(epsilon_A=v['epsilon_A'],added_regions=v['added_regions'],
                angles_between_representatives_deg=v['angles_between_representatives_deg'],
                increments_by_ns=v['increments_by_ns']) for v in primary if v['seed']==seed]
        r['fixed_library']=[v for v in library if v['seed']==seed]
        r['epsilon2_tau5_sensitivity']=[v for v in sensitivity if int(v['seed'])==seed and float(v['epsilon_A'])==2 and float(v['tau_ps'])==5]
        r['epsilon2_order']=[v for v in order if int(v['seed'])==seed and float(v['epsilon_A'])==2]
        summary.append(r)
        for start in range(0,8000,200):
            ii=slice(start,start+200)
            blocks.append(dict(seed=seed,start_ps=float(a['time_ps'][start]),Rg_mean_A=float(a['rg_A'][ii].mean()),
                         Q8_mean=float(a['q'][ii].mean()),potential_mean_kJ_mol=float(a['state'][ii,2].mean()),
                         temperature_mean_K=float(a['state'][ii,-1].mean())))
        hist=a['distances_A'][a['time_ps']<=1000]
        future=a['distances_A'][a['time_ps']>1000][::4]
        started=time.monotonic();near,_=nearest(future,hist)
        elapsed=time.monotonic()-started
        bench.append(dict(seed=seed,history_points=len(hist),query_points=len(future),wall_s=elapsed,
                          nearest_A=[float(v) for v in np.quantile(near,[0,.5,.95,1])],
                          meaning='履歴全点最近傍のCPU計測。B/Cの効果実験ではない。'))
    dump(public/'summary.json',summary);table(public/'physical-blocks.csv',blocks)
    dump(public/'history-distance-benchmark.json',bench)
    counts=[int(v['total_regions']) for v in sensitivity]
    executions=[json.loads(p.read_text()) for p in art.glob('*-execution.json')]
    storage=sum(p.stat().st_size for p in art.rglob('*') if p.is_file())
    runtime=project/'source/.runtime/gq-r2-20261026'
    env_storage=sum(p.stat().st_size for p in runtime.rglob('*') if p.is_file())
    code={}
    for p in [project/'source/p1/server/gq_r2.py',project/'source/p1/server/gq_r2_run.py',project/'source/p1/server/gq_r2_publish.py',
              project/'source/tests/p1/test_gq_r2.py',art/'quality-source.py',art/'calibration-v1-source.py']:
        code[p.name if p.parent==art else str(p.relative_to(project/'source'))]=sha(p)
    dump(public/'validation.json',dict(status='DERIVED',sensitivity_rows=len(sensitivity),expected_rows=1536,
         regions_min_max=[min(counts),max(counts)],all_raw_hashes_unchanged=True,
         source_sha256=code,scientific_strategy_comparisons=False,GPU_compute_seconds=0,
         execution_wall_s_including_failure=sum(e['wall_s'] for e in executions),
         max_sampled_peak_RSS_bytes=max(e['sampled_peak_process_tree_RSS_bytes'] for e in executions),
         artifact_storage_bytes=storage,environment_storage_bytes=env_storage,
         limits_met=storage+env_storage<5*1024**3,
         evidence_type='derived analysis / server CPU measurement',
         S2_independent_final_review='INCOMPLETE',S3='NOT APPROVED'))
    manifest={str(p.relative_to(public)):sha(p) for p in public.rglob('*') if p.is_file()}
    dump(public/'public-sha256.json',manifest)
    print(json.dumps(json.loads((public/'validation.json').read_text()),indent=2))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description='既存GQ-R2解析の公開証拠整理')
    p.add_argument('--project',type=Path,required=True)
    publish(p.parse_args().project)
