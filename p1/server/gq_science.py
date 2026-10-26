"""Approved exploratory GQ probes; reuse pinned OpenMM/mdlearn components."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import time


def save(path, obj):
    path = Path(path)
    with path.open("x") as f:
        json.dump(obj, f, indent=2, allow_nan=False)


def build(method, seed):
    import openmm as mm
    from openmm import app, unit as u
    from .science import ROOT, _upstream_functions
    # Verify the pinned scientific construction source, without modifying it.
    _upstream_functions()
    pdb = app.PDBFile(str(ROOT/"inputs/p1-fsd-ey/1FME-unfolded.pdb"))
    ff = app.ForceField("amber14-all.xml", "implicit/gbn2.xml")
    options = dict(nonbondedMethod=app.NoCutoff if method == "no_cutoff" else app.CutoffNonPeriodic,
                   constraints=app.HBonds)
    if method != "no_cutoff":
        if method not in ("cutoff_1nm", "cutoff_2nm"):
            raise ValueError("Unregistered protocol")
        options["nonbondedCutoff"] = (1 if method == "cutoff_1nm" else 2)*u.nanometer
    system = ff.createSystem(pdb.topology, **options)
    details = []
    for force in system.getForces():
        group = 0 if isinstance(force, mm.NonbondedForce) else (1 if "GB" in type(force).__name__ else 2)
        force.setForceGroup(group)
        item = {"class": type(force).__name__, "group": group}
        for key in ("getNonbondedMethod", "getCutoffDistance", "getReactionFieldDielectric",
                    "getUseSwitchingFunction", "getUseDispersionCorrection"):
            if hasattr(force, key):
                item[key] = str(getattr(force, key)())
        if hasattr(force, "getNumGlobalParameters"):
            item["global_parameters"] = {force.getGlobalParameterName(i): force.getGlobalParameterDefaultValue(i) for i in range(force.getNumGlobalParameters())}
        details.append(item)
    integrator = mm.LangevinIntegrator(300*u.kelvin, 1/u.picosecond, .002*u.picosecond)
    integrator.setConstraintTolerance(1e-5)
    integrator.setRandomNumberSeed(seed)
    sim = app.Simulation(pdb.topology, system, integrator, mm.Platform.getPlatformByName("CUDA"),
                         {"DeviceIndex": "0", "Precision": "mixed", "DeterministicForces": "true"})
    return sim, pdb, details


def system_record(sim, details, out):
    import openmm as mm
    from openmm import app
    from .science import sha256_file
    xml = out/"system.xml"
    xml.write_text(mm.XmlSerializer.serialize(sim.system))
    data = Path(app.__file__).parent/"data"
    ff = {str(p.relative_to(data)): sha256_file(p) for p in [data/"amber14-all.xml", data/"implicit/gbn2.xml", *sorted((data/"amber14").glob("*.xml"))]}
    return {"system_sha256": sha256_file(xml), "forces": details, "forcefield_sha256": ff,
            "particles": sim.system.getNumParticles(), "constraints": sim.system.getNumConstraints(),
            "periodic": sim.system.usesPeriodicBoundaryConditions()}


def physics(req, out):
    import numpy as np
    from openmm import unit as u
    import MDAnalysis as mda
    from .science import ROOT, sha256_file
    initial = ROOT/"inputs/p1-fsd-ey/1FME-unfolded.pdb"
    snapshots = [("unfolded", np.array(mda.Universe(str(initial)).atoms.positions)/10, sha256_file(initial))]
    old = Path(req["s2_run"])
    for rep in (0, 1):
        task = old/"tasks"/f"md-1000ps-r{rep}"
        r = json.loads((task/"result.json").read_text())
        for kind in ("pdb_path", "dcd_path"):
            assert sha256_file(r[kind]) == r["artifact_sha256"][kind]
        universe = mda.Universe(r["pdb_path"], r["dcd_path"])
        for frame in (0, 1999):
            universe.trajectory[frame]
            snapshots.append((f"old-r{rep}-frame{frame}", universe.atoms.positions.copy()/10, r["artifact_sha256"]["dcd_path"]))
    rows, arrays, protocols, coordinate_inputs, coordinate_projected = [], [], [], [], []
    for method in ("cutoff_1nm", "cutoff_2nm", "no_cutoff"):
        sim, pdb, details = build(method, 2026102601)
        sub = out/method
        sub.mkdir()
        protocols.append(dict(method=method, **system_record(sim, details, sub)))
        for source, xyz, sha in snapshots:
            for repeat in range(4):
                begin = time.perf_counter()
                sim.context.setPositions(xyz*u.nanometer)
                sim.context.applyConstraints(1e-5)
                corrected = sim.context.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(u.nanometer)
                coordinate_index=len(coordinate_inputs)
                coordinate_inputs.append(np.array(xyz,copy=True))
                coordinate_projected.append(np.array(corrected,copy=True))
                for group in (-1, 0, 1, 2):
                    state = sim.context.getState(getEnergy=True, getForces=True, groups=-1 if group == -1 else 1 << group)
                    e = float(state.getPotentialEnergy().value_in_unit(u.kilojoule_per_mole))
                    f = np.asarray(state.getForces(asNumpy=True).value_in_unit(u.kilojoule_per_mole/u.nanometer))
                    if not np.isfinite(e) or not np.isfinite(f).all():
                        raise RuntimeError("Nonfinite fixed-coordinate state")
                    rows.append(dict(method=method, source=source, input_sha256=sha, repetition=repeat,
                                     warmup=repeat == 0, group=group, energy_kJ_mol=e,
                                     coordinate_index=coordinate_index,
                                     elapsed_from_setPositions_s=time.perf_counter()-begin,
                                     position_correction_max_nm=float(np.max(np.linalg.norm(corrected-xyz, axis=1)))))
                    arrays.append(f)
        del sim
    np.savez_compressed(out/"forces.npz", forces=np.array(arrays))
    np.savez_compressed(out/"fixed-coordinates.npz",input_nm=np.array(coordinate_inputs),projected_nm=np.array(coordinate_projected))
    save(out/"evaluations.json", rows)
    save(out/"protocols.json", protocols)
    return {"status": "success", "evaluations": len(rows), "fixed_structures": len(snapshots), "MD_steps": 0}


def md(req, out):
    import numpy as np
    import openmm as mm
    from openmm import app, unit as u
    from .science import ROOT, sha256_file
    begin = time.perf_counter()
    sim, pdb, details = build(req["method"], req["seed"])
    systems = system_record(sim, details, out)
    with (out/"initial.pdb").open("x") as f:
        app.PDBFile.writeFile(pdb.topology, pdb.positions, f)
    initial_ns = 0.0
    if req.get("checkpoint"):
        cp = Path(req["checkpoint"])
        if sha256_file(cp) != req["checkpoint_sha256"]:
            raise ValueError("Continuation checkpoint hash mismatch")
        sim.loadCheckpoint(str(cp))
        initial_ns = sim.context.getState().getTime().value_in_unit(u.nanosecond)
        if abs(initial_ns-req["initial_ns"]) > 1e-6:
            raise ValueError("Continuation time mismatch")
        restart = "full_checkpoint_continuation_no_minimization_no_velocity_reset"
    else:
        sim.context.setPositions(pdb.positions)
        sim.minimizeEnergy(tolerance=10*u.kilojoule_per_mole/u.nanometer, maxIterations=1000)
        sim.context.setVelocitiesToTemperature(300*u.kelvin, req["seed"])
        restart = "minimized_coordinates_and_seeded_velocities"
        with (out/"minimized.pdb").open("x") as f:
            app.PDBFile.writeFile(pdb.topology, sim.context.getState(getPositions=True).getPositions(), f)
    initialization = time.perf_counter()-begin
    steps = round(req["length_ns"]*1000/.002)
    if abs(steps*.002-req["length_ns"]*1000) > 1e-8:
        raise ValueError("Noninteger integration length")
    dcd = app.DCDReporter(str(out/"sim.dcd"), 250)
    state_reporter = app.StateDataReporter(str(out/"sim.csv"), 250, step=True, time=True,
                    potentialEnergy=True, kineticEnergy=True, totalEnergy=True, temperature=True)
    sim.reporters.extend([dcd, state_reporter])
    integration_start = time.perf_counter()
    sim.step(steps)
    sim.saveCheckpoint(str(out/"final.chk"))
    state = sim.context.getState(getEnergy=True, getPositions=True, getVelocities=True)
    positions = np.asarray(state.getPositions(asNumpy=True).value_in_unit(u.nanometer))
    if not np.isfinite(positions).all() or not np.isfinite(state.getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)):
        raise RuntimeError("Nonfinite MD result")
    with (out/"final.pdb").open("x") as f:
        app.PDBFile.writeFile(pdb.topology, state.getPositions(), f)
    # Close reporters before hashing, analysis or publication.
    sim.reporters.clear()
    dcd._out.close()
    state_reporter._out.close()
    integration_s = time.perf_counter()-integration_start
    result = dict(status="success", method=req["method"], seed=req["seed"], length_ns=req["length_ns"],
                  initial_ns=initial_ns, final_ns=initial_ns+req["length_ns"], restart=restart,
                  initialization_s=initialization, integration_reporter_checkpoint_s=integration_s,
                  expected_frames=steps//250, systems=systems)
    del sim
    result["internal_s"] = time.perf_counter()-begin
    result["artifacts"] = {p.name: sha256_file(p) for p in out.iterdir() if p.is_file()}
    return result


def ai(req, out):
    import numpy as np
    import torch
    from sklearn.neighbors import LocalOutlierFactor
    from .science import load_config, freeze_snapshot, _trainer, sha256_file
    begin=time.perf_counter()
    records=req["inputs"]["results"]
    # MD provenance is checked against its original MD config. Training epochs
    # are a separate cost-probe recipe, never a rewrite of historical records.
    snapshot=freeze_snapshot(records,records[0]["science_config_id"])
    contacts=[]
    for member in snapshot["results"]:
        contacts.extend(np.load(member["contact_map_path"],allow_pickle=True))
    x=np.empty(len(contacts),dtype=object)
    for i,v in enumerate(contacts):x[i]=v
    data_s=time.perf_counter()-begin
    cfg = load_config()
    model=req["inputs"]["model"]
    cp=Path(model["model_weight_path"])
    if sha256_file(cp)!=model["model_weight_sha256"]:raise ValueError("Cost-probe checkpoint SHA mismatch")
    state=torch.load(cp,map_location="cpu",weights_only=True)
    initial_epoch=int(state["epoch"])
    final_epoch=initial_epoch+req["epochs"] if req["task_type"]=="train" else initial_epoch
    cfg["cvae"]["epochs"]=final_epoch
    cfg["cvae"]["checkpoint_log_every"]=final_epoch
    trainer,torch=_trainer(dict(science_config=cfg,device="cuda",seed=req["seed"],cpu_threads=2))
    torch.cuda.synchronize()
    setup_s=time.perf_counter()-begin-data_s
    operation=time.perf_counter()
    if req["task_type"]=="train":
        trainer.fit(X=x,output_path=out/"model",checkpoint=str(cp))
        torch.cuda.synchronize()
        curve={k:[float(v) for v in values] for k,values in trainer.loss_curve_.items()}
        if not curve or any(not np.isfinite(values).all() for values in curve.values()):raise RuntimeError("Nonfinite training cost probe")
        checkpoint=out/"model/checkpoints"/f"checkpoint-epoch-{final_epoch}.pt"
        if not checkpoint.exists():raise RuntimeError("Missing final cost-probe checkpoint")
        result=dict(model_weight_path=str(checkpoint),model_weight_sha256=sha256_file(checkpoint),loss_curve=curve,
                    initial_epoch=initial_epoch,final_epoch=final_epoch,incremental_epochs=req["epochs"])
    else:
        trainer.model.load_state_dict(state["model_state_dict"])
        torch.cuda.synchronize()
        embeddings,*_=trainer.predict(X=x,inference_batch_size=64)
        torch.cuda.synchronize()
        lof=LocalOutlierFactor(n_neighbors=20,n_jobs=2).fit(embeddings)
        if not np.isfinite(embeddings).all() or not np.isfinite(lof.negative_outlier_factor_).all():raise RuntimeError("Nonfinite inference cost probe")
        np.savez_compressed(out/"inference.npz",embeddings=embeddings,lof=lof.negative_outlier_factor_)
        result=dict(embedding_shape=list(embeddings.shape),candidate_pool=len(x),native_reference_used=False)
    result.update(status="success",valid=True,task_type=req["task_type"],seed=req["seed"],training_frames=len(x),
                  data_preparation_s=data_s,model_initialization_s=setup_s,operation_including_output_s=time.perf_counter()-operation,
                  internal_s=time.perf_counter()-begin,input_snapshot_id=snapshot["snapshot_id"],
                  parent_checkpoint_sha256=model["model_weight_sha256"],input_MD_config_id=records[0]["science_config_id"],
                  device="cuda",cost_only=True,exploration_effect_evaluated=False)
    return result


def main():
    req = json.loads(Path(sys.argv[1]).read_text())
    out = Path(req["output_dir"])
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    try:
        result = {"physics": physics, "md": md, "ai": ai}[req["kind"]](req, out)
        result["worker_elapsed_s"] = time.perf_counter()-start
        save(out/"result.json", result)
    except BaseException as exc:
        save(out/"failure.json", {"error": repr(exc), "elapsed_s": time.perf_counter()-start})
        raise


if __name__ == "__main__":
    main()
