"""S2 evaluator checks; no GPU or experiment improvement claims."""
import unittest

from p1.server.qualification_analysis import physical_features, coverage, selection_comparison


class QualificationTests(unittest.TestCase):
    def test_physical_distances_are_rigid_motion_invariant(self):
        import numpy as np
        x = np.arange(84).reshape(28, 3) / 10
        y = x @ np.array([[0,-1,0],[1,0,0],[0,0,1]]) + 100
        np.testing.assert_allclose(physical_features(x), physical_features(y), atol=1e-12)
        self.assertEqual(len(physical_features(x)), 325)

    def test_duplicate_frames_do_not_create_coverage(self):
        a = coverage([[1., 9.], [1., 9.]], [2.], 8.)
        self.assertEqual(a["contact_fingerprint_states"], 1)
        self.assertEqual(a["distance_bin_states"]["2.0"], 1)

    def test_bin_rule_has_fixed_origin(self):
        a = coverage([[1.99, 8.], [2., 8.]], [2.], 8.)
        self.assertEqual(a["distance_bin_states"]["2.0"], 2)
        self.assertEqual(a["contact_fingerprint_states"], 1)

    def test_reject_nonfinite_coordinates(self):
        import numpy as np
        with self.assertRaises(ValueError):
            physical_features(np.full((28, 3), float("nan")))

    def test_reference_sort_can_hide_model_change(self):
        before = [{"result_id":"a", "frame": i, "lof": -i-1., "rmsd_angstrom": float(i)} for i in range(3)]
        after = [dict(r, lof=-4.-r["lof"]) for r in before]
        result = selection_comparison(before, after, 100)
        self.assertTrue(result["lof_only_top1_changed"])
        self.assertFalse(result["actual_reference_guided_top1_changed"])

    def test_different_candidate_pools_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Candidate pools"):
            selection_comparison([{"result_id":"a","frame":0}], [{"result_id":"b","frame":0}], 1)


if __name__ == "__main__":
    unittest.main()
