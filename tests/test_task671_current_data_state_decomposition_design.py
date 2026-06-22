from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_671_current_data_state_decomposition_design")


class Task671CurrentDataStateDecompositionDesignTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_671_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_current_data_axis_counts(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_671_decision.csv").iloc[0]

        self.assertEqual(int(decision["implementable_axis_count"]), 8)
        self.assertEqual(int(decision["diagnostic_aux_axis_count"]), 1)

    def test_microstructure_is_source_pending_not_used(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_671_decision.csv").iloc[0]
        axis_text = (REPORT_DIR / "task_671_axis_definition.md").read_text(encoding="utf-8")

        self.assertEqual(decision["microstructure_state"], "SOURCE_PENDING_NOT_USED")
        self.assertEqual(int(decision["microstructure_used_in_assignment"]), 0)
        self.assertIn("SOURCE_PENDING_NOT_USED", axis_text)
        self.assertIn("using chart fields as fake microstructure", axis_text)

    def test_required_current_data_axes_exist(self) -> None:
        text = (REPORT_DIR / "task_671_axis_definition.md").read_text(encoding="utf-8")

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
            self.assertIn(axis, text)

    def test_no_action_mapping_allowed(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_671_pass_fail_matrix.csv")
        action_gate = pass_fail[pass_fail["gate"].eq("trading_action_allowed")].iloc[0]
        capital_gate = pass_fail[pass_fail["gate"].eq("real_capital_allowed")].iloc[0]

        self.assertEqual(int(action_gate["pass_flag"]), 0)
        self.assertEqual(int(capital_gate["pass_flag"]), 0)

    def test_gpt_and_manifest_artifacts_exist(self) -> None:
        for filename in [
            "task_671_gpt_review_packet.md",
            "task_671_gpt_review_response.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((REPORT_DIR / filename).exists(), filename)


if __name__ == "__main__":
    unittest.main()
