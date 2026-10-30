"""人工座標と人工時系列だけのN1単体検査。実PDB/DCD/モデルを開かない。"""
import unittest
import numpy as np
from p1.n1_native_metrics import (proper_rmsd, native_contact_mask, q_from_mask,
    consensus_mask, best_so_far, observed_hits)


class NativeMetricsTest(unittest.TestCase):
    def setUp(self):
        self.x = np.array([[0., 0, 0], [1, 0, 0], [0, 2, 0], [0, 0, 3]])

    def test_identity(self):
        self.assertLess(proper_rmsd(self.x, self.x), 1e-12)

    def test_translation(self):
        self.assertLess(proper_rmsd(self.x + [10, -8, 30], self.x), 1e-12)

    def test_proper_rotation(self):
        rotation = np.array([[0., -1, 0], [1, 0, 0], [0, 0, 1]])
        self.assertLess(proper_rmsd(self.x @ rotation + 3, self.x), 1e-12)

    def test_reflection_not_rotation(self):
        self.assertGreater(proper_rmsd(self.x * [-1, 1, 1], self.x), 0.1)

    def test_scale_not_fit(self):
        self.assertGreater(proper_rmsd(self.x * 2, self.x), 0.1)

    def test_atom_order_not_silently_sorted(self):
        self.assertGreater(proper_rmsd(self.x[[1, 0, 2, 3]], self.x), 0.1)

    def test_shape_failure(self):
        with self.assertRaises(ValueError): proper_rmsd(self.x[:3], self.x)

    def test_nan_failure(self):
        x = self.x.copy(); x[0, 0] = np.nan
        with self.assertRaises(ValueError): proper_rmsd(x, self.x)

    def test_self_q(self):
        mask = native_contact_mask(self.x)
        self.assertEqual(q_from_mask(self.x, mask), 1.)
        self.assertEqual(int(mask.sum()), 1)

    def test_empty_native_failure(self):
        with self.assertRaises(ValueError): native_contact_mask(self.x * 100)

    def test_exact_cutoff_strict_vs_inclusive(self):
        x = self.x.copy(); x[3] = [0, 0, 8]
        with self.assertRaises(ValueError): native_contact_mask(x)
        mask = native_contact_mask(x, inclusive=True)
        self.assertEqual(q_from_mask(x, mask), 0.)
        self.assertEqual(q_from_mask(x, mask, inclusive=True), 1.)

    def test_extra_contacts_do_not_change_q_denominator(self):
        mask = native_contact_mask(self.x)
        self.assertEqual(q_from_mask(self.x * .1, mask), 1.)

    def test_invalid_mask(self):
        with self.assertRaises(ValueError): q_from_mask(self.x, np.eye(4, dtype=bool))

    def test_consensus_75_boundary(self):
        e = np.zeros((4, 4), dtype=bool); e[0, 3] = True
        obs = np.repeat(e[None], 4, axis=0); obs[3] = False
        self.assertTrue(consensus_mask(obs, e)[0, 3])

    def test_consensus_empty(self):
        with self.assertRaises(ValueError): consensus_mask(np.zeros((0, 4, 4), dtype=bool), np.zeros((4, 4), dtype=bool))

    def test_masked_best(self):
        a = best_so_far([1, 9, 5, 7], [False, True, True, True])
        np.testing.assert_allclose(a, [np.nan, 9, 5, 5], equal_nan=True)

    def test_censor_no_hit(self):
        r = observed_hits([0, 1, 2], [9, 8, 7], [0, .1, .2], [True]*3, 2)
        self.assertIsNone(r['first_hit_ps']); self.assertTrue(r['right_censored'])

    def test_no_bridge_across_invalid(self):
        r = observed_hits([0, 1, 2, 3], [1]*4, [.9]*4, [True, False, True, True], 2)
        self.assertEqual(r['episodes'], [(0, 0, 0.), (2, 3, 1.)])

    def test_combined_hit(self):
        r = observed_hits([0, 1, 2], [1, 1, 3], [.2, .9, .9], [True]*3, 2, .8)
        self.assertEqual(r['first_hit_ps'], 1.)
        self.assertEqual(r['total_observed_dwell_ps'], 0.)

    def test_threshold_unset_fails(self):
        with self.assertRaises(ValueError): observed_hits([0], [1], [.5], [True])

    def test_duplicate_time_fails(self):
        with self.assertRaises(ValueError): observed_hits([1, 1], [1, 1], [.5, .5], [True, True], 2)

    def test_bad_q_fails(self):
        with self.assertRaises(ValueError): observed_hits([1], [1], [2], [True], 2)


if __name__ == '__main__':
    unittest.main()
