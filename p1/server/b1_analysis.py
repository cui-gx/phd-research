"""B1全枝の物理代理指標と対応差。サーバCPUでのみ実行する。"""
from __future__ import annotations
import csv
import itertools
import json
import os
from pathlib import Path
import resource
import time
import numpy as np
from scipy.stats import spearmanr
from .gq_r2 import dump,sha,table,nearest,distances,regions,circular
from .science import ROOT


def summarize(x):
    return dict(mean=float(np.mean(x)),median=float(np.median(x)),p90=float(np.quantile(x,.9)))


def run(out):
    root=ROOT.parent/'runs/b1-pilot-20261026'
    out.mkdir(exist_ok=False)
    def task(name):return root/'tasks'/name/'science'
    history=dict(np.load(task('decision-pool')/'features.npz'))
    eligible=(history['time_ps']>100)&history['valid']
    a0=history['distances_A'][eligible];angles0=history['angles_rad'][eligible]
    import hashlib
    a0sha=hashlib.sha256(np.ascontiguousarray(a0).tobytes()).hexdigest()
    candidate=json.loads((task('decision-pool')/'indices.json').read_text())['candidate']
    if len(a0)!=len(candidate):raise ValueError('共通履歴と候補対応が不一致です。')
    rankings={};models={};comparisons=[]
    for label in ['F0','F1-b1','F2-b1','F1-b2','F2-b2']:
        rankings[label]=dict(np.load(task('infer-'+label)/'ranking.npz'))
        if rankings[label]['frame_ids'].tolist()!=candidate:raise ValueError('候補池が不一致です。')
        models[label]=json.loads((task('infer-'+label)/'result.json').read_text())['checkpoint_sha256']
    rows=[]
    for label,v in rankings.items():
        ranks=np.empty(len(candidate),int);ranks[v['order']]=np.arange(1,len(candidate)+1)
        for frame,score,rank in zip(v['frame_ids'],v['lof'],ranks):
            rows.append(dict(model=label,frame_id=int(frame),physical_time_ps=float(history['time_ps'][frame]),rank=int(rank),LOF=float(score)))
    table(out/'candidate-rankings.csv',rows)
    for block in (1,2):
        for hi,lo in [('F2','F1'),('F2','F0'),('F1','F0')]:
            aa=rankings[f'{hi}-b{block}' if hi!='F0' else 'F0'];bb=rankings[f'{lo}-b{block}' if lo!='F0' else 'F0']
            aid=aa['frame_ids'][aa['order']];bid=bb['frame_ids'][bb['order']]
            ia,ib=int(aid[0]),int(bid[0])
            comparisons.append(dict(block=block,comparison=hi+'-'+lo,selected_high=ia,selected_low=ib,
                selected_high_time_ps=float(history['time_ps'][ia]),selected_low_time_ps=float(history['time_ps'][ib]),
                selected_dRMSD_A=float(distances(history['distances_A'][ia],history['distances_A'][ib])[0,0]),
                selected_angle_RMS_deg=float(circular(history['angles_rad'][ia],history['angles_rad'][ib])),
                ranking_spearman=float(spearmanr(aa['lof'],bb['lof']).statistic),
                topk=[dict(k=k,intersection=len(set(aid[:k])&set(bid[:k])),jaccard=len(set(aid[:k])&set(bid[:k]))/len(set(aid[:k])|set(bid[:k]))) for k in (1,10,100)]))
    dump(out/'selection-comparisons.json',comparisons);dump(out/'model-sha256.json',models)
    continuous=[];discrete=[];time_blocks=[];quality=[];bench=[]
    for block,arm in itertools.product((1,2),('F0','F1','F2')):
        name=f'md-{arm}-b{block}';folder=task('prepare-'+name)
        a=dict(np.load(folder/'features.npz'));t=a['time_ps'];valid=a['valid']
        source=json.loads((root/'tasks'/name/'request.json').read_text())
        initial=np.load(task(name)/'initial-coordinates-A.npy');selected=np.load(source['selected'])
        if not np.array_equal(initial,selected):raise ValueError('実際のMD初期座標が選択座標と異なります。')
        quality.append(dict(block=block,arm=arm,**json.loads((folder/'quality.json').read_text()),selected_coordinates_exact=True))
        start=time.monotonic();dd,nn=nearest(a['distances_A'],a0);nearest_s=time.monotonic()-start
        check=distances(a['distances_A'][:16],a0[:64]).min(axis=1)
        small=nearest(a['distances_A'][:16],a0[:64],block=3)[0]
        err=float(np.max(np.abs(check-small)))
        if err>1e-12:raise ValueError('分割最近傍照合に失敗しました。')
        np.savez_compressed(out/(name+'-distances.npz'),d_min_A=dd,nearest_A0_id=nn,time_ps=t,valid=valid)
        bench.append(dict(block=block,arm=arm,query_frames=len(dd),history_frames=len(a0),nearest_wall_s=nearest_s,small_exact_error_A=err))
        angular=circular(a['angles_rad'],angles0[nn])
        for burn,prefix in itertools.product((0,100,200,500),(1000,2000,4000)):
            mask=(t>burn)&(t<=prefix+1e-5)&valid
            if not mask.any():raise ValueError('科学代理評価に適格フレームがありません。')
            continuous.append(dict(block=block,arm=arm,burn_ps=burn,prefix_ns=prefix/1000,frames=int(mask.sum()),
                **{'distance_'+k+'_A':v for k,v in summarize(dd[mask]).items()},
                Rg_mean_A=float(a['rg_A'][mask].mean()),Q8_mean=float(a['q'][mask].mean()),
                angle_to_geometric_neighbor_median_deg=float(np.median(angular[mask]))))
            ii=np.flatnonzero((t>burn)&(t<=prefix+1e-5))[::4]
            for eps,tau in itertools.product((1.5,2.,3.),(0,5)):
                reps,confirmed=regions(a['distances_A'][ii],t[ii],eps,tau,valid=valid[ii],history_min_distance=dd[ii])
                discrete.append(dict(block=block,arm=arm,burn_ps=burn,prefix_ns=prefix/1000,epsilon_A=eps,tau_ps=tau,
                     interval_ps=2,added_regions=len(reps),representative_frame_ids=ii[reps].tolist(),confirmation_frame_ids=ii[confirmed].tolist()))
        for start_ps in range(0,4000,100):
            mask=(t>start_ps)&(t<=start_ps+100+1e-5)&valid
            if mask.any():time_blocks.append(dict(block=block,arm=arm,start_ps=start_ps,frames=int(mask.sum()),
                **{'distance_'+k+'_A':v for k,v in summarize(dd[mask]).items()},Rg_mean_A=float(a['rg_A'][mask].mean()),
                Q8_mean=float(a['q'][mask].mean()),potential_mean_kJ_mol=float(a['state'][mask,2].mean())))
        dump(out/'continuous.json',continuous);dump(out/'discrete.json',discrete)
        print('枝評価完了',block,arm,flush=True)
    table(out/'continuous.csv',continuous)
    table(out/'discrete-counts.csv',[{k:v for k,v in r.items() if k not in ['representative_frame_ids','confirmation_frame_ids']} for r in discrete])
    table(out/'time-blocks.csv',time_blocks);dump(out/'quality.json',quality);dump(out/'distance-checks.json',bench)
    paired=[]
    for block,burn,prefix in itertools.product((1,2),(0,100,200,500),(1.,2.,4.)):
        c={r['arm']:r for r in continuous if r['block']==block and r['burn_ps']==burn and r['prefix_ns']==prefix}
        for metric in ['distance_mean_A','distance_median_A','distance_p90_A','Rg_mean_A','Q8_mean','angle_to_geometric_neighbor_median_deg']:
            for hi,lo in [('F2','F1'),('F2','F0'),('F1','F0')]:
                paired.append(dict(block=block,burn_ps=burn,prefix_ns=prefix,metric=metric,epsilon_A=None,tau_ps=None,
                                   comparison=hi+'-'+lo,high=c[hi][metric],low=c[lo][metric],difference=c[hi][metric]-c[lo][metric]))
        for eps,tau in itertools.product((1.5,2.,3.),(0,5)):
            d={r['arm']:r['added_regions'] for r in discrete if r['block']==block and r['burn_ps']==burn and r['prefix_ns']==prefix and r['epsilon_A']==eps and r['tau_ps']==tau}
            for hi,lo in [('F2','F1'),('F2','F0'),('F1','F0')]:
                paired.append(dict(block=block,burn_ps=burn,prefix_ns=prefix,metric='added_regions',epsilon_A=eps,tau_ps=tau,
                                   comparison=hi+'-'+lo,high=d[hi],low=d[lo],difference=d[hi]-d[lo]))
    dump(out/'paired-results.json',paired);table(out/'paired-results.csv',paired)
    costs=[]
    for folder in sorted((root/'tasks').iterdir()):
        req=json.loads((folder/'request.json').read_text());ex=json.loads((folder/'execution.json').read_text());tim=json.loads((folder/'science/timing.json').read_text())
        result=json.loads((folder/'science/result.json').read_text()) if (folder/'science/result.json').exists() else dict(status='failure',artifacts={})
        for n,expected in result['artifacts'].items():
            if sha(folder/'science'/n)!=expected:raise ValueError('原タスク出力SHAが変化しています。')
        costs.append(dict(**ex,status=result['status'],worker_wall_s=tim['worker_wall_s'],CPU_s=tim['cpu_s'],peak_worker_RSS_KiB=tim['peak_RSS_KiB'],
                          components={k:v for k,v in result.items() if k.endswith('_s')}))
    dump(out/'costs.json',costs)
    table(out/'costs.csv',[{k:v for k,v in c.items() if k not in ['components']} for c in costs])
    dump(out/'validation.json',dict(status='MEASURED',history_frames=len(a0),A0_features_sha256=a0sha,
        common_history_shared=True,completed_downstream_MD=6,downstream_MD_ns=24,common_history_MD_ns=4,
        full_trajectory_frames=sum(q['frames'] for q in quality),qualified_downstream_frames=sum(q['valid'] for q in quality),
        continuous_rows=len(continuous),discrete_rows=len(discrete),paired_rows=len(paired),
        GPU_occupation_s=sum(c['GPU_occupation_s'] for c in costs),task_execution_wall_s=sum(c['elapsed_s'] for c in costs),
        analysis_source_sha256=sha(__file__),plan_commit='0c92f6025bcde7a971994d9c515a1184abe83fbe',
        outcome_scope='探索的幾何代理、等MD量。固定壁時計の純利益ではない。',S2_final_review='INCOMPLETE',S3='NOT APPROVED'))
    figures(out)


def figures(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family']='Noto Sans CJK JP'
    data=json.loads((out/'continuous.json').read_text());paired=json.loads((out/'paired-results.json').read_text())
    fig,axs=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for block,ax in zip((1,2),axs):
        for arm in ['F0','F1','F2']:
            r=[v for v in data if v['block']==block and v['arm']==arm and v['burn_ps']==100]
            ax.plot([v['prefix_ns'] for v in r],[v['distance_mean_A'] for v in r],'o-',label=arm)
        ax.set_title(f'対応乱数ブロック{block}');ax.set_xlabel('下流MD物理時間 [ns]');ax.legend();ax.grid(alpha=.2)
    axs[0].set_ylabel('共通履歴への最小距離の平均 [Å]');fig.tight_layout();fig.savefig(out/'continuous-proxies.png',dpi=150);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for block,ax in zip((1,2),axs):
        for comp,marker in [('F2-F1','o'),('F2-F0','s'),('F1-F0','^')]:
            rows=[r for r in paired if r['block']==block and r['burn_ps']==100 and r['prefix_ns']==4 and r['metric']=='added_regions' and r['tau_ps']==5 and r['comparison']==comp]
            ax.plot([r['epsilon_A'] for r in rows],[r['difference'] for r in rows],marker+'-',label=comp)
        ax.axhline(0,color='gray',linewidth=.7);ax.set_xlabel('ε [Å]');ax.set_title(f'対応乱数ブロック{block}');ax.legend();ax.grid(alpha=.2)
    axs[0].set_ylabel('追加領域数の対応差（τ=5 ps）');fig.tight_layout();fig.savefig(out/'paired-regions.png',dpi=150);plt.close(fig)
    blocks=list(csv.DictReader((out/'time-blocks.csv').open()))
    fig,axs=plt.subplots(2,1,figsize=(9,7),sharex=True)
    for rblock,ax in zip((1,2),axs):
        for arm in ['F0','F1','F2']:
            r=[v for v in blocks if int(v['block'])==rblock and v['arm']==arm]
            ax.plot([float(v['start_ps'])/1000 for v in r],[float(v['distance_mean_A']) for v in r],label=arm)
        ax.set_ylabel(f'ブロック{rblock}\n平均最小距離 [Å]');ax.legend();ax.grid(alpha=.2)
    axs[-1].set_xlabel('下流MD物理時間 [ns]（100 ps窓）');fig.tight_layout();fig.savefig(out/'time-evolution.png',dpi=150);plt.close(fig)


if __name__=='__main__':
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='-1':raise RuntimeError('CPU解析ではGPUを不可視にしてください。')
    resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3))
    target=ROOT.parent/'artifacts/b1-pilot-20261026/analysis-v1'
    started=time.perf_counter();cpu=time.process_time()
    try:run(target)
    finally:
        if target.exists():dump(target/'analysis-runtime.json',dict(wall_s=time.perf_counter()-started,CPU_s=time.process_time()-cpu,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,GPU_compute=False))
