"""全量制御の人工行列・根内対応検査。実DCDは読まない。"""
import unittest,tempfile,json
from pathlib import Path
import nmr34_v2
import numpy as np
from nmr34_full import checkpoint
from nmr34_full_analyze import root_effects

class FullTests(unittest.TestCase):
    def test_root_pairing_shared_F0(self):
        x=np.zeros((8,2,3,24,9));x[:,0,1]=2;x[:,0,2]=5;x[:,1,1]=6;x[:,1,2]=1
        result=root_effects(x)
        np.testing.assert_array_equal(result[(2,1)][:,0],3*np.ones((8,24,9)))
        np.testing.assert_array_equal(result[(2,1)][:,1],-5*np.ones((8,24,9)))
        np.testing.assert_array_equal(result[(2,1)][:,2],-np.ones((8,24,9)))
        np.testing.assert_array_equal(result[(2,1)][:,3],-8*np.ones((8,24,9)))
        np.testing.assert_array_equal(result[(1,0)][:,0],2*np.ones((8,24,9)))
    def test_persistent_budget_nonreset(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'budget-state.json';checkpoint(p,dict(spent_s=19.,segment_open=False))
            prior=json.loads(p.read_text());checkpoint(p,dict(spent_s=prior['spent_s']+5,segment_open=False))
            self.assertEqual(json.loads(p.read_text())['spent_s'],24.)
    def test_matrix_structure(self):
        p=Path(__file__).parent.parent/'docs/P1-NMR34-FULL/manifest.json'
        if not p.exists():p=Path(__file__).parent.parent/'bundle/manifest.json'
        if not p.exists():self.skipTest('bundle未配置')
        m=json.loads(p.read_text());self.assertEqual(len(m),272);self.assertEqual(len({x['task_id'] for x in m}),272)
        self.assertEqual(sum(x['frames'] for x in m),2048000)
        for root in range(1,9):
            rr=[e for e in m if e['root_id']==f'r{root:02}'];self.assertEqual(len(rr),34)
            for st in ['s4','s8']:
                for arm,count in [('F0',3),('F1',6),('F2',6)]:
                    self.assertEqual(sum(e.get('state_id')==f'r{root:02}-{st}' and e.get('arm')==arm for e in rr),count)
        for e in m:self.assertEqual(e['scalar_frames'],[0,e['frames']//2,e['frames']-1])

    def test_explicit_partial_recovery_preserves_bytes(self):
        from nmr34_full import preserve_partial
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);dest=root/'partial';dest.mkdir();(dest/'evidence').write_bytes(b'unchanged')
            with self.assertRaises(ValueError):preserve_partial(root,dest,None)
            preserve_partial(root,dest,'researcher-test-approval')
            self.assertFalse(dest.exists())
            self.assertEqual(next((root/'failed-attempts').rglob('evidence')).read_bytes(),b'unchanged')

if __name__=='__main__':unittest.main(verbosity=2)
