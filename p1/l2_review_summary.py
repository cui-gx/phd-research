"""事前契約の全条件から報告用の記述表とroot内対応差を作る。"""
import argparse
from pathlib import Path
import numpy as np
from p1.l2_engineering import read, rows, write, sha, runtime
from p1.l1_frozen_diagnostic import table

def main(a):
    runtime();public=a.output/'public';m=rows(public/'model-metrics.csv');g=rows(public/'geometry.csv');plan=rows(a.plan/'checkpoint-matrix.csv')
    gm={(r['checkpoint'],r['set']):r for r in g if r['scale']=='RAW'}
    overview=[]
    for arm in ['M0','F1','F2']:
        for step in ([0,200,400,800,1600] if arm=='M0' else [200,400,800,1600]):
            for label in ['OLD_VALIDATION','RECENT_HELDOUT']:
                for mask in ['ALL','NONLOCAL','LONG']:
                    rr=[r for r in m if r['arm']==arm and int(r['chain_steps'])==step and r['set']==label and r['mask']==mask];assert len(rr)==12
                    row=dict(arm=arm,chain_steps=step,set=label,mask=mask,models=12,roots=2,states=4)
                    for col in ['MODEL_BCE_per_frame','TRAIN_FREQUENCY_BCE_per_frame','OLD_FREQUENCY_BCE_per_frame','VALIDATION_LOO_BCE_per_frame','A_train','A_mean','KL_per_frame']:
                        row[col+'_mean']=float(np.mean([float(r[col]) for r in rr]))
                    row['A_train_positive']=sum(float(r['A_train'])>0 for r in rr)
                    row['mean_and_all_permutations_positive']=sum(float(r['A_mean'])>0 and all(float(r['A_perm_'+str(k)])>0 for k in [1,17,53,97,149]) for r in rr)
                    gg=[gm[(r['checkpoint'],label)] for r in rr]
                    for col in ['physical_knn_overlap','time_physical_knn_overlap','contact_physical_knn_overlap']:
                        row[col+'_mean']=float(np.mean([float(r[col]) for r in gg]))
                    row['RAW_K10_above_untrained']=sum(float(gm[(r['checkpoint'],label)]['physical_knn_overlap'])>float(gm[(r['state_id']+'-i'+r['init_id']+'-M0-step0000',label)]['physical_knn_overlap']) for r in rr)
                    overview.append(row)
    table(public/'overview.csv',overview)
    root=[]
    for state in ['r01-s4','r01-s8','r02-s4','r02-s8']:
        for step in [200,400,800,1600]:
            for label in ['OLD_VALIDATION','RECENT_HELDOUT']:
                for mask in ['ALL','NONLOCAL','LONG']:
                    rr=[r for r in m if r['state_id']==state and int(r['chain_steps'])==step and r['set']==label and r['mask']==mask]
                    one=dict(state_id=state,root_id=state[:3],step=step,set=label,mask=mask,initializations=3)
                    for field in ['MODEL_BCE_per_frame','A_train','A_mean','KL_per_frame']:
                        one['F2_minus_F1_'+field]=float(np.mean([float(r[field]) for r in rr if r['arm']=='F2'])-np.mean([float(r[field]) for r in rr if r['arm']=='F1']))
                    one['F2_minus_F1_RAW_K10']=float(np.mean([float(gm[(r['checkpoint'],label)]['physical_knn_overlap']) for r in rr if r['arm']=='F2'])-np.mean([float(gm[(r['checkpoint'],label)]['physical_knn_overlap']) for r in rr if r['arm']=='F1']))
                    root.append(one)
    table(public/'root-effects.csv',root)
    curves=[]
    for chain in rows(a.plan/'experiment-matrix.csv'):
        ll=rows(a.output/'chains'/chain['chain_id']/'loss-steps.csv');assert len(ll)==1600
        for epoch in range(1,9):
            rr=[r for r in ll if int(r['epoch'])==epoch];assert len(rr)==200
            one=dict(chain_id=chain['chain_id'],state_id=chain['state_id'],arm=chain['arm'],init_id=chain['init_id'],epoch=epoch,steps=200)
            for col in ['BCE_sum','KL_mean','raw_total','gradient_norm_before_clip']:
                vv=[float(r[col]) for r in rr];one[col+'_mean']=float(np.mean(vv));one[col+'_min']=min(vv);one[col+'_max']=max(vv)
            curves.append(one)
    table(public/'loss-curves.csv',curves)
    raw={str(p.relative_to(a.output)):sha(p) for parent in ['chains','evaluations','engineering'] for p in (a.output/parent).rglob('*') if p.is_file() and p.name!='run.lock'}
    write(public/'raw-output-sha256.json',raw)
    write(public/'output-sha256.json',{p.name:sha(p) for p in public.iterdir() if p.is_file() and p.name!='output-sha256.json'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);p.add_argument('output',type=Path);main(p.parse_args())
