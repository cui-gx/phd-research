"""B1拡張の事前固定した実験行列。科学計算を行わない。"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

RUN_ID = 'b1-expansion-20261026'
M0_SEED = 1600000001
INFERENCE_SEED = 2026102671
ORDER_SEED = 1603000001
BOOTSTRAP_SEED = 1604000001
ROOT_IDS = tuple(f'r{i:02d}' for i in range(1, 9))


def experiment_matrix():
    """共有F0を重複生成せず、240個の不変IDを作る。"""
    roots, states, branches = [], [], []
    for number, root_id in enumerate(ROOT_IDS, 1):
        roots.append(dict(root_id=root_id, history_seed=1600000100+number))
        for milestone in (4, 8):
            state_id = f'{root_id}-s{milestone}'
            train_seeds = {str(t): 1601000000+number*100+milestone*10+t for t in (1, 2)}
            md_seeds = {str(m): 1602000000+number*100+milestone*10+m for m in (1, 2, 3)}
            states.append(dict(root_id=root_id, state_id=state_id, milestone_ns=milestone,
                               boundary_ps=(milestone-2)*1000, M0_seed=M0_SEED,
                               training_seeds=train_seeds, MD_seeds=md_seeds))
            for arm in ('F0', 'F1', 'F2'):
                for t in ((0,) if arm == 'F0' else (1, 2)):
                    for m in (1, 2, 3):
                        branches.append(dict(root_id=root_id, state_id=state_id,
                            milestone_ns=milestone, arm=arm, training_block=t, MD_block=m,
                            training_seed=None if t == 0 else train_seeds[str(t)],
                            MD_seed=md_seeds[str(m)], length_ns=4,
                            branch_id=f'{state_id}-{arm}-t{t}-m{m}'))
    random.Random(ORDER_SEED).shuffle(branches)
    first = next(v for v in branches if v['state_id'] == 'r01-s4')
    branches = [first]+[v for v in branches if v is not first]
    for i, branch in enumerate(branches, 1):
        branch['execution_order'] = i
    assert len(branches) == len({v['branch_id'] for v in branches}) == 240
    assert sum(v['length_ns'] for v in branches) == 960
    return dict(approval='P1-B1-EXPANSION-20261026', run_id=RUN_ID, roots=roots,
                states=states, branches=branches, order_seed=ORDER_SEED,
                inference_seed=INFERENCE_SEED, bootstrap_seed=BOOTSTRAP_SEED,
                engineering_branch_id=first['branch_id'], history_MD_ns=64,
                downstream_MD_ns=960, total_MD_ns=1024)


def write_contract(folder):
    """計画用のJSONと全枝CSVを保存する。"""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    matrix = experiment_matrix()
    (folder/'experiment-matrix.json').write_text(json.dumps(matrix, indent=2)+'\n')
    with (folder/'experiment-matrix.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(matrix['branches'][0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(matrix['branches'])
    return matrix
