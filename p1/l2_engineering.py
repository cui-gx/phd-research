"""L2の入力凍結と人工データによる保存・復元資格を検査する。"""
import argparse
import fcntl
import csv
import hashlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import random
import resource
import time

DESIGN = '8d34e3714e246afb0bd74fe6943abeafd8f89c5b'
STATES = ['r01-s4', 'r01-s8', 'r02-s4', 'r02-s8']

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def rows(path):
    with Path(path).open(newline='') as f:
        return list(csv.DictReader(f))

def runtime():
    """CPU資格検査はGPU不可視、単一worker/数値threadで行う。"""
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1'
    assert all(os.environ[k] == '1' for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'])
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    os.nice(10)

def freeze(a):
    import numpy as np
    raw = a.project/'runs/b1-expansion-20261026'
    expected = read(a.bundle/'raw-artifact-sha256.json')
    audit = {}
    def check(p):
        rel = str(p.relative_to(raw))
        h = sha(p)
        assert h == expected[rel], '原SHA不一致: '+rel
        audit[rel] = h
        return p
    membership = rows(a.plan/'training-membership.csv')
    validation = rows(a.plan/'evaluation-ids.csv')
    summary = []
    atom_signature = None
    # 既存PDBだけを読み、DCDやMDを再処理しない。
    for root in ['r01','r02']:
        for segment in range(1,5):
            folder = raw/'tasks'/f'{root}-h{segment}-md'/'science'
            for name in ['initial.pdb','final.pdb']:
                text = check(folder/name).read_text()
                sig = [(s[12:16].strip(),s[17:20],s[21:27]) for s in text.splitlines()
                       if s.startswith('ATOM  ') and s[12:16].strip() == 'CA']
                assert len(sig) == 28
                if atom_signature is None:
                    atom_signature = sig
                assert sig == atom_signature, 'Cα順序不一致'
    for state in STATES:
        folder = raw/'tasks'/(state+'-decision-pool')/'science'
        sets = read(check(folder/'indices.json'))
        contacts = np.load(check(folder/'contacts.npy'),allow_pickle=True)
        with np.load(check(folder/'features.npz')) as f:
            times = f['time_ps']; valid = f['valid']; distances = f['distances_A']
            assert len(times) == len(contacts) and distances.shape == (len(times),325)
            assert np.all(np.diff(times)>0)
            decision = int(state[-1])*1000
            b = decision-2000
            groups = {}
            for arm in ['M0','F1','F2']:
                ids = [int(r['frame_id_0based']) for r in membership if r['state_id']==state and r['arm']==arm]
                assert ids == sets['old' if arm=='M0' else arm]
                assert len(ids) == len(set(ids)) == 800
                assert np.all(valid[ids]) and np.all(times[ids] <= decision+1e-5)
                groups[arm] = set(ids)
            assert groups['M0'] == groups['F1']
            assert len(groups['F2'] & groups['M0']) == 400
            for label in ['OLD_VALIDATION','RECENT_HELDOUT']:
                rr = [r for r in validation if r['state_id']==state and r['set']==label]
                ids = [int(r['frame_id_0based']) for r in rr]
                assert len(ids) == len(set(ids)) == 200
                assert all(set(ids).isdisjoint(v) for v in groups.values())
                assert np.all(valid[ids]) and np.all(times[ids]<=decision+1e-5)
                assert all(abs(float(r['time_ps'])-times[int(r['frame_id_0based'])])<1e-8 for r in rr)
                if label=='OLD_VALIDATION':
                    assert ids == sets['validation']
                else:
                    eligible=np.flatnonzero(valid & (times>b+1700) & (times<=b+2000+1e-5))
                    assert ids==eligible[np.linspace(0,len(eligible)-1,200,dtype=int)].tolist()
            candidate=sets['candidate']
            assert len(candidate)==(7800 if state.endswith('4') else 15800)
            assert np.all(valid[candidate]) and np.all(times[candidate] <= decision+1e-5)
            summary.append(dict(state_id=state,frames=len(times),candidates=len(candidate),training=800,OLD=200,RECENT=200))
    models=read(a.bundle/'models.json')
    for model in models:
        if model['state_id'] in STATES:
            folder=raw/'tasks'/(model['state_id']+'-'+model['label'])/'science'
            for name in ['checkpoint.pt','recipe.json','exposure.json','result.json']:
                check(folder/name)
            assert sha(folder/'checkpoint.pt')==model['checkpoint_sha256']
    import mdlearn
    installed=Path(inspect.getfile(mdlearn)).parent.parent
    source_checks={}
    for rel,h in read(a.plan.parent/'P1-L1/expected-mdlearn-sha256.json').items():
        assert sha(installed/rel)==h
        source_checks[rel]=h
    write(a.output/'input-freeze.json',dict(status='PASS',design_commit=DESIGN,states=summary,
          original_file_sha256=audit,CA_order=atom_signature,mdlearn_sha256=source_checks,
          environment={k:importlib.metadata.version(k) for k in ['torch','numpy','scikit-learn','mdlearn']},
          new_scientific_steps=0,new_MD=0))

def synthetic(a):
    """人工tensorのみで同じCVAE/RMSpropの保存・再開をbit照合する。"""
    import copy
    import numpy as np
    import torch
    from p1.server.science import _trainer, load_config
    from p1.l1_frozen_diagnostic import tensor_digest, opt_digest
    torch.use_deterministic_algorithms(True)
    def build():
        return _trainer(dict(science_config=load_config(),device='cpu',seed=1700000101,cpu_threads=1))[0]
    def seed():
        random.seed(1701000001);np.random.seed(1701000001);torch.manual_seed(1701000001)
    def rng():
        return dict(python=random.getstate(),numpy=np.random.get_state(),torch=torch.get_rng_state())
    def restore(s):
        random.setstate(s['python']);np.random.set_state(s['numpy']);torch.set_rng_state(s['torch'])
    generator=torch.Generator().manual_seed(991)
    x=torch.randint(0,2,(4,1,28,28),generator=generator).float()
    def step(t):
        t.model.train();t.optimizer.zero_grad()
        _,prediction=t.model(x)
        loss=t.lambda_rec*t.model.recon_loss(x,prediction)+t.model.kld_loss()
        loss.backward();g=torch.nn.utils.clip_grad_norm_(t.model.parameters(),t.clip_grad_max_norm)
        assert torch.isfinite(loss) and torch.isfinite(g)
        t.optimizer.step()
    t=build();seed()
    for _ in range(6):step(t)
    reference=(tensor_digest(t.model.state_dict()),opt_digest(torch,t.optimizer.state_dict()),opt_digest(torch,rng()))
    t=build();seed()
    for _ in range(3):step(t)
    saved=copy.deepcopy(dict(model=t.model.state_dict(),optimizer=t.optimizer.state_dict(),rng=rng()))
    path=a.output/'synthetic-checkpoint.pt';assert not path.exists();torch.save(saved,path)
    parent_sha=sha(path);expected_model=tensor_digest(t.model.state_dict());expected_opt=opt_digest(torch,t.optimizer.state_dict())
    t=build();s=torch.load(path,weights_only=False,map_location='cpu')
    t.model.load_state_dict(s['model'],strict=True);t.optimizer.load_state_dict(s['optimizer']);restore(s['rng'])
    assert tensor_digest(t.model.state_dict())==expected_model and opt_digest(torch,t.optimizer.state_dict())==expected_opt
    # 別processで行う予定のevalを模し、RNGを保存して戻す。
    r=rng();t.model.eval()
    with torch.no_grad():
        z,p=t.model(x);zz,pp=t.model(x)
        assert torch.equal(z,zz) and torch.equal(p,pp)
    restore(r)
    for _ in range(3):step(t)
    resumed=(tensor_digest(t.model.state_dict()),opt_digest(torch,t.optimizer.state_dict()),opt_digest(torch,rng()))
    assert reference==resumed, '連続と再開のbit不一致'
    assert sha(path)==parent_sha
    write(a.output/'engineering-check.json',dict(status='PASS',device='cpu',artificial_tensor=True,
          continuous_equals_resume=True,model_optimizer_RNG_bit_equal=True,parent_unmodified=True,
          eval_repeat_equal=True,scientific_optimizer_steps=0,synthetic_optimizer_steps=12,
          adapter_sha256=sha(Path(__file__))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','synthetic']);p.add_argument('project',type=Path);p.add_argument('plan',type=Path);p.add_argument('bundle',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    runtime();a.output.mkdir(exist_ok=True)
    lock=(a.output/"run.lock").open("a");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    begin=time.monotonic()
    try:
        globals()[a.mode](a)
    except BaseException as e:
        write(a.output/(a.mode+'-failure.json'),dict(status='STOPPED',error=str(e),type=type(e).__name__))
        raise
    finally:
        write(a.output/(a.mode+'-cost.json'),dict(wall_s=time.monotonic()-begin,CPU_s=time.process_time(),peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
