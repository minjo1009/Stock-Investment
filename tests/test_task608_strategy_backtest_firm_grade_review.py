from __future__ import annotations

import unittest

from src.backtest.build_task608_strategy_backtest_firm_grade_review import (
    build_decision,
    build_gpt_review_notes,
    build_upgrade_backlog,
    collect_metric_snapshot,
)


class Task608StrategyBacktestFirmGradeReviewTest(unittest.TestCase):
    def test_metric_snapshot_preserves_current_not_accepted_status(self) -> None:
        metrics = collect_metric_snapshot()
        row = metrics.iloc[0]

        self.assertEqual(row["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(row["deployment_status"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertGreater(float(row["two_year_capital_pnl_pct"]), 0.0)
        self.assertGreater(float(row["avg_degradation_ratio"]), 0.0)

    def test_backlog_prioritizes_dependency_and_neighborhood_audits(self) -> None:
        metrics = collect_metric_snapshot()
        backlog = build_upgrade_backlog(metrics)
        notes = build_gpt_review_notes(metrics)
        decision = build_decision(metrics).iloc[0]

        self.assertEqual(decision["decision"], "RESEARCH_CANDIDATE_NOT_FIRM_GRADE")
        self.assertIn("Task608A", set(backlog["proposed_task_id"]))
        self.assertIn("Task608B", set(backlog["proposed_task_id"]))
        self.assertIn("Task608C", set(backlog["proposed_task_id"]))
        self.assertIn("theme_dependency_must_be_tested", set(notes["finding"]))
        self.assertTrue((backlog["status"] == "accepted_to_backlog").all())


if __name__ == "__main__":
    unittest.main()
