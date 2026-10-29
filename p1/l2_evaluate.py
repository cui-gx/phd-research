"""凍結L2 checkpoint一個を固定CPU条件で評価する。MDと訓練は禁止。"""
import argparse
import fcntl
import math
import os
from pathlib import Path
import resource
import time
from p1.l2_engineering import read, rows, sha, write, runtime


def evaluate(a):
    runtime()
    import numpy as np
    import torch
    from scipy.spatial.distance import cdist
    from scipy.stats import spearmanr
    from sklearn.neighbors import LocalOutlierFactor
    from mdlearn.nn.models.vae.symmetric_conv2d_vae import SymmetricConv2dVAE
    from p1.l1_frozen_diagnostic import tensor_digest, opt_digest, table
    assert not torch.cuda.is_available()
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    lock=(a.output/'cpu.run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cp=next(r for r in rows(a.plan/'checkpoint-matrix.csv') if r['checkpoint_id']==a.checkpoint)
    chain=next(r for r in rows(a.plan/'experiment-matrix.csv') if r['chain_id']==cp['chain_id'])
    path=a.output/'chains'/cp['chain_id']/(a.checkpoint+'.pt')
    manifest=read(path.parent/'result.json');expected=manifest['checkpoints'][path.name];assert sha(path)==expected
    dest=a.output/'evaluations'/a.checkpoint;dest.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();cpu=time.process_time();ledger=read(a.output/'cost-ledger.json')
    def guard():
        assert time.monotonic()-start<300,'単評価300秒復核点'
        assert sum(v['wall_s'] for v in ledger)+time.monotonic()-start<7200,'2時間復核点'
        rss=int(Path('/proc/self/status').read_text().split('VmRSS:')[1].split()[0])*1024
        assert rss<=2*1024**3,'RSS2GiB超過'
        assert sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file())<=2*1024**3,'出力2GiB超過'
    frozen=read(a.output/'engineering/input-freeze.json');raw=a.project/'runs/b1-expansion-20261026'
    pool=raw/'tasks'/(cp['state_id']+'-decision-pool')/'science'
    for name in ['contacts.npy','indices.json','features.npz']:
        assert sha(pool/name)==frozen['original_file_sha256'][str((pool/name).relative_to(raw))]
    contacts=np.load(pool/'contacts.npy',allow_pickle=True);sets=read(pool/'indices.json');features=np.load(pool/'features.npz')
    def dense(ids):
        x=np.zeros((len(ids),1,28,28),np.float32)
        for n,ident in enumerate(ids):
            ij=contacts[ident].reshape(2,-1);x[n,0,ij[0],ij[1]]=1
        return torch.from_numpy(x)
    saved=torch.load(path,map_location='cpu',weights_only=False)
    cfg=manifest['recipe'];model=SymmetricConv2dVAE(**{k:cfg[k] for k in ['input_shape','filters','kernels','strides','affine_widths','affine_dropouts','latent_dim']})
    model.load_state_dict(saved['model_state_dict'],strict=True);model.eval();model.requires_grad_(False)
    assert tensor_digest(model.state_dict())==saved['model_digest']
    assert opt_digest(torch,saved['optimizer_state_dict'])==saved['optimizer_digest']
    gap=np.indices((28,28));gap=gap[1]-gap[0];masks={'ALL':np.ones((28,28),bool),'NONLOCAL':gap>=3,'LONG':gap>=4}
    def bce(y,p):return torch.nn.functional.binary_cross_entropy(p.expand_as(y),y,reduction='none').numpy()[:,0]
    def ranks(d,ids):
        d=d.copy();np.fill_diagonal(d,np.inf)
        return np.array([np.lexsort((np.asarray(ids),r))[:10] for r in d])
    def overlap(x,y):return float(np.mean([len(set(i)&set(j))/10 for i,j in zip(x,y)]))
    def corr(x,y):
        z=float(spearmanr(x,y).statistic);return z if math.isfinite(z) else None
    trainids=[int(r['frame_id_0based']) for r in rows(a.plan/'training-membership.csv') if r['state_id']==cp['state_id'] and r['arm']==cp['arm']]
    oldfreq=(dense(sets['old']).sum(0,keepdim=True)+.5)/801
    trainfreq=(dense(trainids).sum(0,keepdim=True)+.5)/801
    values=[];geometries=[];dimensions=[]
    for label in ['OLD_VALIDATION','RECENT_HELDOUT']:
        rr=[r for r in rows(a.plan/'evaluation-ids.csv') if r['state_id']==cp['state_id'] and r['set']==label]
        rr.sort(key=lambda r:(float(r['time_ps']),int(r['frame_id_0based'])))
        ids=np.array([int(r['frame_id_0based']) for r in rr]);assert not set(ids)&set(trainids)
        y=dense(ids);zs=[];ls=[];pred=[]
        with torch.no_grad():
            for begin in range(0,200,32):
                guard();v=y[begin:begin+32];z,p=model(v);l=model.__logstd__.clone();zz,pp=model(v)
                assert torch.equal(z,zz) and torch.equal(p,pp)
                zs.append(z.clone());ls.append(l);pred.append(p)
            z=torch.cat(zs);l=torch.cat(ls);pr=torch.cat(pred)
            mean=model.decode(z.mean(0,keepdim=True));zero=model.decode(torch.zeros_like(z[:1]))
        assert all(bool(torch.isfinite(v).all()) for v in [z,l,pr,mean,zero])
        variance=(2*l).exp();kl=.5*(z*z+variance-1-2*l)
        errors={'MODEL':bce(y,pr),'OLD_FREQUENCY':bce(y,oldfreq),'TRAIN_FREQUENCY':bce(y,trainfreq),
                'VALIDATION_LOO':bce(y,(y.sum(0,keepdim=True)-y+.5)/200),'MEAN_LATENT':bce(y,mean),'ZERO_LATENT':bce(y,zero)}
        for offset in [1,17,53,97,149]:errors['MISMATCH_'+str(offset)]=bce(y,pr[(np.arange(200)+offset)%200])
        for name,mask in masks.items():
            row=dict(checkpoint=a.checkpoint,state_id=cp['state_id'],root_id=cp['state_id'][:3],arm=cp['arm'],init_id=cp['init_id'],chain_steps=int(cp['chain_steps']),set=label,mask=name,elements=int(mask.sum()),frames=200,KL_per_frame=float(kl.sum(1).mean()))
            for method,e in errors.items():
                row[method+'_BCE_per_frame']=float(e[:,mask].sum(1).mean());row[method+'_BCE_per_element']=float(e[:,mask].mean())
            row['A_train']=row['TRAIN_FREQUENCY_BCE_per_frame']-row['MODEL_BCE_per_frame']
            row['A_mean']=row['MEAN_LATENT_BCE_per_frame']-row['MODEL_BCE_per_frame']
            for offset in [1,17,53,97,149]:row['A_perm_'+str(offset)]=row['MISMATCH_'+str(offset)+'_BCE_per_frame']-row['MODEL_BCE_per_frame']
            target=y.numpy()[:,0][:,mask];loss=errors['MODEL'][:,mask]
            for positive in [0,1]:
                selected=target==positive;count=int(selected.sum());row[f'class{positive}_count']=count
                row[f'class{positive}_BCE_per_element']=float(loss[selected].mean()) if count else None
                row[f'class{positive}_BCE_per_frame']=float(loss[selected].sum()/200)
            values.append(row)
        physical=cdist(features['distances_A'][ids],features['distances_A'][ids])/math.sqrt(325)
        tri=np.triu_indices(200,1);pk=ranks(physical,ids)
        for scale,v in {'RAW':z.numpy(),'STANDARDIZED':(z.numpy()-z.numpy().mean(0))/np.where(z.numpy().std(0)>0,z.numpy().std(0),1)}.items():
            d=cdist(v,v);geometries.append(dict(checkpoint=a.checkpoint,set=label,scale=scale,physical_pair_spearman=corr(d[tri],physical[tri]),physical_knn_overlap=overlap(ranks(d,ids),pk),
                time_physical_knn_overlap=overlap(ranks(np.abs(features['time_ps'][ids,None]-features['time_ps'][None,ids]),ids),pk),
                contact_physical_knn_overlap=overlap(ranks(cdist(y.numpy()[:,0][:,masks['NONLOCAL']],y.numpy()[:,0][:,masks['NONLOCAL']]),ids),pk),
                zero_distance_fraction=float(np.mean(d[tri]==0))))
        eigen=np.linalg.eigvalsh(np.cov(z.numpy(),rowvar=False,bias=True))
        for j in range(3):dimensions.append(dict(checkpoint=a.checkpoint,set=label,dimension=j,mu_mean=float(z[:,j].mean()),mu_min=float(z[:,j].min()),mu_max=float(z[:,j].max()),mu_population_variance=float(z[:,j].var(unbiased=False)),posterior_variance_mean=float(variance[:,j].mean()),KL_dimension_mean=float(kl[:,j].mean()),cov_eigenvalue=float(eigen[j])))
        np.savez_compressed(dest/(label+'.npz'),frame_ids=ids,mu=z.numpy(),logstd=l.numpy(),reconstruction=pr.numpy())
    # FULL集合は固定し、全対の候補距離行列を作らない。
    full_start=time.monotonic();candidate=np.array(sets['candidate']);embedding=[]
    with torch.no_grad():
        for begin in range(0,len(candidate),32):
            guard();v=dense(candidate[begin:begin+32]);z,_=model(v);embedding.append(z.numpy())
    embedding=np.concatenate(embedding);assert np.isfinite(embedding).all()
    lof=LocalOutlierFactor(n_neighbors=20,metric='minkowski',p=2,novelty=False,n_jobs=1).fit(embedding)
    score=lof.negative_outlier_factor_;assert np.isfinite(score).all();order=np.lexsort((candidate,score))
    np.savez_compressed(dest/'ranking.npz',frame_ids=candidate,mu=embedding,lof=score,order=order)
    ident=int(candidate[order[0]])
    write(dest/'selection.json',dict(checkpoint=a.checkpoint,Top1=ident,Top10=candidate[order[:10]].tolist(),Top100=candidate[order[:100]].tolist(),
          Top1_time_ps=float(features['time_ps'][ident]),Top1_origin='OLD' if ident in sets['old'] else ('NEW' if ident in sets['new'] else 'OTHER'),
          score_gap=float(score[order[1]]-score[order[0]]),full_cost_s=time.monotonic()-full_start,downstream_MD='NOT_OBSERVED'))
    assert tensor_digest(model.state_dict())==saved['model_digest'] and sha(path)==expected
    table(dest/'model-metrics.csv',values);table(dest/'geometry.csv',geometries);table(dest/'latent.csv',dimensions)
    guard();cost=dict(checkpoint=a.checkpoint,wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    write(dest/'result.json',dict(status='COMPLETE',source_checkpoint_sha256=expected,repeat_forward_bitwise_equal=True,weights_unmodified=True,cost=cost,files={p.name:sha(p) for p in dest.iterdir() if p.is_file()}))
    ledger.append(cost);write(a.output/'cost-ledger.json',ledger)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path);p.add_argument('checkpoint');a=p.parse_args()
    try:evaluate(a)
    except BaseException as e:
        write(a.output/'evaluation-stop.json',dict(status='STOPPED',checkpoint=a.checkpoint,reason=str(e),type=type(e).__name__))
        raise
