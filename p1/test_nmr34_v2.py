"""人工座標・人工時刻のみのv2工程試験。実データ読取りは禁止。"""
import tempfile
import unittest
from pathlib import Path
from nmr34_v2 import (References, Run, Timer, archive_metadata, ensemble, evaluate_chunks,
                      load_ca_once, proper_rmsd, save_json, sha256, summarize, verify_inputs, window_ids, fingerprint, export_references)
import numpy as np


class SyntheticTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(34)
        self.native = self.rng.normal(size=(34, 28, 3)) * 2
        self.refs = References(self.native)

    def test_rigid_mirror_units(self):
        x = self.native[0]; rot = np.array([[0.,-1,0],[1,0,0],[0,0,1]])
        self.assertLess(proper_rmsd(x@rot+4,x),1e-12)
        self.assertGreater(proper_rmsd(x*[-1,1,1],x),.01)
        self.assertLess(proper_rmsd(x/10*10,x),1e-12)
        with self.assertRaises(ValueError):References(np.zeros((34,27,3)))

    def test_scalar_chunk(self):
        x = self.rng.normal(size=(13,28,3))
        want = np.array([[proper_rmsd(v,r) for r in self.native] for v in x])
        for size in (1,3,13):
            got = np.concatenate([self.refs.rmsd(x[i:i+size]) for i in range(0,len(x),size)])
            self.assertLess(np.max(abs(got-want)),1e-12)
        with self.assertRaises(ValueError):self.refs.rmsd(np.full((1,28,3),np.nan))

    def test_fixed_contacts_boundary(self):
        # index0/3だけを境界の近傍へ配置。他の点も有限に保つ。
        native=np.zeros((34,28,3)); native[:,:,0]=np.arange(28)[None,:]*20
        native[:,3,0]=7.9; native[1,3,0]=8.1
        native[:,7,0]=native[:,4,0]+1.
        refs=References(native)
        x=native[:1].copy();x[0,3,0]=8.
        count,q,margin=refs.contacts(x)
        self.assertEqual(margin[0,0,3],0.)
        self.assertTrue(refs.masks[0,0,3]);self.assertFalse(refs.masks[1,0,3])
        distances=np.linalg.norm(x[:,:,None]-x[:,None,:],axis=-1)
        for k in range(34):
            c=int(((distances[0]<8)&refs.masks[k]).sum())
            self.assertEqual(count[0,k],c);self.assertEqual(q[0,k],c/refs.den[k])
        for v in (np.nextafter(8.,0.),8.,np.nextafter(8.,np.inf)):
            x[0,3,0]=v;cc,_,_=refs.contacts(x)
            self.assertEqual(int(cc[0,0]),int(((np.linalg.norm(x[0,:,None]-x[0,None,:],axis=-1)<8)&refs.masks[0]).sum()))

    def test_ensemble_ties(self):
        r=np.array([[2.,1.,1.],[1.,2.,3.]]);q=np.array([[.9,.2,.8],[.3,.4,.5]])
        minimum,arg,same=ensemble(r,q)
        np.testing.assert_array_equal(arg,[2,1]);np.testing.assert_array_equal(same,[.2,.3])
        np.testing.assert_array_equal(minimum,[1,1])

    def test_window_phase_quality(self):
        t=np.arange(1,801)*.5; valid=np.ones(800,dtype=bool);valid[201]=False
        sampled,ii=window_ids(t,valid,100,1,2.)
        self.assertEqual(sampled[0],200);self.assertEqual(sampled[1],204)
        self.assertTrue(201 not in ii)
        # 浮動表現による旧200ps境界を無断で丸めない。
        t[399]=np.nextafter(200.,np.inf)
        sampled,_=window_ids(t,valid,200,1,.5)
        self.assertEqual(sampled[0],399)

    def test_sha_lock_failure_repeat(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);source=p/'input';source.write_bytes(b'artificial')
            verify_inputs({source:sha256(source)})
            first=fingerprint({'chunk':512},{'input':sha256(source)},[source])
            self.assertEqual(first,fingerprint({'chunk':512},{'input':sha256(source)},[source]))
            self.assertNotEqual(first,fingerprint({'chunk':1},{'input':sha256(source)},[source]))
            with self.assertRaises(ValueError):verify_inputs({source:'0'*64})
            out=p/'run'
            with Run(out,'fixed'):
                with self.assertRaises(BlockingIOError):
                    with Run(out,'fixed'):pass
            with self.assertRaises(ValueError):
                with Run(out,'fixed'):pass
            with self.assertRaises(RuntimeError):
                with Run(p/'failure','fixed'):raise RuntimeError('人工停止')
            self.assertTrue((p/'failure/failure.json').exists())
            with self.assertRaises(ValueError):
                with Run(p/'failure','fixed'):pass

    def test_chunk_output_and_all_windows(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp);x=self.native[:8].copy();t=np.arange(1,9)*.5
            chunks=[(x[:3],t[:3]),(x[3:],t[3:])]
            manifest,timer=evaluate_chunks(chunks,self.refs,out,qualify=True)
            export_references(self.refs,out)
            valid=np.ones(8,dtype=bool)
            archive_metadata(out,np.arange(8),np.arange(8)+20,t,t,valid,np.zeros((8,2),bool))
            windows=[(b,p,s) for b in (0,100,200,500) for p in (1,2,4) for s in (.5,2.)]
            rows=summarize(out,manifest,t,valid,windows,timer)
            self.assertEqual(len(rows),35*24)
            self.assertEqual(sum(r['model']=='NMR34_MIN' for r in rows),24)
            with np.load(out/manifest[0]['path']) as z:
                for i,k in enumerate(z['argmin_model']):
                    self.assertEqual(z['Q_at_RMSD_argmin'][i],z['Q'][i,k-1])
            with self.assertRaises(FileExistsError):evaluate_chunks(chunks,self.refs,out)
            self.assertTrue(all(v['wall_s']>=0 for v in timer.records.values()))

    def test_cache_and_nonoverlap_stop(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'features.npz';np.savez_compressed(p,ca=self.native)
            np.testing.assert_array_equal(load_ca_once(p,1000000),self.native)
            with self.assertRaises(ValueError):load_ca_once(p,1)
            timer=Timer()
            with timer.measure('a'):
                with self.assertRaises(ValueError):
                    with timer.measure('b'):pass
            with self.assertRaises(RuntimeError):
                evaluate_chunks([(self.native[:1],np.array([.5]))],self.refs,Path(temp),
                                check=lambda: (_ for _ in ()).throw(RuntimeError('人工資源超過')))


if __name__=='__main__':unittest.main(verbosity=2)
