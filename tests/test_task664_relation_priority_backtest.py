from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_664_relation_priority_backtest")


class Task664RelationPriorityBacktestTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_664_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_baseline_matches_task639_costed_reference(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_664_decision.csv").iloc[0]

        self.assertAlmostEqual(float(decision["baseline_final_capital_usd"]), 7639.620310821465, places=6)
        self.assertAlmostEqual(float(decision["baseline_max_drawdown_pct"]), -23.755747663170702, places=6)

    def test_no_fixed_hold_or_timing_override(self) -> None:
        specs = pd.read_csv(REPORT_DIR / "relation_priority_candidate_specs.csv")
        grid = pd.read_csv(REPORT_DIR / "relation_priority_candidate_grid.csv")
        names = " ".join(grid["candidate_name"].astype(str).tolist())

        self.assertTrue(pd.to_numeric(specs["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(grid["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertNotIn("hold5", names)
        self.assertNotIn("hold10", names)
        self.assertNotIn("hold20", names)

    def test_priority_changes_accepted_set(self) -> None:
        delta = pd.read_csv(REPORT_DIR / "accepted_priority_delta.csv")

        self.assertGreater(int(pd.to_numeric(delta["accepted_set_changed_flag"], errors="coerce").sum()), 0)

    def test_return_tuned_candidate_cannot_promote(self) -> None:
        specs = pd.read_csv(REPORT_DIR / "relation_priority_candidate_specs.csv")
        promotion = pd.read_csv(REPORT_DIR / "relation_priority_promotion_report.csv")
        return_tuned = set(specs[pd.to_numeric(specs["return_tuned_flag"], errors="coerce").eq(1)]["candidate_name"].astype(str))
        promoted = set(promotion[pd.to_numeric(promotion["promotion_candidate_flag"], errors="coerce").eq(1)]["candidate_name"].astype(str))

        self.assertTrue(promoted.isdisjoint(return_tuned))

    def test_no_promotion_candidate(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "relation_priority_promotion_report.csv")
        decision = pd.read_csv(REPORT_DIR / "task_664_decision.csv").iloc[0]

        self.assertEqual(int(promotion["promotion_candidate_flag"].sum()), 0)
        self.assertEqual(int(decision["promotion_candidate_count"]), 0)


if __name__ == "__main__":
    unittest.main()
