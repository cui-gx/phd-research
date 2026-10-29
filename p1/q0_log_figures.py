"""保存されたQ0表から診断図だけを作る。学習・推論はしない。"""
import os,resource,time,csv,json
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path(__file__).parent/'mpl-cache')
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from q0_log_audit import digest,write,read
p=Path(__import__('sys').argv[1]);o=p/'artifacts/q0-20261029-v1/output';start=time.monotonic();cpu=time.process_time()
curves={}
for r in csv.DictReader((o/'model-loss-per-step.csv').open()):curves.setdefault((r['arm'],r['task_id']),[]).append(float(r['total']))
fig,axes=plt.subplots(1,3,figsize=(12,3.6),sharey=True)
for ax,arm in zip(axes,['M0','F1','F2']):
 for (a,tid),v in curves.items():
  if a==arm:ax.plot(range(1,201),v,color='0.25',alpha=.35,lw=.6)
 ax.set_yscale('log');ax.set_title(arm);ax.set_xlabel('Optimizer step');ax.grid(alpha=.2)
axes[0].set_ylabel('Raw total loss (log scale)');fig.tight_layout();fig.savefig(o/'loss-curves.png',dpi=170);plt.close(fig)
r=read(o/'descriptive-summary.json')['root_records'];fig,axes=plt.subplots(1,2,figsize=(10,3.5))
for ax,field,label in zip(axes,['temperature_K_window_','potential_kJ_mol_window_'],['Temperature (K)','Potential energy (kJ/mol)']):
 for x in r:
  ax.plot(range(4),[x[field+str(t)] for t in [0,100,200,500]],color='0.25' if x['kind']=='history' else '0.65',alpha=.6,lw=.8,linestyle='-' if x['kind']=='history' else '--')
 ax.set_xticks(range(4),['0-100','100-200','200-500','500-end']);ax.set_xlabel('Local window (ps)');ax.set_ylabel(label);ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(o/'md-root-windows.png',dpi=170);plt.close(fig)
f=p/'source/inputs/p1-fsd-ey/1FME-unfolded.pdb';rows=[l for l in f.read_text().splitlines() if l.startswith(('ATOM  ','HETATM'))];res=list(dict.fromkeys(l[21:27] for l in rows));inventory=read(o/'preparation-inventory.json');inventory[0]['first_residue_atom_names']=[l[12:16].strip() for l in rows if l[21:27]==res[0]];inventory[0]['last_residue_atom_names']=[l[12:16].strip() for l in rows if l[21:27]==res[-1]];write(o/'preparation-inventory.json',inventory)
write(o/'figure-costs.json',dict(wall_s=time.monotonic()-start,CPU_s=time.process_time()-cpu,peak_RSS_MiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,code_sha256=digest(Path(__file__)),CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],matplotlib=matplotlib.__version__,startup_and_import_time_included=False))
write(o/'prior-pass-costs.json',dict(main=read(p/'artifacts/q0-20261029-v1/output-before-boundary-fix/costs.json'),summary=read(p/'artifacts/q0-20261029-v1/output-before-boundary-fix/supplemental-costs.json'),one_intermediate_summary_timing='NOT_RETAINED; final costs are not an exact all-process cumulative total'))
write(o/'output-sha256.json',{f.name:digest(f) for f in o.iterdir() if f.is_file() and f.name!='output-sha256.json'})
