"""Build a reviewed allowlist bundle without credentials or unrelated artifacts."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile

from .support import ROOT, digest


def members():
    selected = []
    for directory, pattern in (("p1", "*.py"),
                               ("vendor/mdlearn-938cb80", "*"), ("inputs/p1-fsd-ey", "*"),
                               ("上机准备/2026-10-23-P1", "*.md")):
        selected.extend((ROOT / directory).rglob(pattern))
    selected.extend((ROOT / "configs").glob("p1-server-*.json"))
    for name in ("test_science_adapter.py", "test_policy_engine.py", "test_server_runner.py", "test_server_analysis.py", "test_worker_cleanup.py", "test_component_timing.py", "test_qualification.py"):
        selected.append(ROOT / "tests/p1" / name)
    selected.extend((ROOT / "configs").glob("p1-server-*.txt"))
    selected.extend([ROOT / "configs/p1_server_science.json", ROOT / "p1/server/science_sources.md"])
    selected.append(ROOT / "上机准备/2026-10-23-P1/待确认参数表.json")
    for path in ("LICENSE.md", "README.md", "deepdrivemd/apps/openmm_simulation/app.py"):
        selected.append(ROOT / "literature/p1-concrete-2026-10-19/source-snapshots" / path)
    approved = []
    for path in sorted(set(selected)):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(ROOT)
        if any(p.startswith((".", "__pycache__")) or p in ("build", "dist") or p.endswith(".egg-info") for p in relative.parts):
            continue
        # No arbitrary run lease (may contain machine-specific coordination text).
        if path.parent == ROOT / "configs" and "lease" in path.name and path.name != "p1-server-lease.template.json":
            continue
        if path.suffix in (".pyc", ".pyo"):
            continue
        approved.append(path)
    return approved


def build(output):
    output = Path(output)
    files = members()
    manifest = {str(p.relative_to(ROOT)): digest(p) for p in files}
    with output.open("xb") as stream:
        with tarfile.open(fileobj=stream, mode="w:gz") as archive:
            for path in files:
                archive.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
            body = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
            info = tarfile.TarInfo("BUNDLE_SHA256.json")
            info.size = len(body)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(body))
    return {"path": str(output.resolve()), "sha256": digest(output), "files": len(files), "bytes": output.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output)))


if __name__ == "__main__":
    main()
