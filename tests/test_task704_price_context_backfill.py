from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK704_DIR = Path("docs/reports/task_704_price_context_backfill")


class Task704PriceContextBackfillTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task704_price_context_panel.csv",
            "task704_price_context_summary.csv",
            "task_704_decision.csv",
            "task_704_pass_fail_matrix.csv",
            "task_704_price_context_backfill.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK704_DIR / name).exists(), name)

    def test_full_context_coverage_and_no_leakage(self) -> None:
        panel = pd.read_csv(TASK704_DIR / "task704_price_context_panel.csv")

        self.assertEqual(len(panel), 5265)
        self.assertEqual(int(panel["event_linked_flag"].sum()), 2445)
        self.assertEqual(int(panel["price_context_available_flag"].sum()), 5265)
        self.assertEqual(int(panel[panel["event_linked_flag"].eq(1)]["price_context_available_flag"].sum()), 2445)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)

    def test_summary_and_decision(self) -> None:
        summary = pd.read_csv(TASK704_DIR / "task704_price_context_summary.csv")
        decision = pd.read_csv(TASK704_DIR / "task_704_decision.csv").iloc[0]
        event = summary[summary["scope"].eq("event_linked")].iloc[0]

        self.assertEqual(int(event["price_context_available_count"]), 2445)
        self.assertEqual(int(event["price_context_missing_count"]), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_pass_fail_matrix_passes(self) -> None:
        pass_fail = pd.read_csv(TASK704_DIR / "task_704_pass_fail_matrix.csv")
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
