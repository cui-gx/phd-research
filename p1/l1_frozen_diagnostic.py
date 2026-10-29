"""既存CVAEを変更せず、固定IDでCPUの前向診断だけを行う。"""
import os,sys,time,json,csv,hashlib,resource,argparse,fcntl,math
from pathlib import Path

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def table(p,rows):
 if not rows:return
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,list(dict.fromkeys(k for r in rows for k in r)),lineterminator='\n');w.writeheader();w.writerows(rows)
def tensor_digest(state):
 h=hashlib.sha256()
 for k,v in sorted(state.items()):h.update(k.encode());h.update(v.detach().cpu().numpy().tobytes())
 return h.hexdigest()
def opt_digest(torch,value):
 h=hashlib.sha256()
 def visit(v):
  if isinstance(v,dict):
   h.update(b'dict')
   for k in sorted(v,key=lambda x:str(x)):visit(str(k));visit(v[k])
  elif isinstance(v,(list,tuple)):
   h.update(b'sequence');h.update(str(len(v)).encode())
   for x in v:visit(x)
  elif isinstance(v,torch.Tensor):
   h.update(b'tensor');h.update(str(v.dtype).encode());h.update(str(tuple(v.shape)).encode());h.update(v.detach().cpu().numpy().tobytes())
  else:h.update(repr(v).encode())
 visit(value);return h.hexdigest()
def main(a):
 begin=time.monotonic();cpu=time.process_time();project=a.project.resolve();out=a.output.resolve();raw=project/'runs/b1-expansion-20261026'
 assert os.environ['CUDA_VISIBLE_DEVICES']=='-1' and all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
 assert project.stat().st_uid==os.getuid() and project in out.parents
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
 out.mkdir(exist_ok=a.mode!='freeze');pub=out/'public';pub.mkdir(exist_ok=True)
 lock=(out/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prior=read(out/'cost-ledger.json') if (out/'cost-ledger.json').exists() else []
 def guard():
  if sum(r['wall_s'] for r in prior)+time.monotonic()-begin>=7200:raise RuntimeError('2時間資源復核点')
  rss=int(Path('/proc/self/status').read_text().split('VmRSS:')[1].split()[0])*1024
  if rss>2*1024**3:raise RuntimeError('RSS2GiB超過')
  if sum(p.stat().st_size for p in out.rglob('*') if p.is_file())>1024**3:raise RuntimeError('出力1GiB超過')
 expected=read(a.bundle/'raw-artifact-sha256.json');models=read(a.bundle/'models.json');audit={}
 def check(p):
  guard();rel=str(p.relative_to(raw));h=sha(p)
  if h!=expected[rel]:raise RuntimeError('原SHA不一致:'+rel)
  audit[rel]=h;return p
 import numpy as np
 if a.mode=='freeze':
  ids=[];states={}
  for state in sorted({r['state_id'] for r in models}):
   pool=raw/'tasks'/(state+'-decision-pool')/'science';sets=read(check(pool/'indices.json'));check(pool/'contacts.npy');f=np.load(check(pool/'features.npz'));b=(int(state[-1])-2)*1000
   eligible=np.flatnonzero(f['valid']&(f['time_ps']>b+1700)&(f['time_ps']<=b+2000+1e-5))
   assert len(eligible)>=200;recent=eligible[np.linspace(0,len(eligible)-1,200,dtype=int)].tolist();old=sets['validation'];assert len(old)==len(set(old))==200
   for group,sel in [('OLD_VALIDATION',old),('RECENT_HELDOUT',recent)]:
    assert len(set(sel))==200 and not (set(sel)&(set(sets['F1'])|set(sets['F2'])))
    for i in sel:ids.append(dict(state_id=state,set=group,frame_id_0based=i,time_ps=float(f['time_ps'][i]),M0_temporal_status='POST_HOC_GENERALIZATION' if group=='RECENT_HELDOUT' else 'AVAILABLE_AT_M0',all_training_ID_disjoint=True))
   states[state]=dict(OLD_VALIDATION=old,RECENT_HELDOUT=recent)
  for r in models:
   t=raw/'tasks'/(r['state_id']+'-'+r['label'])/'science'
   for n in ['checkpoint.pt','recipe.json','exposure.json','result.json']:check(t/n)
   assert sha(t/'checkpoint.pt')==r['checkpoint_sha256']
  table(pub/'validation-ids.csv',ids);write(pub/'frozen-cohorts.json',states);write(pub/'freeze-input-sha256.json',audit)
  write(pub/'freeze-status.json',dict(status='READY',models=80,states=16,ID_rows=len(ids),cohort_sha256=sha(pub/'frozen-cohorts.json'),model_loads=0))
 else:
  import torch
  from scipy.spatial.distance import cdist
  from scipy.stats import spearmanr
  from mdlearn.nn.models.vae.symmetric_conv2d_vae import SymmetricConv2dVAE
  torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.manual_seed(2026102901);torch.use_deterministic_algorithms(True)
  def forbidden(*args,**kwargs):raise RuntimeError('L1では逆伝播/optimizer.stepは禁止')
  torch.Tensor.backward=forbidden;torch.autograd.backward=forbidden;torch.optim.RMSprop.step=forbidden
  freeze=read(pub/'freeze-status.json');assert freeze['cohort_sha256']==sha(pub/'frozen-cohorts.json')
  for rel,h in read(pub/'freeze-input-sha256.json').items():assert sha(raw/rel)==h
  cohorts=read(pub/'frozen-cohorts.json');maskij=np.indices((28,28));gap=maskij[1]-maskij[0]
  masks={'ALL':np.ones((28,28),bool),'NONLOCAL':gap>=3,'LONG':gap>=4};assert [m.sum() for m in masks.values()]==[784,325,300]
  def dense(x,ids):
   z=np.zeros((len(ids),1,28,28),np.float32)
   for n,i in enumerate(ids):ii=x[i].reshape(2,-1);z[n,0,ii[0],ii[1]]=1
   return torch.from_numpy(z)
  def bce(y,p):return torch.nn.functional.binary_cross_entropy(p.expand_as(y),y,reduction='none').numpy()[:,0]
  def dist(z):return cdist(z,z)
  def ranks(d):
   d=d.copy();np.fill_diagonal(d,np.inf);return np.argsort(d,axis=1,kind='stable')[:,:10]
  def overlap(x,y):return float(np.mean([len(set(a)&set(b))/10 for a,b in zip(x,y)]))
  def corr(x,y):
   v=float(spearmanr(x,y).statistic);return v if math.isfinite(v) else None
  metric=[];latent=[];frames=[];stable=[];integrity=[]
  arr=out/'arrays';arr.mkdir(exist_ok=True)
  for state,groups in cohorts.items():
   pool=raw/'tasks'/(state+'-decision-pool')/'science';x=np.load(check(pool/'contacts.npy'),allow_pickle=True);sets=read(check(pool/'indices.json'));features=np.load(check(pool/'features.npz'))
   oldfreq=(dense(x,sets['old']).sum(0,keepdim=True)+.5)/801
   cache={}
   for r in [r for r in models if r['state_id']==state]:
    tid=state+'-'+r['label'];t=raw/'tasks'/tid/'science';checkpoint=check(t/'checkpoint.pt');saved=torch.load(checkpoint,map_location='cpu',weights_only=True)
    assert tensor_digest(saved['model_state_dict'])==r['final_model_digest'];assert opt_digest(torch,saved['optimizer_state_dict'])==r['final_optimizer_digest'];assert saved['optimizer_steps_this_task']==200
    assert all(bool(torch.isfinite(v).all()) for v in saved['model_state_dict'].values())
    recipe=read(check(t/'recipe.json'))['cvae'];kwargs={k:recipe[k] for k in ['input_shape','filters','kernels','strides','affine_widths','affine_dropouts','latent_dim']}
    model=SymmetricConv2dVAE(**kwargs);model.load_state_dict(saved['model_state_dict'],strict=True);model.eval();model.requires_grad_(False)
    trainids=read(check(t/'exposure.json'))['frame_ids_0based'];freq=(dense(x,trainids).sum(0,keepdim=True)+.5)/801
    for label,ids in groups.items():
     assert not set(ids)&set(trainids);y=dense(x,ids);zs=[];ls=[];pred=[];zerop=[]
     with torch.no_grad():
      for start in range(0,len(ids),32):
       guard();v=y[start:start+32];mu,recon=model(v);logstd=model.__logstd__.clone();m2,p2=model(v)
       assert torch.equal(mu,m2) and torch.equal(recon,p2);assert not mu.requires_grad and not recon.requires_grad
       zs.append(mu.clone());ls.append(logstd);pred.append(recon);zerop.append(model.decode(torch.zeros_like(mu)))
     z=torch.cat(zs);l=torch.cat(ls);pr=torch.cat(pred);zp=torch.cat(zerop)
     assert all(bool(torch.isfinite(v).all()) for v in [z,l,pr,zp]);variance=(2*l).exp();kl=.5*(z*z+variance-1-2*l)
     loo=(y.sum(0,keepdim=True)-y+.5)/200
     errors={'MODEL':bce(y,pr),'OLD_FREQUENCY':bce(y,oldfreq),'TRAIN_FREQUENCY':bce(y,freq),'VALIDATION_LOO':bce(y,loo),'ZERO_LATENT':bce(y,zp)}
     xyz=features['distances_A'][ids];physical=dist(xyz)/math.sqrt(325);timeD=np.abs(features['time_ps'][ids,None]-features['time_ps'][None,ids]);inputD=dist(y.numpy()[:,0][:,masks['NONLOCAL']]);tri=np.triu_indices(200,1);pk=ranks(physical)
     scales={'RAW':z.numpy(),'STANDARDIZED':(z.numpy()-z.numpy().mean(0))/np.where(z.numpy().std(0)>0,z.numpy().std(0),1)}
     for scale,v in scales.items():
      d=dist(v);latent.append(dict(state_id=state,model=r['label'],set=label,scale=scale,physical_pair_spearman=corr(d[tri],physical[tri]),physical_knn_overlap=overlap(ranks(d),pk),time_physical_knn_overlap=overlap(ranks(timeD),pk),contact_physical_knn_overlap=overlap(ranks(inputD),pk)))
     cache[(r['label'],label)]=dist(z.numpy())
     for name,mask in masks.items():
      row=dict(state_id=state,root_id=state[:3],model=r['label'],arm='F0' if r['label']=='M0' else r['arm'],set=label,mask=name,elements=int(mask.sum()),frames=200,KL_per_frame=float(kl.sum(1).mean()))
      for method,e in errors.items():row[method+'_BCE_per_frame']=float(e[:,mask].sum(1).mean());row[method+'_BCE_per_element']=float(e[:,mask].mean())
      metric.append(row)
     for j in range(3):latent.append(dict(state_id=state,model=r['label'],set=label,scale='DIMENSION',dimension=j,mu_mean=float(z[:,j].mean()),mu_population_variance=float(z[:,j].var(unbiased=False)),posterior_variance_mean=float(variance[:,j].mean()),KL_dimension_mean=float(kl[:,j].mean())))
     eigen=np.linalg.eigvalsh(np.cov(z.numpy(),rowvar=False,bias=True));write(arr/(tid+'-'+label+'-cov.json'),dict(eigenvalues=eigen.tolist()))
     np.savez_compressed(arr/(tid+'-'+label+'.npz'),frame_ids=ids,mu=z.numpy(),logstd=l.numpy(),reconstruction=pr.numpy())
     for i,ident in enumerate(ids):
      row=dict(state_id=state,model=r['label'],set=label,frame_id_0based=ident,KL=float(kl[i].sum()),mu0=float(z[i,0]),mu1=float(z[i,1]),mu2=float(z[i,2]))
      for name,mask in masks.items():row[name+'_BCE']=float(errors['MODEL'][i,mask].sum())
      frames.append(row)
    assert tensor_digest(model.state_dict())==r['final_model_digest'];assert sha(checkpoint)==r['checkpoint_sha256']
    integrity.append(dict(task_id=tid,checkpoint_sha256=r['checkpoint_sha256'],model_digest_matches=True,optimizer_digest_matches=True,finite=True,repeat_forward_bitwise_equal=True,post_model_unchanged=True))
    write(pub/'progress.json',dict(models_complete=len(integrity),expected=80))
    del model,saved;guard()
   for group in groups:
    for arm in ['F1','F2']:
     a1=cache[(arm+'-t1',group)];a2=cache[(arm+'-t2',group)];stable.append(dict(state_id=state,arm=arm,set=group,seed_distance_spearman=corr(a1[tri],a2[tri]),seed_knn_overlap=overlap(ranks(a1),ranks(a2))))
  assert len(integrity)==80 and len(metric)==480 and len(frames)==32000
  table(pub/'model-metrics.csv',metric);table(pub/'latent-diagnostics.csv',latent);table(pub/'frame-diagnostics.csv',frames);table(pub/'seed-stability.csv',stable);table(pub/'checkpoint-audit.csv',integrity)
  state_rows=[]
  for state in cohorts:
   for group in ['OLD_VALIDATION','RECENT_HELDOUT']:
    for arm in ['F0','F1','F2']:
     for mask in masks:
      rr=[r for r in metric if r['state_id']==state and r['set']==group and r['arm']==arm and r['mask']==mask];row=dict(state_id=state,arm=arm,set=group,mask=mask,models=len(rr))
      for k in ['MODEL_BCE_per_frame','OLD_FREQUENCY_BCE_per_frame','TRAIN_FREQUENCY_BCE_per_frame','VALIDATION_LOO_BCE_per_frame','ZERO_LATENT_BCE_per_frame','KL_per_frame']:row[k]=float(np.mean([r[k] for r in rr]))
      state_rows.append(row)
  table(pub/'state-metrics.csv',state_rows)
  for rel,h in read(pub/'freeze-input-sha256.json').items():assert sha(raw/rel)==h
  write(pub/'execution-status.json',dict(status='COMPLETE',models=80,model_sets=160,metric_rows=480,frame_rows=32000,new_train_MD_LOF=0,optimizer_steps=0,raw_unmodified=True,determinism='PASS_same_CPU_same_batch',torch=torch.__version__,numpy=np.__version__,new_scientific_qualification='PENDING'))
  write(pub/'array-sha256.json',{str(p.relative_to(out)):sha(p) for p in arr.iterdir()})
 cost=dict(mode=a.mode,wall_s=time.monotonic()-begin,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,code_sha256=sha(Path(__file__)),affinity_count=1,CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'])
 prior.append(cost);write(out/'cost-ledger.json',prior);write(pub/'cost-ledger.json',prior);write(pub/'output-sha256.json',{p.name:sha(p) for p in pub.iterdir() if p.is_file() and p.name!='output-sha256.json'})
 print(json.dumps(cost))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','evaluate']);p.add_argument('project',type=Path);p.add_argument('output',type=Path);p.add_argument('bundle',type=Path);a=p.parse_args()
 try:main(a)
 except Exception as e:
  if (a.output/'public').exists():write(a.output/'public/failure.json',dict(type=type(e).__name__,message=str(e),status='STOPPED'))
  raise
