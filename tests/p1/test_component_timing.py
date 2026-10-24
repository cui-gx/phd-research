"""Timing-contract tests; no MD/ML performance or exploration claims."""

import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from p1.server import science


class ComponentTimingTests(unittest.TestCase):
    def assert_partition(self, report):
        previous_end = 0.0
        total = 0.0
        for stage in report["stages"]:
            self.assertEqual(stage["start_offset_s"], previous_end)
            self.assertGreaterEqual(stage["end_offset_s"], stage["start_offset_s"])
            self.assertTrue(math.isfinite(stage["wall_time_s"]))
            self.assertAlmostEqual(stage["wall_time_s"], stage["end_offset_s"] - stage["start_offset_s"])
            previous_end = stage["end_offset_s"]
            total += stage["wall_time_s"]
        self.assertAlmostEqual(total, report["wall_time_s"])
        self.assertEqual(previous_end, report["wall_time_s"])

    def test_stages_cover_real_counter_interval_without_overlap(self):
        readings = iter([100.0, 101.0, 104.0, 111.0])
        timer = science.ComponentTimer(clock=lambda: next(readings))
        timer.stage("md_initialization")
        timer.stage("md_simulation")
        report = timer.finish()
        self.assert_partition(report)
        self.assertEqual(report["wall_time_s"], 11)
        self.assertEqual([row["wall_time_s"] for row in report["stages"]], [1, 3, 7])

    def test_checkpoint_is_nested_not_double_counted(self):
        readings = iter([0.0, 1.0, 4.0, 6.0, 10.0, 11.0])
        timer = science.ComponentTimer(clock=lambda: next(readings))
        timer.stage("train_fit_including_checkpoint")
        with timer.nested("checkpoint_write"):
            pass
        timer.stage("train_checkpoint_verification_and_write")
        report = timer.finish()
        self.assert_partition(report)
        child = report["nested_stages"][0]
        self.assertEqual(child["included_in"], "train_fit_including_checkpoint")
        self.assertEqual(child["wall_time_s"], 2)
        self.assertEqual(report["wall_time_s"], 11)
        self.assertIn("must not be added again", report["aggregation"])

    def test_failed_checkpoint_preserves_partial_duration(self):
        readings = iter([0.0, 1.0, 2.0, 5.0, 6.0, 8.0])
        timer = science.ComponentTimer(clock=lambda: next(readings))
        timer.stage("train_fit_including_checkpoint")
        with self.assertRaisesRegex(RuntimeError, "disk fixture"):
            with timer.nested("checkpoint_write"):
                raise RuntimeError("disk fixture")
        timer.stage("worker_finalize", previous_status="failed")
        report = timer.finish()
        self.assert_partition(report)
        self.assertEqual(report["nested_stages"][0]["status"], "failed")
        self.assertEqual(report["nested_stages"][0]["wall_time_s"], 3)
        self.assertEqual(report["stages"][1]["status"], "failed")

    def test_timer_cannot_resume_or_finish_twice(self):
        timer = science.ComponentTimer()
        timer.finish()
        with self.assertRaises(ValueError):
            timer.stage("md_simulation")
        with self.assertRaises(ValueError):
            timer.finish()

    def test_failed_worker_persists_all_timings_and_evidence_limits(self):
        temp_root = science.ROOT / ".runtime/S2-P1-SERVER-RUNPACK-20261022/tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="component-timing-", dir=temp_root) as folder:
            out = Path(folder) / "task"
            req = {"task_type": "simulation", "task_id": "timing-failure", "seed": 17,
                   "device": "cpu", "purpose": "cpu_functional", "inputs": {},
                   "output_dir": str(out)}
            def fail_after_init(request):
                timer = request["_component_timer"]
                timer.stage("md_initialization")
                timer.stage("md_simulation")
                raise RuntimeError("controlled timing fixture failure")
            with patch.object(science, "_simulation", fail_after_init):
                result = science.run_request(req)
            self.assertEqual(result["status"], "failure")
            self.assertFalse(result["exploration_effect_evaluated"])
            self.assertEqual(result["selection_classification"], "existing_upstream_reference_guided_selection")
            self.assertIn("not full Colmena reproduction", result["runtime_reproduction"])
            self.assert_partition(result["component_timing"])
            self.assertEqual(result["wall_time_s"], result["component_timing"]["wall_time_s"])
            self.assertEqual([row["stage"] for row in result["component_timing"]["stages"]],
                             ["worker_setup", "md_initialization", "md_simulation", "worker_finalize"])
            self.assertEqual(result["component_timing"]["stages"][2]["status"], "failed")
            saved = json.loads((out / "result.json").read_text())
            self.assertEqual(saved["component_timing"], result["component_timing"])
            self.assertTrue((out / "failure.txt").is_file())

    def test_successful_worker_does_not_claim_separate_data_task(self):
        temp_root = science.ROOT / ".runtime/S2-P1-SERVER-RUNPACK-20261022/tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="component-timing-", dir=temp_root) as folder:
            req = {"task_type": "inference", "task_id": "timing-success", "seed": 17,
                   "device": "cpu", "purpose": "cpu_functional", "inputs": {},
                   "output_dir": str(Path(folder) / "task")}
            def completed(request):
                timer = request["_component_timer"]
                for stage in ("infer_data_preparation_and_io", "infer_model_load",
                              "infer_embedding", "infer_lof_sort_and_write"):
                    timer.stage(stage)
                return {"valid": True}
            with patch.object(science, "_inference", completed):
                result = science.run_request(req)
            self.assertEqual(result["status"], "success")
            self.assert_partition(result["component_timing"])
            self.assertFalse(result["component_timing"]["data_preparation_is_separately_scheduled"])
            self.assertFalse(result["exploration_effect_evaluated"])


if __name__ == "__main__":
    unittest.main()
