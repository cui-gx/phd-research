"""L2の全固定セルを照合し、対応差と陰性結果を省略せず集約する。"""
import argparse
import itertools
import math
import os
import time
from pathlib import Path
from p1.l2_engineering import read, rows, sha, write, runtime

def aggregate(a):
    runtime()
    begun=time.monotonic()
    def guard():
        assert time.monotonic()-begun<300,"集計300秒復核点"
        rss=int(Path("/proc/self/status").read_text().split("VmRSS:")[1].split()[0])*1024
        assert rss<=2*1024**3,"集計RSS2GiB超過"
    import numpy as np
    from scipy.spatial.distance import cdist
    from scipy.stats import spearmanr
    from p1.l1_frozen_diagnostic import table
    matrix=rows(a.plan/'checkpoint-matrix.csv');chains=rows(a.plan/'experiment-matrix.csv')
    assert len(matrix)==156 and len(chains)==36
    public=a.output/'public';public.mkdir(exist_ok=False)
    metrics=[];geometry=[];latent=[];selection=[];audit=[];cache={};lookup={r['checkpoint_id']:r for r in matrix}
    for cp in matrix:
        name=cp['checkpoint_id'];p=a.output/'evaluations'/name
        status=read(p/'result.json');assert status['status']=='COMPLETE'
        for rel,h in status['files'].items():assert sha(p/rel)==h
        metrics+=rows(p/'model-metrics.csv');geometry+=rows(p/'geometry.csv');latent+=rows(p/'latent.csv')
        selection.append(read(p/'selection.json'));audit.append(dict(checkpoint=name,sha256=status['source_checkpoint_sha256'],weights_unmodified=status['weights_unmodified'],repeat_forward_bitwise_equal=status['repeat_forward_bitwise_equal']))
    assert len(metrics)==936 and len(geometry)==624 and len(latent)==936
    table(public/'model-metrics.csv',metrics);table(public/'geometry.csv',geometry);table(public/'latent.csv',latent);table(public/'selection-summary.csv',selection);table(public/'checkpoint-audit.csv',audit)
    pairs=[]
    def add(kind,left,right):
        assert lookup[left]['state_id']==lookup[right]['state_id']
        pairs.append((kind,left,right))
    def ident(state,i,arm,step):return f'{state}-i{i}-{arm}-step{step:04d}'
    states=['r01-s4','r01-s8','r02-s4','r02-s8'];steps=[200,400,800,1600]
    for st in states:
        for i in [1,2,3]:
            for arm in ['M0','F1','F2']:
                for low,high in itertools.combinations(steps,2):add('STEP_HIGH_MINUS_LOW',ident(st,i,arm,high),ident(st,i,arm,low))
                for step in steps:
                    add('TRAINED_MINUS_UNTRAINED',ident(st,i,arm,step),ident(st,i,'M0',0))
                    if arm!='M0':add('UPDATED_MINUS_FROZEN',ident(st,i,arm,step),ident(st,i,'M0',200))
            for step in steps:add('F2_MINUS_F1',ident(st,i,'F2',step),ident(st,i,'F1',step))
        for arm in ['M0','F1','F2']:
            for step in ([0]+steps if arm=='M0' else steps):
                for low,high in itertools.combinations([1,2,3],2):add('INITIALIZATION',ident(st,high,arm,step),ident(st,low,arm,step))
    metricmap={(r['checkpoint'],r['set'],r['mask']):r for r in metrics}
    columns=['MODEL_BCE_per_frame','A_train','A_mean','KL_per_frame']+['A_perm_'+str(i) for i in [1,17,53,97,149]]
    contrasts=[];stability=[];rankpairs=[]
    def corr(x,y):
        v=float(spearmanr(x,y).statistic);return v if math.isfinite(v) else None
    def knn(d,ids):
        d=d.copy();np.fill_diagonal(d,np.inf);return np.array([np.lexsort((ids,r))[:10] for r in d])
    def arrays(name,label):
        key=(name,label)
        if key not in cache:
            with np.load(a.output/'evaluations'/name/(label+'.npz')) as data:
                cache[key]=(data['frame_ids'].copy(),data['mu'].copy())
        return cache[key]
    ranks_cache={}
    def ranking(name):
        if name not in ranks_cache:
            with np.load(a.output/'evaluations'/name/'ranking.npz') as data:
                ranks_cache[name]={k:data[k].copy() for k in ['frame_ids','lof','order']}
        return ranks_cache[name]
    for kind,left,right in pairs:
        guard()
        state=lookup[left]['state_id']
        for label in ['OLD_VALIDATION','RECENT_HELDOUT']:
            for mask in ['ALL','NONLOCAL','LONG']:
                l=metricmap[(left,label,mask)];r=metricmap[(right,label,mask)]
                rr=dict(kind=kind,state_id=state,root_id=state[:3],left=left,right=right,set=label,mask=mask)
                for col in columns:rr[col+'_left']=float(l[col]);rr[col+'_right']=float(r[col]);rr[col+'_difference']=float(l[col])-float(r[col])
                contrasts.append(rr)
            ids,z=arrays(left,label);rid,rz=arrays(right,label);assert np.array_equal(ids,rid)
            d=cdist(z,z);rd=cdist(rz,rz);tri=np.triu_indices(200,1)
            stable=dict(kind=kind,state_id=state,left=left,right=right,set=label,latent_distance_spearman=corr(d[tri],rd[tri]),knn_overlap=float(np.mean([len(set(x)&set(y))/10 for x,y in zip(knn(d,ids),knn(rd,ids))])))
            stability.append(stable)
        x=ranking(left);y=ranking(right);assert np.array_equal(x['frame_ids'],y['frame_ids'])
        xi=x['frame_ids'][x['order']];yi=y['frame_ids'][y['order']]
        with np.load(a.project/'runs/b1-expansion-20261026/tasks'/(state+'-decision-pool')/'science/features.npz') as feat:
            physical=float(np.linalg.norm(feat['distances_A'][xi[0]]-feat['distances_A'][yi[0]])/math.sqrt(325))
        rankpairs.append(dict(kind=kind,state_id=state,left=left,right=right,score_spearman=corr(x['lof'],y['lof']),Top1_identical=bool(xi[0]==yi[0]),Top10_overlap=len(set(xi[:10])&set(yi[:10]))/10,Top100_overlap=len(set(xi[:100])&set(yi[:100]))/100,Top1_distance_A=physical,downstream_MD='NOT_OBSERVED'))
    table(public/'paired-contrasts.csv',contrasts);table(public/'representation-stability.csv',stability);table(public/'LOF-comparisons.csv',rankpairs)
    # 状態ごとの初期化平均は記述値であり、独立標本CIを作らない。
    state=[]
    for st in states:
        for arm in ['M0','F1','F2']:
            for step in ([0]+steps if arm=='M0' else steps):
                for label in ['OLD_VALIDATION','RECENT_HELDOUT']:
                    for mask in ['ALL','NONLOCAL','LONG']:
                        rr=[r for r in metrics if r['state_id']==st and r['arm']==arm and int(r['chain_steps'])==step and r['set']==label and r['mask']==mask]
                        assert len(rr)==3
                        item=dict(state_id=st,root_id=st[:3],arm=arm,step=step,set=label,mask=mask,initializations=3)
                        for col in columns:
                            vv=[float(r[col]) for r in rr];item[col+'_mean']=float(np.mean(vv));item[col+'_min']=min(vv);item[col+'_max']=max(vv)
                        state.append(item)
    table(public/'state-metrics.csv',state)
    ledger=read(a.output/'cost-ledger.json');write(public/'cost-ledger.json',ledger)
    summary=dict(status='COMPLETE',chains=36,scientific_optimizer_steps=sum(read(a.output/'chains'/r['chain_id']/'result.json')['steps'] for r in chains),evaluation_points=156,metric_rows=len(metrics),geometry_rows=len(geometry),latent_rows=len(latent),paired_conditions=len(pairs),paired_metric_rows=len(contrasts),LOF_comparisons=len(rankpairs),new_MD=0,independent_roots=2,scientific_acceptance='PENDING',wall_s=sum(v['wall_s'] for v in ledger))
    assert summary['scientific_optimizer_steps']==57600
    write(public/'summary.json',summary)
    write(public/'output-sha256.json',{p.name:sha(p) for p in public.iterdir() if p.is_file()})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path);a=p.parse_args();aggregate(a)
