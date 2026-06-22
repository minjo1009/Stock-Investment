from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_645_microstructure_content_source_upgrade")


class Task645MicrostructureContentSourceUpgradeTest(unittest.TestCase):
    def test_task645_outputs_and_gates(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_645_decision.csv").iloc[0]
        pass_fail = pd.read_csv(REPORT_DIR / "task_645_pass_fail_matrix.csv")
        source = pd.read_csv(REPORT_DIR / "task_645_source_audit.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
        self.assertEqual(gates["task639_baseline_reproduced"], 1)
        self.assertEqual(gates["no_shortcut_or_missing_as_negative"], 1)
        self.assertEqual(gates["trading_promotion"], 0)
        self.assertEqual(gates["microstructure_coverage_sufficient_for_micro_rule"], 0)

        self.assertGreater(float(source["quote_covered_row_rate"]), 0.0)
        self.assertLess(float(source["quote_covered_row_rate"]), 0.20)
        self.assertEqual(int(source["missing_microstructure_used_as_negative_flag"]), 0)

    def test_feature_panel_has_required_states(self) -> None:
        panel = pd.read_csv(REPORT_DIR / "task_645_microstructure_content_feature_panel.csv")
        required = {
            "micro_continuation_state",
            "content_quality_tier_task645",
            "combined_quality_micro_state",
            "micro_missing_treated_as_negative_flag",
            "content_assignment_used_outcome_flag",
            "gpt_or_plugin_used_as_source_flag_task645",
        }

        self.assertTrue(required.issubset(panel.columns))
        self.assertEqual(int(pd.to_numeric(panel["micro_missing_treated_as_negative_flag"]).sum()), 0)
        self.assertEqual(int(pd.to_numeric(panel["content_assignment_used_outcome_flag"]).sum()), 0)
        self.assertEqual(int(pd.to_numeric(panel["gpt_or_plugin_used_as_source_flag_task645"]).sum()), 0)
        self.assertIn("fragile_breakout", set(panel["micro_continuation_state"]))
        self.assertIn("strong_contract_quality", set(panel["content_quality_tier_task645"]))


if __name__ == "__main__":
    unittest.main()
