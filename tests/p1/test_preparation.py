import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "p1" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


prep, preflight = module("preparation"), module("preflight")


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / "p1/examples/engineering_fixture.json").read_text())
        self.manifest = json.loads((ROOT / "configs/p1_run_manifest.template.json").read_text())

    def filled_manifest(self):
        # Synthetic values ONLY: no actual machine, permission, dependency or execution evidence.
        m = self.manifest
        m.update(status="frozen_development", run_id="test-only", seed=0)
        m["source"].update(bundle_sha256="a" * 64, adapter_sha256="b" * 64)
        m["environment"] = {k: "c" * 64 for k in m["environment"]}
        m["inputs"] = [{"path": "synthetic-only.json", "sha256": "d" * 64}]
        m["permissions"] = {k: "synthetic-reference-only" for k in m["permissions"]}
        m["limits"].update(cpu_slots=3, control_slots=1, threads_per_worker=1,
                           memory_gib=2, walltime_minutes=10, reserved_cpu_hours=.5,
                           storage_gib=1, max_attempts=1)
        m["thread_environment"] = {k: "1" for k in m["thread_environment"]}
        m["policy_factors"] = {k: "synthetic-fixed" for k in m["policy_factors"]}
        return m

    def test_placeholder_candidate_never_ready(self):
        m = json.loads((ROOT / "configs/p1_pilot_candidate.json").read_text())
        for k in preflight.check_candidate(m)["blockers"]:
            m[k] = "TBD"
        m["formal_evaluation"] = True
        r = preflight.check_candidate(m)
        self.assertEqual(len(r["blockers"]), 11)
        self.assertFalse(r["ready_for_formal_evaluation"])

    def test_filled_candidate_is_not_scientific_certification(self):
        m = json.loads((ROOT / "configs/p1_pilot_candidate.json").read_text())
        for k in preflight.check_candidate(m)["blockers"]:
            m[k] = "unverified evidence reference"
        m.update(quality_equivalence_margin=0, formal_evaluation=True)
        r = preflight.check_candidate(m)
        self.assertTrue(r["field_presence_complete"])
        self.assertTrue(r["manual_evidence_review_required"])
        self.assertFalse(r["ready_for_formal_evaluation"])

    def test_malformed_records_fail_cleanly(self):
        for key, value in [("tasks", [None]), ("models", [42]), ("actions", "wrong")]:
            m = copy.deepcopy(self.fixture)
            m[key] = value
            self.assertFalse(preflight.check_record(m)["ok"])

    def test_closed_loop_fixture_is_only_structural(self):
        r = preflight.check_closed_loop(self.fixture)
        self.assertTrue(r["ok"], r)
        self.assertEqual(len(r["closed_loop_chains"]), 2)
        self.assertFalse(r["real_execution_verified"])

    def test_simulation_only_record_is_not_closed_loop(self):
        self.fixture["tasks"] = self.fixture["tasks"][:3]
        self.fixture["models"] = []
        self.assertTrue(preflight.check_record(self.fixture)["ok"])
        self.assertFalse(preflight.check_closed_loop(self.fixture)["ok"])

    def test_selection_without_inference_lineage_is_not_closed_loop(self):
        infer = self.fixture["tasks"][4]
        infer["phase"] = "selection"
        self.assertFalse(preflight.check_closed_loop(self.fixture)["ok"])

    def test_separate_selection_requires_temporal_provenance(self):
        selection = copy.deepcopy(self.fixture["tasks"][4])
        selection.update(attempt_id="select-v1", task_id="select-v1", phase="selection",
                         submitted_s=7, started_s=7, ended_s=8, cpu_slots=1,
                         inference_parent="infer-v1")
        later = self.fixture["tasks"][-1]
        later.update(selected_by="select-v1", submitted_s=8, started_s=8)
        self.fixture["tasks"].append(selection)
        self.assertTrue(preflight.check_closed_loop(self.fixture)["ok"])
        selection["started_s"] = 6
        self.assertFalse(preflight.check_closed_loop(self.fixture)["ok"])

    def test_draft_manifest_is_blocked(self):
        self.assertFalse(prep.check_manifest(self.manifest)["ok"])

    def test_synthetic_complete_manifest_does_not_authorize_execution(self):
        r = prep.check_manifest(self.filled_manifest())
        self.assertTrue(r["ok"], r)
        self.assertFalse(r["execution_authorized"])
        self.assertFalse(r["ready_for_formal_evaluation"])

    def test_budget_and_resource_misconfiguration(self):
        for key, value in [("reserved_cpu_hours", .49), ("memory_gib", -1),
                           ("storage_gib", float("nan")), ("max_attempts", True),
                           ("threads_per_worker", 4), ("control_slots", 3)]:
            m = copy.deepcopy(self.filled_manifest())
            m["limits"][key] = value
            self.assertFalse(prep.check_manifest(m)["ok"], (key, value))

    def test_missing_dependency_or_evidence_is_blocked(self):
        m = self.filled_manifest()
        m["environment"]["dependency_lock_sha256"] = "not-a-hash"
        m["permissions"]["job_authorization"] = "TBD"
        self.assertFalse(prep.check_manifest(m)["ok"])

    def test_thread_limit_mismatch_is_blocked(self):
        m = self.filled_manifest()
        m["thread_environment"]["OPENBLAS_NUM_THREADS"] = "8"
        self.assertFalse(prep.check_manifest(m)["ok"])

    def test_safe_directory_refuses_overwrite_traversal_and_symlinks(self):
        # Caller supplies its registered disposable directory; no global temp fallback.
        temp_root = os.environ.get("P1_TEST_TMPDIR")
        self.assertTrue(temp_root, "set P1_TEST_TMPDIR to a segment-scoped directory")
        with tempfile.TemporaryDirectory(dir=temp_root) as td:
            root = Path(td)
            run = prep.reserve_run_directory(root, "run-001")
            marker = run / "preserved.txt"
            marker.write_text("original")
            with self.assertRaises(FileExistsError):
                prep.reserve_run_directory(root, "run-001")
            for bad in ("../escape", "/tmp/escape", "a/b", ".", ""):
                with self.assertRaises(ValueError):
                    prep.reserve_run_directory(root, bad)
            (root / "linked").symlink_to(run, target_is_directory=True)
            with self.assertRaises(FileExistsError):
                prep.reserve_run_directory(root, "linked")
            with self.assertRaises(ValueError):
                prep.reserve_run_directory(root / "linked", "child")
            self.assertEqual(marker.read_text(), "original")


if __name__ == "__main__":
    unittest.main()
