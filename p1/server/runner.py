"""Bounded Parsl-backed integration of real MD/learning workers and policies.

This qualification runner deliberately rejects formal evaluation. The current
entry point admits one task at a time on one real GPU (or one CPU test slot).
Historical two-GPU policy functions remain in policy.py for traceability only.
"""
from __future__ import annotations
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from .events import FeedbackLedger
from .policy import Task, PolicyConfig, choose
from .science import load_config, freeze_snapshot, digest_json, validate_pdb_pair
from .support import ROOT, save_new, digest, inspect_host, verify_lease, execute_task, directory_bytes


class TrainingTrigger:
    """Count result-arrival milestones independently of dispatch delay."""
    def __init__(self, every):
        self.every = every
        self.next_count = every

    def observe(self, total_results):
        if total_results < self.next_count:
            return False
        self.next_count = (total_results // self.every + 1) * self.every
        return True


def controller_affinity(cpu_ids):
    """Bind existing controller threads; new Parsl threads inherit this mask."""
    if not hasattr(os, "sched_setaffinity"):
        return {}
    previous = {}
    try:
        for entry in Path("/proc/self/task").iterdir():
            tid = int(entry.name)
            try:
                previous[tid] = os.sched_getaffinity(tid)
                os.sched_setaffinity(tid, cpu_ids)
            except ProcessLookupError:
                previous.pop(tid, None)
        return previous
    except BaseException:
        restore_affinity(previous)
        raise


def restore_affinity(previous):
    for tid, cpus in previous.items():
        try:
            os.sched_setaffinity(tid, cpus)
        except ProcessLookupError:
            pass


def seed_for(campaign_seed, kind, ordinal):
    # Pair by kind/ordinal, not policy-dependent cross-kind dispatch position.
    value = f"{campaign_seed}:{kind}:{ordinal}".encode()
    return int(hashlib.sha256(value).hexdigest()[:8], 16) % (2**31 - 1) + 1


def validate_settings(settings):
    if settings.get("purpose") not in ("cpu_functional", "qualification", "development"):
        raise ValueError("Formal campaigns remain disabled until real-machine and scientific gates pass")
    if settings["purpose"] == "development" and settings.get("calibration_frozen") is not True:
        raise ValueError("Development requires measured estimates and an explicitly frozen calibration record")
    if settings.get("mode") not in ("smoke", "pilot"):
        raise ValueError("mode must be smoke or pilot")
    if type(settings.get("gpu_slots")) is not int or settings["gpu_slots"] != 1:
        raise ValueError("Current runner requires explicit gpu_slots=1; two logical GPUs are not allowed")
    if settings.get("policy") == "Static-reservation-matched":
        raise ValueError("Static-reservation-matched requires two GPUs and is disabled in the single-GPU runner")
    if settings.get("policy") != "Single-GPU-FIFO":
        raise ValueError("Current single-GPU qualification supports only the Single-GPU-FIFO engineering order")
    caps = {"walltime_s": 7200, "task_timeout_s": 3600, "max_tasks": 1000, "max_output_bytes": 20_000_000_000}
    settings.setdefault("max_task_rss_bytes", 4_000_000_000)
    caps["max_task_rss_bytes"] = 32_000_000_000
    for key, cap in caps.items():
        value = settings.get(key)
        if type(value) not in (int, float) or not 0 < value <= cap:
            raise ValueError(f"{key} must be positive and at most preparation cap {cap}")
    if type(settings["max_tasks"]) is not int or type(settings.get("seed")) is not int or settings["seed"] < 1:
        raise ValueError("Task cap and campaign seed must be positive integers")
    if type(settings.get("train_every_results")) is not int or settings["train_every_results"] < 1:
        raise ValueError("Training trigger must be a positive completed-result count")
    for kind in ("md", "train", "infer"):
        if type(settings["cpu_threads"].get(kind)) is not int or settings["cpu_threads"][kind] < 1:
            raise ValueError("Each task must have a positive fixed CPU allocation")
    if settings["purpose"] != "cpu_functional" and settings.get("device") != "cuda":
        raise ValueError("GPU qualification/development cannot silently fall back to CPU")
    if settings["purpose"] == "cpu_functional" and settings.get("device") != "cpu":
        raise ValueError("CPU functional mode requires explicit CPU device")
    PolicyConfig(settings["policy"], settings["walltime_s"], settings["wait_cap_s"],
                 settings["backlog_threshold"], settings["age_threshold_s"],
                 settings["estimates_s"]["md"], settings["estimates_s"]["infer"], gpu_slots=1)
    for key in ("initial_pdb", "reference_pdb"):
        if not Path(settings[key]).is_file():
            raise ValueError(f"Missing {key}")
    validate_pdb_pair(settings["initial_pdb"], settings["reference_pdb"])
    return settings


def run(settings, output_dir, science_config, lease=None):
    settings = validate_settings(dict(settings))
    science_config = load_config(science_config)
    output = Path(output_dir).resolve()
    if output.exists():
        raise ValueError("Run directory already exists; use a fresh immutable run ID")
    inspection = inspect_host()
    if settings["device"] == "cuda":
        if not sys.platform.startswith("linux"):
            raise ValueError("This GPU runner is qualified for Linux only")
        devices, cpus = verify_lease(lease or {}, inspection, settings["walltime_s"] + settings["task_timeout_s"] + 30)
        if len(devices) != 1:
            raise ValueError("Current runner requires exactly one permitted GPU UUID")
    else:
        devices = [None]
        cpus = inspection["cpu_ids_visible"][:1 + max(settings["cpu_threads"].values())]
    if len(cpus) < 1 + max(settings["cpu_threads"].values()):
        raise ValueError("Insufficient permitted logical CPUs for one controller and one task")
    cpus = cpus[:1 + max(settings["cpu_threads"].values())]
    control_cpus, worker_cpus = cpus[:1], cpus[1:]
    output.mkdir(parents=True)
    for key in ("initial_pdb", "reference_pdb"):
        settings[key] = str(Path(settings[key]).resolve())
    manifest = {"schema_version": 1, "settings": settings, "science_config": science_config,
                "lease": lease, "input_sha256": {k: digest(settings[k]) for k in ("initial_pdb", "reference_pdb")},
                "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (ROOT / "p1/server").glob("*.py")},
                "runtime": "Parsl ThreadPoolExecutor with one worker launching isolated per-task subprocesses",
                "evaluation_ready": False, "engineering_only": True,
                "dispatch_role": "single-GPU closed-loop engineering order, not a research comparison",
                "worker_count": 1, "gpu_slots": 1,
                "evidence_type": "local CPU/GPU measurement", "gpu_uuids": devices, "cpu_ids": cpus,
                "controller_cpu_ids": control_cpus, "worker_cpu_ids": worker_cpus,
                "cpu_affinity_supported": hasattr(os, "sched_setaffinity"),
                "end_rule": "stop admissions at horizon or smoke success; drain admitted tasks up to individual timeout"}
    save_new(output / "manifest.json", manifest)
    save_new(output / "environment.json", inspection)
    policy = PolicyConfig(settings["policy"], settings["walltime_s"], settings["wait_cap_s"],
                          settings["backlog_threshold"], settings["age_threshold_s"],
                          settings["estimates_s"]["md"], settings["estimates_s"]["infer"], gpu_slots=1)
    ledger = FeedbackLedger()
    results, completed, model, ranking = [], [], None, None
    ready, running = [], {}
    counts = {"md": 0, "train": 0, "infer": 0}
    training_trigger = TrainingTrigger(settings["train_every_results"])
    infer_frontier, infer_model = 0, None
    ranking_cursor, submitted, ledger_cursor = 0, 0, 0
    tick = time.monotonic()
    stop_file = output / "STOP"
    status, reason = "failure", "not_started"
    closing = False
    logger = (output / "events.jsonl").open("x", buffering=1)

    def elapsed():
        return time.monotonic() - tick

    def log(kind, **payload):
        logger.write(json.dumps({"kind": kind, "at_s": elapsed(), **payload}, sort_keys=True, allow_nan=False) + "\n")

    def flush_ledger():
        nonlocal ledger_cursor
        for event in ledger.events[ledger_cursor:]:
            logger.write(json.dumps(event.to_dict(), sort_keys=True, allow_nan=False) + "\n")
        ledger_cursor = len(ledger.events)

    def pending(kind):
        return any(t.kind == kind for t in ready)

    def new_task(kind):
        ordinal = counts[kind]
        counts[kind] += 1
        return Task(f"{kind}-{ordinal:06d}", kind, elapsed(), settings["estimates_s"][kind],
                    settings["cpu_threads"][kind], model_version=model["model_id"] if kind == "infer" else None)

    executor = None
    previous_affinity = {}
    try:
        previous_affinity = controller_affinity(control_cpus)
        from parsl.concurrent import ParslPoolExecutor
        from parsl.config import Config
        from parsl.executors.threads import ThreadPoolExecutor
        config = Config(executors=[ThreadPoolExecutor(label="p1-worker", max_threads=1)],
                        run_dir=str(output / "parsl"), usage_tracking=0, app_cache=False)
        executor = ParslPoolExecutor(config=config)
        while True:
            # Process all observed completions before any new admission.
            for task_id in sorted(list(running)):
                slot = running[task_id]
                if not slot["future"].done():
                    continue
                outcome = slot["future"].result()
                record_path = Path(outcome["result_path"])
                record = json.loads(record_path.read_text()) if record_path.exists() else {"status": "failure", "error": "missing task result"}
                log("task_completed", task_id=task_id, gpu_slot=slot["gpu"], execution=outcome, result_status=record["status"])
                del running[task_id]
                if outcome["returncode"] != 0 or record.get("status") != "success" or not record.get("valid"):
                    raise RuntimeError(f"Task failed: {task_id}: {record.get('error', outcome)}")
                record["available_at_s"] = elapsed()
                completed.append(record)
                if record["available_at_s"] > settings["walltime_s"]:
                    log("result_after_horizon_excluded", task_id=task_id)
                    continue
                task = slot["task"]
                if task.kind == "md":
                    results.append(record)
                    ledger.result_available(record["result_id"], elapsed())
                    if record.get("restart") and settings["mode"] == "smoke":
                        status, reason = "success", "real_feedback_restart_completed"
                elif task.kind == "train":
                    if record["training_snapshot_id"] != slot["snapshot_id"]:
                        raise RuntimeError("Training snapshot changed between dispatch and model publication")
                    model = record
                    ledger.model_published(record["model_id"], record["training_snapshot_id"], elapsed())
                else:
                    ledger.ranking_published(record["ranking_id"], record["model_id"], record["inference_result_ids"],
                                             elapsed(), inference_task_id=task_id)
                    ranking, ranking_cursor = record, 0
                flush_ledger()
            if status == "success":
                closing = True
            now = elapsed()
            if now >= settings["walltime_s"] and not closing:
                status, reason = ("success", "pilot_horizon_reached") if settings["mode"] == "pilot" else ("incomplete", "smoke_horizon_without_feedback_restart")
                closing = True
                log("admissions_closed", reason=reason)
            if stop_file.exists():
                raise RuntimeError("external_stop_requested")
            if directory_bytes(output) >= settings["max_output_bytes"]:
                raise RuntimeError("output_storage_cap")
            if closing:
                if not running:
                    break
                time.sleep(0.1)
                continue
            if submitted >= settings["max_tasks"] and not running:
                status, reason = ("success", "pilot_task_cap_reached") if settings["mode"] == "pilot" else ("incomplete", "smoke_task_cap_without_feedback_restart")
                break
            # One pending request per learning type; its snapshot is captured only at dispatch.
            if training_trigger.observe(len(results)) and not pending("train"):
                ready.append(new_task("train"))
            if model and (len(results) > infer_frontier or model["model_id"] != infer_model) and not pending("infer"):
                ready.append(new_task("infer"))
            if model:
                ready = [replace(t, model_version=model["model_id"]) if t.kind == "infer" else t for t in ready]
            while sum(t.kind == "md" for t in ready) < len(devices):
                ready.append(new_task("md"))
            for gpu_slot, device in enumerate(devices):
                if submitted >= settings["max_tasks"] or any(v["gpu"] == gpu_slot for v in running.values()):
                    continue
                used_cpus = {c for v in running.values() for c in v["cpu_ids"]}
                free_cpus = [c for c in worker_cpus if c not in used_cpus]
                now = elapsed()
                decision = choose(ready, running_tasks=[s["task"] for s in running.values()], feedback=ledger.feedback(now),
                                  now_s=now, gpu_id=gpu_slot, available_cpu_cores=len(free_cpus), config=policy)
                if decision.task is None:
                    continue
                task = decision.task
                ready.remove(task)
                task_root = output / "tasks" / task.task_id
                task_root.mkdir(parents=True)
                inputs = {}
                snapshot_id = None
                if task.kind == "md":
                    inputs = {"initial_pdb": settings["initial_pdb"], "reference_pdb": settings["reference_pdb"]}
                    selected = None
                    if ranking:
                        selected = ranking["selections"][ranking_cursor % len(ranking["selections"])]
                        ranking_cursor += 1
                        inputs["restart"] = selected
                    ledger.md_dispatched(task.task_id, elapsed(), selected["ranking_id"] if selected else None,
                                         selected["result_id"] if selected else None)
                elif task.kind == "train":
                    inputs = {"results": list(results)}
                    snapshot_id = freeze_snapshot(results, digest_json(science_config, "science-"))["snapshot_id"]
                    ledger.capture_snapshot(snapshot_id, elapsed(), [r["result_id"] for r in results])
                else:
                    inputs = {"results": list(results), "model": model}
                    ledger.inference_dispatched(task.task_id, model["model_id"], [r["result_id"] for r in results], elapsed())
                    infer_frontier, infer_model = len(results), model["model_id"]
                flush_ledger()
                request = {"task_id": task.task_id, "task_type": {"md": "simulation", "train": "train", "infer": "inference"}[task.kind],
                           "seed": seed_for(settings["seed"], task.kind, int(task.task_id.split("-")[-1])),
                           "device": settings["device"], "purpose": settings["purpose"], "cpu_threads": task.cpu_cores,
                           "max_rss_bytes": settings["max_task_rss_bytes"],
                           "output_dir": str(task_root / "artifacts"), "science_config": science_config, "inputs": inputs}
                request_path, result_path = task_root / "request.json", task_root / "result.json"
                save_new(request_path, request)
                assigned = free_cpus[:task.cpu_cores]
                timeout = settings["task_timeout_s"]
                future = executor.submit(execute_task, str(request_path), str(result_path), device, assigned, timeout, str(stop_file))
                running[task.task_id] = {"task": task, "future": future, "gpu": gpu_slot, "cpu_ids": assigned, "snapshot_id": snapshot_id}
                submitted += 1
                log("task_dispatched", task_id=task.task_id, gpu_slot=gpu_slot, gpu_uuid=device,
                    cpu_ids=assigned, decision=decision.to_dict(), input_sha256=digest(request_path))
            time.sleep(0.1)
    except BaseException as exc:
        status = "failure"
        reason = f"{type(exc).__name__}: {exc}"
        log("run_failure", error=reason)
    finally:
        if running:
            stop_file.touch(exist_ok=True)
        try:
            if executor is not None:
                executor.shutdown(wait=True)
        except BaseException as exc:
            status, reason = "failure", f"executor_shutdown: {type(exc).__name__}: {exc}"
            log("run_failure", error=reason)
        finally:
            restore_affinity(previous_affinity)
        flush_ledger()
        wall = elapsed()
        log("run_finished", status=status, reason=reason, wall_time_s=wall)
        logger.close()
        in_window = [r for r in completed if r["available_at_s"] <= settings["walltime_s"]]
        summary = {"status": status, "reason": reason, "submitted_tasks": submitted,
                   "completed_valid_tasks": len(completed), "valid_md_results": len(results),
                   "completed_valid_tasks_after_horizon": len(completed) - len(in_window),
                   "model_published": any(e.kind == "model_published" for e in ledger.events),
                   "ranking_published": any(e.kind == "ranking_published" for e in ledger.events),
                   "restart_md_completed": any(r["task_type"] == "simulation" and r.get("restart") for r in in_window),
                   "publication_and_restart_flags_scope": "observed by controller no later than horizon",
                   "wall_time_s_including_drain": wall, "reserved_gpu_hours_including_drain": len(devices) * wall / 3600 if settings["device"] == "cuda" else 0,
                   "evaluation_ready": False, "formal_evaluation_campaigns": 0, "engineering_only": True,
                   "gpu_slots": 1, "worker_count": 1,
                   "dispatch_role": "single-GPU closed-loop engineering order, not a research comparison",
                   "evidence_type": "local CPU/GPU measurement", "completed_result_ids": [r.get("result_id", r.get("model_id", r.get("ranking_id"))) for r in completed]}
        save_new(output / "summary.json", summary)
        save_new(output / "checksums.json", {str(p.relative_to(output)): digest(p) for p in output.rglob("*") if p.is_file()})
    return summary
