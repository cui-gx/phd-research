import unittest
from p1.server.analysis import sustained_target


class TargetMetricTests(unittest.TestCase):
    def test_ten_frames_do_not_span_one_hundred_ps_at_ten_ps_interval(self):
        self.assertIsNone(sustained_target([1.5] * 10, 10, 2, 100))
        self.assertEqual(sustained_target([1.5] * 11, 10, 2, 100), 10)

    def test_excursion_resets_contiguous_window(self):
        self.assertIsNone(sustained_target([1] * 6 + [3] + [1] * 6, 10, 2, 100))

    def test_nan_and_unbounded_metric_are_not_repaired(self):
        with self.assertRaises(ValueError):
            sustained_target([float("nan")], 10, 2, 100)


if __name__ == "__main__":
    unittest.main()
