"""Bounded real-science workers for the P1 server qualification run pack.

Usage: python -m p1.server.science REQUEST.json RESULT.json
Public interface: run_request(request: dict) -> dict.

Heavy libraries load only inside tasks. Scientific construction/analysis reuse
hash-verified DeepDriveMD source; model and LOF use mdlearn and scikit-learn.
See science_sources.md for adaptation boundaries and the JSON interface.
"""

from __future__ import annotations

import ast
import copy
from contextlib import contextmanager
import hashlib
import importlib.metadata
import inspect
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import time
import traceback
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Dict, Optional, Tuple, Union

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "configs/p1_server_science.json"
UPSTREAM_MD = ROOT / "literature/p1-concrete-2026-10-19/source-snapshots/deepdrivemd/apps/openmm_simulation/app.py"
UPSTREAM_MD_SHA256 = "9e744c4a4628a7833c57666d43ccca14b58e1842e796846c5761b566b17a15ba"
MDLEARN_TRAINER_SHA256 = "df099022af7e38162371eff5abd607ccc31bba22b5f714838b6ea96d0ac4297a"
ADAPTER_VERSION = "p1-science-worker-v2-s2"
PathLike = Union[str, Path]

STAGE_OPERATIONS = {
    "worker_setup": "Installed package version collection and result metadata setup",
    "md_initialization": "Library imports, initial/restart PDB IO, checks, system/context creation, minimization, velocities, reporter setup",
    "md_simulation": "OpenMM step including synchronous trajectory/log reporter IO, final energy retrieval and checks",
    "md_analysis_and_write": "Reporter close, coordinate checks, alignment, contacts/RMSD, array writes, artifact hashing and result assembly",
    "train_data_preparation_and_io": "Imports, immutable snapshot verification/write, array loading/assembly and split-size checks; inside train task",
    "train_model_initialization": "mdlearn/PyTorch import, source verification, seed/device/threads setup and trainer creation; CUDA synchronized at end",
    "train_fit_including_checkpoint": "mdlearn fit: batching, training, validation, scheduled checkpoint IO; CUDA synchronized at end",
    "train_checkpoint_verification_and_write": "Loss checks, final checkpoint existence/hash, model ID and loss JSON writing; actual checkpoint save is nested inside fit",
    "infer_data_preparation_and_io": "Imports, immutable snapshot verification/write and data assembly; inside inference task",
    "infer_model_load": "Model metadata/hash checks, trainer initialization, checkpoint read/load; CUDA synchronized at end",
    "infer_embedding": "mdlearn predict and embedding validity checks; CUDA synchronized at end",
    "infer_lof_sort_and_write": "CPU LOF, stable LOF/RMSD ranking, lineage IDs and embedding/selection writes",
    "worker_finalize": "Successful result merge or failure traceback capture before final result serialization",
}


class ComponentTimer:
    """Disjoint wall-time partition plus explicitly non-additive child timings."""

    def __init__(self, clock=None):
        self.clock = clock or time.perf_counter
        self.start = self.clock()
        self.active_start = self.start
        self.active = "worker_setup"
        self.stages = []
        self.nested_stages = []
        self.finished = False

    def _close(self, end, status):
        self.stages.append({"stage": self.active,
                            "start_offset_s": self.active_start - self.start,
                            "end_offset_s": end - self.start,
                            "wall_time_s": end - self.active_start,
                            "status": status, "includes": STAGE_OPERATIONS[self.active]})

    def stage(self, name, previous_status="complete"):
        if self.finished or name not in STAGE_OPERATIONS:
            raise ValueError("Cannot enter an unknown stage or restart a finished timer")
        now = self.clock()
        self._close(now, previous_status)
        self.active, self.active_start = name, now

    @contextmanager
    def nested(self, name):
        parent, start = self.active, self.clock()
        status = "complete"
        try:
            yield
        except BaseException:
            status = "failed"
            raise
        finally:
            end = self.clock()
            self.nested_stages.append({"stage": name, "included_in": parent,
                                      "start_offset_s": start - self.start,
                                      "end_offset_s": end - self.start,
                                      "wall_time_s": end - start, "status": status})

    def finish(self):
        if self.finished:
            raise ValueError("Timer already finished")
        end = self.clock()
        self._close(end, "complete")
        self.finished = True
        return {"schema_version": 1, "clock": "time.perf_counter",
                "wall_time_s": end - self.start,
                "boundary": "After request.json write through result assembly; excludes CLI startup, request validation/write and final result.json serialization",
                "aggregation": "stages form a disjoint additive partition of wall_time_s; nested_stages are included in their named parent and must not be added again",
                "data_preparation_is_separately_scheduled": False,
                "stages": self.stages, "nested_stages": self.nested_stages}


def _synchronize_cuda(req, torch):
    if req["device"] == "cuda":
        torch.cuda.synchronize()


def digest_json(value: Any, prefix: str = "") -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return prefix + hashlib.sha256(body.encode()).hexdigest()


def sha256_file(path: PathLike) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json_new(path: PathLike, value: Any) -> None:
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def checked_positive(value: Any, name: str, integer: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a positive finite number")
    if not math.isfinite(value) or value <= 0 or (integer and int(value) != value):
        raise ValueError(f"{name} must be a positive finite {'integer' if integer else 'number'}")
    return value


def simulation_counts(config: dict) -> dict:
    """Refuse truncation of fractional steps or partial final report intervals."""
    for field in ("dt_ps", "report_interval_ps", "simulation_length_ns"):
        checked_positive(config[field], field)
    dt = Decimal(str(config["dt_ps"]))
    interval = Decimal(str(config["report_interval_ps"]))
    duration = Decimal(str(config["simulation_length_ns"])) * 1000
    if interval % dt or duration % dt or duration % interval:
        raise ValueError("MD duration and report interval must be exact integer step multiples")
    return {"nsteps": int(duration / dt), "report_steps": int(interval / dt),
            "expected_frames": int(duration / interval)}


def load_config(value: Any = None) -> dict:
    if value is None:
        value = DEFAULT_CONFIG
    config = (copy.deepcopy(value) if isinstance(value, dict)
              else json.loads(Path(value).read_text()))
    required = ("residues", "simulation_length_ns", "report_interval_ps", "dt_ps",
                "temperature_kelvin", "heat_bath_friction_coef", "mda_selection",
                "cutoff_angstrom", "minimum_frames", "num_outliers", "lof_neighbors", "cvae")
    if any(field not in config for field in required):
        raise ValueError("Incomplete science_config; provide the complete frozen configuration")
    if config["residues"] != 28 or config["mda_selection"] != "protein and name CA":
        raise ValueError("This bounded adapter supports the 28-residue BBA CA selection only")
    for field in ("temperature_kelvin", "heat_bath_friction_coef", "cutoff_angstrom"):
        checked_positive(config[field], field)
    for field in ("minimum_frames", "num_outliers", "lof_neighbors"):
        checked_positive(config[field], field, integer=True)
    cvae = config["cvae"]
    if cvae.get("input_shape") != [1, 28, 28]:
        raise ValueError("CVAE input_shape must be [1, 28, 28]")
    for field in ("epochs", "batch_size", "checkpoint_log_every"):
        checked_positive(cvae[field], f"cvae.{field}", integer=True)
    if cvae["checkpoint_log_every"] != cvae["epochs"]:
        raise ValueError("Save the last epoch: checkpoint_log_every must equal epochs")
    if not 0 < cvae.get("split_pct", 0.8) < 1:
        raise ValueError("cvae.split_pct must lie strictly between zero and one")
    if cvae.get("num_data_workers", 0) == 0 and cvae.get("prefetch_factor") is not None:
        raise ValueError("PyTorch with num_data_workers=0 requires prefetch_factor=null")
    if cvae.get("use_wandb", False):
        raise ValueError("External experiment logging is not enabled in this run pack")
    counts = simulation_counts(config)
    if counts["expected_frames"] < config["minimum_frames"]:
        raise ValueError("The requested MD segment produces fewer than minimum_frames")
    digest_json(config)  # Reject nonfinite values anywhere, before importing science libraries.
    return config


def normalize_request(request: dict) -> dict:
    req = copy.deepcopy(request)
    if req.get("task_type") not in {"simulation", "train", "inference"}:
        raise ValueError("task_type must be simulation, train or inference")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", str(req.get("task_id", ""))):
        raise ValueError("task_id must be a nonempty filesystem-safe identifier")
    checked_positive(req.get("seed"), "seed", integer=True)
    if req["seed"] >= 2**31:
        raise ValueError("seed must be in [1, 2**31-1]")
    if req.get("device") not in {"cpu", "cuda"}:
        raise ValueError("device must be explicitly cpu or cuda")
    if req["device"] == "cpu" and req.get("purpose") != "cpu_functional":
        raise ValueError("CPU is allowed only with purpose=cpu_functional")
    if req.get("purpose") not in {"cpu_functional", "qualification", "development"}:
        raise ValueError("Formal evaluation is not enabled; choose an explicit preparation purpose")
    if not isinstance(req.get("inputs"), dict):
        raise ValueError("inputs must be an object")
    if not req.get("output_dir"):
        raise ValueError("A unique output_dir is required")
    req["output_dir"] = str(Path(req["output_dir"]).resolve())
    req["science_config"] = load_config(req.get("science_config"))
    req["science_config_id"] = digest_json(req["science_config"], "science-")
    req["cpu_threads"] = int(checked_positive(req.get("cpu_threads", 1), "cpu_threads", True))
    return req


def validate_pdb_pair(pdb_path: PathLike, reference_path: PathLike) -> None:
    """Check CA residue/name order before a library attempts structural alignment."""
    def signature(path):
        atoms = []
        chains = set()
        models = 0
        for line in Path(path).read_text().splitlines():
            if line.startswith("MODEL "):
                models += 1
                if models > 1:
                    raise ValueError("Use one explicitly selected PDB model")
            if line.startswith(("ATOM  ", "HETATM")) and line[12:16].strip() == "CA":
                if line[16:17].strip() not in {"", "A"}:
                    raise ValueError("Alternative CA coordinates require explicit preprocessing")
                chains.add(line[21:22])
                atoms.append((line[17:20].strip(), line[22:27].strip()))
        if len(chains) != 1:
            raise ValueError("This bounded adapter supports one CA chain only")
        return atoms
    first, reference = signature(pdb_path), signature(reference_path)
    if len(first) != 28 or len(reference) != 28 or first != reference:
        raise ValueError("Initial and reference PDB must have matching ordered 28 CA residues")


def freeze_snapshot(results: list[dict], config_id: str) -> dict:
    """Copy and fingerprint exactly the completed files consumed by a task."""
    if not results:
        raise ValueError("An empty trajectory snapshot cannot be used for learning")
    members, seen = [], set()
    for result in copy.deepcopy(results):
        rid = result.get("result_id")
        if not rid or rid in seen:
            raise ValueError("Missing or duplicate result_id in snapshot")
        seen.add(rid)
        if result.get("status") != "success" or not result.get("valid"):
            raise ValueError("Snapshot contains an unsuccessful or invalid MD result")
        if result.get("science_config_id") != config_id:
            raise ValueError("Snapshot configuration does not match the requested scientific rules")
        member = {"result_id": rid, "frames": result["frames"]}
        for key in ("contact_map_path", "rmsd_path", "pdb_path", "dcd_path"):
            path = Path(result[key]).resolve()
            expected = result.get("artifact_sha256", {}).get(key)
            actual = sha256_file(path)
            if not expected or actual != expected:
                raise ValueError(f"Missing/mismatched immutable artifact hash: {key}")
            member[key] = str(path)
            member[key + "_sha256"] = actual
        members.append(member)
    snapshot = {"science_config_id": config_id, "results": members}
    # IDs do not depend on where a run directory was copied or mounted.
    identity = [{k: v for k, v in row.items() if not k.endswith("_path")} for row in members]
    snapshot["snapshot_id"] = digest_json({"science_config_id": config_id, "results": identity}, "data-")
    return snapshot


def rank_rows(rows: list[dict], num_outliers: int) -> list[dict]:
    """DeepDriveMD LOF-top-N then RMSD; explicit stable ties for reproducibility."""
    checked_positive(num_outliers, "num_outliers", integer=True)
    items = copy.deepcopy(rows)
    for row in items:
        if any(not math.isfinite(float(row[key])) for key in ("lof", "rmsd_angstrom")):
            raise ValueError("Nonfinite LOF/RMSD is an invalid ranking, never repaired to zero")
    tie = lambda row: (str(row["result_id"]), int(row["frame"]))
    shortlist = sorted(items, key=lambda row: (row["lof"], *tie(row)))[:num_outliers]
    return sorted(shortlist, key=lambda row: (row["rmsd_angstrom"], row["lof"], *tie(row)))


def _upstream_functions():
    """Load two audited scientific functions without old Colmena/pydantic imports."""
    if sha256_file(UPSTREAM_MD) != UPSTREAM_MD_SHA256:
        raise ValueError("Pinned DeepDriveMD scientific source hash mismatch")
    import openmm
    import openmm.app as app
    import openmm.unit as u
    import MDAnalysis
    import numpy as np
    from MDAnalysis.analysis import align, distances, rms
    tree = ast.parse(UPSTREAM_MD.read_text())
    configure = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name == "_configure_amber_implicit")
    klass = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                 and node.name == "MDSimulationApplication")
    analyze = next(node for node in klass.body if isinstance(node, ast.FunctionDef)
                   and node.name == "analyze_simulation")
    module = ast.Module(body=[configure, analyze], type_ignores=[])
    env = dict(openmm=openmm, app=app, u=u, MDAnalysis=MDAnalysis, np=np,
               align=align, distances=distances, rms=rms, Dict=Dict, Optional=Optional,
               Tuple=Tuple, Path=Path, PathLike=PathLike)
    exec(compile(module, str(UPSTREAM_MD), "exec"), env)
    return env["_configure_amber_implicit"], env["analyze_simulation"]


def _cuda_binding() -> str:
    value = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if not value or "," in value or value == "-1":
        raise ValueError("CUDA tasks require exactly one assigned CUDA_VISIBLE_DEVICES entry")
    return value


def _seed_all(seed: int, torch_module=None):
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    if torch_module is not None:
        torch_module.manual_seed(seed)
        if torch_module.cuda.is_available():
            torch_module.cuda.manual_seed_all(seed)
        torch_module.backends.cudnn.benchmark = False
        torch_module.backends.cudnn.deterministic = True


def _simulation(req: dict) -> dict:
    timer = req["_component_timer"]
    timer.stage("md_initialization")
    import numpy as np
    import openmm
    import openmm.app as app
    import openmm.unit as u
    import MDAnalysis
    configure, analyze = _upstream_functions()
    config, inputs, out = req["science_config"], req["inputs"], Path(req["output_dir"])
    reference = Path(inputs["reference_pdb"]).resolve()
    pdb_path = out / "initial.pdb"
    lineage = copy.deepcopy(inputs.get("restart"))
    if lineage:
        for key in ("pdb_path", "dcd_path", "frame", "ranking_id", "model_id", "training_snapshot_id"):
            if key not in lineage:
                raise ValueError(f"Restart is missing lineage field {key}")
        source = MDAnalysis.Universe(str(lineage["pdb_path"]), str(lineage["dcd_path"]))
        frame = lineage["frame"]
        if isinstance(frame, bool) or not isinstance(frame, int) or not 0 <= frame < len(source.trajectory):
            raise ValueError("Restart frame outside source trajectory")
        source.trajectory[frame]
        source.atoms.write(str(pdb_path))
    else:
        source_path = Path(inputs["initial_pdb"]).resolve()
        pdb_path.write_bytes(source_path.read_bytes())
    validate_pdb_pair(pdb_path, reference)
    _seed_all(req["seed"])
    if req["device"] == "cuda":
        binding = _cuda_binding()
        platform = openmm.Platform.getPlatformByName("CUDA")
        properties = {"DeviceIndex": "0", "Precision": "mixed"}
    else:
        binding = None
        platform = openmm.Platform.getPlatformByName("CPU")
        properties = {"Threads": str(req["cpu_threads"])}
    sim, pdb = configure(pdb_path, None, config["dt_ps"], config["temperature_kelvin"],
                         config["heat_bath_friction_coef"], platform, properties)
    sim.integrator.setRandomNumberSeed(req["seed"])
    # The upstream helper constructs its Context before exposing the integrator.
    # Rebuild it after setting the RNG seed so the newly created Context uses it.
    sim.context.reinitialize(preserveState=False)
    sim.context.setPositions(pdb.getPositions())
    sim.minimizeEnergy()
    sim.context.setVelocitiesToTemperature(config["temperature_kelvin"] * u.kelvin, req["seed"])
    counts = simulation_counts(config)
    dcd_path, log_path = out / "sim.dcd", out / "sim.log"
    sim.reporters.append(app.DCDReporter(str(dcd_path), counts["report_steps"]))
    sim.reporters.append(app.StateDataReporter(str(log_path), counts["report_steps"],
                        step=True, time=True, potentialEnergy=True, totalEnergy=True, temperature=True))
    timer.stage("md_simulation")
    sim.step(counts["nsteps"])
    final_state = sim.context.getState(getPositions=True, getEnergy=True)
    energies = [final_state.getPotentialEnergy().value_in_unit(u.kilojoules_per_mole),
                final_state.getKineticEnergy().value_in_unit(u.kilojoules_per_mole)]
    if not all(math.isfinite(float(value)) for value in energies):
        raise ValueError("Nonfinite final MD energy")
    actual_platform = sim.context.getPlatform().getName()
    if req["device"] == "cuda" and actual_platform != "CUDA":
        raise ValueError("A CUDA task executed on a different OpenMM platform")
    timer.stage("md_analysis_and_write")
    # Close file handles before analysis and immutable hash calculation.
    sim.reporters.clear()
    del sim
    trajectory = MDAnalysis.Universe(str(pdb_path), str(dcd_path))
    if len(trajectory.trajectory) != counts["expected_frames"]:
        raise ValueError("MD trajectory has an unexpected number of frames")
    for ts in trajectory.trajectory:
        if not np.isfinite(ts.positions).all():
            raise ValueError("Nonfinite coordinates in trajectory")
    analysis_settings = SimpleNamespace(**config, rmsd_reference_pdb=reference)
    contacts, rmsds = analyze(SimpleNamespace(config=analysis_settings), pdb_path, dcd_path)
    contacts_out = np.empty(len(contacts), dtype=object)
    for i, vector in enumerate(contacts):
        contacts_out[i] = np.asarray(vector, dtype=np.int16)
    rmsds = np.asarray(rmsds, dtype=np.float64)
    if len(rmsds) != counts["expected_frames"] or not np.isfinite(rmsds).all():
        raise ValueError("Invalid RMSD analysis output")
    contact_path, rmsd_path = out / "contact_map.npy", out / "rmsd.npy"
    np.save(contact_path, contacts_out, allow_pickle=True)
    np.save(rmsd_path, rmsds, allow_pickle=False)
    artifact_paths = {"contact_map_path": contact_path, "rmsd_path": rmsd_path,
                      "pdb_path": pdb_path, "dcd_path": dcd_path}
    hashes = {key: sha256_file(path) for key, path in artifact_paths.items()}
    result_id = digest_json({"task_id": req["task_id"], "seed": req["seed"],
                            "config": req["science_config_id"], "artifacts": hashes}, "md-")
    return {"result_id": result_id, "valid": True, **{k: str(v) for k, v in artifact_paths.items()},
            "artifact_sha256": hashes, "reference_pdb_sha256": sha256_file(reference),
            "frames": len(rmsds), **counts, "physical_simulation_ns": config["simulation_length_ns"],
            "frame_interval_ps": config["report_interval_ps"], "first_frame_time_ps": config["report_interval_ps"],
            "rmsd_unit": "angstrom", "best_rmsd_angstrom": float(rmsds.min()),
            "actual_platform": actual_platform, "cuda_visible_devices": binding,
            "restart": lineage, "scientific_target_qualified": False}


def _load_snapshot(req: dict):
    import numpy as np
    snapshot = freeze_snapshot(req["inputs"]["results"], req["science_config_id"])
    write_json_new(Path(req["output_dir"]) / "snapshot.json", snapshot)
    contacts, rmsds, frame_rows = [], [], []
    for member in snapshot["results"]:
        # Only our hash-verified own outputs are eligible. Object npy is the
        # upstream sparse-contact format; never load untrusted downloaded npy.
        data = np.load(member["contact_map_path"], allow_pickle=True)
        rms = np.load(member["rmsd_path"], allow_pickle=False)
        if len(data) != len(rms) or len(rms) != member["frames"] or not np.isfinite(rms).all():
            raise ValueError("Inconsistent contact-map/RMSD/frame lengths")
        for frame, vector in enumerate(data):
            vector = np.asarray(vector, dtype=np.int64)
            if vector.ndim != 1 or len(vector) % 2 or (vector < 0).any() or (vector >= 28).any():
                raise ValueError("Malformed sparse CA contact map")
            contacts.append(vector)
            frame_rows.append({"result_id": member["result_id"], "frame": frame,
                               "rmsd_angstrom": float(rms[frame]), "pdb_path": member["pdb_path"],
                               "dcd_path": member["dcd_path"]})
        rmsds.extend(rms)
    x = np.empty(len(contacts), dtype=object)
    for index, vector in enumerate(contacts):
        x[index] = vector
    return snapshot, x, np.asarray(rmsds), frame_rows


def _trainer(req: dict):
    import torch
    from mdlearn.nn.models.vae.symmetric_conv2d_vae import SymmetricConv2dVAETrainer
    source_file = inspect.getsourcefile(SymmetricConv2dVAETrainer)
    if not source_file or sha256_file(source_file) != MDLEARN_TRAINER_SHA256:
        raise ValueError("mdlearn trainer does not match pinned source commit")
    if req["device"] == "cuda":
        _cuda_binding()
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise ValueError("A CUDA task must see exactly its one assigned usable GPU")
    _seed_all(req["seed"], torch)
    torch.set_num_threads(req["cpu_threads"])
    settings = copy.deepcopy(req["science_config"]["cvae"])
    settings.update(seed=req["seed"], device=req["device"])
    trainer = SymmetricConv2dVAETrainer(**settings)
    # Upstream fit calls _set_num_threads. The allocated CPU budget must remain
    # fixed even if upstream defaults to the entire host's CPU count.
    trainer._set_num_threads = lambda: torch.set_num_threads(req["cpu_threads"])
    return trainer, torch


def _train(req: dict) -> dict:
    timer = req["_component_timer"]
    timer.stage("train_data_preparation_and_io")
    import numpy as np
    snapshot, contacts, rmsds, _ = _load_snapshot(req)
    settings = req["science_config"]["cvae"]
    train_size = int(len(contacts) * settings.get("split_pct", 0.8))
    if min(train_size, len(contacts) - train_size) < settings["batch_size"]:
        raise ValueError("Not enough frames for both mdlearn drop_last training and validation batches")
    timer.stage("train_model_initialization")
    trainer, _torch = _trainer(req)
    parent = req["inputs"].get("initial_model")
    checkpoint_input, initial_epoch = None, 0
    if parent is not None:
        if (parent.get("status") != "success" or not parent.get("valid") or
                parent.get("science_config_id") != req["science_config_id"]):
            raise ValueError("Update requires a valid parent with the same scientific configuration")
        checkpoint_input = parent["model_weight_path"]
        if sha256_file(checkpoint_input) != parent["model_weight_sha256"]:
            raise ValueError("Parent checkpoint hash mismatch")
        state = _torch.load(checkpoint_input, map_location="cpu", weights_only=True)
        initial_epoch = int(state["epoch"])
        # mdlearn's public checkpoint interface restores model AND optimizer.
        # Its epochs parameter is an absolute last epoch, ours is an increment.
        trainer.epochs = initial_epoch + settings["epochs"]
    model_dir = Path(req["output_dir"]) / "model"
    _synchronize_cuda(req, _torch)
    timer.stage("train_fit_including_checkpoint")
    # fit imports this original writer on entry. Time it without changing its
    # arguments or behavior, then restore it even when training fails. Each task
    # runs in its own subprocess; this is not a globally concurrent patch.
    import mdlearn.utils as mdlearn_utils
    original_log_checkpoint = mdlearn_utils.log_checkpoint
    def measured_checkpoint(*args, **kwargs):
        with timer.nested("checkpoint_write"):
            return original_log_checkpoint(*args, **kwargs)
    try:
        mdlearn_utils.log_checkpoint = measured_checkpoint
        fit_kwargs = {"checkpoint": checkpoint_input} if checkpoint_input else {}
        trainer.fit(X=contacts, scalars={"rmsd": rmsds}, output_path=model_dir, **fit_kwargs)
        _synchronize_cuda(req, _torch)
    finally:
        mdlearn_utils.log_checkpoint = original_log_checkpoint
    timer.stage("train_checkpoint_verification_and_write")
    if not trainer.loss_curve_ or any(not np.isfinite(values).all() for values in trainer.loss_curve_.values()):
        raise ValueError("Nonfinite CVAE loss; this model cannot be published")
    final_epoch = initial_epoch + settings["epochs"]
    checkpoint = model_dir / "checkpoints" / f"checkpoint-epoch-{final_epoch}.pt"
    if not checkpoint.is_file():
        raise ValueError("Expected final-epoch CVAE checkpoint is missing")
    checkpoint_hash = sha256_file(checkpoint)
    model_id = digest_json({"weights": checkpoint_hash, "snapshot": snapshot["snapshot_id"],
                           "seed": req["seed"], "config": req["science_config_id"]}, "model-")
    write_json_new(Path(req["output_dir"]) / "loss.json", trainer.loss_curve_)
    return {"model_id": model_id, "model_weight_path": str(checkpoint),
            "model_weight_sha256": checkpoint_hash, "training_snapshot_id": snapshot["snapshot_id"],
            "training_result_ids": [r["result_id"] for r in snapshot["results"]],
            "training_frames": len(contacts), "trained_from_scratch": parent is None,
            "parent_model_id": parent["model_id"] if parent else None,
            "parent_checkpoint_sha256": parent["model_weight_sha256"] if parent else None,
            "initial_epoch": initial_epoch, "final_epoch": final_epoch,
            "epochs": settings["epochs"], "loss_curve": trainer.loss_curve_, "valid": True}


def _inference(req: dict) -> dict:
    timer = req["_component_timer"]
    timer.stage("infer_data_preparation_and_io")
    import numpy as np
    from sklearn.neighbors import LocalOutlierFactor
    snapshot, contacts, _rmsds, rows = _load_snapshot(req)
    timer.stage("infer_model_load")
    model = copy.deepcopy(req["inputs"]["model"])
    if model.get("status") != "success" or not model.get("valid"):
        raise ValueError("Inference requires a successful validated model result")
    if model.get("science_config_id") != req["science_config_id"]:
        raise ValueError("Model and inference scientific configurations differ")
    for field in ("model_id", "model_weight_path", "model_weight_sha256", "training_snapshot_id", "training_result_ids"):
        if field not in model:
            raise ValueError(f"Model is missing {field}")
    if sha256_file(model["model_weight_path"]) != model["model_weight_sha256"]:
        raise ValueError("Model checkpoint was modified after publication")
    neighbors = req["science_config"]["lof_neighbors"]
    if len(contacts) <= neighbors:
        raise ValueError("LOF requires more frames than lof_neighbors; do not silently change k")
    trainer, torch = _trainer(req)
    checkpoint = torch.load(model["model_weight_path"], map_location=trainer.device, weights_only=True)
    trainer.model.load_state_dict(checkpoint["model_state_dict"])
    _synchronize_cuda(req, torch)
    timer.stage("infer_embedding")
    embeddings, *_ = trainer.predict(X=contacts, inference_batch_size=req["science_config"].get("inference_batch_size", 128))
    _synchronize_cuda(req, torch)
    if len(embeddings) != len(rows) or not np.isfinite(embeddings).all():
        raise ValueError("Nonfinite or incomplete embeddings; no NaN-to-zero repair is allowed")
    timer.stage("infer_lof_sort_and_write")
    lof = LocalOutlierFactor(n_neighbors=neighbors, n_jobs=req["cpu_threads"])
    lof.fit(embeddings)
    for row, score in zip(rows, lof.negative_outlier_factor_):
        row["lof"] = float(score)
    # S2 diagnostic: preserve all scores before reference-RMSD reordering.
    # Existing selection semantics remain unchanged.
    write_json_new(Path(req["output_dir"]) / "candidate-scores.json", rows)
    selections = rank_rows(rows, req["science_config"]["num_outliers"])
    ranking_id = digest_json({"model_id": model["model_id"], "data": snapshot["snapshot_id"],
                              "selections": [{k: v for k, v in row.items() if not k.endswith("_path")} for row in selections]}, "rank-")
    for row in selections:
        row.update(ranking_id=ranking_id, model_id=model["model_id"],
                   training_snapshot_id=model["training_snapshot_id"],
                   training_result_ids=copy.deepcopy(model["training_result_ids"]))
    np.save(Path(req["output_dir"]) / "embeddings.npy", embeddings, allow_pickle=False)
    write_json_new(Path(req["output_dir"]) / "selections.json", selections)
    return {"ranking_id": ranking_id, "model_id": model["model_id"],
            "training_snapshot_id": model["training_snapshot_id"],
            "training_result_ids": model["training_result_ids"],
            "inference_snapshot_id": snapshot["snapshot_id"],
            "inference_result_ids": [r["result_id"] for r in snapshot["results"]],
            "selections": selections, "valid": True,
            "selection_classification": "existing_upstream_reference_guided_selection",
            "selection_rule": "CVAE embeddings -> LOF top N -> reference RMSD ascending"}


def _versions() -> dict:
    versions = {"python": sys.version.split()[0], "adapter": ADAPTER_VERSION}
    for name in ("openmm", "MDAnalysis", "numpy", "torch", "mdlearn", "scikit-learn"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def run_request(request: dict) -> dict:
    """Execute one request in a new directory. Never overwrites prior task evidence."""
    req = normalize_request(request)
    out = Path(req["output_dir"])
    out.mkdir(parents=True, exist_ok=False)
    write_json_new(out / "request.json", req)
    started = time.time()
    timer = ComponentTimer()
    req["_component_timer"] = timer
    result = {"schema_version": 1, "task_type": req["task_type"], "task_id": req["task_id"],
              "seed": req["seed"], "device": req["device"], "purpose": req["purpose"],
              "output_dir": str(out), "science_config_id": req["science_config_id"],
              "cpu_threads": req["cpu_threads"], "started_unix_s": started,
              "evidence_type": "local CPU/GPU measurement", "engineering_only": req["purpose"] == "cpu_functional",
              "evaluation_ready": False, "exploration_effect_evaluated": False,
              "selection_classification": "existing_upstream_reference_guided_selection",
              "runtime_reproduction": "Parsl worker integration with pinned DeepDriveMD scientific functions; not full Colmena reproduction",
              "versions": _versions(), "status": "failure", "valid": False}
    try:
        result.update({"simulation": _simulation, "train": _train, "inference": _inference}[req["task_type"]](req))
        timer.stage("worker_finalize")
        result["status"] = "success"
    except Exception as error:
        timer.stage("worker_finalize", previous_status="failed")
        result.update(status="failure", valid=False, error_type=type(error).__name__, error=str(error))
        (out / "failure.txt").write_text(traceback.format_exc())
    timing = timer.finish()
    result.update(ended_unix_s=time.time(), wall_time_s=timing["wall_time_s"], component_timing=timing)
    write_json_new(out / "result.json", result)
    return result


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("result", type=Path)
    args = parser.parse_args(argv)
    if args.result.exists():
        parser.error("Result path already exists; refusing to overwrite evidence")
    request = json.loads(args.request.read_text())
    try:
        result = run_request(request)
    except Exception as error:
        result = {"status": "failure", "valid": False, "evaluation_ready": False,
                  "exploration_effect_evaluated": False,
                  "task_id": request.get("task_id"), "task_type": request.get("task_type"),
                  "error_type": type(error).__name__, "error": str(error)}
    args.result.parent.mkdir(parents=True, exist_ok=True)
    if args.result.resolve() != (Path(request.get("output_dir", ".")) / "result.json").resolve():
        write_json_new(args.result, result)
    elif not args.result.exists():
        write_json_new(args.result, result)
    print(json.dumps({"task_id": result.get("task_id"), "status": result["status"]}))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
