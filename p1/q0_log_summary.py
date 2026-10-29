"""Q0の保存ログ表を根ごとに記述し、原品質記録のSHAを追加照合する。"""
import csv,json,hashlib,statistics,resource,os,time,sys
from pathlib import Path
from q0_log_audit import digest,read,write,table
p=Path(sys.argv[1]);o=p/'artifacts/q0-20261029-v1/output';raw=p/'runs/b1-expansion-20261026'
assert os.environ['CUDA_VISIBLE_DEVICES']=='-1';os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10);resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
begin=time.monotonic();cpu=time.process_time();a=list(csv.DictReader((o/'model-loss-summary.csv').open()));md=list(csv.DictReader((o/'md-task-diagnostics.csv').open()));win=list(csv.DictReader((o/'md-window-diagnostics.csv').open()))
def summary(rows,columns):
 return {k:dict(mean=statistics.fmean(float(r[k]) for r in rows),minimum=min(float(r[k]) for r in rows),maximum=max(float(r[k]) for r in rows)) for k in columns}
modelgroups=[]
for arm in ['M0','F1','F2']:
 rr=[r for r in a if r['arm']==arm];modelgroups.append(dict(arm=arm,n=len(rr),last20_lower_than_first20=sum(float(r['last20_total_mean'])<float(r['first20_total_mean']) for r in rr),values=summary(rr,['train_BCE_per_frame','validation_BCE_per_frame','train_KL_batchmean_mean','validation_KL_batchmean_mean','first20_total_mean','last20_total_mean','maximum_step_total'])))
rootrows=[]
for root in ['r%02d'%i for i in range(1,9)]:
 for kind in ['history','downstream']:
  rr=[r for r in md if r['root_id']==root and r['kind']==kind]
  q=dict(root_id=root,kind=kind,n=len(rr))
  for k,v in summary(rr,['temperature_K_mean','potential_kJ_mol_mean']).items():
   for stat,value in v.items():q[k+'_'+stat]=value
  for lo in [0,100,200,500]:
   ss=[r for r in win if r['root_id']==root and r['kind']==kind and float(r['local_start_ps'])==lo]
   q['temperature_K_window_'+str(lo)]=statistics.fmean(float(r['temperature_K_mean']) for r in ss)
   q['potential_kJ_mol_window_'+str(lo)]=statistics.fmean(float(r['potential_kJ_mol_mean']) for r in ss)
  rootrows.append(q)
table(o/'md-root-diagnostics.csv',rootrows)
expected=read(p/'artifacts/q0-20261029-v1/bundle/raw-artifact-sha256.json');checks=[]
q=p/'artifacts/b1-expansion-20261026/summary-v1/quality.json';qbundle=p/'artifacts/q0-20261029-v1/bundle/quality.json'
assert digest(q)==digest(qbundle)
for r in read(q):
 tid=r['branch']['branch_id']+'-analysis'
 for name in ['quality.json','result.json']:
  f=raw/'tasks'/tid/'science'/name
  if not f.exists():continue
  rel=str(f.relative_to(raw));h=digest(f);assert h==expected[rel];checks.append(dict(path=rel,sha256=h))
assert len(checks)>=240
history_quality=[]
for root in ['r%02d'%i for i in range(1,9)]:
 for h in range(1,5):
  tid=root+'-h'+str(h)+'-md-prep'
  for name in ['quality.json','result.json']:
   f=raw/'tasks'/tid/'science'/name;rel=str(f.relative_to(raw));assert digest(f)==expected[rel];checks.append(dict(path=rel,sha256=digest(f)))
  r=read(raw/'tasks'/tid/'science/result.json');history_quality.append(dict(task_id=tid,frames=r['frames'],valid=r['valid'],reasons=json.dumps(r['reasons'])))
table(o/'history-existing-quality.csv',history_quality)
exposure_rows=[]
for r in a:
 f=raw/'tasks'/r['task_id']/'science/exposure.json';assert digest(f)==expected[str(f.relative_to(raw))];e=read(f)
 for i,(frame,pos) in enumerate(zip(e['frame_ids_0based'],e['permutation_positions'])):exposure_rows.append(dict(task_id=r['task_id'],exposure_0based=i,frame_id_0based=frame,permutation_position=pos))
table(o/'model-exposures.csv',exposure_rows)
assert all(sum(int(w['rows']) for w in win if w['task_id']==r['task_id'])==int(r['rows']) for r in md)

manifest=p/'artifacts/b1-expansion-20261026/archives/archive-manifest.json'
archives=[dict(name=n,exists=(manifest.parent/n).is_file(),bytes=(manifest.parent/n).stat().st_size,manifest_bytes=v['bytes'],prior_sha256=v['sha256'],SHA_rehashed_this_task=False) for n,v in read(manifest).items()]
assert len(archives)==9 and all(r['exists'] and r['bytes']==r['manifest_bytes'] for r in archives)
prep=[]
for f in [p/'source/inputs/p1-fsd-ey/1FME-unfolded.pdb',p/'inputs/p1-fsd-ey/1FME-unfolded.pdb']:
 if not f.exists():continue
 lines=[l for l in f.read_text().splitlines() if l.startswith(('ATOM  ','HETATM'))];res={l[21:27]:l[17:20].strip() for l in lines};hyd=sum(l[76:78].strip()=='H' for l in lines)
 prep.append(dict(logical_path='inputs/p1-fsd-ey/1FME-unfolded.pdb',sha256=digest(f),atoms=len(lines),residues=len(res),hydrogens=hyd,waters=sum(v in ['HOH','WAT'] for v in res.values()),terminal_atom_names=[l[12:16].strip() for l in lines if l[12:16].strip() in ['H1','H2','H3','OXT']],pH='UNVERIFIED',preparation_command='UNVERIFIED'))
write(o/'preparation-inventory.json',prep)
write(o/'supplemental-input-audit.json',dict(quality_summary_sha256=digest(q),quality_public_copy_matches=True,quality_raw_records=checks,archives=archives,raw_modified=False))
write(o/'descriptive-summary.json',dict(models=modelgroups,MD_tasks=len(md),MD_report_rows=sum(int(r['rows']) for r in md),all_log_numeric_finite=True,history_task_temperature_mean_range=[min(float(r['temperature_K_mean']) for r in md if r['kind']=='history'),max(float(r['temperature_K_mean']) for r in md if r['kind']=='history')],downstream_task_temperature_mean_range=[min(float(r['temperature_K_mean']) for r in md if r['kind']=='downstream'),max(float(r['temperature_K_mean']) for r in md if r['kind']=='downstream')],root_records=rootrows,statistical_tests=False))
write(o/'supplemental-costs.json',dict(wall_s=time.monotonic()-begin,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,code_sha256=digest(Path(__file__)),CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES']))
write(o/'output-sha256.json',{f.name:digest(f) for f in o.iterdir() if f.is_file() and f.name!='output-sha256.json'})
print('Q0追加照合と根別記述完了')
