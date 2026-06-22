from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK718 = Path("docs/reports/task_718_winner_structure_interaction_brain")


class Task718WinnerStructureInteractionBrainTest(unittest.TestCase):
    def test_artifacts_and_core_contract(self) -> None:
        required = [
            "task718_winner_structure_panel.csv",
            "task718_interaction_graph.csv",
            "task718_watch_decomposition.csv",
            "task718_convexity_audit.csv",
            "task718_guardrail_audit.csv",
            "task718_governance_audit.csv",
            "task_718_decision.csv",
            "task_718_pass_fail_matrix.csv",
            "task_718_winner_structure_interaction_brain.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASK718 / name).exists(), name)

        panel = pd.read_csv(TASK718 / "task718_winner_structure_panel.csv")
        self.assertEqual(len(panel), 5265)
        self.assertEqual(int(panel["source_event_available_flag"].sum()), 2445)
        self.assertGreaterEqual(panel["winner_structure_state"].nunique(), 6)
        self.assertEqual(int(panel["translator_output_is_action_flag"].sum()), 0)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["missing_source_used_as_negative_flag"].sum()), 0)
        self.assertEqual(int(panel["macro_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["top50_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["watch_promoted_to_buy_flag"].sum()), 0)
        self.assertEqual(int(panel["ticker_theme_protection_rule_flag"].sum()), 0)
        self.assertEqual(int(panel["threshold_tuned_from_outcome_flag"].sum()), 0)
        self.assertEqual(set(panel["real_capital_status"]), {"FORBIDDEN"})

    def test_interaction_graph_and_watch_decomposition(self) -> None:
        panel = pd.read_csv(TASK718 / "task718_winner_structure_panel.csv")
        graph = pd.read_csv(TASK718 / "task718_interaction_graph.csv")
        watch = pd.read_csv(TASK718 / "task718_watch_decomposition.csv")

        self.assertEqual(len(graph), len(panel) * 5)
        self.assertEqual(int(graph["assignment_safe_flag"].sum()), len(graph))
        self.assertEqual(int(graph["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertGreaterEqual(graph["relation_type"].nunique(), 5)

        self.assertGreater(len(watch), 0)
        self.assertGreaterEqual(watch["watch_subtype"].nunique(), 2)
        self.assertEqual(int(watch["watch_promoted_to_buy_flag"].sum()), 0)
        self.assertEqual(int(watch["outcome_used_for_assignment_flag"].sum()), 0)

    def test_eval_guardrails_are_eval_only(self) -> None:
        guardrail = pd.read_csv(TASK718 / "task718_guardrail_audit.csv")
        convexity = pd.read_csv(TASK718 / "task718_convexity_audit.csv")
        governance = pd.read_csv(TASK718 / "task718_governance_audit.csv")
        pass_fail = pd.read_csv(TASK718 / "task_718_pass_fail_matrix.csv")
        decision = pd.read_csv(TASK718 / "task_718_decision.csv").iloc[0]

        for audit in [guardrail, convexity]:
            self.assertEqual(int(audit["top50_winner_count_eval_only"].sum()), 50)
            self.assertEqual(int(audit["bottom50_loser_count_eval_only"].sum()), 50)
            self.assertEqual(int(audit["outcome_used_for_assignment_flag"].sum()), 0)
            self.assertEqual(int(audit["outcome_used_for_evaluation_flag"].min()), 1)

        self.assertEqual(int(governance["pass_flag"].min()), 1)
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
