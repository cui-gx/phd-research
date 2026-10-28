"""R1の参照・階層・物理距離に対する小さな境界検査。サーバCPU専用。"""
import importlib.util
import os
from pathlib import Path
import unittest

import numpy as np

from p1.r1_cpu_review import matched_ids, metric_keys, root_statistics, atom_identity


class ReviewTests(unittest.TestCase):
    """不変条件を検査し、科学的改善を合格条件にしない。"""

    def test_count_matching_keeps_global_IDs(self):
        ids = np.array([200, 202, 207, 220, 250, 320, 900])
        np.testing.assert_array_equal(matched_ids(ids, 4), [200, 207, 250, 900])
        with self.assertRaises(ValueError):
            matched_ids(ids, 8)
        with self.assertRaises(ValueError):
            matched_ids(np.array([1, 1, 2]), 2)

    def test_all_registered_scales_present(self):
        keys = metric_keys()
        self.assertEqual(len(keys), 144)
        self.assertEqual(len(set(keys)), 144)
        self.assertEqual({(x[3], x[4]) for x in keys if x[2] == 'added_regions'},
                         {(e, t) for e in (1.5, 2., 3.) for t in (0, 5)})

    def test_root_bootstrap_does_not_treat_frames_as_roots(self):
        draws = np.random.default_rng(1604000001).integers(0, 8, (10000, 8))
        result = root_statistics(np.ones(8)*3, draws)
        self.assertEqual(result['roots'], 8)
        self.assertEqual(result['bootstrap95_low'], 3)
        self.assertEqual(result['bootstrap95_high'], 3)
        with self.assertRaises(ValueError):
            root_statistics(np.ones(16), draws)

    def test_original_geometry_invariance(self):
        source = Path(os.environ['R1_FROZEN_GQ_SOURCE'])
        spec = importlib.util.spec_from_file_location('frozen_test_gq', source)
        gq = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gq)
        xyz = np.arange(84, dtype=float).reshape(28, 3)
        rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        a = gq.descriptors(xyz)
        b = gq.descriptors(xyz@rotation+10)
        self.assertEqual(len(a), 325)
        np.testing.assert_allclose(a, b, atol=1e-12)
        self.assertLess(gq.distances(a, b)[0, 0], 1e-12)

    def test_nested_reference_distance_only_is_monotone(self):
        source = Path(os.environ['R1_FROZEN_GQ_SOURCE'])
        spec = importlib.util.spec_from_file_location('frozen_test_gq2', source)
        gq = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gq)
        points = np.array([[0., 0.], [2., 2.], [6., 6.]])
        old = np.array([[0., 0.]])
        enlarged = np.array([[0., 0.], [6., 6.]])
        d1, _ = gq.nearest(points, old, 1)
        d2, _ = gq.nearest(points, enlarged, 2)
        self.assertTrue(np.all(d2 <= d1))
        # 群差の増減まで点ごとの単調性から導いてはならない。
        self.assertGreater((d2[1]-d2[2]), (d1[1]-d1[2]))


if __name__ == '__main__':
    unittest.main()
