"""Harmless child-process failure injection; not scientific execution evidence."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from p1.server import support


REAL_POPEN = subprocess.Popen
REAL_SAVE = support.save_new
REAL_RMTREE = support.shutil.rmtree


class WorkerCleanupTests(unittest.TestCase):
    @contextmanager
    def task_root(self):
        with tempfile.TemporaryDirectory(dir=os.environ["P1_TEST_TMPDIR"]) as temporary:
            root = Path(temporary)
            task = root / "task"
            task.mkdir()
            REAL_SAVE(task / "request.json", {"task_id": "cleanup-test", "cpu_threads": 1})
            with patch.dict(os.environ, {"P1_TEST_TMPDIR": str(root)}):
                yield task

    def harmless_child(self, children):
        def launch(_args, **kwargs):
            child = REAL_POPEN([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
            children.append(child)
            return child
        return launch

    def execute(self, root):
        return support.execute_task(root / "request.json", root / "result.json", None,
                                    [], 30, root / "STOP")

    def assert_reaped_and_clean(self, root, children):
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())
        self.assertNotEqual(children[0].returncode, 0)
        registration = json.loads((root / "runtime-registration.json").read_text())
        self.assertFalse(Path(registration["temporary_path"]).exists())
        cleanup = json.loads((root / "runtime-cleanup.json").read_text())
        self.assertTrue(cleanup["removed"])
        self.assertIsNone(cleanup["cleanup_error"])

    def test_process_registration_failure_reaps_child_and_keeps_original_error(self):
        children = []
        def failing_save(path, data):
            if Path(path).name == "process.json":
                raise OSError("injected registration failure")
            return REAL_SAVE(path, data)
        with self.task_root() as root:
            with patch.object(support.subprocess, "Popen", side_effect=self.harmless_child(children)), \
                 patch.object(support, "save_new", side_effect=failing_save):
                with self.assertRaisesRegex(OSError, "injected registration failure"):
                    self.execute(root)
            self.assert_reaped_and_clean(root, children)
            execution = json.loads((root / "execution.json").read_text())
            self.assertEqual(execution["termination"], "supervisor_error")
            self.assertIn("injected registration failure", execution["supervisor_error"])
            self.assertIsNone(execution["process_cleanup_error"])

    def test_monitor_exception_reaps_child(self):
        children = []
        with self.task_root() as root:
            with patch.object(support.subprocess, "Popen", side_effect=self.harmless_child(children)), \
                 patch.object(support.time, "sleep", side_effect=RuntimeError("injected monitor failure")):
                with self.assertRaisesRegex(RuntimeError, "injected monitor failure"):
                    self.execute(root)
            self.assert_reaped_and_clean(root, children)
            self.assertIn("injected monitor failure", json.loads((root / "execution.json").read_text())["supervisor_error"])

    def test_keyboard_interrupt_also_reaps_child(self):
        children = []
        with self.task_root() as root:
            with patch.object(support.subprocess, "Popen", side_effect=self.harmless_child(children)), \
                 patch.object(support.time, "sleep", side_effect=KeyboardInterrupt()):
                with self.assertRaises(KeyboardInterrupt):
                    self.execute(root)
            self.assert_reaped_and_clean(root, children)

    def test_cleanup_failure_cannot_turn_success_into_silent_leak(self):
        with self.task_root() as root:
            with patch.object(support, "_execute_task_bound", return_value={"returncode": 0}), \
                 patch.object(support.shutil, "rmtree", side_effect=PermissionError("injected cleanup failure")):
                with self.assertRaisesRegex(PermissionError, "injected cleanup failure"):
                    self.execute(root)
            record = json.loads((root / "runtime-cleanup.json").read_text())
            self.assertFalse(record["removed"])
            self.assertIn("injected cleanup failure", record["cleanup_error"])
            REAL_RMTREE(record["temporary_path"])

    def test_original_execution_failure_survives_secondary_cleanup_failure(self):
        with self.task_root() as root:
            with patch.object(support, "_execute_task_bound", side_effect=RuntimeError("original failure")), \
                 patch.object(support.shutil, "rmtree", side_effect=PermissionError("cleanup failure")):
                with self.assertRaisesRegex(RuntimeError, "original failure") as caught:
                    self.execute(root)
            self.assertTrue(any("cleanup" in note for note in caught.exception.__notes__))
            record = json.loads((root / "runtime-cleanup.json").read_text())
            REAL_RMTREE(record["temporary_path"])

    def test_owned_group_escalates_and_reaps_when_term_is_ignored(self):
        child = Mock(pid=12345)
        child.wait.side_effect = [subprocess.TimeoutExpired("synthetic-child", 5), -9]
        with patch.object(support.os, "killpg") as kill_group:
            support._terminate_owned_group(child)
        self.assertEqual(kill_group.call_args_list[0].args, (12345, signal.SIGTERM))
        self.assertEqual(kill_group.call_args_list[1].args, (12345, signal.SIGKILL))
        self.assertEqual(child.wait.call_count, 2)


if __name__ == "__main__":
    unittest.main()
