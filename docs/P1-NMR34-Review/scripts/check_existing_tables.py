"""保存済みCSVの算術とJSONの転記を監査する。座標・モデルを読み込まない。"""
import argparse
from collections import Counter, defaultdict
import csv
import datetime
import gzip
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import resource
import statistics
import time

METRICS = ('min_RMSD_A', 'mean_RMSD_A', 'median_RMSD_A', 'p10_RMSD_A',
           'final_RMSD_A', 'mean_Q', 'median_Q', 'max_Q', 'Q_at_argmin')
REFS = [str(i) for i in range(1, 35)] + ['NMR34_MIN']
WINDOWS = {f'{b}_{p}_{s}' for b, p, s in
           itertools.product([0, 100, 200, 500], [1., 2., 4.], [.5, 2.])}


def sha(path):
    """既存ファイルを読み取り専用でhashする。"""
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with path.open('x') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('saved_output', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    start, cpu = time.monotonic(), time.process_time()
    args.destination.mkdir(exist_ok=False)
    base, saved, dest = args.bundle, args.saved_output, args.destination
    manifest = json.loads((base / 'manifest.json').read_text())
    compact = json.loads((base / 'compact-results-sha256.json').read_text())
    audit = json.loads((base / 'delivery-audit.json').read_text())
    reference_map = json.loads((base / 'reference-map.json').read_text())
    inputs = []
    for entry in compact:
        path = saved / 'analysis' / entry['path'].removeprefix('results/')
        require(path.stat().st_size == entry['bytes'], 'CSV等のbyte長不一致')
        require(sha(path) == entry['sha256'], 'CSV等のSHA不一致')
        inputs.append(entry)
    ids = {entry['task_id'] for entry in manifest}
    require(len(manifest) == len(ids) == 272, '単位数/重複')
    require(Counter(e['kind'] for e in manifest) == {'HISTORY': 32, 'DOWNSTREAM': 240}, '履歴/枝数')
    require(sum(e['frames'] for e in manifest) == 2048000, 'frame数')
    roots = {f'r{i:02}' for i in range(1, 9)}
    require({e['root_id'] for e in manifest} == roots, '根欠落')
    branches = [e for e in manifest if e['kind'] != 'HISTORY']
    for root, state, arm in itertools.product(roots, ['s4', 's8'], ['F0', 'F1', 'F2']):
        entries = [e for e in branches if e['state_id'] == f'{root}-{state}' and e['arm'] == arm]
        require(len(entries) == (3 if arm == 'F0' else 6), '臂の枝数')
        blocks = {e['training_block'] for e in entries}
        require(len(blocks) == (1 if arm == 'F0' else 2), '学習block数')
        for block in blocks:
            require({str(e['MD_block']) for e in entries if e['training_block'] == block} == {'1', '2', '3'}, 'MD block')
    for ref in reference_map:
        pairs = [tuple(pair) for pair in ref['pairs_zero_based']]
        require(len(pairs) == len(set(pairs)) == ref['denominator'], '接触分母/重複')
        require(all(0 <= i < j < 28 and j - i >= 3 for i, j in pairs), '接触対の資格')

    comparisons = 0
    maximum_error = 0.

    def close(actual, expected):
        nonlocal comparisons, maximum_error
        error = abs(float(actual) - float(expected))
        require(math.isfinite(error) and error <= 1e-10, '既存表の算術不一致')
        maximum_error = max(maximum_error, error)
        comparisons += 1

    main_rows, all_window_signs, main_roots = [], [], []
    row_counts = Counter()
    for ref in REFS:
        folder = saved / 'analysis' / ref
        rows = read_csv(folder / 'branches-s4.csv') + read_csv(folder / 'branches-s8.csv')
        history = read_csv(folder / 'history.csv')
        require(len(rows) == 5760 and len(history) == 768, '枝/履歴の表行数')
        require({(r['task_id'], r['window']) for r in rows + history} ==
                set(itertools.product(ids, WINDOWS)), '全単位/窓の完全性')
        grouped_models, grouped_states = defaultdict(list), defaultdict(list)
        for row in rows:
            grouped_models[(row['state_id'], row['arm'], row['training_block'], row['window'])].append(row)
            grouped_states[(row['state_id'], row['arm'], row['window'])].append(row)
        models = read_csv(folder / 'models.csv')
        states = read_csv(folder / 'state.csv')
        require(len(models) == len(grouped_models) == 1920, 'model表完全性')
        require(len(states) == len(grouped_states) == 1152, 'state表完全性')
        for row in models:
            group = grouped_models[(row['state_id'], row['arm'], row['training_block'], row['window'])]
            require(len(group) == int(row['MD_repeats']) == 3, 'modelの分母')
            for metric in METRICS:
                close(row[metric], statistics.mean(float(r[metric]) for r in group))
        state_values = {}
        for row in states:
            key = (row['state_id'], row['arm'], row['window'])
            group = grouped_states[key]
            state_values[key] = {m: statistics.mean(float(r[m]) for r in group) for m in METRICS}
            for metric in METRICS:
                close(row[metric], state_values[key][metric])
        paired = read_csv(folder / 'root-paired.csv')
        require(len(paired) == 2304, '根対応数')
        groups = defaultdict(list)
        for row in paired:
            hi, lo = row['comparison'].split('-')
            for metric in METRICS:
                delta = [state_values[(row['root_id'] + '-' + s, hi, row['window'])][metric]
                         - state_values[(row['root_id'] + '-' + s, lo, row['window'])][metric]
                         for s in ('s4', 's8')]
                expected = {'S4': delta[0], 'S8': delta[1],
                            'AVERAGE': statistics.mean(delta), 'S8_MINUS_S4': delta[1] - delta[0]}
                close(row[metric], expected[row['stage']])
            groups[(row['stage'], row['window'], row['comparison'])].append(row)
            if ref in ('1', 'NMR34_MIN') and row['window'] == '100_4.0_0.5':
                main_roots.append({'reference': ref, **row})
        summary = read_csv(folder / 'root-summary.csv')
        require(len(summary) == 2592, '根要約数')
        for row in summary:
            group = groups[(row['stage'], row['window'], row['comparison'])]
            require({r['root_id'] for r in group} == roots and len(group) == int(row['roots']) == 8, '独立単位')
            values = [float(r[row['metric']]) for r in group]
            for field, number in {'mean': statistics.mean(values), 'median': statistics.median(values),
                                  'SD': statistics.stdev(values), 'minimum': min(values), 'maximum': max(values),
                                  'positive': sum(v > 0 for v in values), 'negative': sum(v < 0 for v in values),
                                  'zero': sum(v == 0 for v in values)}.items():
                close(row[field], number)
            require(float(row['minimum']) <= float(row['bootstrap95_low']) <= float(row['bootstrap95_high']) <= float(row['maximum']), '既存区間の範囲')
            if row['window'] == '100_4.0_0.5':
                main_rows.append({'reference': ref, **row})
            if row['comparison'] == 'F2-F1' and row['metric'] == 'min_RMSD_A':
                all_window_signs.append({'reference': ref, **row})
        row_counts.update(history=len(history), branches=len(rows), models=len(models), states=len(states),
                          paired=len(paired), summaries=len(summary))

    # 保存済み窓JSONを転記する。新たな品質判定・argmin計算はしない。
    known = {row['path']: row for row in audit['new_outputs']}
    source_index, statuses, metadata_rows = [], Counter(), 0
    output = dest / 'window-metadata.csv.gz'
    with output.open('xb') as binary, gzip.GzipFile(filename='', mode='wb', fileobj=binary, mtime=0) as zipped, io.TextIOWrapper(zipped, encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['task_id', 'kind', 'root_id', 'reference', 'window', 'total', 'valid', 'window_status', 'argmin_frame'], lineterminator='\n')
        writer.writeheader()
        for entry in manifest:
            relative = f"units/{entry['task_id']}/windows.json"
            path = saved / relative
            digest = sha(path)
            require(digest == known[relative]['sha256'], '保存済み窓JSONのSHA不一致')
            source_index.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest})
            rows = json.loads(path.read_text())
            require(len(rows) == 840, '窓JSON行数')
            for row in rows:
                ref = str(row['model'])
                require(ref in REFS and row['window'] in WINDOWS, '参照/窓識別')
                writer.writerow(dict(task_id=entry['task_id'], kind=entry['kind'], root_id=entry['root_id'], reference=ref,
                                     **{k: row[k] for k in ['window', 'total', 'valid', 'window_status', 'argmin_frame']}))
                statuses[(entry['kind'], row['window_status'])] += 1
                metadata_rows += 1
    # 入力CSVの再hashにより本監査中の不変性を確認する。
    for entry in compact:
        path = saved / 'analysis' / entry['path'].removeprefix('results/')
        require(sha(path) == entry['sha256'], '監査後の入力SHA不一致')
    write_csv(dest / 'main-all-contrasts.csv', main_rows)
    write_csv(dest / 'main-root-extract.csv', main_roots)
    write_csv(dest / 'all-window-direction-extract.csv', all_window_signs)
    (dest / 'metadata-source-sha256.json').write_text(json.dumps(source_index, indent=2) + '\n')
    result = dict(status='PASS', checked_at_JST=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
                  scope='EXISTING_TABLE_ARITHMETIC_AND_METADATA_TRANSCRIPTION_ONLY',
                  new_DCD_model_LOF_bootstrap_runs=0, compact_files_SHA_before_after=len(compact),
                  arithmetic_comparisons=comparisons, maximum_arithmetic_error=maximum_error,
                  row_counts=dict(row_counts), metadata_rows=metadata_rows,
                  metadata_status_counts=[dict(kind=k[0], status=k[1], rows=v) for k, v in statuses.items()],
                  reference_contact_denominators=[r['denominator'] for r in reference_map],
                  interval_check='SOURCE_AND_SAVED_BOUNDS_ONLY_NO_NEW_BOOTSTRAP',
                  wall_s=time.monotonic() - start, CPU_s=time.process_time() - cpu,
                  peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (dest / 'table-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
