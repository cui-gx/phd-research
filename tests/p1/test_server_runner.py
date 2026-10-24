import copy
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from concurrent.futures import Future

from p1.server.runner import validate_settings, seed_for, TrainingTrigger, run
from p1.server.support import ROOT, verify_lease, execute_task, save_new


class RunnerGuards(unittest.TestCase):
    def settings(self):
        data = json.loads((ROOT / "configs/p1-server-cpu-smoke.json").read_text())
        data.update(policy="Single-GPU-FIFO", gpu_slots=1)
        for key in ("initial_pdb", "reference_pdb"):
            data[key] = str(ROOT / data[key])
        return data

    def test_concrete_inputs_match(self):
        self.assertEqual(validate_settings(self.settings())["device"], "cpu")

    def test_formal_work_is_not_enabled_by_configuration(self):
        data = self.settings()
        data["purpose"] = "formal"
        with self.assertRaisesRegex(ValueError, "Formal"):
            validate_settings(data)

    def test_unbounded_and_nonfinite_runs_are_rejected(self):
        for value in (0, -1, float("nan"), float("inf"), 7201, True):
            data = self.settings()
            data["walltime_s"] = value
            with self.assertRaises(ValueError):
                validate_settings(data)

    def test_gpu_mode_cannot_be_cpu_fallback(self):
        data = self.settings()
        data["purpose"] = "qualification"
        with self.assertRaisesRegex(ValueError, "fall back"):
            validate_settings(data)

    def test_current_runner_rejects_missing_or_multiple_gpu_slots(self):
        for slots in (None, 0, 2, True, 1.0):
            data = self.settings()
            data["gpu_slots"] = slots
            with self.assertRaisesRegex(ValueError, "gpu_slots=1"):
                validate_settings(data)

    def test_current_runner_rejects_historical_research_policies(self):
        for policy in ("Static-reservation-matched", "Task-aware-F0", "Feedback-first", "Feedback-gated-F1"):
            data = self.settings()
            data["policy"] = policy
            with self.assertRaises(ValueError):
                validate_settings(data)

    def test_seeds_are_stable_and_kind_separated(self):
        self.assertEqual(seed_for(123, "md", 0), seed_for(123, "md", 0))
        self.assertNotEqual(seed_for(123, "md", 0), seed_for(123, "train", 0))
        self.assertTrue(0 < seed_for(123, "md", 0) < 2**31)

    def test_delayed_training_dispatch_does_not_move_result_milestones(self):
        trigger = TrainingTrigger(6)
        self.assertFalse(trigger.observe(5))
        self.assertTrue(trigger.observe(6))
        # Training waits until result 10; the next trigger is still result 12.
        self.assertFalse(trigger.observe(10))
        self.assertTrue(trigger.observe(12))
        self.assertTrue(trigger.observe(25))
        self.assertFalse(trigger.observe(29))
        self.assertTrue(trigger.observe(30))

    def mock_campaign(self, second_fails=False, late_second=False):
        """Exercise orchestration with synthetic outcomes, never scientific evidence."""
        with tempfile.TemporaryDirectory(dir=os.environ["P1_TEST_TMPDIR"]) as tmp:
            output = Path(tmp) / "run"
            seen, workers, clock = [], [], [0.0]

            class DelayedFuture(Future):
                polls = 0
                def done(self):
                    self.polls += 1
                    return self.polls >= 4

            class Executor:
                def __init__(self, **kwargs):
                    pass
                def submit(self, fn, request_path, result_path, device, cpus, timeout, stop):
                    req = json.loads(Path(request_path).read_text())
                    index = len(seen)
                    seen.append((timeout, cpus))
                    record = {"task_type": "simulation", "status": "failure" if second_fails and index == 1 else "success",
                              "valid": not (second_fails and index == 1), "result_id": req["task_id"],
                              "restart": {"synthetic": True} if index == 1 else None}
                    save_new(result_path, record)
                    future = DelayedFuture() if late_second and index == 1 else Future()
                    future.set_result({"result_path": result_path, "returncode": 1 if second_fails and index == 1 else 0})
                    return future
                def shutdown(self, **kwargs):
                    pass

            modules = {"parsl.concurrent": types.SimpleNamespace(ParslPoolExecutor=Executor),
                       "parsl.config": types.SimpleNamespace(Config=lambda **kw: kw),
                       "parsl.executors.threads": types.SimpleNamespace(ThreadPoolExecutor=lambda **kw: workers.append(kw) or kw)}
            settings = self.settings()
            if late_second:
                settings.update(mode="pilot", walltime_s=3)
            def tick(_seconds):
                clock[0] += 1
            with patch.dict("sys.modules", modules), patch("p1.server.runner.inspect_host", return_value={"cpu_ids_visible": [0, 1, 2]}), \
                 patch("p1.server.runner.controller_affinity", return_value={}), \
                 patch("p1.server.runner.time.monotonic", side_effect=lambda: clock[0]), \
                 patch("p1.server.runner.time.sleep", side_effect=tick):
                summary = run(settings, output, ROOT / "configs/p1_server_science.json")
            return summary, (output / "STOP").exists(), {
                "tasks": seen, "workers": workers,
                "manifest": json.loads((output / "manifest.json").read_text())}

    def test_later_sequential_task_failure_is_not_a_success(self):
        summary, _, _ = self.mock_campaign(second_fails=True)
        self.assertEqual(summary["status"], "failure")
        self.assertIn("Task failed", summary["reason"])

    def test_horizon_drains_single_running_task_without_stop_signal(self):
        summary, stopped, details = self.mock_campaign(late_second=True)
        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["submitted_tasks"], 2)
        self.assertEqual(summary["completed_valid_tasks"], 2)
        self.assertEqual(summary["completed_valid_tasks_after_horizon"], 1)
        self.assertFalse(summary["restart_md_completed"])
        self.assertFalse(stopped)
        self.assertEqual({item[0] for item in details["tasks"]}, {self.settings()["task_timeout_s"]})
        self.assertTrue(all(0 not in cpus for _, cpus in details["tasks"]))

    def test_cpu_functional_entry_uses_one_worker_and_one_controller_cpu(self):
        summary, stopped, details = self.mock_campaign()
        self.assertEqual(summary["status"], "success")
        self.assertFalse(stopped)
        self.assertEqual([worker["max_threads"] for worker in details["workers"]], [1])
        self.assertEqual(details["manifest"]["gpu_uuids"], [None])
        self.assertEqual(details["manifest"]["controller_cpu_ids"], [0])
        self.assertEqual(details["manifest"]["worker_cpu_ids"], [1])
        self.assertEqual(details["manifest"]["gpu_slots"], 1)
        self.assertTrue(summary["engineering_only"])
        self.assertEqual(summary["reserved_gpu_hours_including_drain"], 0)

    def fixtures(self):
        host = {"hostname": "approved-host", "cpu_ids_visible": [0, 1, 2, 3],
                "gpu_inventory": {"returncode": 0, "stdout": "0, GPU-aaa, Test GPU, 96000, 570.0\n1, GPU-bbb, Test GPU, 96000, 570.0\n"},
                "gpu_processes": {"returncode": 0, "stdout": ""}}
        lease = {"permission_confirmed": True, "hostname": "approved-host", "gpu_uuids": ["GPU-aaa", "GPU-bbb"],
                 "cpu_ids": [0, 1], "expires_utc": (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat(),
                 "coordination_note": "Synthetic unit-test fixture only"}
        return lease, host

    def test_lease_matches_host_time_devices_and_cpus(self):
        lease, host = self.fixtures()
        self.assertEqual(verify_lease(lease, host, 100), (["GPU-aaa", "GPU-bbb"], [0, 1]))
        for key, value in (("permission_confirmed", False), ("hostname", "elsewhere"), ("gpu_uuids", ["GPU-aaa", "GPU-aaa"]),
                           ("cpu_ids", [0, 99]), ("expires_utc", "2000-01-01T00:00:00+00:00")):
            changed = copy.deepcopy(lease)
            changed[key] = value
            with self.assertRaises(ValueError):
                verify_lease(changed, host, 100)

    def test_existing_process_prevents_run(self):
        lease, host = self.fixtures()
        host["gpu_processes"]["stdout"] = "GPU-bbb, 12345, other-student, 2000\n"
        with self.assertRaisesRegex(ValueError, "already has"):
            verify_lease(lease, host, 100)

    def test_failed_worker_leaves_result_and_stderr(self):
        with tempfile.TemporaryDirectory(dir=os.environ["P1_TEST_TMPDIR"]) as tmp:
            root = Path(tmp)
            save_new(root / "request.json", {"task_id": "invalid", "task_type": "unknown", "cpu_threads": 1})
            value = execute_task(root / "request.json", root / "result.json", None, [], 10, root / "STOP")
            self.assertNotEqual(value["returncode"], 0)
            self.assertEqual(json.loads((root / "result.json").read_text())["status"], "failure")
            self.assertTrue((root / "execution.json").is_file())

    def test_timeout_terminates_own_worker_and_keeps_execution_record(self):
        with tempfile.TemporaryDirectory(dir=os.environ["P1_TEST_TMPDIR"]) as tmp:
            root = Path(tmp)
            save_new(root / "request.json", {"task_id": "timeout", "task_type": "unknown", "cpu_threads": 1})
            value = execute_task(root / "request.json", root / "result.json", None, [], 0.000001, root / "STOP")
            self.assertEqual(value["termination"], "task_timeout")
            self.assertNotEqual(value["returncode"], 0)


if __name__ == "__main__":
    unittest.main()
