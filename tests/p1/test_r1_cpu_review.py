"""R1の参照・階層・物理距離に対する小さな境界検査。サーバCPU専用。"""
import importlib.util
import copy
import json
import os
from pathlib import Path
import unittest

import numpy as np

from p1.r1_cpu_review import matched_ids, metric_keys, root_statistics, Review
from p1.r1_cpu_report import validate_hierarchy


class ReviewTests(unittest.TestCase):
    """不変条件を検査し、科学的改善を合格条件にしない。"""

    def test_count_matching_keeps_global_IDs(self):
        ids = np.array([200, 202, 207, 220, 250, 320, 900])
        np.testing.assert_array_equal(matched_ids(ids, 4), [200, 207, 250, 900])
        with self.assertRaises(ValueError):
            matched_ids(ids, 8)
        with self.assertRaises(ValueError):
            matched_ids(np.array([1, 1, 2]), 2)
        with self.assertRaises(ValueError):
            matched_ids(np.array([], dtype=int), 2)

    def frozen_geometry(self):
        """副作用のない固定数値関数だけをロードする。"""
        source = Path(os.environ['R1_FROZEN_GQ_SOURCE'])
        spec = importlib.util.spec_from_file_location('frozen_extra_gq', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_missing_quality_mask_cannot_be_zero_effect(self):
        review = Review.__new__(Review)
        review.gq = self.frozen_geometry()
        a = dict(distances_A=np.zeros((4, 325)), angles_rad=np.zeros((4, 54)),
                 time_ps=np.arange(1, 5)*.5, valid=np.zeros(4, dtype=bool))
        with self.assertRaises(ValueError):
            review.metrics(a, a, np.array([0]))

    def test_known_nearest_tie_uses_first_reference(self):
        gq = self.frozen_geometry()
        query = np.array([[1., 1.]])
        reference = np.array([[0., 0.], [2., 2.]])
        for block in (1, 64):
            distance, ids = gq.nearest(query, reference, block)
            self.assertEqual(ids.tolist(), [0])
            self.assertEqual(distance.tolist(), [1.])

    def test_invalid_gap_resets_persistence_support(self):
        gq = self.frozen_geometry()
        features = np.ones((4, 2))*3
        times = np.array([0., 2., 4., 6.])
        known = np.zeros((1, 2))
        reps, confirmation = gq.regions(features, times, 1., 5., history=known)
        self.assertEqual((reps, confirmation), ([0], [3]))
        reps, confirmation = gq.regions(features, times, 1., 5., history=known,
                                        valid=np.array([True, True, False, True]))
        self.assertEqual((reps, confirmation), ([], []))

    def test_shared_F0_and_duplicate_hierarchy_are_guarded(self):
        matrix = json.loads(Path(os.environ['R1_MATRIX']).read_text())
        self.assertEqual(validate_hierarchy(matrix)['unique_F0_branches'], 48)
        duplicated = copy.deepcopy(matrix)
        duplicated['roots'][1]['root_id'] = duplicated['roots'][0]['root_id']
        with self.assertRaises(ValueError):
            validate_hierarchy(duplicated)
        duplicated = copy.deepcopy(matrix)
        duplicated['states'][1] = duplicated['states'][0]
        with self.assertRaises(ValueError):
            validate_hierarchy(duplicated)
        duplicated = copy.deepcopy(matrix)
        b = next(b for b in duplicated['branches'] if b['arm'] == 'F0')
        b['training_block'] = 1
        with self.assertRaises(ValueError):
            validate_hierarchy(duplicated)

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
