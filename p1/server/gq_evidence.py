"""Produce compact server-derived audit tables; no GPU work or paper verdict."""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import sys
import subprocess


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def publish(root, analysis, output, artifacts):
    from .qualification import occupancy, pdb_inventory
    from .support import ROOT
    import openmm as mm
    from openmm import app,unit as u
    check=occupancy()
    output.mkdir(parents=True,exist_ok=False)
    def dump(name,value):(output/name).write_text(json.dumps(value,indent=2,allow_nan=False))
    rows=json.loads((root/'budget-ledger.json').read_text())
    totals={s:sum(r['charged_s'] for r in rows if r['stage']==s) for s in ('gq1','gq2','gq3','reserve')}
    assert all(r['status']!='pending' for r in rows)
    assert sum(totals.values())<=3600 and all(totals[s]<=cap for s,cap in zip(totals,(600,1200,1200,600)))
    costs=[]
    for item in rows:
        task=root/'tasks'/item['name'];r=json.loads((task/'science/result.json').read_text())
        request=json.loads((task/'request.json').read_text())
        costs.append(dict(task=item['name'],stage=item['stage'],kind=request['kind'],status=item['status'],
            gpu_occupation_s=item['charged_s'],worker_s=r.get('internal_s',r.get('worker_elapsed_s')),
            initialization_s=r.get('initialization_s',r.get('model_initialization_s')),
            operation_s=r.get('integration_reporter_checkpoint_s',r.get('operation_including_output_s')),
            MD_ns=r.get('length_ns',0),seed=r.get('seed',request.get('seed')),epochs=r.get('incremental_epochs'),
            data_preparation_s=r.get('data_preparation_s'),peak_sampled_RSS_bytes=item['peak_process_tree_rss_bytes']))
    with (output/'task-costs.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=costs[0].keys());w.writeheader();w.writerows(costs)
    dump('budget-summary.json',dict(stage_used_s=totals,total_used_s=sum(totals.values()),remaining_s=3600-sum(totals.values()),
        all_tasks=rows,cost_boundary='supervised child launch through complete reap; all failures and warmup included',
        cpu_only_analysis_charged_as_gpu=False,phase_caps_s=dict(gq1=600,gq2=1200,gq3=1200,reserve=600)))
    for name in ('trajectory-summary.json','grid-sensitivity.json','library-validation.json','shape-alias.json','invariance.json','physics-comparisons.json','analysis-runtime.json'):
        (output/name).write_bytes((analysis/name).read_bytes())
    (output/'trajectory-diagnostics.png').write_bytes((analysis/'trajectory-diagnostics.png').read_bytes())
    # Compact coverage summaries are generated on the server, not hand-filled.
    grids=json.loads((analysis/'grid-sensitivity.json').read_text())
    summaries=[]
    for seed in sorted({r['seed'] for r in grids}):
        subset=[r for r in grids if r['seed']==seed]
        main=[r for r in subset if r['burn_ps']==100 and r['radius_A']==8 and r['rg_width_A']==1 and r['q_width']==.05 and not r['shifted']]
        summaries.append(dict(seed=seed,main_stride_U={str(r['stride']):r['U'] for r in main},
            all_grid_U_min_max=[min(r['U'] for r in subset),max(r['U'] for r in subset)],
            all_grid_U_over_N_max=max(r['U_over_N'] for r in subset),all_grid_max_bin_fraction=max(r['max_bin_fraction'] for r in subset)))
    dump('coverage-summary.json',summaries)
    initial=ROOT/'inputs/p1-fsd-ey/1FME-unfolded.pdb'
    pdb=app.PDBFile(str(initial));system=app.ForceField('amber14-all.xml','implicit/gbn2.xml').createSystem(pdb.topology,nonbondedMethod=app.NoCutoff,constraints=app.HBonds)
    nb=next(f for f in system.getForces() if isinstance(f,mm.NonbondedForce))
    inventory=pdb_inventory(initial);inventory['net_charge_e']=sum(f[0].value_in_unit(u.elementary_charge) for f in (nb.getParticleParameters(i) for i in range(nb.getNumParticles())))
    inventory['preparation_pH']='UNVERIFIED';dump('input-inventory.json',inventory)
    packages={}
    for name in ('openmm','torch','numpy','MDAnalysis','mdlearn','parsl','scikit-learn','matplotlib','psutil'):
        packages[name]=metadata.version(name)
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True).strip()
    dump('environment-summary.json',dict(python=sys.version,packages=packages,openmm_build=mm.version.version,
         gpu_inventory_without_private_identifiers=gpu,CPU_affinity_count=3,numerical_threads=2))
    # Preserve exact installed source and forcefield fingerprints without paths.
    from openmm.app.internal import customgbforces
    source_files=[ROOT/'p1/server'/name for name in ('gq_control.py','gq_science.py','gq_analysis.py','gq_evidence.py','science.py','support.py','supplement_coverage.py')]
    fingerprints={str(p.relative_to(ROOT)):sha(p) for p in source_files}
    fingerprints['installed_openmm_customgbforces.py']=sha(Path(customgbforces.__file__))
    dump('executed-source-sha256.json',fingerprints)
    before=json.loads((artifacts/'original-evidence-before.json').read_text());mismatch=[];count=0
    for run_name,items in before.items():
        for rel,expected in items.items():
            count+=1;p=root.parent/run_name/rel
            if not p.exists() or sha(p)!=expected:mismatch.append(run_name+'/'+rel)
    dump('original-evidence-integrity.json',dict(checked_files=count,mismatches=mismatch,originals_preserved=not mismatch))
    if mismatch:raise RuntimeError('Original evidence changed')
    # Independent arithmetic checks on saved component arrays. These numerical
    # residuals are not scientific acceptance thresholds for a solvent model.
    import numpy as np
    physics=root/'tasks/physics-recheck-01/science'
    evaluations=json.loads((physics/'evaluations.json').read_text())
    arrays=np.load(physics/'forces.npz')['forces'];energy_errors=[];force_errors=[];relative_force_errors=[]
    for method in ('cutoff_1nm','cutoff_2nm','no_cutoff'):
        for source in sorted({r['source'] for r in evaluations}):
            for repetition in range(4):
                indexed={r['group']:i for i,r in enumerate(evaluations) if r['method']==method and r['source']==source and r['repetition']==repetition}
                energy_errors.append(abs(evaluations[indexed[-1]]['energy_kJ_mol']-sum(evaluations[indexed[g]]['energy_kJ_mol'] for g in (0,1,2))))
                force_errors.append(float(np.max(np.abs(arrays[indexed[-1]]-sum(arrays[indexed[g]] for g in (0,1,2))))))
                relative_force_errors.append(float(np.linalg.norm(arrays[indexed[-1]]-sum(arrays[indexed[g]] for g in (0,1,2)))/max(1,np.linalg.norm(arrays[indexed[-1]]))))
    artifact_errors=[]
    for item in rows:
        base=root/'tasks'/item['name']/'science';result=json.loads((base/'result.json').read_text())
        for name,expected in result.get('artifacts',{}).items():
            if sha(base/name)!=expected:artifact_errors.append(item['name']+'/'+name)
    if artifact_errors:raise RuntimeError('New MD immutable artifact hash mismatch')
    dump('numerical-audit.json',dict(component_energy_sum_max_abs_kJ_mol=max(energy_errors),
         component_force_sum_max_abs_kJ_mol_nm=max(force_errors),component_checks=len(energy_errors),new_MD_artifact_hash_mismatches=artifact_errors))
    audit=json.loads((output/'numerical-audit.json').read_text());audit['component_force_sum_max_relative_L2']=max(relative_force_errors);dump('numerical-audit.json',audit)
    old_grids=json.loads((artifacts/'analysis-gq2/grid-sensitivity.json').read_text())
    trajectories=json.loads((analysis/'trajectory-summary.json').read_text());bytask={r['task']:r for r in trajectories}
    prefix=[]
    for suffix in (11,12,13,14):
        seed=2026102600+suffix
        one=next(r for r in old_grids if r['seed']==seed and r['burn_ps']==100 and r['stride']==1 and r['radius_A']==8 and r['rg_width_A']==1 and r['q_width']==.05 and not r['shifted'])
        four=next(r for r in summaries if r['seed']==seed)
        first=bytask[f'root-{suffix}-1ns'];extended=bytask[f'extend-{suffix}-to4ns']
        original=np.load(analysis/f'root-{suffix}-1ns-features.npz');continuation=np.load(analysis/f'extend-{suffix}-to4ns-features.npz')
        d=np.concatenate((original['distances_A'],continuation['distances_A']))
        from .supplement_coverage import drmsd
        distance=drmsd(d,d[0])
        prefix.append(dict(seed=seed,one_ns_U=one['U'],four_ns_U=four['main_stride_U']['1'],
          full_dRMSD_to_initial_A_min_median_max=[float(distance.min()),float(np.median(distance)),float(distance.max())],
          continuation_dihedral_change_abs_deg_median_p95=extended['dihedral_circular_change_from_first_abs_deg_median_p95'],
          nominal_total_ns=4,nominal_post100ps_ns=3.9,
          mean_temperature_K=(first['quality']['temperature_K_mean']+3*extended['quality']['temperature_K_mean'])/4,
          max_constraint_error_A=max(first['quality']['constraint_distance_max_error_A'],extended['quality']['constraint_distance_max_error_A'])))
    dump('one-ns-vs-four-ns.json',prefix)
    manifest={str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and p.name!='round.lock'}
    dump('raw-artifact-sha256.json',manifest)
    dump('validation.json',dict(status='PASS_ARTIFACT_AND_BUDGET_CHECKS_ONLY',scientific_evaluation_ready=False,S3='NOT_APPROVED',
        task_count=len(rows),raw_files=len(manifest),original_files_verified=count,failed_GPU_tasks=sum(r['status']!='complete' for r in rows),
        missing_pending_tasks=False,phase_caps_respected=True,source_role='exploratory_GQ_not_BC_effect_data'))
    print(json.dumps(dict(tasks=len(rows),total_GPU_s=sum(totals.values()),physical_MD_ns=sum(c['MD_ns'] for c in costs),original_files_verified=count,compact_output=str(output))),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--analysis',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();publish(a.root,a.analysis,a.output,a.artifacts)
