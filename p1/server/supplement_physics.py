"""S2 supplement C: same-coordinate OpenMM CPU energy/force evaluations only."""
from __future__ import annotations

import json
from pathlib import Path
import time
import numpy as np

from .science import sha256_file
from .supplement_coverage import local_path

FRAME_IDS = (0, 19, 199, 999, 1999)
METHODS = (("cutoff_1nm", "CutoffNonPeriodic", 1.0),
           ("cutoff_2nm", "CutoffNonPeriodic", 2.0),
           ("no_cutoff", "NoCutoff", None))


def force_summary(system, unit):
    result=[]
    for index,force in enumerate(system.getForces()):
        row={"index":index,"class":force.__class__.__name__,"name":force.getName()}
        for field in ("getNonbondedMethod","getCutoffDistance","getSolventDielectric",
                      "getSoluteDielectric","getKappa","getSurfaceAreaEnergy"):
            if hasattr(force,field):
                value=getattr(force,field)()
                row[field]=str(value)
        result.append(row)
    return result


def snapshots(run):
    import MDAnalysis as mda
    run=Path(run)
    source=Path("inputs/p1-fsd-ey/1FME-unfolded.pdb")
    if not source.exists(): raise ValueError("Initial PDB missing")
    u=mda.Universe(str(source))
    if u.atoms.n_atoms!=504: raise ValueError("Initial topology does not have 504 atoms")
    output=[("unfolded",None,u.atoms.positions.astype(np.float64).copy(),sha256_file(source))]
    for rep in (0,1):
        task=f"md-1000ps-r{rep}"
        result=json.loads((run/"tasks"/task/"result.json").read_text())
        pdb=local_path(run,result["pdb_path"]); dcd=local_path(run,result["dcd_path"])
        if sha256_file(pdb)!=result["artifact_sha256"]["pdb_path"] or sha256_file(dcd)!=result["artifact_sha256"]["dcd_path"]:
            raise ValueError("Raw input hash mismatch")
        traj=mda.Universe(str(pdb),str(dcd))
        if traj.atoms.n_atoms!=504 or len(traj.trajectory)!=2000:
            raise ValueError("Unexpected raw trajectory size")
        for frame in FRAME_IDS:
            traj.trajectory[frame]
            output.append((task,frame,traj.atoms.positions.astype(np.float64).copy(),result["artifact_sha256"]["dcd_path"]))
    if len(output)!=11 or any(not np.isfinite(x[2]).all() for x in output):
        raise ValueError("Missing/nonfinite fixed snapshots")
    return output


def compare_forces(f, reference):
    delta=np.linalg.norm(f-reference,axis=1)
    den=np.sum(reference*reference)
    return {"atom_delta_median_p95_max_kJ_mol_nm":[float(np.median(delta)),float(np.percentile(delta,95)),float(np.max(delta))],
            "force_rms_delta_kJ_mol_nm":float(np.sqrt(np.mean(delta*delta))),
            "relative_force_l2":float(np.sqrt(np.sum(delta*delta)/den)) if den else None}


def analyze(run,out,plan_commit,analysis_commit):
    import openmm
    import openmm.app as app
    import openmm.unit as unit
    run,out=Path(run),Path(out)
    out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    fixed=snapshots(run)
    pdb=app.PDBFile("inputs/p1-fsd-ey/1FME-unfolded.pdb")
    if pdb.topology.getNumAtoms()!=504: raise ValueError("OpenMM topology atoms != 504")
    ff=app.ForceField("amber14-all.xml","implicit/gbn2.xml")
    platform=openmm.Platform.getPlatformByName("CPU")
    rows=[]; systems=[]; errors=[]
    for method_name,method,cutoff in METHODS:
        try:
            create_start=time.monotonic()
            kwargs={"nonbondedMethod":getattr(app,method),"constraints":app.HBonds}
            if cutoff is not None: kwargs["nonbondedCutoff"]=cutoff*unit.nanometer
            system=ff.createSystem(pdb.topology,**kwargs)
            xml=openmm.XmlSerializer.serialize(system)
            xmlpath=out/f"system-{method_name}.xml"
            xmlpath.write_text(xml)
            force_details=force_summary(system,unit)
            # Capture every relevant force's actual method/cutoff, not just app kwargs.
            relevant=[f for f in force_details if "Nonbonded" in f["class"] or "GB" in f["class"]]
            if len(relevant)<2: raise ValueError("Could not inspect both nonbonded and GB forces")
            systems.append({"method":method_name,"create_system_s":time.monotonic()-create_start,
                            "xml_sha256":sha256_file(xmlpath),"forces":force_details})
            integrator=openmm.LangevinIntegrator(300*unit.kelvin,1/unit.picosecond,0.002*unit.picosecond)
            context_start=time.monotonic()
            context=openmm.Context(system,integrator,platform,{"Threads":"2"})
            systems[-1]["create_context_s"]=time.monotonic()-context_start
            for source,frame,xyz,sha in fixed:
                position_start=time.monotonic()
                context.setPositions((xyz/10.0)*unit.nanometer)
                position_s=time.monotonic()-position_start
                for repetition in range(4):
                    request_start=time.monotonic()
                    state=context.getState(getEnergy=True,getForces=True)
                    request_s=time.monotonic()-request_start
                    energy=float(state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole))
                    forces=np.asarray(state.getForces(asNumpy=True).value_in_unit(unit.kilojoules_per_mole/unit.nanometer),dtype=np.float64)
                    if forces.shape!=(504,3) or not np.isfinite(forces).all() or not np.isfinite(energy):
                        raise ValueError("Nonfinite energy/force or bad shape")
                    source_result=json.loads((run/"tasks"/source/"result.json").read_text()) if source!="unfolded" else None
                    rows.append({"run_id":"s2-pilot-02","task_id":source,"result_id":
                                 source_result["result_id"] if source_result else "original-unfolded",
                                 "seed":source_result["seed"] if source_result else None,
                                 "method":method_name,"parameter_id":method_name,
                                 "analysis_commit":analysis_commit,"plan_commit":plan_commit,
                                 "frame_id_0based":frame,
                                 "physical_time_ps":None if frame is None else (frame+1)*0.5,
                                 "input_sha256":sha,"technical_repetition":repetition,
                                 "warmup":repetition==0,"set_positions_s":position_s if repetition==0 else None,
                                 "request_s":request_s,"energy_kJ_mol":energy,
                                 "forces":forces})
                    if time.monotonic()-start>300: raise TimeoutError("C 300s cap")
            systems[-1]["integrator_steps"]=0
            del context, integrator, system
        except Exception as e:
            errors.append({"method":method_name,"error":repr(e)})
            break
    (out/"systems.json").write_text(json.dumps(systems,indent=2))
    # Persist every request, including technical repetitions; force arrays are local processed data.
    np.savez_compressed(out/"physics-raw-evaluations.npz",forces=np.asarray([r.pop("forces") for r in rows]))
    (out/"physics-evaluations.json").write_text(json.dumps(rows,indent=2,allow_nan=False))
    summary=[]
    if not errors and len(rows)==132:
        arr=np.load(out/"physics-raw-evaluations.npz")["forces"]
        bykey={(r["method"],r["task_id"],r["frame_id_0based"],r["technical_repetition"]):(r,arr[i]) for i,r in enumerate(rows)}
        for source,frame,_,_ in fixed:
            nc=bykey[("no_cutoff",source,frame,1)]
            nc0=bykey[("no_cutoff","unfolded",None,1)][0]["energy_kJ_mol"]
            for method,_,_ in METHODS:
                repeats=[bykey[(method,source,frame,rep)] for rep in (1,2,3)]
                energy=[a[0]["energy_kJ_mol"] for a in repeats]
                forces=[a[1] for a in repeats]
                ref=nc[0]["energy_kJ_mol"]
                e0=bykey[(method,"unfolded",None,1)][0]["energy_kJ_mol"]
                # Repeat tolerance is relative to the first measured state.
                e_error=max(abs(v-energy[0])/max(1,abs(energy[0])) for v in energy)
                f_error=max(float(np.max(np.linalg.norm(f-forces[0],axis=1)/np.maximum(1,np.linalg.norm(forces[0],axis=1)))) for f in forces)
                summary.append({"source":source,"frame_id_0based":frame,"method":method,
                                "energy_kJ_mol_median_min_max":[float(np.median(energy)),min(energy),max(energy)],
                                "delta_E_vs_NoCutoff_kJ_mol":float(np.median(energy)-ref),
                                "relative_conformation_delta_E_kJ_mol":float((np.median(energy)-e0)-(ref-nc0)),
                                "request_s_median_min_max":[float(v) for v in (np.median([a[0]["request_s"] for a in repeats]),
                                                             min(a[0]["request_s"] for a in repeats),
                                                             max(a[0]["request_s"] for a in repeats))],
                                **compare_forces(forces[0],nc[1]),
                                "technical_repeat_energy_relative_max":e_error,
                                "technical_repeat_force_relative_max":f_error,
                                "repeat_warning":max(e_error,f_error)>1e-5})
    (out/"physics-sensitivity.json").write_text(json.dumps(summary,indent=2,allow_nan=False))
    (out/"physics-manifest.json").write_text(json.dumps({"status":"MEASURED" if len(summary)==33 else "INCOMPLETE",
        "platform":"CPU","openmm_version":openmm.version.version,"plan_commit":plan_commit,
        "analysis_commit":analysis_commit,"elapsed_s":time.monotonic()-start,"getState_calls":len(rows),
        "timed_calls":len([r for r in rows if not r["warmup"]]),"integrator_steps":0,"errors":errors},indent=2))
