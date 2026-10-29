"""L1の凍結診断結果を記述表と図へまとめる。モデルは実行しない。"""
import sys,os,time,resource,csv,json,statistics
from pathlib import Path
from l1_frozen_diagnostic import read,write,table,sha
begin=time.monotonic();cpu=time.process_time();project=Path(sys.argv[1]);out=project/'artifacts/l1-20261029-v1/output';p=out/'public'
assert os.environ['CUDA_VISIBLE_DEVICES']=='-1';os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
r=list(csv.DictReader((p/'model-metrics.csv').open()));lat=list(csv.DictReader((p/'latent-diagnostics.csv').open()));seed=list(csv.DictReader((p/'seed-stability.csv').open()));groups=[]
for group in ['OLD_VALIDATION','RECENT_HELDOUT']:
 for mask in ['ALL','NONLOCAL','LONG']:
  for arm in ['F0','F1','F2']:
   a=[x for x in r if x['set']==group and x['mask']==mask and x['arm']==arm];z=dict(set=group,mask=mask,arm=arm,models=len(a))
   for key in ['MODEL_BCE_per_frame','OLD_FREQUENCY_BCE_per_frame','TRAIN_FREQUENCY_BCE_per_frame','VALIDATION_LOO_BCE_per_frame','ZERO_LATENT_BCE_per_frame','KL_per_frame']:
    v=[float(x[key]) for x in a];z[key+'_mean']=statistics.fmean(v);z[key+'_min']=min(v);z[key+'_max']=max(v)
   z['better_than_old_frequency']=sum(float(x['MODEL_BCE_per_frame'])<float(x['OLD_FREQUENCY_BCE_per_frame']) for x in a);z['better_than_training_frequency']=sum(float(x['MODEL_BCE_per_frame'])<float(x['TRAIN_FREQUENCY_BCE_per_frame']) for x in a);z['better_than_LOO']=sum(float(x['MODEL_BCE_per_frame'])<float(x['VALIDATION_LOO_BCE_per_frame']) for x in a);groups.append(z)
table(p/'overview.csv',groups)
geo=[]
for group in ['OLD_VALIDATION','RECENT_HELDOUT']:
 for scale in ['RAW','STANDARDIZED']:
  for arm in ['F0','F1','F2']:
   a=[x for x in lat if x['set']==group and x['scale']==scale and ('F0' if x['model']=='M0' else x['model'][:2])==arm];z=dict(set=group,scale=scale,arm=arm,models=len(a))
   for key in ['physical_pair_spearman','physical_knn_overlap','time_physical_knn_overlap','contact_physical_knn_overlap']:
    v=[float(x[key]) for x in a if x[key]];z[key+'_mean']=statistics.fmean(v) if v else None;z[key+'_min']=min(v) if v else None;z[key+'_max']=max(v) if v else None
   geo.append(z)
table(p/'geometry-overview.csv',geo)
case=[x for x in r if x['state_id']=='r07-s4' and x['mask']=='NONLOCAL'];table(p/'r07-s4-case.csv',case)
eigen=[]
for f in (out/'arrays').glob('*-cov.json'):eigen.append(dict(model_set=f.stem.removesuffix('-cov'),**{'eigenvalue'+str(i):v for i,v in enumerate(read(f)['eigenvalues'])}))
table(p/'covariance-eigenvalues.csv',eigen)
write(p/'summary.json',dict(reconstruction=groups,geometry=geo,seed_stability=seed,case=case,limitations=['exploratory conditional diagnosis','same-root correlated frames','no collapse threshold','zero-code ablation is not a mean-code ablation','no scientific exploration evaluation']))
os.environ['MPLCONFIGDIR']=str(out/'mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(10,4))
for ax,group in zip(axes,['OLD_VALIDATION','RECENT_HELDOUT']):
 for arm,m in [('F0','o'),('F1','s'),('F2','^')]:
  a=[x for x in r if x['set']==group and x['mask']=='NONLOCAL' and x['arm']==arm];ax.scatter([float(x['OLD_FREQUENCY_BCE_per_frame']) for x in a],[float(x['MODEL_BCE_per_frame']) for x in a],marker=m,s=18,label=arm,alpha=.6)
 lim=ax.get_xlim();ylim=ax.get_ylim();lo=min(lim[0],ylim[0]);hi=max(lim[1],ylim[1]);ax.plot([lo,hi],[lo,hi],color='0.4',ls='--');ax.set_title(group);ax.set_xlabel('Old-frequency BCE / frame (325 pairs)');ax.set_ylabel('CVAE BCE / frame (325 pairs)');ax.legend();ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(p/'reconstruction-baseline.png',dpi=170);plt.close(fig)
prior=read(out/'cost-ledger.json');prior.append(dict(mode='summary_and_figures',wall_s=time.monotonic()-begin,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,code_sha256=sha(Path(__file__))))
write(out/'cost-ledger.json',prior);write(p/'cost-ledger.json',prior)
write(p/'output-sha256.json',{f.name:sha(f) for f in p.iterdir() if f.is_file() and f.name!='output-sha256.json'})
print(json.dumps({'NONLOCAL':[x for x in groups if x['mask']=='NONLOCAL'],'geometry':geo},ensure_ascii=False))
