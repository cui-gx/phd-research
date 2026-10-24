"""Dependency-free contract tests; these are not molecular/AI measurements."""

import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from p1.server import science


class ScienceContractTests(unittest.TestCase):
    def setUp(self):
        self.cfg = science.load_config()

    def request(self):
        return {"task_type": "simulation", "task_id": "smoke-1", "seed": 17,
                "device": "cpu", "purpose": "cpu_functional", "inputs": {},
                "output_dir": "/unused/test-only", "science_config": self.cfg}

    def test_md_units_and_frame_count(self):
        counts = science.simulation_counts(self.cfg)
        self.assertEqual(counts, {"nsteps": 10000, "report_steps": 250, "expected_frames": 40})
        self.cfg.update(simulation_length_ns=10, report_interval_ps=10)
        self.assertEqual(science.simulation_counts(self.cfg)["nsteps"], 5_000_000)
        self.assertEqual(science.simulation_counts(self.cfg)["expected_frames"], 1000)

    def test_reject_silent_step_truncation(self):
        for field, value in (("dt_ps", 0.003), ("simulation_length_ns", 0.020001),
                             ("report_interval_ps", 0.0001)):
            cfg = copy.deepcopy(self.cfg)
            cfg[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                science.simulation_counts(cfg)

    def test_cpu_is_not_gpu_evidence(self):
        req = self.request()
        req["purpose"] = "qualification"
        with self.assertRaisesRegex(ValueError, "CPU is allowed"):
            science.normalize_request(req)

    def test_formal_run_is_not_enabled(self):
        req = self.request()
        req.update(device="cuda", purpose="formal")
        with self.assertRaisesRegex(ValueError, "Formal evaluation"):
            science.normalize_request(req)

    def test_request_and_scientific_config_are_deep_copied(self):
        req = self.request()
        req["inputs"] = {"results": [{"result_id": "original"}]}
        normalized = science.normalize_request(req)
        req["inputs"]["results"][0]["result_id"] = "changed"
        req["science_config"]["cvae"]["optimizer_hparams"]["lr"] = 1
        self.assertEqual(normalized["inputs"]["results"][0]["result_id"], "original")
        self.assertEqual(normalized["science_config"]["cvae"]["optimizer_hparams"]["lr"], .001)

    def test_config_must_save_final_model(self):
        self.cfg["cvae"]["checkpoint_log_every"] = 2
        with self.assertRaisesRegex(ValueError, "last epoch"):
            science.load_config(self.cfg)

    def test_modern_torch_prefetch_contract(self):
        self.cfg["cvae"]["prefetch_factor"] = 2
        with self.assertRaisesRegex(ValueError, "prefetch_factor=null"):
            science.load_config(self.cfg)

    def test_gpu_must_have_one_binding(self):
        for value in ("", "-1", "0,1"):
            with self.subTest(value=value), patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": value}):
                with self.assertRaises(ValueError):
                    science._cuda_binding()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "GPU-my-assigned-uuid"}):
            self.assertEqual(science._cuda_binding(), "GPU-my-assigned-uuid")

    def test_selection_keeps_lof_shortlist_then_orders_rmsd(self):
        rows = [{"result_id": "a", "frame": 0, "lof": -4, "rmsd_angstrom": 4},
                {"result_id": "b", "frame": 0, "lof": -3, "rmsd_angstrom": 2},
                {"result_id": "c", "frame": 0, "lof": -1, "rmsd_angstrom": .1}]
        self.assertEqual([r["result_id"] for r in science.rank_rows(rows, 2)], ["b", "a"])
        self.assertEqual(rows[0]["result_id"], "a")

    def test_selection_ties_have_explicit_stable_order(self):
        rows = [{"result_id": rid, "frame": frame, "lof": -1, "rmsd_angstrom": 2}
                for rid, frame in (("b", 0), ("a", 1), ("a", 0))]
        self.assertEqual([(r["result_id"], r["frame"]) for r in science.rank_rows(rows, 3)],
                         [("a", 0), ("a", 1), ("b", 0)])

    def test_nan_is_not_repaired_into_a_valid_scientific_result(self):
        rows = [{"result_id": "a", "frame": 0, "lof": float("nan"), "rmsd_angstrom": 2}]
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            science.rank_rows(rows, 1)

    def test_snapshot_has_immutable_members_and_detects_tampering(self):
        temp_root = science.ROOT / ".runtime/S2-P1-SERVER-RUNPACK-20261022/tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="science-", dir=temp_root) as directory:
            result = {"result_id": "md-1", "status": "success", "valid": True,
                      "science_config_id": "cfg", "frames": 40, "artifact_sha256": {}}
            for key in ("contact_map_path", "rmsd_path", "pdb_path", "dcd_path"):
                path = Path(directory) / key
                path.write_text("fixture for immutable file contract only")
                result[key] = str(path)
                result["artifact_sha256"][key] = science.sha256_file(path)
            snapshot = science.freeze_snapshot([result], "cfg")
            result["result_id"] = "changed-after-submission"
            self.assertEqual(snapshot["results"][0]["result_id"], "md-1")
            Path(result["rmsd_path"]).write_text("modified")
            with self.assertRaisesRegex(ValueError, "immutable artifact hash"):
                science.freeze_snapshot([result], "cfg")

    def test_failed_and_duplicate_md_never_enter_snapshot(self):
        invalid = {"result_id": "failed", "status": "failure", "valid": False}
        with self.assertRaisesRegex(ValueError, "unsuccessful"):
            science.freeze_snapshot([invalid], "cfg")
        with self.assertRaisesRegex(ValueError, "empty"):
            science.freeze_snapshot([], "cfg")

    def test_configuration_mismatch_rejected_before_reading_files(self):
        invalid = {"result_id": "r", "status": "success", "valid": True,
                   "science_config_id": "different"}
        with self.assertRaisesRegex(ValueError, "configuration"):
            science.freeze_snapshot([invalid], "cfg")

    def test_pinned_science_source_is_available_and_unchanged(self):
        self.assertEqual(science.sha256_file(science.UPSTREAM_MD), science.UPSTREAM_MD_SHA256)


if __name__ == "__main__":
    unittest.main()
