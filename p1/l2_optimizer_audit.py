"""RMSprop実stateのstepをmetadataから独立に照合する。前向計算はしない。"""
import argparse
from pathlib import Path
import time
from p1.l2_engineering import read,rows,write,runtime,sha
from p1.l1_frozen_diagnostic import table

def main(a):
    runtime()
    import torch
    torch.set_num_threads(1);start=time.monotonic();result=[]
    for cp in rows(a.plan/'checkpoint-matrix.csv'):
        assert time.monotonic()-start<300
        path=a.output/'chains'/cp['chain_id']/(cp['checkpoint_id']+'.pt')
        r=read(path.parent/'result.json');assert sha(path)==r['checkpoints'][path.name]
        saved=torch.load(path,map_location='cpu',weights_only=False);opt=saved['optimizer_state_dict']
        steps=[float(v['step']) for v in opt['state'].values() if 'step' in v]
        expected=int(cp['lifetime_optimizer_steps'])
        assert (not steps and expected==0) or (steps and all(x==expected for x in steps)),cp['checkpoint_id']
        assert all(g['lr']==0.001 and g['weight_decay']==0.00001 for g in opt['param_groups'])
        result.append(dict(checkpoint=cp['checkpoint_id'],expected_lifetime_steps=expected,optimizer_state_entries=len(opt['state']),parameters=sum(len(g['params']) for g in opt['param_groups']),actual_step_min=min(steps) if steps else None,actual_step_max=max(steps) if steps else None,step0_empty=not steps,hyperparameters_match=True))
    pub=a.output/'public';target=pub/'optimizer-step-audit.csv';assert not target.exists();table(target,result)
    write(pub/'optimizer-step-integrity.json',dict(status='PASS',checkpoints=len(result),actual_RMSprop_state_counters_match=True,new_forward=0,new_optimizer_steps=0,wall_s=time.monotonic()-start))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('plan',type=Path);p.add_argument('output',type=Path);main(p.parse_args())
