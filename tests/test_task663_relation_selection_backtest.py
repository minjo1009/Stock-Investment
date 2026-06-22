from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_663_relation_selection_backtest")


class Task663RelationSelectionBacktestTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_663_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_no_fixed_hold_or_timing_override(self) -> None:
        grid = pd.read_csv(REPORT_DIR / "relation_selection_candidate_grid.csv")
        specs = pd.read_csv(REPORT_DIR / "relation_selection_candidate_specs.csv")
        names = " ".join(grid["candidate_name"].astype(str).tolist())

        self.assertTrue(pd.to_numeric(grid["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(specs["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertNotIn("hold5", names)
        self.assertNotIn("hold10", names)
        self.assertNotIn("hold20", names)

    def test_oos_selection_moves_account_results(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "relation_selection_promotion_report.csv")

        both_oos = promotion[
            pd.to_numeric(promotion["validation_improves_task639_flag"], errors="coerce").eq(1)
            & pd.to_numeric(promotion["recent_oos_improves_task639_flag"], errors="coerce").eq(1)
        ]
        self.assertGreater(len(both_oos), 0)

    def test_no_promotion_candidate(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "relation_selection_promotion_report.csv")
        decision = pd.read_csv(REPORT_DIR / "task_663_decision.csv").iloc[0]

        self.assertEqual(int(promotion["promotion_candidate_flag"].sum()), 0)
        self.assertEqual(int(decision["promotion_candidate_count"]), 0)

    def test_relation_state_diagnostics_show_recent_spread(self) -> None:
        diagnostics = pd.read_csv(REPORT_DIR / "relation_state_oos_diagnostics.csv")
        recent = diagnostics[diagnostics["split_name"].astype(str).eq("recent_oos")]
        reinforcing = recent[recent["mechanism_relation_state"].eq("mechanism_reinforcing_company_positive")].iloc[0]
        quality_confirmed = recent[recent["mechanism_relation_state"].eq("company_quality_price_confirmed")].iloc[0]

        self.assertGreater(float(reinforcing["avg_return_pct"]), float(quality_confirmed["avg_return_pct"]))


if __name__ == "__main__":
    unittest.main()
