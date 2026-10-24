import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("p1_preflight", ROOT / "p1/preflight.py")
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / "p1/examples/engineering_fixture.json").read_text())

    def rejected(self, expected):
        result = preflight.check_record(self.record)
        self.assertFalse(result["ok"])
        self.assertTrue(any(expected in s for s in result["errors"]), result)

    def test_valid_feedback_fixture_and_accounting(self):
        r = preflight.check_record(self.record)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["reserved_cpu_seconds"], 36)
        self.assertEqual(r["assigned_worker_cpu_seconds"], 20)
        self.assertEqual(r["unique_valid_simulation_outputs"], 3)
        self.assertEqual(r["failed_attempts"], 1)
        self.assertFalse(r["scientific_benefit_verified"])

    def test_cpu_overcommit_counts_control(self):
        self.record["budget_cpu_slots"] = 2
        self.rejected("CPU budget exceeded")

    def test_finite_timestamps(self):
        self.record["tasks"][0]["ended_s"] = float("nan")
        self.rejected("finite number")

    def test_end_before_start(self):
        self.record["tasks"][0]["ended_s"] = -1
        self.rejected("invalid task interval")

    def test_duplicate_attempt(self):
        self.record["tasks"].append(copy.deepcopy(self.record["tasks"][0]))
        self.rejected("duplicate/missing attempt_id")

    def test_retry_keeps_input_identity(self):
        self.record["tasks"][1]["input_hash"] = "different-input"
        self.rejected("retry changed phase or input")

    def test_retries_do_not_overlap(self):
        self.record["tasks"][1]["submitted_s"] = 0
        self.record["tasks"][1]["started_s"] = 0
        self.rejected("overlapping retries")

    def test_failed_result_not_valid(self):
        self.record["tasks"][0]["output_valid"] = True
        self.rejected("failed output marked valid")

    def test_model_no_time_travel(self):
        self.record["models"][0]["available_s"] = 8
        self.rejected("model used before available")

    def test_training_cannot_use_failed_input(self):
        self.record["models"][0]["training_members"] = ["s0-fail"]
        self.rejected("unavailable training data")

    def test_training_no_future_input(self):
        self.record["models"][0]["training_members"] = ["s2-ok"]
        self.rejected("unavailable training data")

    def test_model_requires_successful_training(self):
        self.record["tasks"][3]["status"] = "failure"
        self.rejected("invalid training result")

    def test_duplicate_model_version(self):
        self.record["models"] *= 2
        self.rejected("duplicate/missing model version")

    def test_selection_no_time_travel(self):
        self.record["tasks"][-1]["submitted_s"] = 6
        self.rejected("invalid/future selection parent")

    def test_split_leakage(self):
        self.record["heldout_groups"] = self.record["development_groups"]
        self.rejected("leakage")

    def test_action_ack_order(self):
        self.record["actions"][0]["effective_s"] = 1
        self.rejected("acknowledgement")

    def test_retry_does_not_add_unique_output(self):
        t = copy.deepcopy(self.record["tasks"][-1])
        t.update(attempt_id="s2-again", attempt=2, submitted_s=10,
                 started_s=10, ended_s=11)
        self.record["tasks"].append(t)
        r = preflight.check_record(self.record)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["unique_valid_simulation_outputs"], 3)
        self.assertEqual(r["assigned_worker_cpu_seconds"], 22)

    def test_fixture_cannot_be_called_measurement(self):
        self.record["evidence_type"] = "local CPU/GPU measurement"
        self.rejected("fixture must be labelled")

    def test_candidate_remains_blocked(self):
        candidate = json.loads((ROOT / "configs/p1_pilot_candidate.json").read_text())
        r = preflight.check_candidate(candidate)
        self.assertFalse(r["ready_for_formal_evaluation"])
        self.assertEqual(len(r["blockers"]), 11)


if __name__ == "__main__":
    unittest.main()
