"""Read-only discovery, immutable output files and bounded child execution."""
from __future__ import annotations
import datetime as dt
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def save_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def command(args, timeout=15):
    try:
        p = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        return {"argv": args, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": args, "returncode": None, "error": str(exc)}


def inspect_host():
    packages = {}
    for name in ("openmm", "MDAnalysis", "torch", "mdlearn", "parsl", "numpy", "scikit-learn"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "schema_version": 1, "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hostname": platform.node(), "platform": platform.platform(), "python": sys.version,
        "cpu_ids_visible": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else list(range(os.cpu_count() or 1)),
        "packages": packages,
        "memory": command(["free", "-b"]) if sys.platform.startswith("linux") else command(["sysctl", "hw.memsize"]),
        "gpu_inventory": command(["nvidia-smi", "--query-gpu=index,uuid,name,memory.total,driver_version", "--format=csv,noheader,nounits"]),
        "gpu_processes": command(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory", "--format=csv,noheader,nounits"]),
        "evaluation_ready": False,
    }


def verify_lease(lease, inspection, required_seconds):
    """A record of separately obtained permission, never a way to obtain it."""
    if lease.get("permission_confirmed") is not True:
        raise ValueError("Record explicit server/resource permission before GPU execution")
    if lease.get("hostname") != inspection["hostname"]:
        raise ValueError("Lease hostname does not match this machine")
    expires = dt.datetime.fromisoformat(lease["expires_utc"])
    if expires.tzinfo is None or (expires - dt.datetime.now(dt.timezone.utc)).total_seconds() < required_seconds:
        raise ValueError("Resource reservation expires before the run cap")
    ids = lease.get("gpu_uuids", [])
    if not ids or len(ids) > 2 or len(ids) != len(set(ids)) or any(not x.startswith("GPU-") for x in ids):
        raise ValueError("Supply one or two distinct whole GPU UUIDs")
    inventory, processes = inspection["gpu_inventory"], inspection["gpu_processes"]
    if inventory.get("returncode") != 0 or processes.get("returncode") != 0:
        raise ValueError("Cannot verify GPU inventory and existing compute processes")
    present = {row.split(",")[1].strip() for row in inventory["stdout"].splitlines() if len(row.split(",")) >= 2}
    if not set(ids) <= present:
        raise ValueError("Requested GPU UUID is absent")
    if any(row.split(",")[0].strip() in ids for row in processes["stdout"].splitlines()):
        raise ValueError("A requested GPU already has a compute process; coordinate, do not kill it")
    cpus = lease.get("cpu_ids", [])
    if not cpus or len(cpus) != len(set(cpus)) or any(type(x) is not int for x in cpus) or not set(cpus) <= set(inspection["cpu_ids_visible"]):
        raise ValueError("Provide a distinct, available permitted CPU affinity set")
    if not lease.get("coordination_note"):
        raise ValueError("Record the agreed use window and resource scope")
    return ids, cpus


def execute_task(request_path, result_path, gpu_uuid, cpu_ids, timeout_s, stop_file):
    """Register task-local caches, execute, then remove only these caches."""
    base = Path(os.environ.get("P1_TEST_TMPDIR", tempfile.gettempdir()))
    runtime = base / ("doctoral-hpc-P1-task-" + uuid.uuid4().hex)
    save_new(Path(request_path).parent / "runtime-registration.json", {"temporary_path": str(runtime), "scope": "this task only"})
    created, primary_error = False, None
    try:
        runtime.mkdir()
        created = True
        return _execute_task_bound(request_path, result_path, gpu_uuid, cpu_ids, timeout_s, stop_file, runtime)
    except BaseException as exc:
        primary_error = exc
        raise
    finally:
        cleanup_error = None
        # Never remove a path if our own mkdir failed (e.g. a UUID collision).
        if created:
            try:
                shutil.rmtree(runtime)
            except FileNotFoundError:
                pass
            except BaseException as exc:
                cleanup_error = exc
        record = {"temporary_path": str(runtime), "created": created,
                  "removed": not runtime.exists(),
                  "cleanup_error": repr(cleanup_error) if cleanup_error else None}
        try:
            save_new(Path(request_path).parent / "runtime-cleanup.json", record)
        except BaseException as exc:
            if cleanup_error is None:
                cleanup_error = exc
            else:
                cleanup_error.add_note(f"Could not save cleanup diagnostic: {exc!r}")
        if cleanup_error is not None:
            if primary_error is not None:
                primary_error.add_note(f"Task runtime cleanup also failed: {cleanup_error!r}")
            else:
                raise cleanup_error


def _terminate_owned_group(child, grace_seconds=5):
    """Terminate only the new session created for this task and reap its leader.

    The leader may exit before its descendants. After the grace period, signal
    the same owned process group once more so such descendants cannot survive.
    This helper must never receive an externally discovered PID.
    """
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    finally:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=grace_seconds)


def _execute_task_bound(request_path, result_path, gpu_uuid, cpu_ids, timeout_s, stop_file, runtime):
    """Called by Parsl. Kill only this task's own session when its cap expires."""
    request_path, result_path = Path(request_path), Path(result_path)
    env = os.environ.copy()
    # Do not inherit a scheduler's broad GPU visibility into individual tasks.
    env["CUDA_VISIBLE_DEVICES"] = gpu_uuid if gpu_uuid else "-1"
    req = json.loads(request_path.read_text())
    rss_limit = req.get("max_rss_bytes")
    if rss_limit:
        import psutil
    threads = str(req["cpu_threads"])
    for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS", "OPENMM_CPU_THREADS"):
        env[key] = threads
    env.update(PYTHONDONTWRITEBYTECODE="1", WANDB_MODE="disabled", MPLBACKEND="Agg")
    env.update(TMPDIR=str(runtime), XDG_CACHE_HOME=str(runtime / "cache"), MPLCONFIGDIR=str(runtime / "matplotlib"),
               TORCH_HOME=str(runtime / "torch"), NUMBA_CACHE_DIR=str(runtime / "numba"), CUDA_CACHE_PATH=str(runtime / "cuda"))
    env["P1_CPU_AFFINITY"] = ",".join(map(str, cpu_ids))
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    started = time.monotonic()
    child, primary_error, cleanup_error = None, None, None
    stopped, peak_rss = None, 0
    try:
        with (request_path.parent / "stdout.txt").open("x") as stdout, (request_path.parent / "stderr.txt").open("x") as stderr:
            child = subprocess.Popen([sys.executable, "-m", "p1.server.worker", str(request_path), str(result_path)],
                                     cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            save_new(request_path.parent / "process.json", {"pid": child.pid, "gpu_uuid": gpu_uuid, "cpu_ids": cpu_ids, "timeout_s": timeout_s})
            while child.poll() is None:
                current_rss = 0
                if rss_limit:
                    try:
                        process = psutil.Process(child.pid)
                        for item in [process, *process.children(recursive=True)]:
                            try:
                                current_rss += item.memory_info().rss
                            except psutil.NoSuchProcess:
                                pass
                    except psutil.NoSuchProcess:
                        pass
                    peak_rss = max(peak_rss, current_rss)
                if time.monotonic() - started >= timeout_s or Path(stop_file).exists() or (rss_limit and current_rss > rss_limit):
                    stopped = "task_timeout" if time.monotonic() - started >= timeout_s else ("task_rss_cap" if rss_limit and current_rss > rss_limit else "run_stop")
                    _terminate_owned_group(child)
                    break
                time.sleep(0.1)
            child.wait()
    except BaseException as exc:
        primary_error = exc
        if stopped is None:
            stopped = "supervisor_error"
        raise
    finally:
        # This also covers process.json write failures and monitor exceptions.
        if child is not None and (primary_error is not None or child.poll() is None):
            try:
                _terminate_owned_group(child)
            except BaseException as exc:
                cleanup_error = exc
                if primary_error is not None:
                    primary_error.add_note(f"Owned process cleanup also failed: {exc!r}")
        outcome = {"returncode": child.returncode if child is not None else None,
                   "termination": stopped, "wall_time_s": time.monotonic() - started,
                   "peak_sampled_process_tree_rss_bytes": peak_rss if rss_limit else None,
                   "rss_limit_bytes": rss_limit, "result_path": str(result_path),
                   "gpu_uuid": gpu_uuid, "cpu_ids": cpu_ids,
                   "supervisor_error": repr(primary_error) if primary_error else None,
                   "process_cleanup_error": repr(cleanup_error) if cleanup_error else None}
        try:
            save_new(request_path.parent / "execution.json", outcome)
        except BaseException as exc:
            if primary_error is not None:
                primary_error.add_note(f"Could not save execution diagnostic: {exc!r}")
            elif cleanup_error is not None:
                cleanup_error.add_note(f"Could not save execution diagnostic: {exc!r}")
            else:
                raise
        if cleanup_error is not None and primary_error is None:
            raise cleanup_error
    return outcome


def directory_bytes(path):
    return sum(p.stat().st_size for p in Path(path).rglob("*") if p.is_file() and not p.is_symlink())
