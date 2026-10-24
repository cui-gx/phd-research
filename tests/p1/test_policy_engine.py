"""Deterministic engineering fixtures; none is molecular/performance evidence."""
from dataclasses import FrozenInstanceError, replace
import json
import unittest

from p1.server.events import FeedbackLedger
from p1.server.policy import POLICIES, PolicyConfig, Task, choose


def config(name="Task-aware-F0", **kwargs):
    values = dict(name=name, horizon_s=1000, wait_cap_s=100,
                  backlog_threshold=2, age_threshold_s=100,
                  md_estimate_s=10, inference_estimate_s=5)
    values.update(kwargs)
    return PolicyConfig(**values)


def adopted_ledger():
    ledger = FeedbackLedger()
    ledger.result_available("r0", 1)
    ledger.result_available("r1", 2)
    ledger.capture_snapshot("s0", 3)
    ledger.model_published("m0", "s0", 4)
    ledger.inference_dispatched("i0", "m0", ["r0", "r1"], 5)
    ledger.ranking_published("q0", "m0", ["r0", "r1"], 6, inference_task_id="i0")
    ledger.md_dispatched("md0", 7, "q0", "r0")
    return ledger


class FeedbackEventsTests(unittest.TestCase):
    def test_bootstrap_stays_na_through_model_and_ranking_publication(self):
        ledger = FeedbackLedger()
        ledger.result_available("r0", 1)
        ledger.capture_snapshot("s0", 2)
        ledger.model_published("m0", "s0", 3)
        ledger.inference_dispatched("i0", "m0", ["r0"], 4)
        ledger.ranking_published("q0", "m0", ["r0"], 5, inference_task_id="i0")
        state = ledger.feedback(6)
        self.assertTrue(state.bootstrap)
        self.assertIsNone(state.backlog_results)
        self.assertIsNone(state.data_age_s)
        self.assertEqual(state.latest_model_version, "m0")
        self.assertEqual(state.unused_ranking_ids, ("q0",))

    def test_inference_with_old_model_does_not_erase_training_backlog(self):
        ledger = adopted_ledger()
        ledger.result_available("r2", 8)
        ledger.inference_dispatched("i1", "m0", ["r0", "r1", "r2"], 9)
        ledger.ranking_published("q1", "m0", ["r0", "r1", "r2"], 10, inference_task_id="i1")
        ledger.md_dispatched("md1", 11, "q1", "r2")
        state = ledger.feedback(12)
        self.assertEqual(state.backlog_results, 1)
        self.assertEqual(state.data_age_s, 10)  # data at t=2, NOT model t=4 or rank t=10

    def test_new_model_and_ranking_do_not_refresh_b_a_until_adoption(self):
        ledger = adopted_ledger()
        ledger.result_available("r2", 8)
        ledger.capture_snapshot("s1", 9)
        ledger.model_published("m1", "s1", 10)
        state = ledger.feedback(11)
        self.assertEqual(state.unranked_model_versions, ("m1",))
        self.assertEqual(state.adopted_model_version, "m0")
        ledger.inference_dispatched("i1", "m1", ["r0", "r1", "r2"], 12)
        ledger.ranking_published("q1", "m1", ["r0", "r1", "r2"], 13, inference_task_id="i1")
        before = ledger.feedback(14)
        self.assertEqual((before.backlog_results, before.data_age_s), (1, 12))
        ledger.md_dispatched("md1", 15, "q1", "r2")
        after = ledger.feedback(15)
        self.assertEqual((after.backlog_results, after.data_age_s), (0, 7))
        self.assertEqual(after.adopted_snapshot_id, "s1")

    def test_snapshot_is_immutable_and_independent_of_later_results(self):
        ledger = FeedbackLedger()
        ledger.result_available("a", 1)
        ids = ["a"]
        snapshot = ledger.capture_snapshot("s", 2, ids)
        ids.append("future")
        ledger.result_available("b", 3)
        self.assertEqual(snapshot.result_ids, ("a",))
        self.assertEqual(snapshot.latest_data_at_s, 1)
        with self.assertRaises(FrozenInstanceError):
            snapshot.snapshot_id = "other"
        with self.assertRaises(ValueError):
            ledger.capture_snapshot("s", 4)
        self.assertEqual(ledger.snapshot("s").sha256, snapshot.sha256)

    def test_snapshot_hash_is_order_independent_and_sensitive_to_membership(self):
        ledger = FeedbackLedger()
        ledger.result_available("a", 1)
        ledger.result_available("b", 2)
        a = ledger.capture_snapshot("s1", 3, ["a", "b"])
        b = ledger.capture_snapshot("s2", 3, ["b", "a"])
        c = ledger.capture_snapshot("s3", 3, ["b"])
        self.assertEqual(a.sha256, b.sha256)
        self.assertNotEqual(a.sha256, c.sha256)

    def test_future_data_and_backdated_observations_are_rejected(self):
        ledger = FeedbackLedger()
        ledger.result_available("r", 1)
        with self.assertRaises(ValueError):
            ledger.capture_snapshot("future", 2, ["not-arrived"])
        self.assertEqual(len(ledger.events), 1)
        ledger.feedback(5)
        with self.assertRaises(ValueError):
            ledger.result_available("backdated", 4)
        with self.assertRaises(ValueError):
            ledger.feedback(2)

    def test_inference_cannot_ingest_data_arriving_after_its_dispatch(self):
        ledger = adopted_ledger()
        ledger.inference_dispatched("i1", "m0", ["r0", "r1"], 8)
        ledger.result_available("r2", 9)
        with self.assertRaises(ValueError):
            ledger.ranking_published("q1", "m0", ["r0", "r1", "r2"], 10,
                                     inference_task_id="i1")
        ledger.ranking_published("q1", "m0", ["r0", "r1"], 10, inference_task_id="i1")

    def test_unknown_ranking_and_duplicate_md_dispatch_rejected(self):
        ledger = adopted_ledger()
        with self.assertRaises(ValueError):
            ledger.md_dispatched("md1", 8, "future", "r0")
        with self.assertRaises(ValueError):
            ledger.md_dispatched("md0", 8, "q0", "r0")
        with self.assertRaises(ValueError):
            ledger.md_dispatched("md1", 8, "q0", "outside-ranking")
        with self.assertRaises(ValueError):
            ledger.md_dispatched("md1", 8)

    def test_event_export_is_json_serializable_and_cannot_mutate_state(self):
        ledger = adopted_ledger()
        records = [e.to_dict() for e in ledger.events]
        json.dumps(records, allow_nan=False)
        records[2]["results"].append({"result_id": "future", "available_at_s": 100})
        self.assertEqual(len(ledger.snapshot("s0").results), 2)
        self.assertEqual([r["sequence"] for r in records], list(range(len(records))))


class DispatchPolicyTests(unittest.TestCase):
    def setUp(self):
        self.ledger = adopted_ledger()
        self.now = 20
        self.md_running = Task("md-running", "md", 0, 10)

    def pick(self, tasks, name="Task-aware-F0", *, running=None, gpu=0, cfg=None, now=None, cpu=32):
        now = self.now if now is None else now
        return choose(tasks, running_tasks=[self.md_running] if running is None else running,
                      feedback=self.ledger.feedback(now), now_s=now, gpu_id=gpu,
                      available_cpu_cores=cpu, config=cfg or config(name))

    def test_f0_uses_wait_divided_by_estimated_duration(self):
        old_slow = Task("a", "md", 0, 100)
        new_fast = Task("b", "train", 10, 10)
        self.assertEqual(self.pick([old_slow, new_fast]).task, new_fast)

    def test_id_tie_break_does_not_depend_on_queue_order(self):
        a, b = Task("a", "md", 10, 10), Task("b", "train", 10, 10)
        for tasks in ([a, b], [b, a]):
            self.assertEqual(self.pick(tasks).task, a)

    def test_low_feedback_gate_differs_from_unconditional_learning_priority(self):
        md, train = Task("md", "md", 0, 5), Task("train", "train", 19, 5)
        self.assertEqual(self.pick([md, train], "Task-aware-F0").task, md)
        self.assertEqual(self.pick([md, train], "Feedback-gated-F1").task, md)
        self.assertEqual(self.pick([md, train], "Feedback-first").task, train)

    def test_high_backlog_gate_changes_f0_action(self):
        self.ledger.result_available("r2", 8)
        self.ledger.result_available("r3", 9)
        md, train = Task("md", "md", 0, 5), Task("train", "train", 19, 5)
        result = self.pick([md, train], "Feedback-gated-F1")
        self.assertEqual(result.task, train)
        self.assertTrue(result.gated)
        self.assertEqual(self.pick([md, train], "Task-aware-F0").task, md)

    def test_age_gate_can_fire_without_backlog(self):
        md, train = Task("md", "md", 0, 5), Task("train", "train", 19, 5)
        result = self.pick([md, train], cfg=config("Feedback-gated-F1", age_threshold_s=10))
        self.assertEqual(result.task, train)
        self.assertTrue(result.gated)

    def test_unranked_model_prioritizes_its_inference(self):
        self.ledger.capture_snapshot("s1", 8)
        self.ledger.model_published("m1", "s1", 9)
        infer = Task("infer", "infer", 19, 5, model_version="m1")
        train = Task("train", "train", 0, 5)
        result = self.pick([infer, train], cfg=config("Feedback-gated-F1", age_threshold_s=10))
        self.assertEqual(result.task, infer)

    def test_bootstrap_is_shared_across_dynamic_policies(self):
        self.ledger = FeedbackLedger()
        md, train = Task("md", "md", 0, 5), Task("train", "train", 19, 5)
        for policy in POLICIES[1:]:
            result = self.pick([md, train], policy)
            self.assertEqual(result.task, train)
            self.assertEqual(result.reason, "common_bootstrap")

    def test_wait_guard_prevents_md_and_learning_starvation(self):
        for policy in POLICIES[1:]:
            cfg = config(policy, wait_cap_s=10)
            md, train = Task("md", "md", 19, 5), Task("train", "train", 0, 5)
            result = self.pick([md, train], running=[], cfg=cfg)
            self.assertEqual(result.task, train)  # even no MD running: overdue wins
            self.assertEqual(result.reason, "common_wait_guard")
            md, train = Task("md", "md", 0, 5), Task("train", "train", 19, 5)
            self.assertEqual(self.pick([md, train], cfg=cfg).task, md)

    def test_md_progress_when_learning_priority_would_otherwise_fill_both_gpus(self):
        md = Task("md", "md", 19, 10)
        train = Task("train", "train", 0, 5)
        for policy in POLICIES[1:]:
            result = self.pick([md, train], policy, running=[])
            self.assertEqual(result.task, md)
            self.assertEqual(result.reason, "common_md_progress")

    def test_static_partition_stays_idle_and_cannot_borrow_learning_gpu(self):
        md = Task("md", "md", 0, 5)
        result = self.pick([md], "Static-reservation-matched", gpu=1)
        self.assertIsNone(result.task)
        self.assertIn(("md", "static_reservation"), result.excluded)
        self.assertEqual(self.pick([md], "Task-aware-F0", gpu=1).task, md)

    def test_static_partition_overrides_learning_priority_and_waiting(self):
        train = Task("train", "train", 0, 5)
        result = self.pick([train], cfg=config("Static-reservation-matched", wait_cap_s=10), gpu=0)
        self.assertIsNone(result.task)
        self.assertEqual(self.pick([train], "Static-reservation-matched", gpu=1).task, train)

    def test_shared_horizon_filter_excludes_learning_chain_but_allows_md_drain(self):
        md, train = Task("md", "md", 0, 5), Task("train", "train", 0, 10)
        for policy in POLICIES[1:]:
            result = self.pick([md, train], cfg=config(policy, horizon_s=40))
            self.assertEqual(result.task, md)
            self.assertIn(("train", "estimated_feedback_chain_exceeds_horizon"), result.excluded)
        self.assertIsNone(self.pick([md], cfg=config(horizon_s=20)).task)

    def test_cpu_and_same_kind_concurrency_limits(self):
        train = Task("train", "train", 0, 10, cpu_cores=8)
        self.assertIsNone(self.pick([train], cpu=4).task)
        other_train = Task("train-running", "train", 0, 10)
        self.assertIsNone(self.pick([train], running=[other_train]).task)
        infer = Task("infer", "infer", 0, 5, model_version="m0")
        self.assertEqual(self.pick([infer], running=[other_train]).task, infer)

    def test_unpublished_model_and_future_task_cannot_run(self):
        infer = Task("infer", "infer", 0, 5, model_version="future")
        md = Task("md", "md", 21, 5)
        result = self.pick([infer, md])
        self.assertIsNone(result.task)
        self.assertIn(("infer", "model_not_published"), result.excluded)
        self.assertIn(("md", "not_yet_ready"), result.excluded)

    def test_duplicate_dispatch_and_stale_feedback_fail_closed(self):
        md = Task("md", "md", 0, 5)
        with self.assertRaises(ValueError):
            self.pick([md], running=[md])
        state = self.ledger.feedback(20)
        with self.assertRaises(ValueError):
            choose([md], feedback=state, now_s=21, gpu_id=0, available_cpu_cores=32, config=config())

    def test_policy_input_and_decision_json_reject_nonfinite_values(self):
        with self.assertRaises(ValueError):
            Task("bad", "md", 0, float("nan"))
        with self.assertRaises(ValueError):
            config(wait_cap_s=0)
        md = Task("md", "md", 0, 5)
        json.dumps(self.pick([md]).to_dict(), allow_nan=False)

    def test_single_gpu_fifo_does_not_force_an_md_ahead_of_older_learning(self):
        train = Task("train", "train", 10, 100)
        md = Task("md", "md", 19, 1)
        result = self.pick([md, train], running=[], cfg=config("Single-GPU-FIFO", gpu_slots=1))
        self.assertEqual(result.task, train)
        self.assertEqual(result.reason, "single_gpu_engineering_fifo")
        self.assertFalse(result.gated)

    def test_single_gpu_fifo_is_strict_fifo_even_during_bootstrap(self):
        self.ledger = FeedbackLedger()
        md, train = Task("md", "md", 0, 100), Task("train", "train", 19, 1)
        result = self.pick([train, md], running=[], cfg=config("Single-GPU-FIFO", gpu_slots=1))
        self.assertEqual(result.task, md)
        self.assertEqual(result.reason, "single_gpu_engineering_fifo")

    def test_single_gpu_cannot_admit_second_simultaneous_task(self):
        train = Task("train", "train", 0, 5)
        result = self.pick([train], cfg=config("Single-GPU-FIFO", gpu_slots=1))
        self.assertIsNone(result.task)
        self.assertEqual(result.reason, "gpu_capacity_full")

    def test_single_gpu_rejects_second_logical_device_and_static_partition(self):
        with self.assertRaisesRegex(ValueError, "two distinct GPUs"):
            config("Static-reservation-matched", gpu_slots=1)
        with self.assertRaisesRegex(ValueError, "exactly one GPU"):
            config("Single-GPU-FIFO", gpu_slots=2)
        md = Task("md", "md", 0, 5)
        with self.assertRaisesRegex(ValueError, "frozen device"):
            self.pick([md], running=[], gpu=1, cfg=config("Single-GPU-FIFO", gpu_slots=1))

    def test_single_gpu_learning_advances_when_new_md_requests_keep_arriving(self):
        cfg = config("Single-GPU-FIFO", gpu_slots=1)
        old_md = Task("md-old", "md", 8, 1)
        train = Task("train", "train", 9, 1)
        self.assertEqual(self.pick([old_md, train], running=[], cfg=cfg).task, old_md)
        fresh_md = Task("md-new", "md", 21, 1)
        self.assertEqual(self.pick([fresh_md, train], running=[], cfg=cfg, now=22).task, train)


if __name__ == "__main__":
    unittest.main()
