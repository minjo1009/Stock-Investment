from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK719 = Path("docs/reports/task_719_watch_subtype_confirmation_contract")


class Task719WatchSubtypeConfirmationContractTest(unittest.TestCase):
    def test_artifacts_and_core_contract(self) -> None:
        required = [
            "task719_watch_confirmation_contract_panel.csv",
            "task719_confirmation_rulebook.csv",
            "task719_confirmation_interaction_graph.csv",
            "task719_confirmation_gap_audit.csv",
            "task719_guardrail_audit.csv",
            "task719_governance_audit.csv",
            "task_719_decision.csv",
            "task_719_pass_fail_matrix.csv",
            "task_719_watch_subtype_confirmation_contract.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASK719 / name).exists(), name)

        panel = pd.read_csv(TASK719 / "task719_watch_confirmation_contract_panel.csv")
        self.assertEqual(len(panel), 358)
        self.assertEqual(panel["watch_subtype"].nunique(), 4)
        self.assertEqual(int(panel["confirmation_contract_satisfied"].sum()), 0)
        self.assertEqual(set(panel["missing_data_state"]), {"missing_or_unconfirmed_treated_as_unknown"})
        self.assertEqual(int(panel["translator_output_is_action_flag"].sum()), 0)
        self.assertEqual(int(panel["assignment_used_flag"].sum()), 0)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["top50_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["winner_structure_eval_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["ticker_theme_protection_rule_flag"].sum()), 0)
        self.assertEqual(int(panel["threshold_tuned_from_outcome_flag"].sum()), 0)
        self.assertEqual(int(panel["buy_sell_or_sizing_instruction_flag"].sum()), 0)
        self.assertEqual(int(panel["missing_source_used_as_negative_flag"].sum()), 0)
        self.assertEqual(set(panel["real_capital_status"]), {"FORBIDDEN"})

    def test_rulebook_and_graph(self) -> None:
        panel = pd.read_csv(TASK719 / "task719_watch_confirmation_contract_panel.csv")
        rulebook = pd.read_csv(TASK719 / "task719_confirmation_rulebook.csv")
        graph = pd.read_csv(TASK719 / "task719_confirmation_interaction_graph.csv")

        self.assertEqual(len(rulebook), 4)
        self.assertEqual(int(rulebook["single_condition_promotion_allowed_flag"].sum()), 0)
        self.assertEqual(int(rulebook["buy_sell_or_sizing_instruction_flag"].sum()), 0)
        self.assertEqual(set(rulebook["missing_data_policy"]), {"missing_is_unknown_not_negative"})

        self.assertEqual(len(graph), len(panel) * 5)
        self.assertEqual(int(graph["assignment_safe_flag"].sum()), len(graph))
        self.assertEqual(int(graph["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertGreaterEqual(graph["relation_type"].nunique(), 2)

    def test_eval_guardrails_are_eval_only(self) -> None:
        guardrail = pd.read_csv(TASK719 / "task719_guardrail_audit.csv")
        governance = pd.read_csv(TASK719 / "task719_governance_audit.csv")
        pass_fail = pd.read_csv(TASK719 / "task_719_pass_fail_matrix.csv")
        decision = pd.read_csv(TASK719 / "task_719_decision.csv").iloc[0]

        self.assertEqual(int(guardrail["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(guardrail["outcome_used_for_evaluation_flag"].min()), 1)
        self.assertLessEqual(int(guardrail["top50_winner_count_eval_only"].sum()), 50)
        self.assertLessEqual(int(guardrail["bottom50_loser_count_eval_only"].sum()), 50)

        self.assertEqual(int(governance["pass_flag"].min()), 1)
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
