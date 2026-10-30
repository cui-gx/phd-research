"""N1全枝の固定窓・根内対応と図をサーバCPUで整理する。"""
import csv,json,time,resource,hashlib,itertools
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
from n1_cpu_evaluate import sha,dump,table
import argparse

def main(a):
    start=time.monotonic();cpu=time.process_time();assert json.loads((a.out/'execution-status.json').read_text())['completed_units']==272
    dest=a.out/'summary';dest.mkdir(exist_ok=False)
    branches=list(csv.DictReader((a.bundle/'branch-index.csv').open()));bmap={b['md_task_id']:b for b in branches}
    rows=[];audit=[];arrays={}
    for unit in sorted((a.out/'units').iterdir()):
        r=json.loads((unit/'receipt.json').read_text());assert r['status']=='PASS'
        for n,h in r['outputs'].items():assert sha(unit/n)==h
        w=list(csv.DictReader((unit/'windows.csv').open()));rows+=w;audit.append(r)
        if unit.name in bmap:
            with np.load(unit/'frames.npz') as z:arrays[unit.name]={k:z[k] for k in ['RMSD_A','Q','valid','local_time_ps']}
    assert len(rows)==272*24
    table(dest/'all-windows.csv',rows)
    metrics=['min_RMSD_A','mean_RMSD_A','median_RMSD_A','p10_RMSD_A','final_RMSD_A','mean_Q','median_Q','max_Q','Q_at_argmin']
    cells={};modelcells={}
    for r in rows:
        if r['kind']!='DOWNSTREAM':continue
        key=(r['state_id'],r['sampling_ps'],r['burn_ps'],r['prefix_ns'])
        cells.setdefault(key,{}).setdefault(r['arm'],[]).append(r)
        mkey=(*key,r['arm'],r['training_block']);modelcells.setdefault(mkey,[]).append(r)
    model=[]
    for key,v in modelcells.items():
        sid,sp,b,p,arm,tb=key;first=bmap[v[0]['task_id']]
        model.append(dict(state_id=sid,sampling_ps=sp,burn_ps=b,prefix_ns=p,arm=arm,training_block=tb,MD_repeats=len(v),model_task_id=first['model_task_id'],model_checkpoint_sha256=first['model_checkpoint_sha256'],**{m:float(np.mean([float(x[m]) for x in v])) for m in metrics}))
    table(dest/'model-windows.csv',model)
    state=[];paired=[]
    for key,arms in cells.items():
        sid,sp,b,p=key;assert [len(arms[x]) for x in ['F0','F1','F2']]==[3,6,6]
        means={arm:{m:float(np.mean([float(x[m]) for x in v])) for m in metrics} for arm,v in arms.items()}
        for arm,v in means.items():state.append(dict(state_id=sid,root_id=sid[:3],sampling_ps=sp,burn_ps=b,prefix_ns=p,arm=arm,**v))
        for hi,lo in [('F2','F1'),('F1','F0'),('F2','F0')]:
            for m in metrics:paired.append(dict(state_id=sid,root_id=sid[:3],sampling_ps=sp,burn_ps=b,prefix_ns=p,comparison=hi+'-'+lo,metric=m,difference=means[hi][m]-means[lo][m]))
    table(dest/'state-windows.csv',state);table(dest/'state-paired.csv',paired)
    index={(r['state_id'],r['sampling_ps'],r['burn_ps'],r['prefix_ns'],r['comparison'],r['metric']):r['difference'] for r in paired}
    roots=[];stats=[];rng=np.random.default_rng(17103001);draw=rng.integers(0,8,(10000,8))
    for sp,b,p,c,m in itertools.product(['0.5','2.0'],['0','100','200','500'],['1.0','2.0','4.0'],['F2-F1','F1-F0','F2-F0'],metrics):
        values={s:[] for s in ['S4','S8','AVERAGE','S8_MINUS_S4']}
        for i in range(1,9):
            rid=f'r{i:02}';v4=index[(rid+'-s4',sp,b,p,c,m)];v8=index[(rid+'-s8',sp,b,p,c,m)]
            for stage,v in [('S4',v4),('S8',v8),('AVERAGE',(v4+v8)/2),('S8_MINUS_S4',v8-v4)]:
                values[stage].append(v);roots.append(dict(root_id=rid,stage=stage,sampling_ps=sp,burn_ps=b,prefix_ns=p,comparison=c,metric=m,difference=v))
        for stage,v in values.items():
            v=np.array(v);ci=np.quantile(v[draw].mean(axis=1),[.025,.975]);stats.append(dict(stage=stage,sampling_ps=sp,burn_ps=b,prefix_ns=p,comparison=c,metric=m,roots=8,mean=float(v.mean()),median=float(np.median(v)),SD=float(v.std(ddof=1)),minimum=float(v.min()),maximum=float(v.max()),positive=int(sum(v>0)),negative=int(sum(v<0)),zero=int(sum(v==0)),bootstrap95_low=float(ci[0]),bootstrap95_high=float(ci[1])))
    table(dest/'root-paired.csv',roots);table(dest/'root-summary.csv',stats)
    geom=list(csv.DictReader((a.bundle/'r1-continuous.csv').open()));native={(r['task_id'].removesuffix('-md'),r['burn_ps'],r['prefix_ns']):r for r in rows if r['kind']=='DOWNSTREAM' and r['sampling_ps']=='0.5'}
    joined=[]
    for g in geom:
        r=native[(g['branch_id'],g['burn_ps'],g['prefix_ns'])];assert int(g['frames'])==int(r['valid']),'旧窓適格件数不一致'
        joined.append(dict(reference_mode=g['reference_mode'],branch_id=g['branch_id'],root_id=g['root_id'],state_id=g['state_id'],arm=g['arm'],burn_ps=g['burn_ps'],prefix_ns=g['prefix_ns'],distance_mean_A=float(g['distance_mean_A']),min_RMSD_A=float(r['min_RMSD_A']),mean_RMSD_A=float(r['mean_RMSD_A']),mean_Q=float(r['mean_Q'])))
    table(dest/'geometry-native-joined.csv',joined)
    cor=[]
    for mode in sorted({r['reference_mode'] for r in joined}):
        for b,p in itertools.product(['0','100','200','500'],['1.0','2.0','4.0']):
            v=[r for r in joined if r['reference_mode']==mode and r['burn_ps']==b and r['prefix_ns']==p]
            for stage in ['S4','S8','ALL']:
                sub=[r for r in v if stage=='ALL' or r['state_id'].endswith(stage.lower())]
                for m in ['min_RMSD_A','mean_RMSD_A','mean_Q']:
                    corr=float(spearmanr([r['distance_mean_A'] for r in sub],[r[m] for r in sub]).statistic)
                    cor.append(dict(reference_mode=mode,burn_ps=b,prefix_ns=p,stage=stage,metric=m,branches=len(sub),Spearman=corr,scope='DESCRIPTIVE_CORRELATED_BRANCHES_NO_P_VALUE'))
    table(dest/'geometry-correlations.csv',cor)
    # 同一MD量での履歴bestと下流bestの差。wall-clock利益ではない。
    progress=[]
    for sid in sorted({b['state_id'] for b in branches}):
        rid=sid[:3];segments=2 if sid.endswith('s4') else 4;h=[]
        for k in range(1,segments+1):
            with np.load(a.out/'units'/f'{rid}-h{k}-md'/'frames.npz') as z:
                ix=z['valid']&(z['time_ps']>100);h.extend(z['RMSD_A'][ix])
        baseline=float(min(h))
        for b in [x for x in branches if x['state_id']==sid]:
            r=native[(b['branch_id'],'100','4.0')];value=float(r['min_RMSD_A']);progress.append(dict(branch_id=b['branch_id'],state_id=sid,root_id=rid,arm=b['arm'],history_min_RMSD_A=baseline,downstream_min_RMSD_A=value,new_best_gain_A=max(0,baseline-value),analysis='POST_HOC_EQUAL_MD_NOT_WALL_CLOCK'))
    table(dest/'history-progress.csv',progress)
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    plt.rcParams['font.family']='Noto Sans CJK JP'
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for arm in ['F0','F1','F2']:
        vs=[r for r in state if r['arm']==arm and r['sampling_ps']=='0.5' and r['burn_ps']=='100' and r['prefix_ns']=='4.0']
        axs[0].plot(np.arange(16),[r['min_RMSD_A'] for r in vs],'o-',label=arm)
        rr=[];qq=[]
        for tid,v in arrays.items():
            if bmap[tid]['arm']==arm:
                ids=np.flatnonzero(v['valid']&(v['local_time_ps']>100))[::40];rr.extend(v['RMSD_A'][ids]);qq.extend(v['Q'][ids])
        axs[1].scatter(rr,qq,s=2,alpha=.2,label=arm)
    axs[0].set(xlabel='状態索引（16、同根内相関）',ylabel='MD枝の最小RMSDの平均 [Å]');axs[1].set(xlabel='Cα RMSD [Å]',ylabel='native Q');axs[0].legend();axs[1].legend();fig.tight_layout();fig.savefig(dest/'native-overview.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for arm in ['F0','F1','F2']:
        vv=[v for tid,v in arrays.items() if bmap[tid]['arm']==arm];curves=np.array([np.minimum.accumulate(np.where(v['valid']&(v['local_time_ps']>100),v['RMSD_A'],np.inf)) for v in vv]);curve=np.mean(curves,axis=0);axs[0].plot((np.arange(8000)+1)*.0005,curve,label=arm)
    axs[0].set(xlabel='下流MD時間 [ns]',ylabel='枝別best-so-farの平均 [Å]',xlim=(.101,4));axs[0].legend()
    for c in ['F2-F1','F1-F0','F2-F0']:
        v=[r for r in roots if r['comparison']==c and r['stage']=='AVERAGE' and r['sampling_ps']=='0.5' and r['burn_ps']=='100' and r['prefix_ns']=='4.0' and r['metric']=='min_RMSD_A'];axs[1].plot(np.arange(1,9),[r['difference'] for r in v],'o-',label=c)
    axs[1].axhline(0,color='gray');axs[1].set(xlabel='独立乱数履歴根',ylabel='最小RMSD対応差 [Å]');axs[1].legend();fig.tight_layout();fig.savefig(dest/'progress-and-pairs.png',dpi=160);plt.close(fig)
    costs=dict(status='COMPLETE',units=272,frames=sum(r['frames'] for r in audit),unit_wall_s=sum(r['wall_s'] for r in audit),unit_CPU_s=sum(r['CPU_s'] for r in audit),max_RSS_MiB=max(r['peak_RSS_MiB'] for r in audit),max_DCD_time_error_ps=max(r['DCD_max_time_error_ps'] for r in audit),summary_wall_s=time.monotonic()-start,summary_CPU_s=time.process_time()-cpu,summary_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,output_bytes=sum(p.stat().st_size for p in a.out.rglob('*') if p.is_file()),failed_units=0,scope='POST_HOC_EXPLORATORY',NMR34='NOT_EXECUTED')
    assert costs['summary_RSS_MiB']<2048 and costs['output_bytes']<2*1024**3
    dump(dest/'costs.json',costs);dump(dest/'unit-audit.json',audit);dump(dest/'output-sha256.json',{p.name:sha(p) for p in dest.iterdir() if p.is_file()});print(json.dumps(costs))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out',type=Path);p.add_argument('bundle',type=Path);main(p.parse_args())
