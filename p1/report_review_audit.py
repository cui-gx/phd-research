"""固定済みB1公開表をCPUで再照合し、報告用の派生表だけを別領域に作る。"""
from __future__ import annotations
import argparse
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import time
import numpy as np

METRICS = ('distance_mean_A','distance_median_A','distance_p90_A','Rg_mean_A','Q8_mean','angle_to_geometric_neighbor_median_deg')
COMPARISONS = ('F2-F1','F2-F0','F1-F0')
SEED = 1604000001


def digest(path):
    """入力証拠は変更せずSHAを読む。"""
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def key(row,metric=None):
    """CSVとJSONの空値を同じ指標キーへ正規化する。"""
    def number(v):return None if v in ('',None) else float(v)
    return (float(row['burn_ps']),float(row['prefix_ns']),metric or row['metric'],number(row.get('epsilon_A')),number(row.get('tau_ps')))


def spec(k):return dict(zip(('burn_ps','prefix_ns','metric','epsilon_A','tau_ps'),k))


def describe(values):
    """小標本の記述量。独立性や検出力を認定しない。"""
    a=np.asarray(values,float)
    return dict(n=len(a),mean=float(a.mean()),median=float(np.median(a)),minimum=float(a.min()),maximum=float(a.max()),SD=float(a.std(ddof=1)) if len(a)>1 else None)


def ranks(values):
    """同順位を平均順位にする。"""
    a=np.asarray(values,float);order=np.argsort(a,kind='stable');r=np.empty(len(a));i=0
    while i<len(a):
        j=i+1
        while j<len(a) and a[order[j]]==a[order[i]]:j+=1
        r[order[i:j]]=(i+j-1)/2;i=j
    return r


def correlation(x,y):
    """定数の場合を欠損とし、擬似的な相関を作らない。"""
    x,y=ranks(x),ranks(y)
    if x.std()==0 or y.std()==0:return None
    return float(np.corrcoef(x,y)[0,1])


def audit(input_dir,output_dir):
    """将来MD・モデル学習・推論を実行しない表の検証。"""
    begin=time.perf_counter();cpu=time.process_time();base=Path(input_dir);out=Path(output_dir)
    if out.exists():raise ValueError('既存の報告監査は上書きできません。別出力先を指定してください。')
    used={};checks={};errors={}
    def rows(name):
        p=base/name;used[name]=digest(p)
        with p.open() as f:return list(csv.DictReader(f))
    def load(name):
        p=base/name;used[name]=digest(p);return json.loads(p.read_text())
    def close(actual,expected,kind):
        error=abs(float(actual)-float(expected));errors[kind]=max(errors.get(kind,0.),error)
        if error>1e-10:raise ValueError('既存表との不一致：'+kind)
        checks[kind]=checks.get(kind,0)+1
    validation=load('validation.json');assert validation['completed_downstream']==240 and validation['top_level_independent_units']==8
    continuous=rows('continuous.csv');discrete=rows('discrete-counts.csv');pairs=rows('paired-effects.csv');states=rows('state-effects.csv');roots=rows('root-effects.csv');summaries=rows('root-summary.csv');times=rows('state-time-differences.csv')
    outcome={}
    for r in continuous:
        for metric in METRICS:outcome[(r['state_id'],r['arm'],int(r['training_block']),int(r['MD_block']),key(r,metric))]=float(r[metric])
    for r in discrete:outcome[(r['state_id'],r['arm'],int(r['training_block']),int(r['MD_block']),key(r,'added_regions'))]=float(r['added_regions'])
    pair_values={};f0_ids={}
    for r in pairs:
        k=key(r);high,low=r['comparison'].split('-');t,m=int(r['training_block']),int(r['MD_block']);sid=r['state_id']
        hi=outcome[(sid,high,t,m,k)];lo=outcome[(sid,low,0 if low=='F0' else t,m,k)]
        close(r['high'],hi,'pair_high');close(r['low'],lo,'pair_low');close(r['difference'],hi-lo,'pair_difference');assert r['status']=='MEASURED'
        pair_values[(sid,r['comparison'],t,m,k)]=hi-lo
        if low=='F0':
            assert r['shared_F0_branch_id']==f'{sid}-F0-t0-m{m}'
            f0_ids.setdefault((sid,r['comparison'],k),set()).add(r['shared_F0_branch_id'])
    assert all(len(v)==3 for v in f0_ids.values())
    state_values={}
    for r in states:
        k=key(r);values=[pair_values[(r['state_id'],r['comparison'],t,m,k)] for t in (1,2) for m in (1,2,3)]
        value=float(np.mean(values));close(r['mean_difference'],value,'state_mean');assert int(r['complete_pairs'])==6
        state_values[(r['root_id'],int(r['milestone_ns']),r['comparison'],k)]=value
    root_values={}
    for r in roots:
        k=key(r);v=(state_values[(r['root_id'],4,r['comparison'],k)]+state_values[(r['root_id'],8,r['comparison'],k)])/2
        close(r['mean_difference'],v,'root_mean');root_values[(r['root_id'],r['comparison'],k)]=v
    for r in times:
        k=key(r);v=state_values[(r['root_id'],8,r['comparison'],k)]-state_values[(r['root_id'],4,r['comparison'],k)]
        close(r['state8_minus_state4'],v,'state_time_difference')
    root_ids=[f'r{i:02d}' for i in range(1,9)];resampling=np.random.default_rng(SEED).integers(0,8,(10000,8))
    def interval(values):return [float(v) for v in np.quantile(np.asarray(values)[resampling].mean(axis=1),[.025,.975])]
    main=[];root_table=[]
    for r in summaries:
        k=key(r);v=[root_values[(rid,r['comparison'],k)] for rid in root_ids];ci=interval(v)
        close(r['mean'],np.mean(v),'global_mean');close(r['root_SD'],np.std(v,ddof=1),'root_SD');close(r['bootstrap95_low'],ci[0],'bootstrap_low');close(r['bootstrap95_high'],ci[1],'bootstrap_high');assert int(r['complete_roots'])==8
        if k[0]!=100 or k[1]!=4:continue
        s4=[state_values[(rid,4,r['comparison'],k)] for rid in root_ids];s8=[state_values[(rid,8,r['comparison'],k)] for rid in root_ids];delta=[b-a for a,b in zip(s4,s8)]
        main.append(dict(comparison=r['comparison'],**spec(k),global_mean=float(np.mean(v)),global_CI=ci,global_root_SD=float(np.std(v,ddof=1)),root_positive=int(np.sum(np.array(v)>0)),root_negative=int(np.sum(np.array(v)<0)),S4_mean=float(np.mean(s4)),S4_CI=interval(s4),S8_mean=float(np.mean(s8)),S8_CI=interval(s8),time_mean=float(np.mean(delta)),time_CI=interval(delta),time_positive=int(np.sum(np.array(delta)>0))))
        if k[2]=='distance_mean_A':
            root_table.extend(dict(root_id=rid,comparison=r['comparison'],S4=a,S8=b,root_mean=c,S8_minus_S4=b-a) for rid,a,b,c in zip(root_ids,s4,s8,v))
    noise=load('randomness-decomposition.json');noise_main=[]
    for r in noise:
        k=key(r);sid=r['state_id'];q=r['quantity']
        if q=='F0':
            x=np.array([outcome[(sid,'F0',0,m,k)] for m in (1,2,3)]);close(r['mean'],x.mean(),'noise_F0_mean');close(r['MD_SD'],x.std(ddof=1),'noise_F0_MD_SD')
        else:
            x=np.array([[pair_values[(sid,'F2-F1',t,m,k)] if q=='paired_F2-F1' else outcome[(sid,q,t,m,k)] for m in (1,2,3)] for t in (1,2)])
            row=x.mean(axis=1);col=x.mean(axis=0);res=x-row[:,None]-col[None,:]+x.mean()
            close(r['mean'],x.mean(),'noise_mean');close(r['training_mean_difference'],row[1]-row[0],'noise_training_difference');close(r['training_mean_SD'],row.std(ddof=1),'noise_training_SD');close(r['additive_residual_RMS'],np.sqrt(np.mean(res**2)),'noise_residual')
            for a,b in zip(r['MD_SD_by_training'],x.std(axis=1,ddof=1)):close(a,b,'noise_MD_SD')
        if k[0]==100 and k[1]==4 and k[2]=='distance_mean_A':noise_main.append(r)
    features=load('features.json');fmap={r['state_id']:r for r in features};diagnostics=rows('state-diagnostics.csv');variation=rows('feature-variation.csv');feature_summary=[]
    for r in diagnostics:
        milestone=int(r['milestone_ns']);xx=[fmap[f'{rid}-s{milestone}']['X'][r['feature']] for rid in root_ids];yy=[state_values[(rid,milestone,'F2-F1',(100.,4.,r['metric'],None if r['epsilon_A']=='' else float(r['epsilon_A']),None if r['tau_ps']=='' else float(r['tau_ps'])))] for rid in root_ids];ww=[fmap[f'{rid}-s{milestone}']['W']['grid_cells_total'] for rid in root_ids]
        for field,val in [('X_effect_spearman',correlation(xx,yy)),('X_W_grid_spearman',correlation(xx,ww))]:
            if val is None:assert r[field]==''
            else:close(r[field],val,'descriptive_correlation')
    for name in features[0]['X']:
        a=[fmap[f'{rid}-s4']['X'][name] for rid in root_ids];b=[fmap[f'{rid}-s8']['X'][name] for rid in root_ids]
        lo=max(min(a),min(b));hi=min(max(a),max(b));rows_here=[r for r in diagnostics if r['feature']==name and r['metric']=='distance_mean_A']
        feature_summary.append(dict(feature=name,S4=describe(a),S8=describe(b),range_intersection=[lo,hi] if lo<=hi else None,S4_in_other_range=sum(min(b)<=v<=max(b) for v in a),S8_in_other_range=sum(min(a)<=v<=max(a) for v in b),S4_rho=next((float(r['X_effect_spearman']) if r['X_effect_spearman'] else None) for r in rows_here if r['milestone_ns']=='4'),S8_rho=next((float(r['X_effect_spearman']) if r['X_effect_spearman'] else None) for r in rows_here if r['milestone_ns']=='8')))
    selection=rows('selection-comparisons.csv');selection_summary=[];selected={}
    for r in selection:
        t=int(r['training_block']);high,low=r['comparison'].split('-');selected[(r['state_id'],high,t)]=int(r['selected_high']);selected[(r['state_id'],low,0 if low=='F0' else t)]=int(r['selected_low'])
    for comparison in COMPARISONS:
        rr=[r for r in selection if r['comparison']==comparison]
        selection_summary.append(dict(comparison=comparison,pairs=len(rr),different_top1=sum(r['selected_high']!=r['selected_low'] for r in rr),dRMSD_A=describe([float(r['selected_dRMSD_A']) for r in rr]),angle_RMS_deg=describe([float(r['selected_angle_RMS_deg']) for r in rr]),overlap_top10=describe([json.loads(r['overlaps'])['10'] for r in rr]),overlap_top100=describe([json.loads(r['overlaps'])['100'] for r in rr])))
    models=load('models.json');mm={(r['state_id'],r['label']):r for r in models};checkpoints=load('checkpoint-readback.json');quality=load('quality.json');timeline=load('temporal-and-SHA-audit.json')
    for sid in fmap:
        m0=mm[(sid,'M0')]
        assert m0['optimizer_steps']==200 and m0['exposures']==800
        for t in (1,2):
            a,b=mm[(sid,f'F1-t{t}')],mm[(sid,f'F2-t{t}')]
            for k in ['initial_model_digest','initial_optimizer_digest','initial_rng_digest','optimizer_steps','exposures','parent_checkpoint_sha256']:assert a[k]==b[k]
            assert a['initial_model_digest']==m0['final_model_digest'] and a['initial_optimizer_digest']==m0['final_optimizer_digest'] and a['parent_checkpoint_sha256']==m0['checkpoint_sha256']
    assert len({mm[(sid,'M0')]['initial_model_digest'] for sid in fmap})==1
    for r in checkpoints:assert r['model_digest']==mm[(r['state_id'],r['label'])]['final_model_digest'] and r['optimizer_digest']==mm[(r['state_id'],r['label'])]['final_optimizer_digest']
    assert len(checkpoints)==80 and all(r['selected_coordinates_exact'] and r['qualified_frames']==r['frames']==8000 for r in quality)
    assert timeline['passed'] and not timeline['result_SHA_mismatches']
    costs=load('costs.json');groups={}
    for r in costs:
        kind=r['kind'];task=r['task']
        label=('history_MD' if '-h' in task else 'downstream_MD') if kind=='md' else ('inference' if '-infer-' in task else 'M0_training' if task.endswith('-M0') else 'additional_training') if kind=='ai' else kind
        groups.setdefault(label,[]).append(r)
    cost_summary=[]
    for label,rr in sorted(groups.items()):
        cost_summary.append(dict(category=label,count=len(rr),GPU_occupation_s=sum(r['GPU_occupation_s'] or 0 for r in rr),execution_wall_s=sum(r['execution_wall_s'] or 0 for r in rr),worker_CPU_s=sum(r['CPU_s'] or 0 for r in rr),wall_distribution=describe([r['execution_wall_s'] for r in rr]),fit_s=describe([r['components']['fit_s'] for r in rr]) if all('fit_s' in r['components'] for r in rr) else None))
    close(sum(r['GPU_occupation_s'] or 0 for r in costs),validation['GPU_occupation_s'],'GPU_total');close(sum(r['execution_wall_s'] or 0 for r in costs),validation['task_execution_wall_s'],'task_wall_total')
    # 元図の生成コードと同じ既定セルを索引化し、図の目視結果と照合する。
    fig_points={}
    chosen=[r for r in states if key(r)==(100.,4.,'distance_mean_A',None,None) and r['comparison']=='F2-F1']
    fig_points['root-state-effects.png']=[dict(root_id=r['root_id'],state_id=r['state_id'],x=int(r['root_id'][1:])+(-.12 if r['milestone_ns']=='4' else .12),y=float(r['mean_difference'])) for r in chosen]
    fig_points['feedback-diagnostic.png']=[dict(root_id=r['root_id'],state_id=r['state_id'],x=fmap[r['state_id']]['X']['new_nonrepeat_fraction_eps2'],y=float(r['mean_difference'])) for r in chosen]
    fig_points['multiscale-effects.png']=[dict(root_id=r['root_id'],state_id=r['state_id'],epsilon_A=float(r['epsilon_A']),tau_ps=5,x=int(r['root_id'][1:]),y=float(r['mean_difference'])) for r in states if r['comparison']=='F2-F1' and key(r)[0:3]==(100.,4.,'added_regions') and r['tau_ps']=='5']
    for name in fig_points:used[name]=digest(base/name)
    extra=[]
    for name in ['finalization-runtime.json','publication-runtime.json']:
        if (base/name).exists():extra.append(dict(name=name,record=load(name)))
    assert len(continuous)==2880 and len(discrete)==17280 and len(pairs)==41472 and len(states)==6912 and len(roots)==3456 and len(summaries)==432
    result=dict(status='DERIVED',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),role='既存表に対するCPU統計復核。原結果を置換しない。',python=platform.python_version(),numpy=np.__version__,code_SHA256=digest(__file__),input_SHA256=used,checks=checks,max_abs_errors=errors,main_comparisons=main,main_root_rows=root_table,main_noise_rows=noise_main,features=feature_summary,selection=selection_summary,training_seed_top1_changed={arm:sum(selected[(sid,arm,1)]!=selected[(sid,arm,2)] for sid in fmap) for arm in ('F1','F2')},model_records_verified=len(models),checkpoint_metadata_verified=len(checkpoints),quality_branches_verified=len(quality),cost_by_category=cost_summary,extra_runtime_records=extra,figure_points=fig_points,figure_SHA256={name:used[name] for name in fig_points},new_MD=0,new_training=0,new_GPU_inference=0,bootstrap_replicates=10000,bootstrap_seed=SEED,top_level_roots=8,wall_s=time.perf_counter()-begin,CPU_s=time.process_time()-cpu)
    out.mkdir(parents=True,exist_ok=False)
    (out/'review-statistics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (out/'main-root-effects.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(root_table[0]));w.writeheader();w.writerows(root_table)
    print(json.dumps(dict(status='PASS_既存集計との数値照合',checks=checks,max_abs_errors=errors,wall_s=result['wall_s'],output_files=['review-statistics.json','main-root-effects.csv']),ensure_ascii=False,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='既存B1表のCPU照合だけを行う。')
    parser.add_argument('--input-dir',type=Path,required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();audit(args.input_dir,args.output_dir)
