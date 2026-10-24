"""Validate immutable target-GPU engineering evidence; no exploration metric."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib,math,csv
import numpy as np
import MDAnalysis as mda
ROOT=Path(__file__).resolve().parents[4]
base=ROOT/'results/raw/remote/2026-10-24-P1-gpu-loop-01'
art=Path(__file__).parent/'private-server-artifacts'
s=json.loads((base/'summary.json').read_text());m=json.loads((base/'manifest.json').read_text())
checks=json.loads((base/'checksums.json').read_text())
assert all(hashlib.sha256((base/p).read_bytes()).hexdigest()==h for p,h in checks.items())
results=[json.loads(p.read_text()) for p in sorted((base/'tasks').glob('*/result.json'))]
assert s['status']=='success' and len(results)==s['completed_valid_tasks']==7
assert s['gpu_slots']==s['worker_count']==1 and len(m['gpu_uuids'])==1
assert all(r['valid'] and r['device']=='cuda' and not r['exploration_effect_evaluated'] for r in results)
events=[json.loads(x) for x in (base/'events.jsonl').read_text().splitlines()]
active=set()
for e in events:
 if e['kind']=='task_dispatched':
  assert not active and e['gpu_uuid']==m['gpu_uuids'][0]
  assert set(e['cpu_ids']).issubset(set(m['worker_cpu_ids']))
  active.add(e['task_id'])
 elif e['kind']=='task_completed':
  assert e['task_id'] in active
  active.remove(e['task_id'])
assert not active
stages=defaultdict(float)
for r in results:
 t=r['component_timing'];last=0
 for st in t['stages']:
  assert math.isclose(st['start_offset_s'],last,abs_tol=1e-8) and st['wall_time_s']>=0
  last=st['end_offset_s'];stages[st['stage']]+=st['wall_time_s']
 assert math.isclose(last,r['wall_time_s'],abs_tol=1e-8)
md=[r for r in results if r['task_type']=='simulation']
assert all(r['actual_platform']=='CUDA' and r['frames']==40 and r['physical_simulation_ns']==0.02 for r in md)
train=next(r for r in results if r['task_type']=='train');infer=next(r for r in results if r['task_type']=='inference');restart=next(r for r in md if r.get('restart'))
assert train['model_id']==infer['model_id']==restart['restart']['model_id']
assert train['training_snapshot_id']==infer['training_snapshot_id']==restart['restart']['training_snapshot_id']
assert infer['ranking_id']==restart['restart']['ranking_id']
assert any(x['result_id']==restart['restart']['result_id'] and x['frame']==restart['restart']['frame'] for x in infer['selections'])
remote_run=Path(restart['output_dir']).parents[2]
def local(remote):return base/Path(remote).relative_to(remote_run)
lineage=restart['restart'];u=mda.Universe(str(local(lineage['pdb_path'])),str(local(lineage['dcd_path'])));u.trajectory[lineage['frame']]
v=mda.Universe(str(local(restart['pdb_path'])))
# PDB uses three decimal places in Angstrom. Allow only its representation error.
coord_error=float(np.max(np.abs(u.atoms.positions-v.atoms.positions)));assert coord_error<=0.001
telemetry=list(csv.reader((art/'gpu-loop-01-telemetry.csv').read_text().splitlines()))
assert telemetry and all(row[1].strip()==m['gpu_uuids'][0] for row in telemetry)
probe=json.loads((art/'cuda-probe.json').read_text());cap=json.loads((art/'installed-capability.json').read_text())
assert probe['finite_cuda_matmul'] and probe['visible_gpu_count']==1
peak=max(float(row[3]) for row in telemetry);util=[float(row[2]) for row in telemetry]
report={'status':'pass','evidence_type':'local CPU/GPU measurement','location':'authorized laboratory node','gpu_model':probe['device_name'],'gpu_count':1,'driver_version':cap['gpu_inventory']['stdout'].strip().split(',')[-1].strip(),'torch_cuda':probe['torch_cuda'],'compute_capability':probe['compute_capability'],'checksum_files_verified':len(checks),'task_counts':dict(Counter(r['task_type'] for r in results)),'wall_time_s_including_drain':s['wall_time_s_including_drain'],'physical_simulation_ns':sum(r['physical_simulation_ns'] for r in md),'total_frames':sum(r['frames'] for r in md),'task_wall_s':{r['task_id']:r['wall_time_s'] for r in results},'stage_total_s':dict(stages),'component_partition_verified':True,'max_simultaneous_tasks':1,'cpu_affinity_supported':m['cpu_affinity_supported'],'worker_controller_affinity_disjoint':not set(m['controller_cpu_ids'])&set(m['worker_cpu_ids']),'lineage_verified':True,'restart_coordinate_max_abs_error_angstrom':coord_error,'restart_coordinate_tolerance_angstrom':0.001,'telemetry_sample_period_ms':500,'telemetry_samples':len(telemetry),'gpu_memory_peak_mib':peak,'gpu_utilization_percent_min':min(util),'gpu_utilization_percent_max':max(util),'gpu_utilization_percent_sample_mean':sum(util)/len(util),'versions':train['versions'],'exploration_effect_evaluated':False,'formal_evaluation_campaigns':0,'framework_reproduction':'Parsl adapter reusing pinned DeepDriveMD science functions and mdlearn; original Colmena orchestration not run','known_summary_limitation':'completed_result_ids repeats model_id for inference; correct ranking_id and lineage verified in task results'}
print(json.dumps(report,ensure_ascii=False,indent=2))
