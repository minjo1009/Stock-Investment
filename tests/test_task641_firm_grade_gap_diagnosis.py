from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_641_firm_grade_gap_diagnosis")


class Task641FirmGradeGapDiagnosisTest(unittest.TestCase):
    def test_baseline_and_decision_are_locked(self) -> None:
        baseline = pd.read_csv(REPORT_DIR / "task_641_task639_baseline_diagnostic.csv").iloc[0]
        decision = pd.read_csv(REPORT_DIR / "task_641_decision.csv").iloc[0]

        self.assertEqual(decision["decision"], "DIAGNOSE_FIRM_GRADE_GAPS_BEFORE_MORE_ALPHA_SEARCH")
        self.assertAlmostEqual(float(baseline["final_capital_usd"]), 7639.620310821465, places=2)
        self.assertAlmostEqual(float(baseline["max_drawdown_pct"]), -23.755747663170702, places=2)
        self.assertEqual(int(baseline["accepted_trade_count"]), 54)
        self.assertEqual(int(baseline["skipped_due_capacity_count"]), 1567)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_gap_matrix_prioritizes_execution_and_risk_not_etf(self) -> None:
        gap = pd.read_csv(REPORT_DIR / "task_641_firm_grade_gap_matrix.csv")
        ordered = gap.sort_values("priority")

        self.assertEqual(ordered.iloc[0]["gap"], "entry_quality_confirmation_missing")
        self.assertIn("risk_normalized_sizing_missing", set(gap["gap"]))
        self.assertIn("microstructure_source_gap", set(gap["gap"]))
        self.assertNotIn("leveraged_etf_overlay", set(gap["gap"]))

    def test_gpt_review_was_captured(self) -> None:
        response = REPORT_DIR / "task_641_gpt_review_response.md"

        self.assertTrue(response.exists())
        text = response.read_text(encoding="utf-8")
        self.assertIn("Entry Quality", text)
        self.assertIn("Risk Normalization", text)
        self.assertIn("microstructure", text)


if __name__ == "__main__":
    unittest.main()
