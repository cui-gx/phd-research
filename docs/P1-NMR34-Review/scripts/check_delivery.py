"""審査文書のリンク・転送SHA・原成果不変性だけを確認する。科学解析はしない。"""
import ast
import csv
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess


def main():
    root = Path(__file__).resolve().parents[3]
    doc = root / 'docs/P1-NMR34-Review'
    manifest = json.loads((doc / 'evidence/transfer-manifest.json').read_text())
    for entry in manifest['files']:
        path = doc / ('scripts/check_existing_tables.py' if entry['path'] == 'check_existing_tables.py'
                      else 'evidence/' + entry['path'])
        assert path.stat().st_size == entry['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    links, sources = 0, set()
    pending = {'remote-readback.json'}
    for path in doc.rglob('*.md'):
        if path.name.startswith('._'):
            continue
        for url in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' in url or url.startswith('#'):
                continue
            target = (path.parent / url.split('#')[0]).resolve()
            if target.name in pending and not target.exists():
                continue
            assert target.is_file(), (path, url)
            links += 1
            if doc not in target.parents:
                sources.add(target)
    for path in (doc / 'scripts').glob('*.py'):
        if path.name.startswith('._'):
            continue
        ast.parse(path.read_text())
    with (doc / 'evidence/main-all-contrasts.csv').open() as stream:
        main_rows = list(csv.DictReader(stream))
    with (root / 'docs/P1-NMR34-FULL/results/main-reference-sensitivity.csv').open() as stream:
        assert main_rows == list(csv.DictReader(stream))
    with (doc / 'evidence/all-window-direction-extract.csv').open() as stream:
        directions = list(csv.DictReader(stream))
    assert len(directions) == 35 * 24 * 4
    for row in directions:
        if row['stage'] == 'S4':
            assert float(row['mean']) > 0
        if row['stage'] == 'S8':
            assert float(row['mean']) < 0
    keys = set()
    invalid = 0
    with gzip.open(doc / 'evidence/window-metadata.csv.gz', 'rt') as stream:
        for row in csv.DictReader(stream):
            key = (row['task_id'], row['reference'], row['window'])
            assert key not in keys
            keys.add(key)
            invalid += int(row['valid']) != int(row['total'])
    tasks = json.loads((root / 'docs/P1-NMR34-FULL/manifest.json').read_text())
    windows = {f'{b}_{p}_{s}' for b, p, s in itertools.product([0, 100, 200, 500], [1., 2., 4.], [.5, 2.])}
    assert keys == set(itertools.product([e['task_id'] for e in tasks],
                                       [str(i) for i in range(1, 35)] + ['NMR34_MIN'], windows))
    protected = ['p1', 'docs/P1-B1-Expansion', 'docs/P1-B1-R1', 'docs/P1-Q0', 'docs/P1-L1',
                 'docs/P1-L2', 'docs/P1-N1', 'docs/P1-NMR34-FULL', 'docs/P1-NMR34-QA', 'docs/P1-NMR34-v2']
    changed = subprocess.check_output(['git', 'diff', '--name-only', 'e9162145d60c4e88b5b147609b2da0ec20542cb7', '--', *protected], cwd=root, text=True)
    assert not changed, changed
    assert hashlib.sha256((root / 'README.md').read_bytes()).hexdigest() == '7942e3c12cc0fd9988c40b1424d218b73c4c09c2b57ef9141052ad18c116cadd'
    for path in (root / 'docs/P1-NMR34-FULL').glob('*.json'):
        if not path.name.startswith('._'):
            sources.add(path)
    for path in [root / 'p1/nmr34_full.py', root / 'p1/nmr34_full_analyze.py', root / 'p1/nmr34_full_audit.py',
                 root / 'p1/nmr34_v2.py', root / 'p1/n1_native_metrics.py']:
        sources.add(path)
    source_rows = [dict(path=str(path.relative_to(root)), bytes=path.stat().st_size,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in sorted(sources)]
    (doc / 'review-source-sha256.json').write_text(json.dumps(source_rows, indent=2, ensure_ascii=False) + '\n')
    result = dict(status='PASS', internal_links=links, transfer_files=len(manifest['files']),
                  main_rows_identical=len(main_rows), window_keys_unique=len(keys),
                  metadata_rows_with_quality_exclusion=invalid, frozen_source_and_results='UNCHANGED',
                  existing_user_README='PRESERVED_NOT_STAGED', new_scientific_computations=0,
                  new_bootstrap=0, source_index_files=len(source_rows),
                  document_check_note='文書点検の2回の試行はAppleDoubleファイルのUTF-8読取りで停止。Markdown/Python/JSON補助ファイルを対象外とした。科学検算の失敗ではない。')
    (doc / 'delivery-check.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
