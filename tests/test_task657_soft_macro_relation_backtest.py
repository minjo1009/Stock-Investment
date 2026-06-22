from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_657_soft_macro_relation_backtest")


class Task657SoftMacroRelationBacktestTest(unittest.TestCase):
    def test_decision_remains_not_accepted(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_657_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_candidate_grid_contains_baseline_and_soft_candidates(self) -> None:
        grid = pd.read_csv(REPORT_DIR / "task_657_candidate_account_grid.csv")

        self.assertIn("baseline_task639_core", set(grid["candidate_name"]))
        self.assertGreater(len(grid), 3)
        self.assertTrue(pd.to_numeric(grid["label_used_in_assignment_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(grid["return_used_in_assignment_flag"], errors="coerce").eq(0).all())

    def test_permission_audit_blocks_no_forbidden_macro_authority(self) -> None:
        audit = pd.read_csv(REPORT_DIR / "task_657_permission_audit.csv")

        self.assertTrue(pd.to_numeric(audit["forbidden_macro_authority_used_flag"], errors="coerce").eq(0).all())

    def test_promotion_report_is_consistent(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "task_657_promotion_report.csv")
        decision = pd.read_csv(REPORT_DIR / "task_657_decision.csv").iloc[0]

        self.assertEqual(int(promotion["promotion_candidate_flag"].sum()), int(decision["promotion_candidate_count"]))


if __name__ == "__main__":
    unittest.main()
