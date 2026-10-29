"""L2全checkpointの系譜・実exposure・RNGを前向なしで照合する。"""
import argparse
import json
from pathlib import Path
import time
from p1.l2_engineering import read, rows, sha, write, runtime

def audit(a):
    runtime()
    import numpy as np
    import torch
    from p1.l1_frozen_diagnostic import tensor_digest,opt_digest,table
    torch.set_num_threads(1);begin=time.monotonic()
    original=read(a.output/'engineering/input-freeze.json')['original_file_sha256'];raw=a.project/'runs/b1-expansion-20261026'
    for rel,h in original.items():assert sha(raw/rel)==h
    matrix=rows(a.plan/'checkpoint-matrix.csv');chains=rows(a.plan/'experiment-matrix.csv');data={};auditrows=[]
    memberships=rows(a.plan/'training-membership.csv');initial={}
    for cp in matrix:
        assert time.monotonic()-begin<300,'監査300秒復核点'
        path=a.output/'chains'/cp['chain_id']/(cp['checkpoint_id']+'.pt');result=read(path.parent/'result.json')
        assert sha(path)==result['checkpoints'][path.name]
        s=torch.load(path,map_location='cpu',weights_only=False)
        assert tensor_digest(s['model_state_dict'])==s['model_digest']
        assert opt_digest(torch,s['optimizer_state_dict'])==s['optimizer_digest']
        assert s['chain_steps']==int(cp['chain_steps']) and s['lifetime_steps']==int(cp['lifetime_optimizer_steps'])
        assert all(bool(torch.isfinite(v).all()) for v in s['model_state_dict'].values())
        assert len(s['rng']['torch_cuda'])==1
        if int(cp['chain_steps'])==0:
            k=cp['init_id'];h=s['model_digest']
            if k in initial:assert initial[k]==h
            initial[k]=h
        data[(cp['chain_id'],int(cp['chain_steps']))]=(s['model_digest'],s['optimizer_digest'],opt_digest(torch,s['rng']))
        auditrows.append(dict(checkpoint=cp['checkpoint_id'],sha256=sha(path),chain_steps=s['chain_steps'],lifetime_steps=s['lifetime_steps'],tensor_digest_matches=True,optimizer_digest_matches=True,RNG_digest=data[(cp['chain_id'],int(cp['chain_steps']))][2]))
    assert len(set(initial.values()))==3
    parentrows=[]
    for r in chains:
        folder=a.output/'chains'/r['chain_id'];result=read(folder/'result.json')
        exp=rows(folder/'exposures.csv');loss=rows(folder/'loss-steps.csv');assert len(exp)==6400 and len(loss)==1600
        ids=[int(v['frame_id_0based']) for v in memberships if v['state_id']==r['state_id'] and v['arm']==r['arm']]
        gen=np.random.default_rng(int(r['permutation_seed']))
        for epoch in range(1,9):
            rr=[v for v in exp if int(v['epoch'])==epoch];order=gen.permutation(800)
            assert [int(v['position']) for v in rr]==order.tolist()
            assert [int(v['frame_id']) for v in rr]==np.array(ids)[order].tolist()
        if r['arm']!='M0':
            parent=a.output/'chains'/r['parent_checkpoint'].rsplit('-step',1)[0]/(r['parent_checkpoint']+'.pt')
            assert result['parent_sha256']==sha(parent)
            assert result['initial_parent_model_digest']==data[(r['parent_checkpoint'].rsplit('-step',1)[0],200)][0]
            parentrows.append(dict(chain_id=r['chain_id'],parent_sha256=sha(parent),initial_parent_model_matches=True))
    rngpairs=[]
    for st in ['r01-s4','r01-s8','r02-s4','r02-s8']:
        for i in [1,2,3]:
            for step in [200,400,800,1600]:
                left=data[(f'{st}-i{i}-F1',step)][2];right=data[(f'{st}-i{i}-F2',step)][2]
                assert left==right,'F1/F2同歩数RNG不一致'
                rngpairs.append(dict(state_id=st,init_id=i,step=step,F1_F2_RNG_equal=True,RNG_digest=left))
    pub=a.output/'audit';pub.mkdir(exist_ok=False)
    table(pub/'checkpoint-lineage.csv',auditrows);table(pub/'parent-audit.csv',parentrows);table(pub/'RNG-pair-audit.csv',rngpairs)
    write(pub/'integrity.json',dict(status='PASS',original_files_rehashed=len(original),checkpoints=156,parent_pairs=24,F1_F2_RNG_pairs=48,exposure_rows=230400,loss_rows=57600,independent_initial_weights=3,
          initial_child_RNG_direct_snapshot='NOT_SAVED_at_step0; identical reseeding is source-controlled; actual saved same-step F1/F2 RNGs were compared',wall_s=time.monotonic()-begin))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path);audit(p.parse_args())
