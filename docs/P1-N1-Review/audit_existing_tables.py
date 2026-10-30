"""保存済みN1表の件数・キー・算術恒等式を点検する。新しい科学解析はしない。

DCD、NPZ、モデル、サーバを開かず、推定量・相関・区間を新たに推定しない。
既報値の転記と集約式の整合確認だけを行い、旧ファイルは読み取り専用とする。
"""
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SRC = ROOT / 'docs/P1-N1/CPU-v1'
METRICS = ['min_RMSD_A', 'mean_RMSD_A', 'median_RMSD_A', 'p10_RMSD_A',
           'final_RMSD_A', 'mean_Q', 'median_Q', 'max_Q', 'Q_at_argmin']
COUNTS = {'all-windows.csv': 6528, 'model-windows.csv': 1920,
          'state-windows.csv': 1152, 'state-paired.csv': 10368,
          'root-paired.csv': 20736, 'root-summary.csv': 2592,
          'geometry-native-joined.csv': 11520, 'geometry-correlations.csv': 432,
          'history-progress.csv': 240}


def read_csv(name):
    with (SRC / name).open() as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != COUNTS[name]:
        raise ValueError(f'件数不一致: {name}')
    return rows


def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    inventory = []
    for path in sorted(SRC.iterdir()):
        if not path.is_file() or path.name.startswith('._'):
            continue
        data = path.read_bytes()
        item = dict(path=str(path.relative_to(ROOT)), bytes=len(data),
                    sha256=hashlib.sha256(data).hexdigest())
        if path.suffix == '.json':
            value = json.loads(data)
            item['entries'] = len(value)
        inventory.append(item)
    tables = {name: read_csv(name) for name in COUNTS}
    checks = defaultdict(int)
    max_error = 0.0

    def equal(observed, expected):
        nonlocal max_error
        error = abs(float(observed) - float(expected))
        if not math.isfinite(error) or error > 1e-10:
            raise ValueError('既報表の算術恒等式が一致しません。')
        max_error = max(max_error, error)
        checks['arithmetic_equalities'] += 1

    cells = defaultdict(list)
    boundary_counts = defaultdict(set)
    for row in tables['all-windows.csv']:
        if int(row['total']) != int(row['valid']) + int(row['excluded']):
            raise ValueError('品質分母が一致しません。')
        if row['kind'] == 'DOWNSTREAM':
            cells[tuple(row[k] for k in ['state_id','sampling_ps','burn_ps','prefix_ns','arm'])].append(row)
            if row['sampling_ps'] == '0.5' and row['prefix_ns'] == '4.0':
                boundary_counts[row['burn_ps']].add(int(row['total']))
    for row in tables['state-windows.csv']:
        key = tuple(row[k] for k in ['state_id','sampling_ps','burn_ps','prefix_ns','arm'])
        branches = cells[key]
        expected = 3 if row['arm'] == 'F0' else 6
        if len(branches) != expected or len({r['task_id'] for r in branches}) != expected:
            raise ValueError('共有F0または枝の件数に不一致があります。')
        for metric in METRICS:
            equal(row[metric], sum(float(r[metric]) for r in branches) / expected)
    state = {tuple(r[k] for k in ['state_id','sampling_ps','burn_ps','prefix_ns','arm']): r
             for r in tables['state-windows.csv']}
    for row in tables['state-paired.csv']:
        key = tuple(row[k] for k in ['state_id','sampling_ps','burn_ps','prefix_ns'])
        hi, lo = row['comparison'].split('-')
        equal(row['difference'], float(state[(*key,hi)][row['metric']]) - float(state[(*key,lo)][row['metric']]))
    paired = {tuple(r[k] for k in ['state_id','sampling_ps','burn_ps','prefix_ns','comparison','metric']): float(r['difference'])
              for r in tables['state-paired.csv']}
    roots = defaultdict(list)
    for row in tables['root-paired.csv']:
        suffix = tuple(row[k] for k in ['sampling_ps','burn_ps','prefix_ns','comparison','metric'])
        s4, s8 = [paired[(row['root_id'] + '-' + s, *suffix)] for s in ['s4','s8']]
        equal(row['difference'], {'S4': s4, 'S8': s8, 'AVERAGE': (s4+s8)/2, 'S8_MINUS_S4': s8-s4}[row['stage']])
        roots[(row['stage'], *suffix)].append(row)
    for row in tables['root-summary.csv']:
        key = tuple(row[k] for k in ['stage','sampling_ps','burn_ps','prefix_ns','comparison','metric'])
        rr = roots[key]
        if len(rr) != 8 or len({r['root_id'] for r in rr}) != 8:
            raise ValueError('独立根の件数が一致しません。')
        equal(row['mean'], sum(float(r['difference']) for r in rr)/8)
        if sum(int(row[k]) for k in ['positive','negative','zero']) != 8:
            raise ValueError('符号の件数が一致しません。')
    # 数値を再推定せず、元CSVの行をそのまま抜き出す。
    main_rows = [r for r in tables['root-summary.csv'] if r['sampling_ps']=='0.5' and r['burn_ps']=='100' and r['prefix_ns']=='4.0']
    write_csv('reported-primary-contrasts.csv', main_rows)
    write_csv('reported-all-window-F2-F1.csv', [r for r in tables['root-summary.csv'] if r['comparison']=='F2-F1'])
    write_csv('reported-root-primary.csv', [r for r in tables['root-paired.csv'] if r['sampling_ps']=='0.5' and r['burn_ps']=='100' and r['prefix_ns']=='4.0' and r['comparison']=='F2-F1'])
    write_csv('reported-primary-correlations.csv', [r for r in tables['geometry-correlations.csv'] if r['burn_ps']=='100' and r['prefix_ns']=='4.0'])
    for item in inventory:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('読取り中に入力が変化しました。')
    (OUT/'review-input-inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n')
    result = dict(status='PASS', checked_JST=datetime.now(timezone(timedelta(hours=9))).isoformat(),
                  scope='STATIC_SAVED_TABLE_CONSISTENCY_AND_EXACT_ROW_COPY',
                  table_rows=COUNTS, checks=dict(checks), max_arithmetic_error=max_error,
                  bootstrap_recomputed=False, correlations_recomputed=False,
                  DCD_or_NPZ_read=False, server_sessions=0, new_scientific_results=0,
                  input_files_unchanged=len(inventory),
                  reported_4ns_window_counts={key: sorted(value) for key, value in boundary_counts.items()},
                  window_boundary_note='100ps主窓は7800点。200/500ps窓は7601/7001点で、理想格子の厳密除外より各1点多い。原表を修正せず記録。')
    (OUT/'static-table-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
