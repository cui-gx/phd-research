"""Offline P1 record checks. No workload launch, scheduler, or performance model.

All times are seconds on one run-local monotonic timeline. Passing this checker
establishes structural consistency only, never scientific validity or benefit.
"""
import argparse
import json
import math
from pathlib import Path

PHASES = {"simulation", "train", "inference", "selection", "analysis"}
EVIDENCE = {"derived analysis", "local CPU/GPU measurement",
            "trace-driven simulation", "small Slurm/pilot testbed"}


def _check_record(data):
    errors = []

    def require(ok, message):
        if not ok:
            errors.append(message)

    def number(value, name):
        ok = type(value) in (int, float) and math.isfinite(value)
        require(ok, f"{name}: finite number required")
        return float(value) if ok else 0.0

    require(data.get("schema_version") == 1, "schema_version must be 1")
    require(bool(data.get("run_id")), "run_id required")
    kind = data.get("record_kind")
    require(kind in {"engineering_fixture", "measurement"}, "invalid record_kind")
    require(data.get("evidence_type") in EVIDENCE, "invalid evidence_type")
    if kind == "engineering_fixture":
        require(data.get("evidence_type") == "derived analysis",
                "fixture must be labelled derived analysis")
    if kind == "measurement":
        require(bool(data.get("source_ref")), "measurement requires source_ref")
    start = number(data.get("started_s"), "started_s")
    end = number(data.get("ended_s"), "ended_s")
    require(0 <= start < end, "invalid run interval")
    budget = data.get("budget_cpu_slots")
    control = data.get("reserved_control_slots")
    require(type(budget) is int and budget > 0, "positive integer CPU budget required")
    require(type(control) is int and control >= 0, "nonnegative control slots required")
    if type(budget) is not int or type(control) is not int:
        return {"ok": False, "errors": errors}
    require(control < budget, "control reservation consumes entire budget")
    require(data.get("allocation_semantics") == "fixed_reservation",
            "only fixed_reservation accounting implemented")
    dev = set(data.get("development_groups", []))
    held = set(data.get("heldout_groups", []))
    require(not dev.intersection(held), "development/heldout leakage")
    tasks = data.get("tasks", [])
    require(isinstance(tasks, list) and bool(tasks), "nonempty tasks list required")
    if not isinstance(tasks, list):
        return {"ok": False, "errors": errors}
    by_id, intervals, successes, attempts = {}, [], set(), set()
    assigned_seconds = 0.0
    for t in tasks:
        key = t.get("attempt_id")
        require(isinstance(key, str) and bool(key) and key not in by_id,
                f"duplicate/missing attempt_id: {key}")
        by_id[key] = t
        require(bool(t.get("task_id")), f"{key}: task_id required")
        attempt = t.get("attempt")
        require(type(attempt) is int and attempt >= 1, f"{key}: invalid attempt")
        pair = (t.get("task_id"), attempt)
        require(pair not in attempts, f"{key}: repeated logical attempt")
        attempts.add(pair)
        require(t.get("phase") in PHASES, f"{key}: invalid phase")
        require(bool(t.get("input_hash")), f"{key}: input_hash required")
        submitted = number(t.get("submitted_s"), f"{key}.submitted_s")
        a = number(t.get("started_s"), f"{key}.started_s")
        b = number(t.get("ended_s"), f"{key}.ended_s")
        require(start <= submitted <= a < b <= end, f"{key}: invalid task interval")
        slots = t.get("cpu_slots")
        require(type(slots) is int and slots > 0, f"{key}: positive integer slots required")
        if type(slots) is int and slots > 0:
            intervals.append((a, b, slots, key))
            assigned_seconds += slots * (b - a)
        status = t.get("status")
        require(status in {"success", "failure", "timeout"}, f"{key}: invalid status")
        require(type(t.get("output_valid")) is bool, f"{key}: output_valid must be boolean")
        if status != "success":
            require(t.get("output_valid") is False, f"{key}: failed output marked valid")
            require(bool(t.get("failure_reason")), f"{key}: failure reason required")
        if t.get("output_valid") and status == "success":
            require(bool(t.get("output_key")), f"{key}: output_key required")
            # Only complete valid simulation recipes count as molecular work.
            if t.get("phase") == "simulation":
                successes.add(t.get("output_key"))
        if t.get("phase") == "train":
            cutoff = number(t.get("training_cutoff_s"), f"{key}.training_cutoff_s")
            require(start <= cutoff <= a, f"{key}: future training cutoff")
    # Intervals are half open: a worker freed at t can be reused at t.
    for point in sorted({x for a, b, _, _ in intervals for x in (a, b)}):
        usage = control + sum(s for a, b, s, _ in intervals if a <= point < b)
        require(usage <= budget, f"CPU budget exceeded at {point}: {usage}>{budget}")
    logical = {}
    for t in tasks:
        logical.setdefault(t.get("task_id"), []).append(t)
    for key, group in logical.items():
        require(len({(t.get("phase"), t.get("input_hash")) for t in group}) == 1,
                f"{key}: retry changed phase or input")
        ordered = sorted(group, key=lambda t: number(t.get("started_s"), f"{key}.start"))
        for previous, current in zip(ordered, ordered[1:]):
            require(number(previous.get("ended_s"), f"{key}.end") <=
                    number(current.get("started_s"), f"{key}.start"),
                    f"{key}: overlapping retries")
    models = {}
    for model in data.get("models", []):
        key = model.get("version")
        require(isinstance(key, str) and bool(key) and key not in models,
                f"duplicate/missing model version: {key}")
        models[key] = model
        available = number(model.get("available_s"), f"{key}.available_s")
        training = by_id.get(model.get("train_attempt_id"))
        require(training is not None, f"{key}: missing training attempt")
        if training:
            require(training.get("phase") == "train" and training.get("status") == "success"
                    and training.get("output_valid") is True, f"{key}: invalid training result")
            train_end = number(training.get("ended_s"), f"{key}.train_end")
            require(train_end <= available <= end, f"{key}: model available before training ends")
            cutoff = number(training.get("training_cutoff_s"), f"{key}.cutoff")
            members = model.get("training_members", [])
            require(bool(members) and len(members) == len(set(members)),
                    f"{key}: training members missing or duplicated")
            for member in members:
                parent = by_id.get(member)
                require(parent is not None, f"{key}: unknown training member {member}")
                if parent:
                    parent_end = number(parent.get("ended_s"), f"{member}.ended_s")
                    require(parent.get("phase") == "simulation" and parent.get("status") == "success"
                            and parent.get("output_valid") is True and parent_end <= cutoff,
                            f"{key}: unavailable training data {member}")
    for key, t in by_id.items():
        if t.get("phase") == "selection" and "inference_parent" in t:
            parent = by_id.get(t["inference_parent"])
            require(parent is not None, f"{key}: unknown inference parent")
            if parent:
                require(parent.get("phase") == "inference" and parent.get("status") == "success"
                        and parent.get("output_valid") is True
                        and number(parent.get("ended_s"), f"{key}.inference_end") <=
                        number(t.get("started_s"), f"{key}.selection_start"),
                        f"{key}: invalid/future inference parent")
        if t.get("phase") == "inference":
            model = models.get(t.get("model_version"))
            require(model is not None, f"{key}: unknown model version")
            if model:
                available = number(model.get("available_s"), f"{key}.model_available")
                a = number(t.get("started_s"), f"{key}.start")
                require(available <= a, f"{key}: model used before available")
        if "selected_by" in t:
            parent = by_id.get(t["selected_by"])
            require(parent is not None, f"{key}: unknown selection parent")
            if parent:
                parent_end = number(parent.get("ended_s"), f"{key}.parent_end")
                submitted = number(t.get("submitted_s"), f"{key}.submission")
                require(parent.get("phase") in {"inference", "selection"}
                        and parent.get("status") == "success" and parent.get("output_valid") is True
                        and parent_end <= submitted, f"{key}: invalid/future selection parent")
    for action in data.get("actions", []):
        requested = number(action.get("requested_s"), "action.requested_s")
        effective = number(action.get("effective_s"), "action.effective_s")
        require(start <= requested <= effective <= end, "invalid action acknowledgement interval")
        require(action.get("boundary") == "task_boundary", "only task_boundary action allowed")
        require(bool(action.get("reason")), "action reason missing")
    return {"ok": not errors, "errors": errors, "record_kind": kind,
            "evidence_type": data.get("evidence_type"),
            "unique_valid_simulation_outputs": len(successes),
            "failed_attempts": sum(t.get("status") != "success" for t in tasks),
            "reserved_cpu_seconds": budget * (end - start),
            "assigned_worker_cpu_seconds": assigned_seconds,
            "scientific_benefit_verified": False}


def check_record(data):
    """Return a failed check for malformed nested data as well as semantic errors."""
    try:
        if not isinstance(data, dict):
            raise ValueError("top-level object required")
        return _check_record(data)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        return {"ok": False, "errors": [f"invalid input: {exc}"],
                "scientific_benefit_verified": False}


def check_closed_loop(data):
    """Find a complete provenance chain, without attesting execution authenticity."""
    result = check_record(data)
    result.update(real_execution_verified=False, closed_loop_chains=[])
    if not result["ok"]:
        return result
    tasks = {t["attempt_id"]: t for t in data["tasks"]}
    models = {m["version"]: m for m in data.get("models", [])}

    def valid(task, phase):
        return (task is not None and task.get("phase") == phase
                and task.get("status") == "success" and task.get("output_valid") is True)

    for task in tasks.values():
        if not valid(task, "simulation"):
            continue
        selected = tasks.get(task.get("selected_by"))
        inference = selected
        if valid(selected, "selection"):
            inference = tasks.get(selected.get("inference_parent"))
            if not valid(inference, "inference") or inference["ended_s"] > selected["started_s"]:
                continue
        if not valid(inference, "inference"):
            continue
        model = models.get(inference.get("model_version"))
        if model:
            for member in model["training_members"]:
                result["closed_loop_chains"].append({
                    "evidence_attempt": member, "train_attempt": model["train_attempt_id"],
                    "model_version": model["version"], "inference_attempt": inference["attempt_id"],
                    "selection_attempt": selected["attempt_id"],
                    "later_simulation_attempt": task["attempt_id"]})
    if not result["closed_loop_chains"]:
        result["errors"].append("no complete simulation-training-model-inference-selection-simulation chain")
    result["ok"] = not result["errors"]
    return result


def unresolved(value):
    """Recognize missing facts; zero may be a legitimate predeclared margin."""
    if value is None or value is False:
        return True
    if isinstance(value, str):
        s = value.strip().lower()
        return not s or s in {"tbd", "todo", "unknown", "pending", "需要本人提供", "待确认"} or s.startswith("tbd_")
    if isinstance(value, (dict, list)):
        return not value or any(unresolved(v) for v in (value.values() if isinstance(value, dict) else value))
    return type(value) not in (int, float) or not math.isfinite(value)


def check_candidate(data):
    """Missing external facts remain blockers; existence of prose is not readiness."""
    fields = ("machine_capability", "permission_evidence", "dependency_lock",
              "real_closed_loop_evidence", "legal_action_evidence", "quality_target",
              "quality_equivalence_margin", "minimum_useful_effect", "repetition_plan",
              "costed_budget", "nearest_work_resolution")
    if not isinstance(data, dict):
        data = {}
    blockers = [f for f in fields if unresolved(data.get(f))]
    return {"design_draft_present": data.get("status") == "candidate",
            "field_presence_complete": not blockers,
            "ready_for_formal_evaluation": False,
            "manual_evidence_review_required": True,
            "review_note": "Presence checks cannot authenticate evidence, validate targets or authorize experiments.",
            "blockers": blockers, "scientific_benefit_verified": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("record", type=Path)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--candidate", action="store_true")
    mode.add_argument("--closed-loop", action="store_true")
    args = p.parse_args()
    try:
        data = json.loads(args.record.read_text())
        if not isinstance(data, dict):
            raise ValueError("top-level object required")
        result = (check_candidate(data) if args.candidate else
                  check_closed_loop(data) if args.closed_loop else check_record(data))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = {"ok": False, "errors": [f"invalid input: {exc}"]}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    passed = result.get("ready_for_formal_evaluation", False) if args.candidate else result.get("ok", False)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
