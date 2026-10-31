"""実DCDを使わず、境界・全窓要約と外部保護門を検証する。"""
import tempfile
import unittest
from pathlib import Path
from nmr34_v2 import evaluate_chunks, References, summarize, window_ids, archive_metadata
from nmr34_v2_execute import canonical_keys, exclusive_json, limit_reason, stage
import numpy as np


class ExecutionTests(unittest.TestCase):
    def test_boundaries_and_phase(self):
        t=np.arange(1,8001,dtype=float)*.5
        for burn in (100,200,500):
            t2=t.copy();t2[2*burn-1]=np.nextafter(float(burn),np.inf)
            valid=np.ones(8000,dtype=bool);valid[2*burn+3]=False
            for spacing in (.5,2.):
                raw,ids=window_ids(t2,valid,burn,4,spacing)
                truth=np.array([i for i,v in enumerate(t2) if v>burn and v<=4000+1e-5])[::int(spacing/.5)]
                np.testing.assert_array_equal(raw,truth);np.testing.assert_array_equal(ids,truth[valid[truth]])
                self.assertEqual(raw[0],2*burn-1)

    def test_all_summaries_against_explicit_truth(self):
        rng=np.random.default_rng(34);refs=References(rng.normal(size=(34,28,3)))
        n=1100;x=rng.normal(size=(n,28,3));t=np.arange(1,n+1)*.5;valid=np.ones(n,dtype=bool);valid[10::23]=False
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);manifest,timer=evaluate_chunks([(x[i:i+100],t[i:i+100]) for i in range(0,n,100)],refs,p)
            windows=[(b,prefix,s) for b in (0,100,200,500) for prefix in (1,2,4) for s in (.5,2.)]
            rows=summarize(p,manifest,t,valid,windows,timer)
            r=refs.rmsd(x);_,q,_=refs.contacts(x);aa=r.argmin(axis=1);minimum=r[np.arange(n),aa];same=q[np.arange(n),aa]
            for row in rows:
                b,prefix,s=map(float,row['window'].split('_'));_,ii=window_ids(t,valid,b,prefix,s)
                if row['model']=='NMR34_MIN':rr,qq=minimum[ii],same[ii]
                else:k=row['model']-1;rr,qq=r[ii,k],q[ii,k]
                expect={'min_RMSD_A':rr.min(),'mean_RMSD_A':rr.mean(),'median_RMSD_A':np.median(rr),
                        'p10_RMSD_A':np.quantile(rr,.1),'argmin_frame':ii[rr.argmin()],
                        'Q_at_argmin':qq[rr.argmin()],'mean_Q':qq.mean()}
                for key,value in expect.items():self.assertAlmostEqual(row[key],value,places=11)
            self.assertEqual(len(rows),840)
            with self.assertRaises(ValueError):archive_metadata(p,np.arange(n),np.arange(n),t,t,~valid,np.zeros((n,1),bool))

    def test_atom_keys_and_resource_gates(self):
        self.assertEqual(canonical_keys([[['A','   1',' ','GLU',' ']]]),[[('A','1','','GLU','')]])
        limit={'wall_s':900,'stage_s':300,'RSS_bytes':2*1024**3,'output_bytes':256*1024**2}
        self.assertIsNone(limit_reason(1,1,1,1,limit))
        for args,want in [((900,1,1,1),'wall'),((1,300,1,1),'stage'),((1,1,2*1024**3+1,1),'RSS'),((1,1,1,256*1024**2+1),'disk')]:
            self.assertEqual(limit_reason(*args,limit),want)
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);stage(p,'artificial');self.assertTrue((p/'stage.json').exists())
            exclusive_json(p/'receipt.json',{'status':'PASS'})
            with self.assertRaises(FileExistsError):exclusive_json(p/'receipt.json',{})

    def test_external_watchdog_and_restart(self):
        import json,sys
        from nmr34_v2_execute import supervise
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);bundle=p/'bundle';bundle.mkdir()
            limits={'wall_s':.2,'stage_s':300,'RSS_bytes':2*1024**3,'output_bytes':256*1024**2}
            (bundle/'config.json').write_text(json.dumps({'limits':limits}))
            with self.assertRaises(RuntimeError):
                supervise(p,bundle,p/'out',[sys.executable,'-c','import time;time.sleep(2)'])
            result=json.loads((p/'out/supervisor-final.json').read_text())
            self.assertEqual(result['status'],'STOPPED');self.assertEqual(result['protection_reason'],'wall')
            with self.assertRaises(ValueError):supervise(p,bundle,p/'out')
            self.assertTrue((p/'out/budget.jsonl').read_text().count('END')==1)


if __name__=='__main__':unittest.main(verbosity=2)
