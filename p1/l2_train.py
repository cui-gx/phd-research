"""固定L2行列の一chainだけを実行し、親・乱数・全中間点を保存する。"""
import argparse
import copy
import csv
import fcntl
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import time

from p1.l2_engineering import DESIGN, read, rows, sha, write


def execute(a):
    import numpy as np
    import torch
    from torch.utils.data import DataLoader, TensorDataset
    from p1.server.science import _trainer, load_config
    from p1.l1_frozen_diagnostic import tensor_digest, opt_digest
    assert a.project.resolve() in a.output.resolve().parents
    assert read(a.output/'engineering/engineering-check.json')['status']=='PASS'
    freeze=read(a.output/'engineering/input-freeze.json')
    assert freeze['status']=='PASS'
    receipt=read(a.output/'execution-release.json')
    assert receipt['design_commit']==DESIGN and receipt['remote_readback']=='PASS'
    assert receipt['train_adapter_sha256']==sha(Path(__file__))
    assert all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'])
    assert os.environ['CUDA_VISIBLE_DEVICES']=='0'
    gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip()
    assert not gpu, 'GPU使用プロセスあり。開始せず停止。'
    os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    lock=(a.output/'training.run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    matrix=rows(a.plan/'experiment-matrix.csv');r=next(v for v in matrix if v['chain_id']==a.chain)
    dest=a.output/'chains'/a.chain;dest.mkdir(parents=True,exist_ok=False)
    start=time.monotonic();cpu=time.process_time()
    ledger=read(a.output/'cost-ledger.json') if (a.output/'cost-ledger.json').exists() else []
    def guard():
        assert time.monotonic()-start<300,'単工程300秒復核点'
        assert sum(v['wall_s'] for v in ledger)+time.monotonic()-start<7200,'累計2時間復核点'
        rss=int(Path('/proc/self/status').read_text().split('VmRSS:')[1].split()[0])*1024
        assert rss<=2*1024**3,'RSS2GiB超過'
        assert torch.cuda.memory_reserved()<=8*1024**3,'GPU reserved8GiB超過'
        assert sum(p.stat().st_size for p in a.output.rglob('*') if p.is_file())<=2*1024**3,'出力2GiB超過'
    raw=a.project/'runs/b1-expansion-20261026'
    source=raw/'tasks'/(r['state_id']+'-decision-pool')/'science/contacts.npy'
    assert sha(source)==freeze['original_file_sha256'][str(source.relative_to(raw))]
    contacts=np.load(source,allow_pickle=True)
    ids=np.array([int(v['frame_id_0based']) for v in rows(a.plan/'training-membership.csv') if v['state_id']==r['state_id'] and v['arm']==r['arm']])
    x=np.zeros((800,1,28,28),dtype=np.float32)
    for i,ident in enumerate(ids):
        ij=contacts[ident].reshape(2,-1);x[i,0,ij[0],ij[1]]=1
    trainer,_=_trainer(dict(science_config=load_config(),device='cuda',seed=int(r['init_seed']),cpu_threads=1))
    parent=None
    if r['arm']!='M0':
        parent=a.output/'chains'/r['parent_checkpoint'].rsplit('-step',1)[0]/(r['parent_checkpoint']+'.pt')
        parent_manifest=read(parent.parent/'result.json')
        assert sha(parent)==parent_manifest['checkpoints'][parent.name]
        saved=torch.load(parent,map_location='cpu',weights_only=False)
        assert saved['chain_steps']==200 and saved['arm']=='M0'
        trainer.model.load_state_dict(saved['model_state_dict'],strict=True)
        trainer.optimizer.load_state_dict(saved['optimizer_state_dict'])
        assert tensor_digest(trainer.model.state_dict())==saved['model_digest']
        assert opt_digest(torch,trainer.optimizer.state_dict())==saved['optimizer_digest']
    seed=int(r['optimization_seed']);random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    order_rng=np.random.default_rng(int(r['permutation_seed']))
    loader_rng=torch.Generator().manual_seed(seed)
    def snapshot(step):
        torch.cuda.synchronize();guard()
        saved=copy.deepcopy(dict(model_state_dict=trainer.model.state_dict(),optimizer_state_dict=trainer.optimizer.state_dict(),
            chain_id=a.chain,arm=r['arm'],chain_steps=step,lifetime_steps=step+(200 if parent else 0),
            model_digest=tensor_digest(trainer.model.state_dict()),optimizer_digest=opt_digest(torch,trainer.optimizer.state_dict()),
            rng=dict(python=random.getstate(),numpy=np.random.get_state(),torch_cpu=torch.get_rng_state(),torch_cuda=torch.cuda.get_rng_state_all(),
                     permutation=order_rng.bit_generator.state,loader=loader_rng.get_state()),
            epoch=step//200,next_batch=0,parent_sha256=sha(parent) if parent else None))
        path=dest/(a.chain+f'-step{step:04d}.pt');assert not path.exists();torch.save(saved,path)
        return path.name,sha(path)
    checks={}
    if parent is None:
        name,h=snapshot(0);checks[name]=h
    with (dest/'loss-steps.csv').open('w',newline='') as lf,(dest/'exposures.csv').open('w',newline='') as ef:
        losswriter=csv.writer(lf,lineterminator='\n');losswriter.writerow(['chain_steps','lifetime_steps','epoch','batch','BCE_sum','KL_mean','raw_total','BCE_per_frame','BCE_per_element','gradient_norm_before_clip'])
        ew=csv.writer(ef,lineterminator='\n');ew.writerow(['epoch','presentation','position','frame_id'])
        for epoch in range(8):
            guard();order=order_rng.permutation(800)
            for pos,index in enumerate(order):ew.writerow([epoch+1,pos,int(index),int(ids[index])])
            loader=DataLoader(TensorDataset(torch.from_numpy(x[order])),batch_size=4,shuffle=False,num_workers=0,generator=loader_rng)
            trainer.model.train()
            for batch,(v,) in enumerate(loader):
                v=v.to('cuda');trainer.optimizer.zero_grad();_,prediction=trainer.model(v)
                bce=trainer.model.recon_loss(v,prediction);kl=trainer.model.kld_loss();loss=trainer.lambda_rec*bce+kl
                loss.backward();grad=torch.nn.utils.clip_grad_norm_(trainer.model.parameters(),trainer.clip_grad_max_norm)
                assert all(bool(torch.isfinite(t)) for t in [loss,bce,kl,grad]),'非有限loss/gradient'
                trainer.optimizer.step();step=epoch*200+batch+1
                losswriter.writerow([step,step+(200 if parent else 0),epoch+1,batch,float(bce),float(kl),float(loss),float(bce)/4,float(bce)/3136,float(grad)])
            assert all(bool(torch.isfinite(v).all()) for v in trainer.model.state_dict().values())
            if step in [200,400,800,1600]:
                name,h=snapshot(step);checks[name]=h
            lf.flush();ef.flush();guard()
    torch.cuda.synchronize()
    cost=dict(chain_id=a.chain,wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
              peak_GPU_allocated_bytes=torch.cuda.max_memory_allocated(),peak_GPU_reserved_bytes=torch.cuda.max_memory_reserved())
    write(dest/'result.json',dict(status='COMPLETE',chain_id=a.chain,steps=1600,exposures=6400,parent_sha256=sha(parent) if parent else None,
          initial_parent_model_digest=saved['model_digest'] if parent else None,checkpoints=checks,cost=cost,recipe=load_config()['cvae'],optimizer_param_groups=trainer.optimizer.state_dict()['param_groups']))
    ledger.append(cost);write(a.output/'cost-ledger.json',ledger)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('plan',type=Path);p.add_argument('output',type=Path);p.add_argument('chain');a=p.parse_args()
    try:execute(a)
    except BaseException as e:
        write(a.output/'training-stop.json',dict(status='STOPPED',chain=a.chain,type=type(e).__name__,reason=str(e)))
        raise
