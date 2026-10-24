"""Small deterministic checks before S2 supplement real-data runs."""
import unittest
import copy
from fractions import Fraction
import numpy as np

from p1.server.supplement_coverage import ca_measures, distance_features, drmsd, bins, occupancy, centers, center_visits, q_bin_indices
from p1.server.supplement_physics import compare_forces
from p1.server.supplement_selection import score_order, compare, optimizer_digest


class SupplementTests(unittest.TestCase):
    def test_units_distances_and_rigid_invariance(self):
        x=np.zeros((28,3),dtype=float)
        x[:,0]=np.arange(28)
        rg,q,ree,count=ca_measures(x,8)
        self.assertAlmostEqual(ree,27)
        self.assertEqual(count,90)
        self.assertEqual(len(distance_features(x)),325)
        transform=x@np.array([[0,1,0],[-1,0,0],[0,0,1]])+np.array([10,-7,3])
        self.assertTrue(np.allclose(distance_features(x),distance_features(transform),atol=1e-6))
        self.assertAlmostEqual(float(drmsd(distance_features(x),distance_features(transform))),0,places=6)
        self.assertTrue(np.allclose(ca_measures(x)[0:3],ca_measures(transform)[0:3]))

    def test_bin_boundary_and_negative_controls(self):
        x=np.array([0.0,1.0,2.0]); y=np.array([0.0,.05,.10])
        label=bins(x,y,1,.05)
        self.assertEqual(label.tolist(),[[0,0],[1,1],[2,2]])
        self.assertEqual(occupancy(label)["U"],3)
        self.assertEqual(occupancy(np.concatenate((label,label)))["U"],3)
        self.assertEqual(occupancy(label[::-1])["U"],3)
        self.assertLessEqual(occupancy(label[::2])["U"],3)
        with self.assertRaises(ValueError):bins(np.array([-1]),np.array([0]),1,.05)

    def test_center_strict_boundary_and_holdout(self):
        f=np.zeros((21,325),float)
        f[10]=1.0;f[20]=2.0
        ids=centers(f,1.0)
        self.assertEqual(ids,[0,20])
        result=center_visits(f[[0,10,20]],f[ids],ids,1.0)
        self.assertEqual(result["visited"],2)
        self.assertEqual(result["out_of_library_frames"],0)

    def test_all_exact_q_boundaries(self):
        counts=np.arange(301)
        for width in (.02,.05,.10):
            for shifted in (False,True):
                expected=[int((Fraction(int(c),300)/Fraction(str(width))-
                              (Fraction(1,2) if shifted else 0))//1) for c in counts]
                self.assertEqual(q_bin_indices(counts,width,shifted).tolist(),expected)
        self.assertEqual(int(q_bin_indices(np.array([45]),.05)[0]),3)

    def test_lof_stable_tie_and_identity(self):
        a=[{"result_id":"b","frame":2,"lof":-2.0},{"result_id":"a","frame":10,"lof":-2.0}]
        a.extend({"result_id":"c","frame":i,"lof":-1.0} for i in range(798))
        self.assertEqual(score_order(a)[0]["result_id"],"a")
        with self.assertRaises(ValueError):compare(a,a[::-1])

    def test_force_per_atom_not_cancellation(self):
        f=np.zeros((504,3));r=np.zeros((504,3));f[0,0]=1;f[1,0]=-1
        result=compare_forces(f,r)
        self.assertEqual(result["atom_delta_median_p95_max_kJ_mol_nm"][2],1)
        self.assertIsNone(result["relative_force_l2"])

    def test_restored_optimizer_does_not_mutate_shared_checkpoint(self):
        import torch
        parameter=torch.nn.Parameter(torch.tensor([1.0]))
        optimizer=torch.optim.RMSprop([parameter],lr=0.01)
        parameter.grad=torch.tensor([2.0]); optimizer.step()
        baseline=copy.deepcopy(optimizer.state_dict())
        digest=optimizer_digest(torch,baseline)
        other=torch.nn.Parameter(torch.tensor([1.0]))
        restored=torch.optim.RMSprop([other],lr=0.01)
        restored.load_state_dict(copy.deepcopy(baseline))
        other.grad=torch.tensor([3.0]); restored.step()
        self.assertEqual(optimizer_digest(torch,baseline),digest)
        self.assertNotEqual(optimizer_digest(torch,restored.state_dict()),digest)


if __name__=="__main__": unittest.main()
