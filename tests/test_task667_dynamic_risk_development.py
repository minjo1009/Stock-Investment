from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_667_dynamic_risk_development")


class Task667DynamicRiskDevelopmentTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_667_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_baseline_matches_task639_costed_reference(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_667_decision.csv").iloc[0]

        self.assertAlmostEqual(float(decision["baseline_final_capital_usd"]), 7639.620310821465, places=6)
        self.assertAlmostEqual(float(decision["baseline_max_drawdown_pct"]), -23.755747663170702, places=6)

    def test_no_fixed_hold_or_timing_override(self) -> None:
        specs = pd.read_csv(REPORT_DIR / "task667_candidate_specs.csv")
        grid = pd.read_csv(REPORT_DIR / "task667_candidate_grid.csv")
        names = " ".join(grid["candidate_name"].astype(str).tolist())

        self.assertTrue(pd.to_numeric(specs["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(grid["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertNotIn("hold5", names)
        self.assertNotIn("hold10", names)
        self.assertNotIn("hold20", names)

    def test_account_drawdown_overlay_is_diagnostic_only(self) -> None:
        specs = pd.read_csv(REPORT_DIR / "task667_candidate_specs.csv")
        diagnostic = specs[specs["active_relation_cap_mode"].astype(str).str.contains("account", na=False)]

        self.assertGreater(len(diagnostic), 0)
        self.assertTrue(pd.to_numeric(diagnostic["diagnostic_only_flag"], errors="coerce").eq(1).all())

    def test_no_promotion_candidate(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "task667_promotion_report.csv")
        decision = pd.read_csv(REPORT_DIR / "task_667_decision.csv").iloc[0]

        self.assertEqual(int(promotion["promotion_candidate_flag"].sum()), 0)
        self.assertEqual(int(decision["promotion_candidate_count"]), 0)

    def test_contextual_sizing_reduces_drawdown_but_not_enough(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "task667_promotion_report.csv")
        reference = promotion[promotion["candidate_name"].eq("task666_active_relation_cap3_reference")].iloc[0]
        contextual = promotion[promotion["candidate_name"].eq("relation_cap3_contextual_risk_sizing")].iloc[0]

        self.assertGreater(float(contextual["all_max_drawdown_pct"]), float(reference["all_max_drawdown_pct"]))
        self.assertLess(float(contextual["all_max_drawdown_pct"]), -23.755747663170702)
        self.assertEqual(int(contextual["promotion_candidate_flag"]), 0)

    def test_required_audits_exist(self) -> None:
        for filename in [
            "task667_allocation_panel.csv",
            "task667_sizing_audit.csv",
            "task667_mdd_interval_audit.csv",
            "task667_promotion_blocker_report.md",
            "task_667_gpt_review_response.md",
        ]:
            self.assertTrue((REPORT_DIR / filename).exists(), filename)


if __name__ == "__main__":
    unittest.main()
