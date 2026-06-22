from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_672_current_data_state_axis_panel")


class Task672CurrentDataStateAxisPanelTest(unittest.TestCase):
    def test_decision_remains_diagnostic_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_672_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["deployment_status"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_required_state_axes_exist(self) -> None:
        panel = pd.read_csv(REPORT_DIR / "task672_state_axis_panel.csv", nrows=10)

        for axis in [
            "source_integrity_state",
            "macro_market_state",
            "rates_dollar_credit_liquidity_state",
            "theme_leadership_state",
            "company_catalyst_state",
            "price_chart_acceptance_state",
            "relation_transmission_state",
            "portfolio_capacity_state",
            "proxy_risk_context",
        ]:
            self.assertIn(axis, panel.columns)

    def test_microstructure_is_not_used(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_672_decision.csv").iloc[0]
        audit = pd.read_csv(REPORT_DIR / "task672_forbidden_input_audit.csv")
        micro = audit[audit["check_name"].eq("microstructure_used_in_assignment")].iloc[0]

        self.assertEqual(decision["microstructure_state"], "SOURCE_PENDING_NOT_USED")
        self.assertEqual(int(decision["microstructure_used_in_assignment"]), 0)
        self.assertEqual(int(micro["violation_count"]), 0)

    def test_forbidden_input_audit_is_clean(self) -> None:
        audit = pd.read_csv(REPORT_DIR / "task672_forbidden_input_audit.csv")

        self.assertEqual(int(pd.to_numeric(audit["violation_count"], errors="coerce").sum()), 0)
        self.assertTrue(pd.to_numeric(audit["pass_flag"], errors="coerce").eq(1).all())

    def test_comparison_preserves_reference_results(self) -> None:
        comparison = pd.read_csv(REPORT_DIR / "task672_comparison_summary.csv")
        baseline = comparison[
            comparison["candidate_name"].eq("baseline_task639")
            & comparison["split_name"].eq("all")
            & comparison["comparison_type"].eq("account_result")
        ].iloc[0]
        active = comparison[
            comparison["candidate_name"].eq("active_relation_cap3_reference")
            & comparison["split_name"].eq("all")
            & comparison["comparison_type"].eq("account_result")
        ].iloc[0]

        self.assertAlmostEqual(float(baseline["final_capital_usd"]), 7639.620310821465, places=6)
        self.assertAlmostEqual(float(active["final_capital_usd"]), 10887.474713480713, places=6)
        self.assertAlmostEqual(float(active["max_drawdown_pct"]), -30.524857842425657, places=6)

    def test_diagnostic_artifacts_exist(self) -> None:
        for filename in [
            "task672_axis_value_performance.csv",
            "task672_active_relation_cap3_axis_exposure.csv",
            "task672_mdd_axis_exposure_report.csv",
            "task672_capacity_context_report.csv",
            "task672_sparse_cell_report.csv",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((REPORT_DIR / filename).exists(), filename)


if __name__ == "__main__":
    unittest.main()
