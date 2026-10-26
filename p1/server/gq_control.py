"""Persistent, fail-closed GPU budget for the approved GQ round; no policy study."""
from __future__ import annotations
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

CAPS = {"gq1": 600, "gq2": 1200, "gq3": 1200, "reserve": 600}


def allowance(rows, stage):
    if stage not in CAPS:
        raise ValueError("Unknown approved GQ stage")
    used = sum(r["charged_s"] for r in rows)
    stage_used = sum(r["charged_s"] for r in rows if r["stage"] == stage)
    return min(3600-used, CAPS[stage]-stage_used)


def admit(rows, stage, timeout, margin=15):
    if timeout <= 0 or timeout+margin > allowance(rows, stage):
        raise RuntimeError("Insufficient persistent stage/global budget")
    if any(r["status"] == "pending" for r in rows):
        raise RuntimeError("Unsettled task: reconcile its reserved budget before any restart")


def atomic(path, obj):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def run_task(root, name, stage, request, timeout, lease):
    from .support import ROOT, inspect_host, verify_lease, _terminate_owned_group
    from .qualification import occupancy
    root = Path(root).resolve()
    if root != (ROOT.parent/"runs/gq-r1-20261026").resolve():
        raise ValueError("This approved round has one fixed ledger root; no directory budget reset")
    root.mkdir(parents=True, exist_ok=True)
    with (root/"round.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = root/"budget-ledger.json"
        rows = json.loads(ledger.read_text()) if ledger.exists() else []
        admit(rows, stage, timeout)
        devices, cpus = verify_lease(lease, inspect_host(), timeout+15)
        if len(devices) != 1 or len(cpus) != 3:
            raise ValueError("GQ requires exactly one GPU and three CPU affinity IDs")
        task = root/"tasks"/name
        task.mkdir(parents=True, exist_ok=False)
        (task/"occupancy.json").write_text(json.dumps(occupancy(), indent=2))
        request = dict(request, output_dir=str(task/"science"))
        (task/"request.json").write_text(json.dumps(request, indent=2))
        env = os.environ.copy()
        env.update(CUDA_VISIBLE_DEVICES=devices[0], PYTHONDONTWRITEBYTECODE="1",
                   OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2",
                   NUMEXPR_NUM_THREADS="2", OPENMM_CPU_THREADS="2", WANDB_MODE="disabled",
                   MPLBACKEND="Agg")
        cache = task/"runtime-cache"
        cache.mkdir()
        for key in ("TMPDIR", "XDG_CACHE_HOME", "MPLCONFIGDIR", "CUDA_CACHE_PATH", "NUMBA_CACHE_DIR"):
            target = cache/key
            target.mkdir()
            env[key] = str(target)
        row = {"name": name, "stage": stage, "status": "pending", "charged_s": timeout+15,
               "timeout_s": timeout, "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "boundary": "child launch to complete reap, includes imports/context/I-O/failure"}
        rows.append(row)
        atomic(ledger, rows)  # Reserve the worst case BEFORE launching any GPU work.
        start = time.monotonic()
        child = telemetry = None
        error = None
        peak = 0
        import psutil
        try:
            with (task/"stdout.txt").open("x") as stdout, (task/"stderr.txt").open("x") as stderr, (task/"gpu.csv").open("x") as gpu:
                telemetry = subprocess.Popen(["nvidia-smi", "--query-gpu=timestamp,memory.used,utilization.gpu,power.draw", "--format=csv", "--loop-ms=500"], stdout=gpu, stderr=subprocess.STDOUT)
                child = subprocess.Popen(["taskset", "-c", ",".join(map(str, cpus[1:])), sys.executable,
                                          "-B", "-m", "p1.server.gq_science", str(task/"request.json")],
                                         env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                (task/"process.json").write_text(json.dumps({"owned_pid": child.pid, "cpus": cpus[1:], "gpu_uuid": devices[0]}))
                while child.poll() is None:
                    try:
                        proc = psutil.Process(child.pid)
                        rss = sum(p.memory_info().rss for p in [proc, *proc.children(recursive=True)] if p.is_running())
                        peak = max(peak, rss)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    if time.monotonic()-start >= timeout or peak > 16*1024**3 or (root/"STOP").exists():
                        error = "timeout/RSS/STOP safety gate"
                        _terminate_owned_group(child)
                        break
                    time.sleep(0.1)
                child.wait()
                if child.returncode:
                    error = error or f"child exit {child.returncode}"
                result_path = task/"science/result.json"
                if not result_path.exists() or json.loads(result_path.read_text()).get("status") != "success":
                    error = error or "missing or failed scientific result"
        except BaseException as e:
            error = repr(e)
            if child is not None:
                _terminate_owned_group(child)
            raise
        finally:
            # No resource can be reclaimed from another user's PID.
            if child is not None and child.poll() is None:
                _terminate_owned_group(child)
            if telemetry is not None:
                telemetry.terminate()
                telemetry.wait(timeout=5)
            elapsed = time.monotonic()-start
            row.update(charged_s=elapsed, status="failure" if error else "complete",
                       error=error, peak_process_tree_rss_bytes=peak,
                       returncode=child.returncode if child else None)
            atomic(ledger, rows)
            (task/"execution.json").write_text(json.dumps(row, indent=2))
            import shutil
            shutil.rmtree(cache)
        if error:
            raise RuntimeError(error)
        print(json.dumps({"task": name, "charged_s": elapsed, "total_used_s": sum(r["charged_s"] for r in rows), "stage_remaining_s": allowance(rows, stage)}), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--name", required=True)
    p.add_argument("--stage", required=True, choices=CAPS)
    p.add_argument("--request", required=True, type=Path)
    p.add_argument("--lease", required=True, type=Path)
    p.add_argument("--timeout", required=True, type=float)
    a = p.parse_args()
    if not a.name.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Unsafe task name")
    run_task(a.root, a.name, a.stage, json.loads(a.request.read_text()), a.timeout,
             json.loads(a.lease.read_text()))


if __name__ == "__main__":
    main()
