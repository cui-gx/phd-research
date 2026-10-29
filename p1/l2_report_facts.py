"""固定指標の全結果から判定用の記述集計を作る。科学実行は追加しない。"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
import statistics
from p1.l2_engineering import rows,write,runtime,sha
from p1.l1_frozen_diagnostic import table

def main(a):
    runtime();p=a.output/'public';m=rows(p/'model-metrics.csv');g=rows(p/'geometry.csv');stable=rows(p/'representation-stability.csv');lof=rows(p/'LOF-comparisons.csv')
    gm={(r['checkpoint'],r['set']):r for r in g if r['scale']=='RAW'}
    mm={(r['checkpoint'],r['set'],r['mask']):r for r in m}
    checkpoints={r['checkpoint']:r for r in m};checks=[];decision=[]
    numeric_count=0;NA=[]
    for name in ['model-metrics.csv','geometry.csv','latent.csv','paired-contrasts.csv','representation-stability.csv','LOF-comparisons.csv']:
        for i,r in enumerate(rows(p/name),2):
            for key,v in r.items():
                if v=='':NA.append(dict(file=name,line=i,column=key));continue
                try:f=float(v)
                except ValueError:continue
                assert math.isfinite(f),(name,i,key);numeric_count+=1
    for arm in ['M0','F1','F2']:
        selected=[r for r in m if r['arm']==arm and r['chain_steps']=='1600' and r['mask'] in ['NONLOCAL','LONG']]
        assert len(selected)==48
        for r in selected:
            uid=r['state_id']+'-i'+r['init_id']+'-M0-step0000'
            geom_delta=float(gm[(r['checkpoint'],r['set'])]['physical_knn_overlap'])-float(gm[(uid,r['set'])]['physical_knn_overlap'])
            one=dict(checkpoint=r['checkpoint'],arm=arm,state_id=r['state_id'],init_id=r['init_id'],set=r['set'],mask=r['mask'],A_train=float(r['A_train']),A_mean=float(r['A_mean']),minimum_A_perm=min(float(r['A_perm_'+str(k)]) for k in [1,17,53,97,149]),K10_minus_untrained=geom_delta)
            one['reconstruction_advantage']=one['A_train']>0
            one['input_dependence_all_controls']=one['A_mean']>0 and one['minimum_A_perm']>0
            one['geometry_above_untrained']=geom_delta>0
            one['joint_directional_support']=all(one[k] for k in ['reconstruction_advantage','input_dependence_all_controls','geometry_above_untrained'])
            decision.append(one)
        rr=[r for r in decision if r['arm']==arm]
        checks.append(dict(arm=arm,cells=48,reconstruction_cells=sum(r['reconstruction_advantage'] for r in rr),input_dependence_cells=sum(r['input_dependence_all_controls'] for r in rr),geometry_cells=sum(r['geometry_above_untrained'] for r in rr),joint_cells=sum(r['joint_directional_support'] for r in rr),claim='LIMITED_DIRECTIONAL_SUPPORT' if all(r['joint_directional_support'] for r in rr) else 'PARTIAL_INCONCLUSIVE',learning_convergence='UNVERIFIED'))
    table(p/'decision-cells.csv',decision);write(p/'qualification-checks.json',checks)
    improvements=[]
    for arm in ['M0','F1','F2']:
        for label in ['OLD_VALIDATION','RECENT_HELDOUT']:
            for mask in ['ALL','NONLOCAL','LONG']:
                rr=[r for r in m if r['arm']==arm and r['chain_steps']=='1600' and r['set']==label and r['mask']==mask]
                diffs=[]
                for r in rr:
                    lo=r['checkpoint'].replace('step1600','step0200');before=mm[(lo,label,mask)]
                    diffs.append((float(r['MODEL_BCE_per_frame'])-float(before['MODEL_BCE_per_frame']),float(gm[(r['checkpoint'],label)]['physical_knn_overlap'])-float(gm[(lo,label)]['physical_knn_overlap'])))
                improvements.append(dict(arm=arm,set=label,mask=mask,models=12,BCE_1600_minus_200_mean=statistics.fmean(x[0] for x in diffs),K10_1600_minus_200_mean=statistics.fmean(x[1] for x in diffs),BCE_improved=sum(x[0]<0 for x in diffs),K10_improved=sum(x[1]>0 for x in diffs),both_improved=sum(x[0]<0 and x[1]>0 for x in diffs)))
    table(p/'step-improvement-summary.csv',improvements)
    effects=[]
    for step in [200,400,800,1600]:
        for label in ['OLD_VALIDATION','RECENT_HELDOUT']:
            for mask in ['ALL','NONLOCAL','LONG']:
                rr=[r for r in m if r['arm']=='F2' and int(r['chain_steps'])==step and r['set']==label and r['mask']==mask]
                dd=[]
                for r in rr:
                    right=r['checkpoint'].replace('-F2-','-F1-');other=mm[(right,label,mask)]
                    dd.append((float(r['MODEL_BCE_per_frame'])-float(other['MODEL_BCE_per_frame']),float(gm[(r['checkpoint'],label)]['physical_knn_overlap'])-float(gm[(right,label)]['physical_knn_overlap'])))
                effects.append(dict(step=step,set=label,mask=mask,paired_models=12,BCE_F2_minus_F1_mean=statistics.fmean(x[0] for x in dd),BCE_min=min(x[0] for x in dd),BCE_max=max(x[0] for x in dd),BCE_F2_lower=sum(x[0]<0 for x in dd),BCE_F2_higher=sum(x[0]>0 for x in dd),K10_F2_minus_F1_mean=statistics.fmean(x[1] for x in dd),K10_min=min(x[1] for x in dd),K10_max=max(x[1] for x in dd),K10_F2_higher=sum(x[1]>0 for x in dd),joint_F2_better=sum(x[0]<0 and x[1]>0 for x in dd)))
    table(p/'update-effects-summary.csv',effects)
    groups=defaultdict(list)
    for r in stable:
        if r['kind']=='INITIALIZATION':
            meta=checkpoints[r['left']];groups[(meta['arm'],meta['chain_steps'],r['set'])].append(r)
    ist=[]
    for (arm,step,label),rr in groups.items():
        valid=[float(r['latent_distance_spearman']) for r in rr if r['latent_distance_spearman']!=''];vv=[float(r['knn_overlap']) for r in rr]
        ist.append(dict(arm=arm,step=int(step),set=label,dependent_pairs=len(rr),distance_rank_valid_pairs=len(valid),distance_rank_mean=statistics.fmean(valid) if valid else None,knn_mean=statistics.fmean(vv),knn_min=min(vv),knn_max=max(vv)))
    table(p/'initialization-summary.csv',ist)
    groups=defaultdict(list)
    for r in lof:
        l=checkpoints[r['left']];right=checkpoints[r['right']]
        groups[(r['kind'],l['arm'],right['arm'],l['chain_steps'],right['chain_steps'])].append(r)
    ls=[]
    for (kind,left,right,step,rs),rr in groups.items():
        ss=[float(r['score_spearman']) for r in rr if r['score_spearman']!=''];dd=[float(r['Top1_distance_A']) for r in rr]
        ls.append(dict(kind=kind,left_arm=left,right_arm=right,left_step=int(step),right_step=int(rs),dependent_pairs=len(rr),Top1_identical=sum(r['Top1_identical']=='True' for r in rr),Top10_overlap_mean=statistics.fmean(float(r['Top10_overlap']) for r in rr),Top100_overlap_mean=statistics.fmean(float(r['Top100_overlap']) for r in rr),score_rank_valid_pairs=len(ss),score_rank_mean=statistics.fmean(ss) if ss else None,Top1_distance_A_mean=statistics.fmean(dd),Top1_distance_A_min=min(dd),Top1_distance_A_max=max(dd),downstream_MD='NOT_OBSERVED'))
    assert sum(r['dependent_pairs'] for r in ls)==660
    table(p/'LOF-summary.csv',ls)
    write(p/'numeric-validation.json',dict(status='PASS',numeric_cells_checked=numeric_count,nonfinite_numeric_cells=0,blank_cells=len(NA),blank_cell_index=NA,blanks_meaning='非該当class条件または定数距離/scoreの未定義相関。欠測モデルを意味しない。',scientific_units_missing=0))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);main(p.parse_args())
