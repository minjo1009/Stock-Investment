from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_651_relation_state_machine")


class Task651RelationStateMachineTest(unittest.TestCase):
    def test_decision_remains_research_only(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_651_decision.csv").iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertGreater(float(decision["task651_final_capital_usd"]), float(decision["task651_qqq_final_capital_usd"]))
        self.assertEqual(int(decision["beats_task639_recomputed_flag"]), 0)

    def test_gate_panel_has_required_outputs(self) -> None:
        panel = pd.read_csv(REPORT_DIR / "task_651_gate_state_panel.csv")
        required = {
            "source_gate_state",
            "macro_gate_state",
            "policy_geo_gate_state",
            "sector_gate_state",
            "company_gate_state",
            "chart_gate_state",
            "relation_state",
            "action_bucket",
            "research_only_flag",
            "action_reason_codes",
        }

        self.assertGreater(len(panel), 0)
        self.assertTrue(required.issubset(set(panel.columns)))
        self.assertGreaterEqual(panel["relation_state"].nunique(), 2)
        self.assertGreaterEqual(panel["action_bucket"].nunique(), 2)

    def test_leakage_audit_passes(self) -> None:
        leakage = pd.read_csv(REPORT_DIR / "task_651_leakage_audit.csv")
        violations = pd.to_numeric(leakage["violation_count"], errors="coerce")

        self.assertTrue(violations.eq(0).all())
        self.assertTrue(pd.to_numeric(leakage["pass_flag"], errors="coerce").eq(1).all())

    def test_account_comparison_keeps_task639_baseline(self) -> None:
        account = pd.read_csv(REPORT_DIR / "task_651_account_comparison.csv")
        names = set(account["comparison_name"])

        self.assertIn("task651_relation_action_strategy", names)
        self.assertIn("task639_recomputed_positive_contract_or_supply", names)
        task651 = account[account["comparison_name"].eq("task651_relation_action_strategy") & account["split_name"].eq("all")].iloc[0]
        task639 = account[account["comparison_name"].eq("task639_recomputed_positive_contract_or_supply") & account["split_name"].eq("all")].iloc[0]
        self.assertLess(float(task651["final_capital_usd"]), float(task639["final_capital_usd"]))


if __name__ == "__main__":
    unittest.main()
