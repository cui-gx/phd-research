"""Approved P1 S2 probes, reusing existing science workers and Parsl adapter.

Not a scheduling benchmark. Each invocation creates a new immutable evidence
directory. Hardware permission is provided separately in the existing lease.
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import time

from . import science
from .support import ROOT, execute_task, inspect_host, save_new, verify_lease, directory_bytes


def pdb_inventory(path):
    lines = Path(path).read_text().splitlines()
    atoms = [s for s in lines if s.startswith(("ATOM  ", "HETATM"))]
    # For multi-model PDB report first model's topology, full model count apart.
    first = []
    for s in lines:
        if s.startswith("ENDMDL"):
            break
        if s.startswith(("ATOM  ", "HETATM")):
            first.append(s)
    residues = list(dict.fromkeys((s[21:22], s[22:27].strip(), s[17:20]) for s in first))
    return {"sha256": science.sha256_file(path), "atoms_first_model": len(first),
            "atoms_all_models": len(atoms), "model_records": sum(s.startswith("MODEL ") for s in lines),
            "residues_first_model": residues,
            "hydrogens_first_model": sum(s[76:78].strip() in {"H", "D"} for s in first),
            "cryst1": [s for s in lines if s.startswith("CRYST1")],
            "terminal_atom_names": [[s[12:16].strip() for s in first if (s[21:22], s[22:27].strip(), s[17:20]) == r]
                                    for r in (residues[0], residues[-1])],
            "nonprotein_residue_names": sorted({s[17:20].strip() for s in first if s.startswith("HETATM")})}


def audit(output):
    """CPU-only system introspection, without integration or protocol changes."""
    import openmm
    import openmm.app as app
    import openmm.unit as u
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    cfg = science.load_config()
    configure, _ = science._upstream_functions()
    sim, pdb = configure(ROOT / "inputs/p1-fsd-ey/1FME-unfolded.pdb", None,
                         cfg["dt_ps"], cfg["temperature_kelvin"], cfg["heat_bath_friction_coef"],
                         openmm.Platform.getPlatformByName("CPU"), {"Threads": "2"})
    system = sim.system
    xml = openmm.XmlSerializer.serialize(system)
    (out / "system.xml").write_text(xml)
    forces = []
    charge = 0.0
    for f in system.getForces():
        row = {"class": type(f).__name__}
        if hasattr(f, "getNonbondedMethod"):
            row["nonbonded_method_enum"] = int(f.getNonbondedMethod())
            row["cutoff_nm"] = f.getCutoffDistance().value_in_unit(u.nanometer)
        if isinstance(f, openmm.NonbondedForce):
            charge = sum(f.getParticleParameters(i)[0].value_in_unit(u.elementary_charge) for i in range(f.getNumParticles()))
        if hasattr(f, "getNumGlobalParameters"):
            row["global_parameters"] = {f.getGlobalParameterName(i): f.getGlobalParameterDefaultValue(i)
                                       for i in range(f.getNumGlobalParameters())}
        forces.append(row)
    files = {}
    data = Path(app.__file__).parent / "data"
    # Include every installed Amber14 XML as well as GBn2 to pin the actual files.
    for p in [data / "amber14-all.xml", data / "implicit/gbn2.xml", *sorted((data / "amber14").glob("*.xml"))]:
        files[str(p.relative_to(data))] = science.sha256_file(p)
    record = {"status": "MEASURED", "evidence_type": "local CPU/GPU measurement", "versions": science._versions(),
              "inputs": {p.name: pdb_inventory(p) for p in (ROOT / "inputs/p1-fsd-ey").glob("*.pdb")},
              "system": {"particles": system.getNumParticles(), "constraints": system.getNumConstraints(),
                         "periodic": system.usesPeriodicBoundaryConditions(), "net_charge_e": charge,
                         "forces": forces, "xml_sha256": hashlib.sha256(xml.encode()).hexdigest()},
              "forcefield_files_sha256": files,
              "integrator": {"class": type(sim.integrator).__name__,
                             "constraint_tolerance": sim.integrator.getConstraintTolerance(),
                             "dt_ps": sim.integrator.getStepSize().value_in_unit(u.picosecond),
                             "temperature_K": sim.integrator.getTemperature().value_in_unit(u.kelvin),
                             "friction_per_ps": sim.integrator.getFriction().value_in_unit(u.picosecond**-1)},
              "no_md_integration_performed": True}
    save_new(out / "audit.json", record)
    return record


def occupancy():
    """Fail closed before each GPU task; snapshots remain private raw evidence."""
    import subprocess
    def cmd(args):
        return subprocess.run(args, capture_output=True, text=True, check=True, timeout=15).stdout
    queries = []
    for attempt in range(7):
        procs = cmd(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory", "--format=csv,noheader,nounits"])
        memory = cmd(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"])
        queries.append({"compute_processes": procs, "memory_utilization": memory})
        if procs.strip() or any(float(row.split(",")[0]) > 100 for row in memory.splitlines()):
            break
        if all(float(row.split(",")[1]) == 0 for row in memory.splitlines()):
            break
        # nvidia-smi utilization is a trailing sample. After our own child exits,
        # require a fresh idle sample, never bypass a process or memory conflict.
        if attempt < 6:
            time.sleep(0.5)
    import psutil
    others = []
    for p in psutil.process_iter(["pid", "username", "cpu_times", "cmdline"]):
        try:
            a = p.info
            if a["username"] != psutil.Process().username():
                others.append({"pid": a["pid"], "owner": a["username"], "command": (a["cmdline"] or [""])[0]})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "gpu_processes": procs,
              "gpu_memory_utilization": memory, "load_1_5_15": os.getloadavg(),
              "available_memory_bytes": psutil.virtual_memory().available, "other_processes": others,
              "gpu_query_history": queries}
    if procs.strip():
        raise RuntimeError("GPU compute process appeared; coordinate rather than preempt")
    if any(float(row.split(",")[0]) > 100 or float(row.split(",")[1]) > 0 for row in memory.splitlines()):
        raise RuntimeError("GPU memory/utilization appeared without identifiable process; stop")
    if os.getloadavg()[0] > 4 or psutil.virtual_memory().available < 16_000_000_000:
        raise RuntimeError("Shared CPU/memory use exceeds bounded pilot gate")
    return record


def run_pilot(output, lease_file, manifest_file):
    import subprocess
    import parsl
    from parsl.config import Config
    from parsl.executors.threads import ThreadPoolExecutor
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(Path(manifest_file).read_text())
    save_new(out / "manifest.json", manifest)
    lease = json.loads(Path(lease_file).read_text())
    inventory = inspect_host()
    gpu, cpus = verify_lease(lease, inventory, manifest["walltime_cap_s"])
    if len(gpu) != 1 or len(cpus) != 3:
        raise ValueError("One GPU and three logical CPU IDs required for this bounded pilot")
    save_new(out / "environment.json", inventory)
    save_new(out / "lease.json", lease)
    os.sched_setaffinity(0, {cpus[0]})
    start = time.monotonic()
    records = []
    parsl.load(Config(executors=[ThreadPoolExecutor(label="p1-s2", max_threads=1)],
                      run_dir=str(out / "parsl"), strategy=None))
    task_app = parsl.python_app(execute_task, executors=["p1-s2"])
    def task(name, kind, cfg, inputs, seed):
        # No overlap: occupancy check after previous task has been fully reaped.
        snapshot = occupancy()
        save_new(out / f"occupancy-{name}.json", snapshot)
        if time.monotonic() - start + manifest["task_timeout_s"] > manifest["walltime_cap_s"]:
            raise RuntimeError("Insufficient budget for another bounded task")
        if directory_bytes(out) > manifest["output_cap_bytes"]:
            raise RuntimeError("Output cap reached")
        request = {"task_type": kind, "task_id": name, "seed": seed, "device": "cuda",
                   "purpose": "qualification", "cpu_threads": 2, "science_config": cfg,
                   "inputs": inputs, "output_dir": str(out / "tasks" / name / "science"),
                   "max_rss_bytes": manifest["task_rss_cap_bytes"]}
        reqfile, resultfile = out / "tasks" / name / "request.json", out / "tasks" / name / "result.json"
        save_new(reqfile, request)
        dispatch = time.perf_counter()
        execution = task_app(str(reqfile), str(resultfile), gpu[0], cpus[1:],
                             manifest["task_timeout_s"], str(out / "STOP")).result()
        observed = time.perf_counter() - dispatch
        result = json.loads(resultfile.read_text()) if resultfile.exists() else {}
        save_new(out / "tasks" / name / "dispatch.json", {"dispatch_to_result_s": observed,
                  "supervised_child_s": execution["wall_time_s"], "worker_internal_s": result.get("wall_time_s"),
                  "boundary_note": "Residual includes startup, imports outside worker timer, serialization, polling, Parsl dispatch and teardown; not pure scheduler cost"})
        records.append(result)
        if execution["returncode"] != 0 or result.get("status") != "success":
            raise RuntimeError(f"Task {name} failed; see immutable logs")
        return result
    telemetry_file = (out / "gpu-telemetry.csv").open("x")
    telemetry = subprocess.Popen(["nvidia-smi", "--query-gpu=timestamp,memory.used,utilization.gpu,utilization.memory,power.draw",
                                  "--format=csv", "--loop-ms=500"], stdout=telemetry_file, stderr=subprocess.STDOUT)
    save_new(out / "telemetry-process.json", {"owned_pid": telemetry.pid, "sample_interval_ms": 500})
    try:
        md_groups = {}
        for length in manifest["md_lengths_ns"]:
            cfg = science.load_config()
            cfg["simulation_length_ns"] = length
            group = []
            for repeat in range(manifest["repeats"]):
                name = f"md-{int(length*1000)}ps-r{repeat}"
                result = task(name, "simulation", cfg,
                    {"initial_pdb": str(ROOT / "inputs/p1-fsd-ey/1FME-unfolded.pdb"),
                     "reference_pdb": str(ROOT / "inputs/p1-fsd-ey/1FME-folded-model1.pdb")},
                    manifest["md_seeds"][repeat])
                import numpy as np
                with (Path(result["output_dir"]) / "sim.log").open() as stream:
                    logs = list(csv.reader(stream))
                values = np.array(logs[1:], dtype=float)
                if len(values) != result["frames"] or not np.isfinite(values).all():
                    raise RuntimeError("Short-to-long qualification gate failed: incomplete/nonfinite state log")
                group.append(result)
            md_groups[str(length)] = group
        cfg = science.load_config()
        cfg["simulation_length_ns"] = manifest["comparison_length_ns"]
        common = md_groups[str(manifest["comparison_length_ns"])]
        before = task("train-before", "train", cfg, {"results": common[:1]}, manifest["model_seed"])
        updated = task("train-updated", "train", cfg, {"results": common, "initial_model": before}, manifest["model_seed"])
        for model_label, model in (("frozen", before), ("updated", updated)):
            for repeat in range(2):
                task(f"infer-{model_label}-r{repeat}", "inference", cfg,
                     {"results": common, "model": model}, manifest["inference_seed"])
        save_new(out / "summary.json", {"status": "success", "tasks": len(records),
                 "end_to_end_s": time.monotonic() - start, "evaluation_ready": False,
                 "physical_md_ns": sum(r.get("physical_simulation_ns", 0) for r in records),
                 "science_decisions_changed": False, "purpose": "PILOT scientific qualification and cost only"})
    except BaseException as error:
        save_new(out / "failure.json", {"error_type": type(error).__name__, "error": str(error),
                                       "completed_records": len(records), "elapsed_s": time.monotonic()-start})
        raise
    finally:
        telemetry.terminate()
        telemetry.wait(timeout=10)
        telemetry_file.close()
        parsl.dfk().cleanup()
        parsl.clear()
        hashes = {str(p.relative_to(out)): science.sha256_file(p) for p in sorted(out.rglob("*"))
                  if p.is_file() and not p.name.startswith("._") and p.name != "checksums.json"}
        save_new(out / "checksums.json", hashes)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["audit", "run"])
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--lease", type=Path)
    p.add_argument("--manifest", type=Path)
    args = p.parse_args()
    if args.action == "audit":
        audit(args.output)
    else:
        if not args.lease or not args.manifest:
            p.error("run requires separately documented permission lease and frozen manifest")
        run_pilot(args.output, args.lease, args.manifest)


if __name__ == "__main__":
    main()
