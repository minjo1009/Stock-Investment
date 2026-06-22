from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_668_regime_theme_playbook")


class Task668RegimeThemePlaybookTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_668_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_baseline_and_reference_are_preserved(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "task668_promotion_report.csv")
        baseline = promotion[promotion["candidate_name"].eq("baseline_task639")].iloc[0]
        reference = promotion[promotion["candidate_name"].eq("active_relation_cap3_reference")].iloc[0]

        self.assertAlmostEqual(float(baseline["all_final_capital_usd"]), 7639.620310821465, places=6)
        self.assertAlmostEqual(float(baseline["all_max_drawdown_pct"]), -23.755747663170702, places=6)
        self.assertAlmostEqual(float(reference["all_final_capital_usd"]), 10887.474713480713, places=6)
        self.assertAlmostEqual(float(reference["all_max_drawdown_pct"]), -30.524857842425657, places=6)

    def test_no_fixed_hold_or_timing_override(self) -> None:
        specs = pd.read_csv(REPORT_DIR / "task668_candidate_specs.csv")
        grid = pd.read_csv(REPORT_DIR / "task668_candidate_grid.csv")
        names = " ".join(grid["candidate_name"].astype(str).tolist())

        self.assertTrue(pd.to_numeric(specs["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertTrue(pd.to_numeric(grid["fixed_hold_or_timing_override_flag"], errors="coerce").eq(0).all())
        self.assertNotIn("hold5", names)
        self.assertNotIn("hold10", names)
        self.assertNotIn("hold20", names)

    def test_playbook_artifacts_exist(self) -> None:
        for filename in [
            "task668_playbook_panel.csv",
            "task668_playbook_performance.csv",
            "task668_transition_matrix.csv",
            "task668_capacity_decision_panel.csv",
            "task668_mdd_interval_audit.csv",
            "task_668_gpt_review_response.md",
        ]:
            self.assertTrue((REPORT_DIR / filename).exists(), filename)

    def test_playbook_lite_sizing_reduces_reference_drawdown_but_does_not_promote(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "task668_promotion_report.csv")
        reference = promotion[promotion["candidate_name"].eq("active_relation_cap3_reference")].iloc[0]
        lite = promotion[promotion["candidate_name"].eq("relation_priority_playbook_lite_sizing")].iloc[0]

        self.assertGreater(float(lite["all_max_drawdown_pct"]), float(reference["all_max_drawdown_pct"]))
        self.assertGreater(float(lite["all_final_capital_usd"]), 10000.0)
        self.assertEqual(int(lite["promotion_candidate_flag"]), 0)

    def test_no_promotion_candidate(self) -> None:
        promotion = pd.read_csv(REPORT_DIR / "task668_promotion_report.csv")
        decision = pd.read_csv(REPORT_DIR / "task_668_decision.csv").iloc[0]

        self.assertEqual(int(promotion["promotion_candidate_flag"].sum()), 0)
        self.assertEqual(int(decision["promotion_candidate_count"]), 0)

    def test_confirmation_required_state_is_audit_visible(self) -> None:
        perf = pd.read_csv(REPORT_DIR / "task668_playbook_performance.csv")
        reference = perf[
            perf["candidate_name"].eq("active_relation_cap3_reference")
            & perf["split_scope"].eq("all")
            & perf["playbook_id"].eq("confirmation_required")
        ]

        self.assertGreater(len(reference), 0)
        self.assertGreater(float(reference.iloc[0]["trade_count"]), 0)


if __name__ == "__main__":
    unittest.main()
