"""Codex-operated entry point; every scientific run is explicitly bounded."""
import argparse
import json
from pathlib import Path
import sys

from .support import ROOT, inspect_host, save_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Read-only host/GPU inventory; no GPU computation")
    inspect.add_argument("--output", type=Path, required=True)
    execute = commands.add_parser("run", help="Explicit CPU functional or GPU qualification/development run")
    execute.add_argument("--settings", type=Path, required=True)
    execute.add_argument("--science", type=Path)
    execute.add_argument("--lease", type=Path)
    execute.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check-inputs", help="Validate pinned sources and single-model structural input")
    check.add_argument("--output", type=Path, required=True)
    summary = commands.add_parser("summarize", help="Describe timing and version lineage without scientific-effect claims")
    summary.add_argument("run", type=Path)
    summary.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "inspect":
        save_new(args.output, inspect_host())
        return 0
    if args.command == "check-inputs":
        from .science import validate_pdb_pair, sha256_file, UPSTREAM_MD, UPSTREAM_MD_SHA256
        validate_pdb_pair(ROOT / "inputs/p1-fsd-ey/1FME-unfolded.pdb", ROOT / "inputs/p1-fsd-ey/1FME-folded-model1.pdb")
        if sha256_file(UPSTREAM_MD) != UPSTREAM_MD_SHA256:
            raise ValueError("Pinned source mismatch")
        manifest = json.loads((ROOT / "inputs/p1-fsd-ey/manifest.json").read_text())
        for item in manifest["records"]:
            if sha256_file(ROOT / item["path"]) != item["sha256"]:
                raise ValueError("Input hash mismatch")
        pre = manifest["preprocessing"]
        if sha256_file(ROOT / pre["output"]) != pre["output_sha256"]:
            raise ValueError("Reference preprocessing hash mismatch")
        save_new(args.output, {"status": "pass", "evidence_type": "derived analysis", "evaluation_ready": False})
        return 0
    if args.command == "summarize":
        from .analysis import describe_run
        save_new(args.output, describe_run(args.run))
        return 0
    from .runner import run
    settings = json.loads(args.settings.read_text())
    for name in ("initial_pdb", "reference_pdb"):
        if not Path(settings[name]).is_absolute():
            settings[name] = str(ROOT / settings[name])
    science = args.science or ROOT / ("configs/p1-server-science-cpu-smoke.json" if settings["purpose"] == "cpu_functional" else "configs/p1_server_science.json")
    summary = run(settings, args.output, science, json.loads(args.lease.read_text()) if args.lease else None)
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["status"] == "success" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"STOP: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
