"""B1拡張の枝別物理代理と根単位の探索的集計。サーバCPU用。"""
from __future__ import annotations
import csv
import itertools
import json
import time
from pathlib import Path
import numpy as np
from .gq_r2 import dump,sha,table,nearest,distances,regions,circular
from .expansion_contract import BOOTSTRAP_SEED

CONTINUOUS=('distance_mean_A','distance_median_A','distance_p90_A','Rg_mean_A','Q8_mean','angle_to_geometric_neighbor_median_deg')
COMPARISONS=(('F2','F1'),('F2','F0'),('F1','F0'))


def safe_correlation(x,y,rank=False):
    """定数・不足データの相関は欠損として保持する。"""
    if len(x)<2 or np.std(x)==0 or np.std(y)==0:return None
    if rank:
        from scipy.stats import spearmanr
        value=float(spearmanr(x,y).statistic)
    else:value=float(np.corrcoef(x,y)[0,1])
    return value if np.isfinite(value) else None


def analyze_branch(req,out):
    """一枝・一共通A0ずつ扱い、全保存点への厳密距離を保持する。"""
    a=dict(np.load(Path(req['prepared'])/'features.npz'));h=dict(np.load(Path(req['pool'])/'features.npz'))
    mask=(h['time_ps']>100)&h['valid'];a0=h['distances_A'][mask];angles0=h['angles_rad'][mask]
    if not np.array_equal(np.load(Path(req['md_dir'])/'initial-coordinates-A.npy'),np.load(req['selected'])):raise ValueError('選点と実MD入力が一致しません。')
    start=time.perf_counter();dd,nn=nearest(a['distances_A'],a0)
    check=distances(a['distances_A'][:16],a0[:64]).min(axis=1);split=nearest(a['distances_A'][:16],a0[:64],block=3)[0]
    err=float(np.max(np.abs(check-split)))
    if err>1e-12:raise ValueError('分割距離検査に失敗しました。')
    np.savez_compressed(out/'distances.npz',d_min_A=dd,nearest_A0_id=nn,time_ps=a['time_ps'],valid=a['valid'])
    angular=circular(a['angles_rad'],angles0[nn]);rows=[];discrete=[];windows=[]
    t=a['time_ps'];valid=a['valid']
    for burn,prefix in itertools.product((0,100,200,500),(1000,2000,4000)):
        m=(t>burn)&(t<=prefix+1e-5)&valid
        if not m.any():raise ValueError('適格な下流フレームがありません。')
        rows.append(dict(burn_ps=burn,prefix_ns=prefix/1000,frames=int(m.sum()),distance_mean_A=float(dd[m].mean()),
            distance_median_A=float(np.median(dd[m])),distance_p90_A=float(np.quantile(dd[m],.9)),Rg_mean_A=float(a['rg_A'][m].mean()),
            Q8_mean=float(a['q'][m].mean()),angle_to_geometric_neighbor_median_deg=float(np.median(angular[m]))))
        ii=np.flatnonzero((t>burn)&(t<=prefix+1e-5))[::4]
        for eps,tau in itertools.product((1.5,2.,3.),(0,5)):
            reps,conf=regions(a['distances_A'][ii],t[ii],eps,tau,valid=valid[ii],history_min_distance=dd[ii])
            rr=ii[reps];cc=ii[conf]
            discrete.append(dict(burn_ps=burn,prefix_ns=prefix/1000,epsilon_A=eps,tau_ps=tau,added_regions=len(reps),
                representative_frame_ids=rr.tolist(),confirmation_frame_ids=cc.tolist(),representative_time_ps=t[rr].tolist(),confirmation_time_ps=t[cc].tolist()))
    for lo in range(0,4000,100):
        m=(t>lo)&(t<=lo+100+1e-5)&valid
        if m.any():windows.append(dict(start_ps=lo,frames=int(m.sum()),distance_mean_A=float(dd[m].mean()),Rg_mean_A=float(a['rg_A'][m].mean()),Q8_mean=float(a['q'][m].mean())))
    autocorrelation=[]
    for name,value in [('Rg',a['rg_A']),('Q8',a['q']),('distance',dd)]:
        for lag in (1,4,20,200):
            m=valid[:-lag]&valid[lag:]&(t[:-lag]>100)
            autocorrelation.append(dict(observable=name,lag_ps=lag*.5,eligible_pairs=int(m.sum()),correlation=safe_correlation(value[:-lag][m],value[lag:][m]),
                scope='有限非定常系列の診断。独立フレーム数や平衡性の認定ではない。'))
    dump(out/'continuous.json',rows);table(out/'continuous.csv',rows);dump(out/'discrete.json',discrete)
    table(out/'discrete-counts.csv',[{k:v for k,v in r.items() if k in ('burn_ps','prefix_ns','epsilon_A','tau_ps','added_regions')} for r in discrete])
    table(out/'time-windows.csv',windows);dump(out/'autocorrelation.json',autocorrelation)
    return dict(branch=req['branch'],history_frames=len(a0),frames=len(t),qualified_frames=int(valid.sum()),A0_features_sha256=sha(Path(req['pool'])/'features.npz'),
                selected_coordinates_exact=True,small_exact_error_A=err,evaluation_s=time.perf_counter()-start,continuous_rows=len(rows),discrete_rows=len(discrete))


def metric_key(burn,prefix,metric,eps=None,tau=None):return (burn,prefix,metric,eps,tau)


def randomness_summary(values):
    """2×3セルの加法記述。純粋な交互作用分散と解釈しない。"""
    x=np.asarray(values,float)
    if x.shape!=(2,3):raise ValueError('2学習seed×3MDseedの行列が必要です。')
    row=x.mean(axis=1);col=x.mean(axis=0);grand=x.mean();residual=x-row[:,None]-col[None,:]+grand
    return dict(mean=float(grand),training_means=row.tolist(),training_mean_difference=float(row[1]-row[0]),
        training_mean_SD=float(row.std(ddof=1)),MD_SD_by_training=x.std(axis=1,ddof=1).tolist(),
        MD_column_means=col.tolist(),additive_residual_RMS=float(np.sqrt(np.mean(residual**2))),
        pure_interaction_variance_identified=False)


def finalize_campaign(run,art,matrix):
    """共有F0を保持し、根を再標本化して全予定セルを集計する。"""
    start=time.perf_counter();out=art/'summary-v1'
    if out.exists():raise ValueError('既存集計を上書きできません。新しい版が必要です。')
    out.mkdir();attempts=json.loads((run/'attempt-map.json').read_text()) if (run/'attempt-map.json').exists() else {}
    def science(name):return run/'tasks'/attempts.get(name,name)/'science'
    outcomes={};branch_status=[];quality=[];windows=[];correlations=[];continuous=[];discrete=[];features=[];selections=[];models=[]
    for state in matrix['states']:
        sid=state['state_id']
        if not (science(sid+'-features')/'state-features.json').exists():continue
        f=json.loads((science(sid+'-features')/'state-features.json').read_text());features.append(f)
        if not (science(sid+'-selection')/'selection-comparisons.json').exists():continue
        ss=json.loads((science(sid+'-selection')/'selection-comparisons.json').read_text())
        for r in ss:selections.append(dict(root_id=state['root_id'],state_id=sid,**{**r,'overlaps':json.dumps(r['overlaps'])}))
        for label in ['M0','F1-t1','F1-t2','F2-t1','F2-t2']:
            p=science(sid+'-'+label)
            if not (p/'result.json').exists():continue
            r=json.loads((p/'result.json').read_text());models.append(dict(root_id=state['root_id'],state_id=sid,label=label,**r))
    for b in matrix['branches']:
        bid=b['branch_id'];p=science(bid+'-analysis');success=(p/'result.json').exists()
        md_success=(science(bid+'-md')/'result.json').exists()
        branch_status.append(dict(**b,status='success' if success else 'missing',MD_status='success' if md_success else 'missing',analysis_status='success' if success else 'missing'))
        if not success:continue
        result=json.loads((p/'result.json').read_text());quality.append(result)
        for r in json.loads((p/'continuous.json').read_text()):
            continuous.append(dict(**b,**r))
            for metric in CONTINUOUS:outcomes[(b['state_id'],b['arm'],b['training_block'],b['MD_block'],metric_key(r['burn_ps'],r['prefix_ns'],metric))]=r[metric]
        for r in json.loads((p/'discrete.json').read_text()):
            small={k:v for k,v in r.items() if not isinstance(v,list)};discrete.append(dict(**b,**small))
            outcomes[(b['state_id'],b['arm'],b['training_block'],b['MD_block'],metric_key(r['burn_ps'],r['prefix_ns'],'added_regions',r['epsilon_A'],r['tau_ps']))]=r['added_regions']
        with (p/'time-windows.csv').open() as f:
            windows.extend(dict(**b,**r) for r in csv.DictReader(f))
        correlations.extend(dict(**b,**r) for r in json.loads((p/'autocorrelation.json').read_text()))
    keys=[metric_key(b,p,m) for b,p,m in itertools.product((0,100,200,500),(1.,2.,4.),CONTINUOUS)]
    keys += [metric_key(b,p,'added_regions',e,t) for b,p,e,t in itertools.product((0,100,200,500),(1.,2.,4.),(1.5,2.,3.),(0,5))]
    paired=[];state_effects=[];randomness=[]
    for state in matrix['states']:
        sid=state['state_id']
        for key in keys:
            spec=dict(zip(('burn_ps','prefix_ns','metric','epsilon_A','tau_ps'),key));state_differences={}
            for high,low in COMPARISONS:
                cell=[]
                for t,m in itertools.product((1,2),(1,2,3)):
                    hv=outcomes.get((sid,high,t,m,key));lv=outcomes.get((sid,low,0 if low=='F0' else t,m,key))
                    difference=hv-lv if hv is not None and lv is not None else None
                    paired.append(dict(root_id=state['root_id'],state_id=sid,training_block=t,MD_block=m,comparison=high+'-'+low,**spec,
                        high=hv,low=lv,difference=difference,status='MEASURED' if difference is not None else 'MISSING_PAIR',
                        shared_F0_branch_id=f'{sid}-F0-t0-m{m}' if low=='F0' else None))
                    cell.append(difference)
                full=all(v is not None for v in cell);mean=float(np.mean(cell)) if full else None
                state_effects.append(dict(root_id=state['root_id'],state_id=sid,milestone_ns=state['milestone_ns'],comparison=high+'-'+low,**spec,
                    mean_difference=mean,complete_pairs=sum(v is not None for v in cell),shared_F0_unique_observations=3 if low=='F0' else 0))
                state_differences[high+'-'+low]=mean
            delta=[outcomes.get((sid,'F2',t,m,key))-outcomes.get((sid,'F1',t,m,key)) if (sid,'F2',t,m,key) in outcomes and (sid,'F1',t,m,key) in outcomes else None for t,m in itertools.product((1,2),(1,2,3))]
            if all(v is not None for v in delta):randomness.append(dict(root_id=state['root_id'],state_id=sid,**spec,quantity='paired_F2-F1',**randomness_summary(np.array(delta).reshape(2,3))))
            for arm in ('F1','F2'):
                cell=[outcomes.get((sid,arm,t,m,key)) for t,m in itertools.product((1,2),(1,2,3))]
                if all(v is not None for v in cell):randomness.append(dict(root_id=state['root_id'],state_id=sid,**spec,quantity=arm,**randomness_summary(np.array(cell).reshape(2,3))))
            f0=[outcomes.get((sid,'F0',0,m,key)) for m in (1,2,3)]
            if all(v is not None for v in f0):randomness.append(dict(root_id=state['root_id'],state_id=sid,**spec,quantity='F0',mean=float(np.mean(f0)),MD_SD=float(np.std(f0,ddof=1)),unique_observations=3))
    lookup={(r['root_id'],r['milestone_ns'],r['comparison'],metric_key(*[r[k] for k in ('burn_ps','prefix_ns','metric','epsilon_A','tau_ps')])):r['mean_difference'] for r in state_effects}
    root_effects=[];time_effects=[];summary=[];rng=np.random.default_rng(BOOTSTRAP_SEED);resampling=rng.integers(0,8,(10000,8))
    for comp,key in itertools.product(('F2-F1','F2-F0','F1-F0'),keys):
        spec=dict(zip(('burn_ps','prefix_ns','metric','epsilon_A','tau_ps'),key));vv=[]
        for root in matrix['roots']:
            rid=root['root_id'];four=lookup.get((rid,4,comp,key));eight=lookup.get((rid,8,comp,key));complete=four is not None and eight is not None
            value=(four+eight)/2 if complete else None;vv.append(value)
            root_effects.append(dict(root_id=rid,comparison=comp,**spec,mean_difference=value,status='complete' if complete else 'missing'))
            time_effects.append(dict(root_id=rid,comparison=comp,**spec,state8_minus_state4=eight-four if complete else None))
        valid=np.array([v for v in vv if v is not None]);n=len(valid)
        draws=valid[resampling] if n==8 else valid[rng.integers(0,n,(10000,n))] if n else None
        bounds=np.quantile(draws.mean(axis=1),[.025,.975]).tolist() if n>=2 else [None,None]
        summary.append(dict(comparison=comp,**spec,complete_roots=n,expected_roots=8,mean=float(valid.mean()) if n else None,median=float(np.median(valid)) if n else None,
            minimum=float(valid.min()) if n else None,maximum=float(valid.max()) if n else None,root_SD=float(valid.std(ddof=1)) if n>=2 else None,
            bootstrap95_low=bounds[0],bootstrap95_high=bounds[1],scope='8根の探索的区間。功效・有意性・因果的Xを認定しない。'))
    diagnostics=[];feature_variation=[];fmap={f['state_id']:f for f in features}
    for milestone in (4,8):
        states=[s for s in matrix['states'] if s['milestone_ns']==milestone and s['state_id'] in fmap]
        if not states:continue
        for xname in (features[0]['X'] if features else []):
            xx=[fmap[s['state_id']]['X'][xname] for s in states];finite=all(v is not None for v in xx)
            feature_variation.append(dict(milestone_ns=milestone,feature=xname,count=len(xx),minimum=min(xx) if finite else None,maximum=max(xx) if finite else None,SD=float(np.std(xx,ddof=1)) if finite else None,
                constant_observed=bool(np.std(xx)==0) if finite else None))
            if not finite:continue
            ww=[fmap[s['state_id']]['W']['grid_cells_total'] for s in states]
            for key in keys:
                if key[0]!=100 or key[1]!=4:continue
                yy=[lookup[(s['root_id'],milestone,'F2-F1',key)] for s in states]
                pairs=[(x,y) for x,y in zip(xx,yy) if y is not None]
                diagnostics.append(dict(milestone_ns=milestone,feature=xname,metric=key[2],epsilon_A=key[3],tau_ps=key[4],roots=len(pairs),
                    X_effect_spearman=safe_correlation(*zip(*pairs),rank=True) if len(pairs)>=2 else None,
                    X_W_grid_spearman=safe_correlation(xx,ww,rank=True),scope='時刻内の記述的関連。Z/W条件付き増分予測・因果性ではない。'))
    costs=[];failures=[];raw_sha={};history_ns=0;GPU_samples=[]
    for task in sorted((run/'tasks').iterdir()):
        ex=json.loads((task/'execution.json').read_text()) if (task/'execution.json').exists() else {}
        timing=json.loads((task/'science/timing.json').read_text()) if (task/'science/timing.json').exists() else {}
        success=(task/'science/result.json').exists();req=json.loads((task/'request.json').read_text());result=json.loads((task/'science/result.json').read_text()) if success else {}
        if success and any(sha(task/'science'/n)!=h for n,h in result['artifacts'].items()):raise ValueError('最終原データSHA検査が不一致です。')
        if success and req['kind']=='md' and '-h' in task.name:history_ns+=req['length_ns']
        costs.append(dict(task=task.name,kind=req['kind'],status='success' if success else 'failure',GPU_occupation_s=ex.get('GPU_occupation_s'),execution_wall_s=ex.get('elapsed_s'),CPU_s=timing.get('cpu_s'),peak_RSS_KiB=timing.get('peak_RSS_KiB'),components={k:v for k,v in result.items() if k.endswith('_s')}))
        telemetry=task/'telemetry.jsonl'
        if telemetry.exists():
            samples=[]
            for line in telemetry.read_text().splitlines():
                info=json.loads(line).get('GPU_diagnostic')
                if not info or info['query_returncode']:continue
                vals=info['utilization_memory_power'].split(',')
                if len(vals)!=3:continue
                try:samples.append([float(v.strip()) for v in vals])
                except ValueError:continue
            if samples:
                values=np.array(samples);GPU_samples.append(dict(task=task.name,status='success' if success else 'failure',samples=len(samples),utilization_arithmetic_mean_percent=float(values[:,0].mean()),memory_max_MiB=float(values[:,1].max()),power_mean_W=float(values[:,2].mean()),scope='約1秒間隔の全GPU診断。kernel活動時間の積分ではない。'))
        if not success:failures.append(dict(task=task.name,request_sha256=sha(task/'request.json'),failure_class='requires_inspection'))
        for f in task.rglob('*'):
            if f.is_file() and 'runtime-cache' not in f.parts:raw_sha[str(f.relative_to(run))]=sha(f)
    for name,rows in [('branch-status',branch_status),('continuous',continuous),('discrete-counts',discrete),('time-windows',windows),('paired-effects',paired),('state-effects',state_effects),('root-effects',root_effects),('state-time-differences',time_effects),('root-summary',summary),('state-diagnostics',diagnostics),('feature-variation',feature_variation),('selection-comparisons',selections)]:
        if rows:table(out/(name+'.csv'),rows)
    dump(out/'randomness-decomposition.json',randomness);dump(out/'features.json',features);dump(out/'models.json',models);dump(out/'quality.json',quality);dump(out/'autocorrelation.json',correlations);dump(out/'costs.json',costs);dump(out/'failures.json',failures);dump(out/'raw-artifact-sha256.json',raw_sha)
    validation=dict(status='MEASURED',expected_roots=8,expected_states=16,expected_downstream=240,completed_downstream=sum(v['status']=='success' for v in branch_status),completed_downstream_MD=sum(v['MD_status']=='success' for v in branch_status),
        downstream_MD_ns=4*sum(v['status']=='success' for v in branch_status),common_history_MD_ns=history_ns,completed_states=len(features),qualified_frames=sum(v['qualified_frames'] for v in quality),
        GPU_occupation_s=sum(v['GPU_occupation_s'] or 0 for v in costs),task_execution_wall_s=sum(v['execution_wall_s'] or 0 for v in costs),
        success_tasks=sum(v['status']=='success' for v in costs),failed_tasks=len(failures),top_level_independent_units=len({v['root_id'] for v in features}),
        F0_shared_observations_not_duplicated=True,C_predictor_trained=False,B2_executed=False,S3='NOT APPROVED',
        analysis_s=time.perf_counter()-start,analysis_source_sha256=sha(__file__))
    audit=audit_timeline(run,matrix);dump(out/'temporal-and-SHA-audit.json',audit);validation['temporal_and_SHA_audit_passed']=audit['passed']
    if GPU_samples:table(out/'GPU-diagnostics.csv',GPU_samples)
    dump(out/'validation.json',validation);make_figures(out,state_effects,root_effects,fmap)
    return validation



def audit_timeline(run,matrix):
    """実イベントから未来データ・結果SHA・状態凍結の順序を再検査する。"""
    events=[json.loads(line) for line in (run/'events.jsonl').read_text().splitlines()] if (run/'events.jsonl').exists() else []
    available={e['task']:e for e in events if e['kind']=='task_output_available'}
    dispatched={e['task']:e for e in events if e['kind']=='task_dispatched'}
    frozen={e['state']:e for e in events if e['kind']=='decision_state_frozen'}
    origin=json.loads((run/'manifest.json').read_text())['monotonic_origin'] if (run/'manifest.json').exists() else 0
    mismatches=[];states=[]
    for name,e in available.items():
        p=run/'tasks'/e.get('actual_task',name)/'science/result.json'
        if not p.exists() or sha(p)!=e['result_sha256']:mismatches.append(name)
    for s in matrix['states']:
        sid=s['state_id'];m0=available.get(sid+'-M0');new=dispatched.get(f"{s['root_id']}-h{2 if s['milestone_ns']==4 else 4}-md")
        before_new=bool(m0 and new and m0['at_s']<new['at_s']);fp=run/'states'/(sid+'.json');freeze=frozen.get(sid)
        freeze_ok=bool(freeze and fp.exists() and sha(fp)==freeze['sha256'])
        x=run/'tasks'/(sid+'-features')/'science/state-features.json'
        # 修復attemptの場合は元の凍結ファイルが参照するハッシュとイベントを保持する。
        attempts=json.loads((run/'attempt-map.json').read_text()) if (run/'attempt-map.json').exists() else {}
        x=run/'tasks'/attempts.get(sid+'-features',sid+'-features')/'science/state-features.json'
        order=False
        if x.exists() and fp.exists():
            v=json.loads(x.read_text());f=json.loads(fp.read_text())
            branch=[e['at_s'] for n,e in dispatched.items() if n.startswith(sid+'-') and (n.startswith(sid+'-F1-') or n.startswith(sid+'-F2-') or n.startswith(sid+'-infer-'))]
            order=bool(branch and v['inputs_available_monotonic']<=v['feature_start_monotonic']<=v['feature_end_monotonic']<=f['frozen_monotonic']<=origin+min(branch))
        states.append(dict(state_id=sid,M0_before_new_MD=before_new,state_freeze_sha_matches=freeze_ok,features_before_branches=order))
    return dict(passed=bool(events) and not mismatches and all(all(v for k,v in r.items() if k!='state_id') for r in states),result_SHA_mismatches=mismatches,states=states,source='保存イベントと凍結ファイルを最終時に再読した診断')


def make_figures(out,effects,root_effects,features):
    """集計表だけから日本語の審査用図を生成する。"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family']='Noto Sans CJK JP'
    chosen=[r for r in effects if r['metric']=='distance_mean_A' and r['burn_ps']==100 and r['prefix_ns']==4 and r['comparison']=='F2-F1' and r['mean_difference'] is not None]
    fig,ax=plt.subplots(figsize=(9,4))
    for milestone,offset in [(4,-.12),(8,.12)]:
        rows=[r for r in chosen if r['milestone_ns']==milestone];ax.scatter([int(r['root_id'][1:])+offset for r in rows],[r['mean_difference'] for r in rows],label=f'{milestone} ns状態')
    ax.axhline(0,color='gray');ax.set(xlabel='独立履歴根',ylabel='F2−F1 平均最小距離差 [Å]');ax.legend();fig.tight_layout();fig.savefig(out/'root-state-effects.png',dpi=150);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for milestone,ax in zip((4,8),axs):
        rows=[r for r in chosen if r['milestone_ns']==milestone];ax.scatter([features[r['state_id']]['X']['new_nonrepeat_fraction_eps2'] for r in rows],[r['mean_difference'] for r in rows])
        for r in rows:ax.annotate(r['root_id'],(features[r['state_id']]['X']['new_nonrepeat_fraction_eps2'],r['mean_difference']))
        ax.axhline(0,color='gray');ax.set(title=f'{milestone} ns状態：記述的関連',xlabel='新データ非重複割合（ε=2 Å）',ylabel='F2−F1 平均距離差 [Å]')
    fig.tight_layout();fig.savefig(out/'feedback-diagnostic.png',dpi=150);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(10,4))
    for milestone,ax in zip((4,8),axs):
        for eps in (1.5,2.,3.):
            rows=[r for r in effects if r['milestone_ns']==milestone and r['metric']=='added_regions' and r['burn_ps']==100 and r['prefix_ns']==4 and r['tau_ps']==5 and r['epsilon_A']==eps and r['comparison']=='F2-F1' and r['mean_difference'] is not None]
            ax.plot([int(r['root_id'][1:]) for r in rows],[r['mean_difference'] for r in rows],'o-',label=f'ε={eps} Å')
        ax.axhline(0,color='gray');ax.set(title=f'{milestone} ns状態',xlabel='独立履歴根',ylabel='追加領域数の平均対応差');ax.legend()
    fig.tight_layout();fig.savefig(out/'multiscale-effects.png',dpi=150);plt.close(fig)
