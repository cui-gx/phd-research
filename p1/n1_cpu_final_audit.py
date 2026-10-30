"""N1保存済み派生結果・転送・原archiveの最終読取り監査。"""
import sys,json,csv,time,resource,importlib.metadata
from pathlib import Path
from n1_cpu_evaluate import sha,dump
p=Path(sys.argv[1]);a=p/'artifacts/n1-cpu-20261030-v1';o=a/'output';s=o/'summary';start=time.monotonic();cpu=time.process_time()
receipts=[json.loads(f.read_text()) for f in o.glob('units/*/receipt.json')];assert len(receipts)==272
units=[]
for r in receipts:
 d=o/'units'/r['task_id'];assert all(sha(d/n)==h for n,h in r['outputs'].items());units.append(dict(task_id=r['task_id'],frames=r['frames'],qualified=r['qualified']))
archives=p/'artifacts/b1-expansion-20261026/archives';am=json.loads((archives/'archive-manifest.json').read_text());ar=[dict(name=n,exists=(archives/n).is_file(),size_match=(archives/n).stat().st_size==v['bytes'],expected_SHA256=v['sha256'],SHA_rehashed=False) for n,v in am.items()];assert len(ar)==9 and all(x['exists'] and x['size_match'] for x in ar)
pr=list(csv.DictReader((s/'history-progress.csv').open()));facts={}
for arm in ['F0','F1','F2']:
 v=[r for r in pr if r['arm']==arm];facts[arm]=dict(branches=len(v),history_improving_branches=sum(float(r['new_best_gain_A'])>0 for r in v),mean_gain_A=sum(float(r['new_best_gain_A']) for r in v)/len(v),minimum_branch_RMSD_A=min(float(r['downstream_min_RMSD_A']) for r in v),maximum_branch_RMSD_A=max(float(r['downstream_min_RMSD_A']) for r in v))
dump(s/'descriptive-facts.json',facts)
dump(s/'final-server-audit.json',dict(status='PASS',units=units,frames=sum(r['frames'] for r in receipts),qualified=sum(r['qualified'] for r in receipts),archive=ar,code_SHA256={f.name:sha(f) for f in (a/'code').glob('*.py')},bundle_SHA256={f.name:sha(f) for f in (a/'bundle').iterdir() if f.is_file()},versions={n:importlib.metadata.version(n) for n in ['MDAnalysis','numpy','scipy','matplotlib']},wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,new_MD_training_inference_LOF=0,MAC_RAW_BACKUP='WAIVED_BY_RESEARCHER'))
dump(s/'final-transfer-sha256.json',{f.name:sha(f) for f in s.iterdir() if f.is_file()})
print(json.dumps(facts))
