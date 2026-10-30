"""人工DCDのÅ単位・frame・欠損の工学資格。実軌跡は読まない。"""
import tempfile,json
from pathlib import Path
import numpy as np
import MDAnalysis as mda
from n1_native_metrics import proper_rmsd,native_contact_mask,q_from_mask
x=np.array([[0,0,0],[1,0,0],[0,2,0],[0,0,3]],dtype=float)
checks={}
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'artificial.dcd';u=mda.Universe.empty(4,trajectory=True)
 with mda.Writer(str(p),4,dt=.5) as w:
  for k in range(3):u.atoms.positions=x+k;w.write(u.atoms)
 v=mda.Universe.empty(4);v.load_new(str(p),convert_units=True)
 checks['three_frames']=len(v.trajectory)==3
 checks['Angstrom_roundtrip']=all(np.array_equal(ts.positions,x+i) for i,ts in enumerate(v.trajectory))
 checks['nm_to_A_explicit']=np.allclose((x/10)*10,x)
 try:v.load_new(str(Path(d)/'missing.dcd'));checks['missing_rejected']=False
 except (OSError,ValueError):checks['missing_rejected']=True
checks['proper_rotation']=proper_rmsd(x@np.array([[0,-1,0],[1,0,0],[0,0,1]])+3,x)<1e-12
y=x.copy();y[:,0]*=-1;checks['mirror_prohibited']=proper_rmsd(y,x)>1e-5
try:proper_rmsd(x[:3],x);checks['missing_atom_rejected']=False
except ValueError:checks['missing_atom_rejected']=True
try:proper_rmsd(np.full_like(x,np.nan),x);checks['NaN_rejected']=False
except ValueError:checks['NaN_rejected']=True
checks['native_self_Q']=q_from_mask(x,native_contact_mask(x))==1
assert all(checks.values()),checks
print(json.dumps(dict(status='PASS',synthetic_checks=checks,real_trajectories_read=0)))
