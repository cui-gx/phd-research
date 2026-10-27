"""既存証拠を上書きせず、公開用エクスポートとSHAの対応を保存する。"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def file_sha256(path: Path) -> str:
    """ファイルを分割してSHA-256を計算する。"""
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def import_public_export(source: Path, destination: Path) -> dict:
    """衝突する新証拠を別名で保存し、全論理名の対応表を作成する。"""
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('入力と保存先は別のディレクトリにしてください。')
    manifest_path = source / 'public-sha256.json'
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict):
        raise ValueError('公開manifestはファイル名とSHAの対応表である必要があります。')
    for name, expected in manifest.items():
        if (not isinstance(name, str) or Path(name).name != name
                or name in ('', '.', '..', 'public-sha256.json')
                or name.startswith('._') or '/' in name or '\\' in name):
            raise ValueError('公開manifestのファイル名が不正です。')
        if not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected):
            raise ValueError('公開manifestのSHAが不正です。')
        if not (source / name).is_file() or file_sha256(source / name) != expected:
            raise ValueError('エクスポートのSHAが一致しません：' + name)
    extras = {p.name for p in source.iterdir() if not p.name.startswith('._')} - set(manifest) - {'public-sha256.json'}
    if extras:
        raise ValueError('manifest外のエクスポート項目があります。')

    destination.mkdir(parents=True, exist_ok=True)
    plan = []
    mapping = {}
    for name, expected in sorted(manifest.items()):
        target = destination / name
        conflict = target.exists() and (not target.is_file() or file_sha256(target) != expected)
        if conflict:
            target = destination / ('server-final-export-v1-' + name)
        mapping[name] = dict(path=target.name, sha256=expected, prior_name_conflict=conflict)
        plan.append((source / name, target, expected))
    export_manifest = destination / 'server-final-export-v1-public-sha256.json'
    manifest_sha = file_sha256(manifest_path)
    plan.append((manifest_path, export_manifest, manifest_sha))
    index = dict(schema_version=1, files=mapping,
                 export_manifest=dict(path=export_manifest.name, sha256=manifest_sha),
                 previous_evidence_overwritten=False)
    index_path = destination / 'public-export-index.json'
    if index_path.exists() and json.loads(index_path.read_text()) != index:
        raise ValueError('既存の取込索引と一致しません。別エクスポートとして点検してください。')
    for _, target, expected in plan:
        if target.exists() and (not target.is_file() or file_sha256(target) != expected):
            raise ValueError('取込先の別名証拠が一致しません：' + target.name)
    # 全照合の後にだけ作成し、既存ファイルは変更しない。
    for original, target, expected in plan:
        if not target.exists():
            with target.open('xb') as out, original.open('rb') as incoming:
                for chunk in iter(lambda: incoming.read(1024 * 1024), b''):
                    out.write(chunk)
        if file_sha256(target) != expected:
            raise ValueError('保存後のSHAが一致しません：' + target.name)
    if not index_path.exists():
        with index_path.open('x') as out:
            json.dump(index, out, ensure_ascii=False, indent=2)
            out.write('\n')
    return index
