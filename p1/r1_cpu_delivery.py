"""登録済み主表示の行だけを転記し、読者用の小型CSVを作る。科学値を再推定しない。"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description='R1派生表の主表示viewとSHA索引')
    p.add_argument('--output', required=True)
    out = Path(p.parse_args().output)
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '-1':
        raise RuntimeError('GPU不可視が必須です。')
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    os.nice(10)
    specs = [('root-summary.csv', 'main-root-summary.csv', 576),
             ('root-stage-effects.csv', 'main-root-stage-effects.csv', 1152),
             ('reference-decomposition.csv', 'main-reference-decomposition.csv', 288),
             ('continuous.csv', 'main-continuous.csv', 960),
             ('discrete-counts.csv', 'main-discrete-counts.csv', 5760)]
    audit = []
    for source, target, expected in specs:
        if (out/target).exists():
            raise RuntimeError('既存viewは上書きしません。')
        with (out/source).open() as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames
            rows = [r for r in reader if float(r['burn_ps']) == 100 and float(r['prefix_ns']) == 4]
        if len(rows) != expected:
            raise RuntimeError('主表示viewの件数が一致しません。')
        if source == 'discrete-counts.csv':
            fields = ['reference_mode', 'root_id', 'state_id', 'arm', 'training_block', 'MD_block',
                      'branch_id', 'burn_ps', 'prefix_ns', 'epsilon_A', 'tau_ps', 'added_regions']
        with (out/target).open('w', newline='') as f:
            w = csv.DictWriter(f, fields, lineterminator='\n', extrasaction='ignore')
            w.writeheader()
            w.writerows(rows)
        audit.append(dict(source=source, source_sha256=sha(out/source), view=target,
                          view_sha256=sha(out/target), rows=len(rows),
                          filter='事前登録主表示 burn=100ps, prefix=4ns。全参照/全比較/全尺度を保持。',
                          numeric_values_recomputed=False, columns=fields))
    (out/'compact-view-audit.json').write_text(json.dumps(dict(status='PASS', views=audit,
          source_sha256=sha(Path(__file__)), full_tables_retained=True), ensure_ascii=False, indent=2)+'\n')
    hashes = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and
              p.name not in ('output-sha256.json', 'public-evidence-index.json', 'run.lock', 'pipeline.lock')}
    (out/'output-sha256.json').write_text(json.dumps(hashes, indent=2)+'\n')
    files = [dict(path=p.name, bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(out.iterdir())
             if p.is_file() and p.suffix in ('.md', '.csv', '.json', '.png', '.log', '.txt') and p.name != 'public-evidence-index.json']
    (out/'public-evidence-index.json').write_text(json.dumps(dict(status='SERVER_GENERATED_WITH_EDITORIAL_REVIEW',
            files=files, raw_arrays_included=False, scientific_tables_and_figures_unchanged=True,
            compact_views_are_exact_row_projections=True), ensure_ascii=False, indent=2)+'\n')
    print('主表示view5件を値の再推定なしで作成しました。全表も保持しています。')


if __name__ == '__main__':
    main()
