"""審査資料のリンク・構文・原証拠不変性だけを静的に確認する。"""
import ast
import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = '2d1e8a1a304c669fc6b625dd802d7e1e680d7d3f'
SHARED = {'.gitignore', 'AGENTS.md', 'docs/collaboration-policy.md',
          'docs/博士研究_全局总档案.md', 'docs/协作交接记录.md',
          '教程/研究规范/术语与定义.md'}
README_SHA = '7942e3c12cc0fd9988c40b1424d218b73c4c09c2b57ef9141052ad18c116cadd'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_paths = set()
    links = []
    for path in sorted(OUT.glob('*.md')):
        if path.name.startswith('._'):
            continue
        for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            value = match.group(1).strip('<>').split('#')[0]
            if not value or '://' in value:
                continue
            dest = (path.parent / unquote(value)).resolve()
            if not dest.is_file():
                raise ValueError(f'参照先がありません: {path.name} → {value}')
            rel = str(dest.relative_to(ROOT))
            links.append({'from': str(path.relative_to(ROOT)), 'to': rel})
            if not dest.is_relative_to(OUT):
                source_paths.add(rel)
    for item in json.loads((OUT/'review-input-inventory.json').read_text()):
        if sha(ROOT/item['path']) != item['sha256']:
            raise ValueError('既存N1入力が変更されています。')
        source_paths.add(item['path'])
    source_paths.add('docs/P1-N1/sources.json')
    sources = []
    for name in sorted(source_paths):
        data = (ROOT/name).read_bytes()
        baseline = subprocess.check_output(['git', 'show', BASE+':'+name], cwd=ROOT)
        if data != baseline:
            raise ValueError(f'基準版と原証拠が異なります: {name}')
        sources.append({'path': name, 'bytes': len(data), 'sha256': sha(ROOT/name)})
    changed = subprocess.check_output(['git','diff','--name-only','-z',BASE],cwd=ROOT).decode().split('\0')
    for name in filter(None, changed):
        if name not in SHARED | {'README.md'} and not name.startswith('docs/P1-N1-Review/'):
            raise ValueError(f'許可外の変更: {name}')
    if sha(ROOT/'README.md') != README_SHA:
        raise ValueError('既存README作業が変化しました。')
    rows = {}
    for p in OUT.glob('*.csv'):
        if p.name.startswith('._'):
            continue
        rows[p.name] = len(list(csv.DictReader(p.open())))
    for p in OUT.glob('*.py'):
        if p.name.startswith('._'):
            continue
        ast.parse(p.read_text(), filename=str(p))
    for p in OUT.glob('*.json'):
        if p.name.startswith('._'):
            continue
        json.loads(p.read_text())
    manifest = {'baseline_commit': BASE, 'sources': sources,
                'note': '既報/旧ソースのbyte同一性。サーバrawを再読した証拠ではない。'}
    (OUT/'review-source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    result = {'status': 'PASS', 'checked_JST': datetime.now(timezone(timedelta(hours=9))).isoformat(),
              'markdown_links': len(links), 'source_files_unchanged_from_baseline': len(sources),
              'row_copy_counts': rows, 'python_AST': 'PASS', 'JSON_parse': 'PASS',
              'existing_root_README_preserved_sha256': README_SHA,
              'new_scientific_computations': 0, 'server_sessions': 0,
              'external_review': 'PENDING', 'researcher_scientific_acceptance': 'PENDING',
              'remote_delivery': 'SEPARATE_RECEIPT',
              'local_setup_note': 'PyYAMLは未導入。import確認のみ失敗し、追加導入せず標準ライブラリの静的点検を使用した。科学処理の失敗ではない。',
              'static_validator_repair': '初回のglobがmacOS AppleDoubleを本文と読んでUnicodeDecodeError。メタデータ除外を追加し再点検。転記CSVはGit空白検査でCRLFを指摘されLF出力に統一した。元値・原表は不変で、科学データの再解析はしていない。',
              'links': links}
    (OUT/'delivery-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='links'},ensure_ascii=False))


if __name__ == '__main__':
    main()
