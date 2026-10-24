"""Predeclared helpers; qualification output is never a scientific effect claim."""
from __future__ import annotations
import json
import math
from pathlib import Path
import statistics


def sustained_target(rmsd, interval_ps, threshold_angstrom, duration_ps):
    """Return first qualifying last-frame index within ONE continuous segment.

    N equally spaced frames span (N-1)*interval, not N*interval. No joining
    independent restart segments. This returns geometry, not folding kinetics.
    """
    for x in (interval_ps, threshold_angstrom, duration_ps):
        if not math.isfinite(x) or x <= 0:
            raise ValueError("Metric parameters must be finite and positive")
    required = math.ceil(duration_ps / interval_ps) + 1
    consecutive = 0
    for index, value in enumerate(rmsd):
        if not math.isfinite(float(value)):
            raise ValueError("A nonfinite frame cannot silently become a valid target")
        consecutive = consecutive + 1 if value <= threshold_angstrom else 0
        if consecutive >= required:
            return index
    return None


def describe_run(run_dir):
    root = Path(run_dir)
    manifest = json.loads((root / "manifest.json").read_text())
    summary = json.loads((root / "summary.json").read_text())
    events = [json.loads(row) for row in (root / "events.jsonl").read_text().splitlines() if row]
    durations = {"simulation": [], "train": [], "inference": []}
    for path in sorted((root / "tasks").glob("*/result.json")):
        value = json.loads(path.read_text())
        if value.get("status") == "success":
            durations[value["task_type"]].append(value["wall_time_s"])
    snapshots = {e["snapshot_id"]: e for e in events if e["kind"] == "training_snapshot_captured"}
    models = {e["model_version"]: e for e in events if e["kind"] == "model_published"}
    ranks = {e["ranking_id"]: e for e in events if e["kind"] == "ranking_published"}
    consumed = []
    for event in events:
        if event["kind"] != "md_dispatched" or not event.get("ranking_id"):
            continue
        rank = ranks[event["ranking_id"]]
        model = models[rank["model_version"]]
        snapshot = snapshots[model["snapshot_id"]]
        newest = max(r["available_at_s"] for r in snapshot["results"])
        consumed.append({"md_task_id": event["task_id"], "model_version": model["model_version"],
                         "training_snapshot_id": model["snapshot_id"], "newest_training_data_to_dispatch_s": event["at_s"] - newest,
                         "model_publish_to_dispatch_s": event["at_s"] - model["at_s"],
                         "ranking_publish_to_dispatch_s": event["at_s"] - rank["at_s"]})
    return {"run": str(root.resolve()), "policy": manifest["settings"]["policy"], "summary": summary,
            "component_wall_seconds": {kind: {"n": len(values), "median": statistics.median(values) if values else None,
                                               "min": min(values) if values else None, "max": max(values) if values else None}
                                       for kind, values in durations.items()},
            "model_adoptions": consumed,
            "scientific_effect_evaluated": False,
            "note": "Component timing and lineage only. No policy superiority, target success, or GPU speedup is inferred."}
