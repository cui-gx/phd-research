"""B1の時間抽出、SHA保護、同一履歴距離の再利用を小標本で検査する。"""
import unittest
import tempfile
from pathlib import Path
import numpy as np
from p1.server.b1_science import indices,require_hash
from p1.server.gq_r2 import regions,nearest,sha


class B1Tests(unittest.TestCase):
    def test_restoration_helpers_import(self):
        from p1.server.supplement_selection import tensor_digest,optimizer_digest
        self.assertTrue(callable(tensor_digest) and callable(optimizer_digest))

    def test_time_split_and_no_replacement(self):
        t=np.arange(1,8001)*.5;valid=np.ones(8000,dtype=bool)
        old=indices(t,valid,100,1600,800);new=indices(t,valid,2000,3600,400)
        self.assertEqual(len(set(old)),800)
        self.assertTrue(t[old].max()<=1600 and t[new].min()>2000)
        self.assertFalse(set(old)&set(new))

    def test_shortage_stops(self):
        with self.assertRaises(ValueError):indices(np.arange(10),np.ones(10,dtype=bool),0,5,800)

    def test_sha_change_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';p.write_text('first');expected=sha(p);p.write_text('changed')
            with self.assertRaises(ValueError):require_hash(p,expected)

    def test_history_cache_identical_and_no_free_seed(self):
        f=np.array([[0],[2],[2.1],[2.2],[4.]]);t=np.arange(5);history=np.array([[0],[.1]])
        dd=nearest(f,history)[0]
        for tau in (0,1,2):
            self.assertEqual(regions(f,t,1,tau,history=history),regions(f,t,1,tau,history_min_distance=dd))
        self.assertEqual(regions(f,t,10,history_min_distance=dd),([],[]))

    def test_invalid_cache_rejected(self):
        with self.assertRaises(ValueError):regions(np.ones((3,1)),np.arange(3),1,history_min_distance=[-1,0,1])
        with self.assertRaises(ValueError):regions(np.ones((3,1)),np.arange(3),1,history_min_distance=[0,1])


if __name__=='__main__':unittest.main()
