"""固定35系列・全窓を8独立履歴根で対応集計する。frameを独立標本にしない。"""
import csv,json,itertools,time
from pathlib import Path
import numpy as np
from nmr34_v2 import require,save_json,sha256
from nmr34_v2_execute import stage
METRICS=['min_RMSD_A','mean_RMSD_A','median_RMSD_A','p10_RMSD_A','final_RMSD_A','mean_Q','median_Q','max_Q','Q_at_argmin']
COMPS=[('F2','F1'),('F1','F0'),('F2','F0')]


def table(path,rows):
    """CSVを排他作成し、標準LFで全行を保存する。"""
    rows=iter(rows);first=next(rows)
    with Path(path).open('x') as f:
        w=csv.DictWriter(f,fieldnames=list(first),lineterminator='\n');w.writeheader();w.writerow(first);w.writerows(rows)


def root_effects(arm_means):
    """root×S4/S8×arm×窓×metricから全3対比と段階を作る。"""
    # F0は一つの共有対照。学習seedやframeの独立複製を作らない。
    result={}
    for hi,lo in [(2,1),(1,0),(2,0)]:
        d=arm_means[:,:,hi]-arm_means[:,:,lo]
        result[(hi,lo)]=np.stack([d[:,0],d[:,1],d.mean(axis=1),d[:,1]-d[:,0]],axis=1)
    return result


def analyze(out,bundle):
    """raw座標は読み直さず、新窓表だけを集約する。"""
    from scipy.stats import spearmanr
    start=time.monotonic();cpu=time.process_time()
    manifest=json.loads((bundle/'manifest.json').read_text());dest=out/'analysis';dest.mkdir(exist_ok=False)
    stage(out,'analysis_load')
    values=np.empty((35,272,24,9));window_keys=None;hist=[];branches=[]
    receipts=[]
    for i,e in enumerate(manifest):
        unit=out/'units'/e['task_id'];r=json.loads((unit/'receipt.json').read_text());require(r['status']=='PASS','未成功単位')
        for name,h in r['outputs'].items():require(sha256(unit/name)==h,'出力SHA不一致')
        rows=json.loads((unit/'windows.json').read_text());require(len(rows)==840,'全窓欠落')
        keys=[x['window'] for x in rows[:24]]
        if window_keys is None:window_keys=keys
        require(keys==window_keys,'窓順序不一致')
        for m in range(35):
            for w in range(24):values[m,i,w]=[rows[m*24+w][metric] for metric in METRICS]
        (hist if e['kind']=='HISTORY' else branches).append(i);receipts.append(r)
    require(len(hist)==32 and len(branches)==240,'行列欠落')
    rng=np.random.default_rng(17103001);draw=rng.integers(0,8,(10000,8));main_rows=[];reference_ranges=[]
    geometry=list(csv.DictReader((bundle/'geometry-native-joined.csv').open()))
    # 同一geometry行の旧native値は使用せず、branch/windowキーのみ結合する。
    for model in range(35):
        label=str(model+1) if model<34 else 'NMR34_MIN';stage(out,'analysis_'+label)
        md=dest/label;md.mkdir();data=values[model]
        def flat(indices):
            for i in indices:
                e=manifest[i]
                for w,key in enumerate(window_keys):
                    yield dict(task_id=e['task_id'],root_id=e['root_id'],state_id=e.get('state_id',''),arm=e.get('arm',''),training_block=e.get('training_block',''),MD_block=e.get('MD_block',''),window=key,**dict(zip(METRICS,map(float,data[i,w]))))
        table(md/'history.csv',flat(hist))
        for suffix in ('s4','s8'):table(md/('branches-'+suffix+'.csv'),flat([i for i in branches if manifest[i]['state_id'].endswith(suffix)]))
        means=np.empty((8,2,3,24,9));state_rows=[];model_rows=[]
        for ri,si,ai in itertools.product(range(8),range(2),range(3)):
            rid=f'r{ri+1:02}';sid=rid+('-s4' if si==0 else '-s8');arm=f'F{ai}'
            ii=[i for i in branches if manifest[i]['state_id']==sid and manifest[i]['arm']==arm]
            require(len(ii)==(3 if ai==0 else 6),'階層不正');means[ri,si,ai]=data[ii].mean(axis=0)
            for w,key in enumerate(window_keys):state_rows.append(dict(root_id=rid,state_id=sid,arm=arm,window=key,**dict(zip(METRICS,map(float,means[ri,si,ai,w])))))
            for tb in sorted({manifest[i]['training_block'] for i in ii}):
                jj=[i for i in ii if manifest[i]['training_block']==tb];require(len(jj)==3,'MDseed階層不正')
                vv=data[jj].mean(axis=0)
                for w,key in enumerate(window_keys):model_rows.append(dict(state_id=sid,arm=arm,training_block=tb,MD_repeats=3,window=key,**dict(zip(METRICS,map(float,vv[w])))))
        table(md/'state.csv',state_rows);table(md/'models.csv',model_rows)
        effects=root_effects(means);roots=[];summary=[]
        for (hi,lo),v in effects.items():
            comp=f'F{hi}-F{lo}'
            for st,window in itertools.product(range(4),range(24)):
                statename=['S4','S8','AVERAGE','S8_MINUS_S4'][st];vv=v[:,st,window]
                for ri in range(8):roots.append(dict(root_id=f'r{ri+1:02}',stage=statename,window=window_keys[window],comparison=comp,**dict(zip(METRICS,map(float,vv[ri])))))
                ci=np.quantile(vv[draw].mean(axis=1),[.025,.975],axis=0)
                for mi,metric in enumerate(METRICS):
                    vals=vv[:,mi];row=dict(stage=statename,window=window_keys[window],comparison=comp,metric=metric,roots=8,mean=float(vals.mean()),median=float(np.median(vals)),SD=float(vals.std(ddof=1)),minimum=float(vals.min()),maximum=float(vals.max()),positive=int(sum(vals>0)),negative=int(sum(vals<0)),zero=int(sum(vals==0)),bootstrap95_low=float(ci[0,mi]),bootstrap95_high=float(ci[1,mi]))
                    summary.append(row)
                    if window_keys[window]=='100_4.0_0.5':main_rows.append(dict(reference=label,**row))
        table(md/'root-paired.csv',roots);table(md/'root-summary.csv',summary)
        if model==0:
            old=list(csv.DictReader((bundle/'N1-root-summary.csv').open()))
            lookup={(r['stage'],f"{int(r['burn_ps'])}_{float(r['prefix_ns'])}_{float(r['sampling_ps'])}",r['comparison'],r['metric']):r for r in old}
            error=0.
            for r in summary:
                prior=lookup[(r['stage'],r['window'],r['comparison'],r['metric'])]
                for field in ['mean','median','SD','minimum','maximum','positive','negative','zero','bootstrap95_low','bootstrap95_high']:
                    error=max(error,abs(r[field]-float(prior[field])))
            require(error<=1e-8,'旧N1根級集約の再現不一致')
            save_json(dest/'M1-root-reproduction.json',dict(rows=len(summary),maximum_error=error,status='PASS'))
        index={(manifest[i]['task_id'].removesuffix('-md'),key):data[i,w] for i in branches for w,key in enumerate(window_keys)}
        correlations=[]
        for mode in sorted({r['reference_mode'] for r in geometry}):
            for burn,prefix,st in itertools.product([0,100,200,500],[1.,2.,4.],['S4','S8','ALL']):
                sub=[r for r in geometry if r['reference_mode']==mode and float(r['burn_ps'])==burn and float(r['prefix_ns'])==prefix and (st=='ALL' or r['state_id'].endswith(st.lower()))]
                key=f'{burn}_{prefix}_0.5'
                for metric in ['min_RMSD_A','mean_RMSD_A','mean_Q']:
                    coefficient=float(spearmanr([float(r['distance_mean_A']) for r in sub],[index[(r['branch_id'],key)][METRICS.index(metric)] for r in sub]).statistic)
                    correlations.append(dict(reference_mode=mode,window=key,stage=st,metric=metric,branches=len(sub),Spearman=coefficient,scope='DESCRIPTIVE_CORRELATED_BRANCHES_NO_P_VALUE'))
        table(md/'geometry-correlations.csv',correlations)
    table(dest/'main-reference-sensitivity.csv',main_rows)
    # 参照minの自明な低下と条件群差の変化を区別する枝ごとの数値差。
    differences=[]
    for i in range(272):
        for w,key in enumerate(window_keys):differences.append(dict(task_id=manifest[i]['task_id'],window=key,**{metric:float(values[0,i,w,k]-values[34,i,w,k]) for k,metric in enumerate(METRICS)}))
    for sampling in ['0.5','2.0']:
        table(dest/f'M1-minus-min34-{sampling}.csv',[r for r in differences if r['window'].endswith('_'+sampling)])
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    plt.rcParams['font.family']='Noto Sans CJK JP'
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    for st in ['S4','S8','AVERAGE']:
        rr=[r for r in main_rows if r['stage']==st and r['comparison']=='F2-F1' and r['metric']=='min_RMSD_A']
        axs[0].plot(range(1,36),[r['mean'] for r in rr],'.-',label=st)
    for st in ['S4','S8','AVERAGE']:
        rr=[r for r in main_rows if r['stage']==st and r['comparison']=='F2-F1' and r['metric']=='mean_Q']
        axs[1].plot(range(1,36),[r['mean'] for r in rr],'.-',label=st)
    for ax in axs:ax.axhline(0,color='gray');ax.set_xlabel('NMR参照（35 = ensemble-min）');ax.legend()
    axs[0].set_ylabel('F2−F1 最小RMSD [Å]');axs[1].set_ylabel('F2−F1 平均Q');fig.tight_layout();fig.savefig(dest/'reference-sensitivity.png',dpi=170);plt.close(fig)
    save_json(out/'analysis-complete.json',dict(status='PASS',references=35,window_conditions=24,roots=8,wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,scope='POST_HOC_EXPLORATORY'))
