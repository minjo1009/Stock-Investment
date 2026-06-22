from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_670_state_decomposition_design")


class Task670StateDecompositionDesignTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_670_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_core_and_diagnostic_axis_counts(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_670_decision.csv").iloc[0]

        self.assertEqual(int(decision["core_axis_count"]), 8)
        self.assertEqual(int(decision["diagnostic_axis_count"]), 3)

    def test_axis_definition_contains_required_axes(self) -> None:
        text = (REPORT_DIR / "task_670_axis_definition.md").read_text(encoding="utf-8")

        for axis in [
            "source_integrity_state",
            "market_macro_state",
            "liquidity_credit_state",
            "theme_leadership_state",
            "rotation_participation_state",
            "company_catalyst_quality_state",
            "price_acceptance_state",
            "portfolio_capacity_state",
            "factor_exposure_state",
            "microstructure_state",
            "crowding_risk_state",
        ]:
            self.assertIn(axis, text)

    def test_no_action_mapping_allowed(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_670_pass_fail_matrix.csv")
        action_gate = pass_fail[pass_fail["gate"].eq("trading_action_allowed")].iloc[0]
        capital_gate = pass_fail[pass_fail["gate"].eq("real_capital_allowed")].iloc[0]

        self.assertEqual(int(action_gate["pass_flag"]), 0)
        self.assertEqual(int(capital_gate["pass_flag"]), 0)

    def test_gpt_review_artifacts_exist(self) -> None:
        self.assertTrue((REPORT_DIR / "task_670_gpt_review_packet.md").exists())
        self.assertTrue((REPORT_DIR / "task_670_gpt_review_response.md").exists())
        self.assertTrue((REPORT_DIR / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
