"""Offline development manifest checks and non-destructive run-directory reservation.

No scientific launcher, SSH, package installation, or scheduler integration exists here.
Passing validates structure only. Permission references require independent review.
"""
import argparse
import json
import math
from pathlib import Path
import re


def reserve_run_directory(root, run_id):
    """Reserve a NEW directory under an existing trusted root; never remove anything.

    Intended for a user-owned root without concurrent untrusted filesystem writers.
    This function does not sanitize or execute an upstream spec.py.
    """
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", run_id):
        raise ValueError("run_id must be a single safe path component")
    root = Path(root).absolute()
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError("symlink roots are forbidden")
    if not root.is_dir():
        raise ValueError("an existing approved root is required")
    target = root / run_id
    target.mkdir(exist_ok=False)  # Atomic refusal if file, directory or symlink exists.
    return target


def check_manifest(data):
    errors = []

    def need(ok, message):
        if not ok:
            errors.append(message)

    def positive(value):
        return type(value) in (int, float) and math.isfinite(value) and value > 0

    def text(value):
        return (isinstance(value, str) and bool(value.strip()) and
                value.strip().lower() not in {"tbd", "unknown", "pending", "todo"}
                and not value.strip().lower().startswith("tbd_"))

    def digest(value):
        return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))

    try:
        need(data.get("schema_version") == 1, "schema_version must be 1")
        need(data.get("status") == "frozen_development", "development manifest must be frozen")
        need(data.get("scientific_evaluation") is False, "formal evaluation is outside this checker")
        need(data.get("purpose") in {"component_smoke", "closed_loop_smoke", "action_probe"}, "invalid purpose")
        need(isinstance(data.get("run_id"), str) and bool(re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", data["run_id"])), "safe unique run_id required")
        need(type(data.get("seed")) is int and data["seed"] >= 0, "nonnegative integer seed required")
        source = data["source"]
        need(isinstance(source.get("commit"), str) and bool(re.fullmatch(r"[0-9a-f]{40}", source["commit"])), "source commit required")
        for key in ("bundle_sha256", "adapter_sha256"):
            need(digest(source.get(key)), f"source.{key}: SHA-256 required")
        for key in ("dependency_lock_sha256", "environment_fingerprint_sha256", "solver_fingerprint_sha256"):
            need(digest(data["environment"].get(key)), f"environment.{key}: SHA-256 required")
        inputs = data["inputs"]
        need(isinstance(inputs, list) and bool(inputs), "nonempty inputs required")
        for item in inputs:
            need(text(item.get("path")) and digest(item.get("sha256")), "input path and SHA-256 required")
        for key in ("machine_evidence", "environment_authorization", "job_authorization", "approved_run_root"):
            need(text(data["permissions"].get(key)), f"permissions.{key}: reviewed reference required")
        limits = data["limits"]
        for key in ("cpu_slots", "max_attempts", "threads_per_worker"):
            need(type(limits.get(key)) is int and limits[key] > 0, f"limits.{key}: positive integer required")
        for key in ("memory_gib", "walltime_minutes", "storage_gib", "reserved_cpu_hours"):
            need(positive(limits.get(key)), f"limits.{key}: finite positive limit required")
        control = limits.get("control_slots")
        need(type(control) is int and control >= 0, "nonnegative control slots required")
        if type(control) is int and type(limits.get("cpu_slots")) is int:
            need(control < limits["cpu_slots"], "control reservation leaves no workers")
            if type(limits.get("threads_per_worker")) is int:
                need(limits["threads_per_worker"] <= limits["cpu_slots"] - control, "worker threads exceed worker budget")
        if positive(limits.get("walltime_minutes")) and positive(limits.get("reserved_cpu_hours")) and positive(limits.get("cpu_slots")):
            need(limits["cpu_slots"] * limits["walltime_minutes"] / 60 <= limits["reserved_cpu_hours"] + 1e-12,
                 "walltime and CPU reservation exceed CPU-hour cap")
        for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
            need(data["thread_environment"].get(key) == str(limits.get("threads_per_worker")), f"{key}: must match worker thread limit")
        for key in ("allocation", "selection", "learning_trigger", "learning_configuration", "horizon"):
            need(text(data["policy_factors"].get(key)), f"policy_factors.{key} required")
        need(data["failure_rules"].get("on_existing_run") == "stop", "existing run must stop")
        need(data["failure_rules"].get("on_limit") == "stop_and_preserve", "limit must stop and preserve")
        need(data["failure_rules"].get("on_solver_error") == "stop_and_preserve", "development solver errors must stop")
        required = {"manifest.json", "environment.json", "events.jsonl", "stdout.log", "stderr.log", "exit_status.json", "checksums.sha256"}
        need(required <= set(data["expected_outputs"]), "required provenance outputs missing")
    except (TypeError, KeyError, AttributeError, ValueError) as exc:
        errors.append(f"malformed manifest: {exc}")
    return {"ok": not errors, "errors": errors, "evidence_type": "derived analysis",
            "structural_validation_only": True, "execution_authorized": False,
            "ready_for_formal_evaluation": False, "scientific_benefit_verified": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    args = p.parse_args()
    try:
        result = check_manifest(json.loads(args.manifest.read_text()))
    except (OSError, ValueError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
