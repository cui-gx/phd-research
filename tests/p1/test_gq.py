"""Budget failure and admission invariants: stdlib only; run on server."""
import unittest
from p1.server.gq_control import allowance, admit


class BudgetTests(unittest.TestCase):
    def test_failures_and_other_stages_consume_global_budget(self):
        rows = [{"stage": "gq1", "charged_s": 599, "status": "failure"},
                {"stage": "gq2", "charged_s": 1190, "status": "complete"}]
        self.assertEqual(allowance(rows, "gq1"), 1)
        with self.assertRaises(RuntimeError):
            admit(rows, "gq1", 1)

    def test_pending_reservation_blocks_restart(self):
        with self.assertRaises(RuntimeError):
            admit([{"stage": "gq1", "charged_s": 115, "status": "pending"}], "gq2", 100)

    def test_stage_cap_cannot_borrow_unused_other_stage(self):
        with self.assertRaises(RuntimeError):
            admit([], "gq1", 600)
        admit([], "gq1", 585)

    def test_unknown_stage_and_negative_timeout_rejected(self):
        with self.assertRaises(ValueError):
            admit([], "new-name", 1)
        with self.assertRaises(RuntimeError):
            admit([], "gq1", -1)


if __name__ == "__main__":
    unittest.main()
