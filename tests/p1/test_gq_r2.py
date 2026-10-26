"""合成小標本による境界条件検査。科学的有効性の認証ではない。"""
import unittest
import numpy as np
from p1.server.gq_r2 import regions, nearest, distances, descriptors, farthest_cover, quantiles


class RegionTests(unittest.TestCase):
    def test_empty_distribution_is_missing(self):
        self.assertIsNone(quantiles([]))

    def test_persistent_region_and_duplicate_time(self):
        f=np.array([[0],[2],[2.1],[2.2],[2.3]])
        t=np.array([0,1,2,3,4])
        reps,confirmed=regions(f,t,1,2)
        self.assertEqual(reps,[0,1])
        self.assertEqual(confirmed,[0,3])
        a,b=regions(np.repeat(f,2,axis=0),np.repeat(t,2),1,2)
        self.assertEqual(len(a),2)
        self.assertEqual(b[-1]//2,3)

    def test_invalid_gap_breaks_support(self):
        f=np.array([[0],[2],[2],[2],[2]])
        reps,_=regions(f,np.arange(5),1,2,valid=[True,True,False,True,True])
        self.assertEqual(reps,[0])
        reps,_=regions(f,[0,1,2,20,21],1,3,max_gap=1.01)
        self.assertEqual(reps,[0])

    def test_common_history_and_deadline(self):
        f=np.array([[0],[.2],[2],[2.1],[2.2]])
        history=np.array([[0],[.1]])
        reps,_=regions(f,np.arange(5),1,1,history=history)
        self.assertEqual(reps,[2])
        reps,_=regions(f,np.arange(5),1,1,history=history,published=[0,1,2,9,10],cutoff=3)
        self.assertEqual(reps,[])

    def test_exact_boundary_and_repeats(self):
        reps,_=regions(np.array([[0],[1],[1.0001],[0]]),np.arange(4),1)
        self.assertEqual(reps,[0,2])
        reps,_=regions(np.zeros((100,3)),np.arange(100),.5)
        self.assertEqual(reps,[0])

    def test_order_is_not_a_partition(self):
        a=np.array([[0],[.9],[1.8]])
        self.assertEqual(len(regions(a,np.arange(3),1)[0]),2)
        self.assertEqual(len(regions(a[[1,0,2]],np.arange(3),1)[0]),1)

    def test_blocked_distances_and_cover(self):
        rng=np.random.default_rng(1);f=rng.normal(size=(40,325))
        exact=distances(f,f[:7])
        d,ids=nearest(f,f[:7],block=3)
        np.testing.assert_allclose(d,exact.min(axis=1),atol=1e-12)
        rep=farthest_cover(f,1.3)
        self.assertLessEqual(nearest(f,f[rep])[0].max(),1.3+1e-10)

    def test_rigid_and_mirror_blind_spot(self):
        rng=np.random.default_rng(2);x=rng.normal(size=(28,3))
        y=x@np.diag([-1,-1,1])+13
        np.testing.assert_allclose(descriptors(x),descriptors(y),atol=1e-12)
        np.testing.assert_allclose(descriptors(x),descriptors(x*[-1,1,1]),atol=1e-12)

    def test_time_order_and_nonfinite_rejection(self):
        with self.assertRaises(ValueError):regions(np.ones((2,1)),[1,0],1,1)
        with self.assertRaises(ValueError):regions(np.array([[np.nan]]),[0],1)


if __name__=='__main__':
    unittest.main()
