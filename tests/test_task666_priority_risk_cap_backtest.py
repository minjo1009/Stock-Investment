from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_666_priority_risk_cap_backtest")


class Task666PriorityRiskCapBacktestTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_666_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_baseline_matches_task639_costed_reference(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_666_decision.csv").iloc[0]

        self.assertAlmostEqual(float(decision["baseline_final_capital_usd"]), 7639.620310821465, places=6)
        self.assertAlmostEqual(float(decision["baseline_max_drawdown_pct"]), -23.755747663170702, places=6)

    def test_no_fixed_hold_or_timing_override(self) -> None:
        specs = pd.read_csv(REPORT_DIR / "priority_risk_cap_specs.csv")
        grid = pd.read_csv(REPORT_DIR / "priority_risk_cap_candidate_grid.csv")
        names = " ".join(grid["candidate_name"].astype(str).tolist())

        self.assertTrue(pd.to_numeric(specs["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(grid["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertNotIn("hold5", names)
        self.assertNotIn("hold10", names)
        self.assertNotIn("hold20", names)

    def test_return_tuned_candidate_cannot_promote(self) -> None:
        specs = pd.read_csv(REPORT_DIR / "priority_risk_cap_specs.csv")
        promotion = pd.read_csv(REPORT_DIR / "priority_risk_cap_promotion_report.csv")
        return_tuned = set(specs[pd.to_numeric(specs["return_tuned_flag"], errors="coerce").eq(1)]["candidate_name"].astype(str))
        promoted = set(promotion[pd.to_numeric(promotion["promotion_candidate_flag"], errors="coerce").eq(1)]["candidate_name"].astype(str))

        self.assertTrue(promoted.isdisjoint(return_tuned))

    def test_no_promotion_candidate(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "priority_risk_cap_promotion_report.csv")
        decision = pd.read_csv(REPORT_DIR / "task_666_decision.csv").iloc[0]

        self.assertEqual(int(promotion["promotion_candidate_flag"].sum()), 0)
        self.assertEqual(int(decision["promotion_candidate_count"]), 0)

    def test_cap_audit_artifacts_exist(self) -> None:
        allocation = pd.read_csv(REPORT_DIR / "task666_capacity_allocation_panel.csv")
        displacement = pd.read_csv(REPORT_DIR / "task666_displacement_pairs.csv")
        theme = pd.read_csv(REPORT_DIR / "task666_theme_concentration_audit.csv")
        relation = pd.read_csv(REPORT_DIR / "task666_relation_concentration_audit.csv")

        self.assertGreater(len(allocation), 0)
        self.assertGreater(len(displacement), 0)
        self.assertGreater(len(theme), 0)
        self.assertGreater(len(relation), 0)
        self.assertIn("active_relation_cap", set(allocation["allocation_reason"].astype(str)))

    def test_active_relation_cap_is_research_evidence_not_promotion(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "priority_risk_cap_promotion_report.csv")
        row = promotion[promotion["candidate_name"].eq("priority_active_relation_cap3")].iloc[0]

        self.assertGreater(float(row["all_final_capital_usd"]), 7639.620310821465)
        self.assertLess(float(row["all_max_drawdown_pct"]), -23.755747663170702)
        self.assertEqual(int(row["promotion_candidate_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
