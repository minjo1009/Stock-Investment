from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_642_priority_solution_design")


class Task642PrioritySolutionDesignTest(unittest.TestCase):
    def test_priority_order_is_locked(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_642_decision.csv").iloc[0]

        self.assertEqual(decision["decision"], "LOCK_PRIORITY_ORDER_ENTRY_RISK_TIER_TURNOVER_NOT_ACCEPTED")
        self.assertEqual(decision["priority_1"], "Task642A_entry_quality_confirmation")
        self.assertEqual(decision["priority_2"], "Task642B_volatility_risk_sizing")
        self.assertEqual(decision["priority_3"], "Task642C_signal_tier_sizing")
        self.assertEqual(decision["priority_4"], "Task642D_exit_capital_recycling")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_solution_queue_blocks_overfit_shortcuts(self) -> None:
        queue = pd.read_csv(REPORT_DIR / "task_642_solution_queue.csv")
        blocked = " ".join(queue["do_not_use"].astype(str).tolist())

        self.assertEqual(queue.iloc[0]["task_id"], "Task642A")
        self.assertIn("symbol blacklist", blocked)
        self.assertIn("After-the-fact loser labels", blocked)
        self.assertIn("Realized drawdown labels", blocked)

    def test_gpt_discussion_was_captured(self) -> None:
        response = REPORT_DIR / "task_642_gpt_solution_discussion_response.md"

        self.assertTrue(response.exists())
        text = response.read_text(encoding="utf-8")
        self.assertIn("Entry", text)
        self.assertIn("Risk", text)
        self.assertIn("Capital", text)


if __name__ == "__main__":
    unittest.main()
