from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK720 = Path("docs/reports/task_720_watch_bucket_interaction_diagnostics")


class Task720WatchBucketInteractionDiagnosticsTest(unittest.TestCase):
    def test_artifacts_and_core_contract(self) -> None:
        required = [
            "task720_watch_bucket_interaction_panel.csv",
            "task720_institutional_context_pack.csv",
            "task720_bucket_interaction_matrix.csv",
            "task720_human_review_queue.csv",
            "task720_eval_guardrail.csv",
            "task720_leakage_guardrail.csv",
            "task720_governance_audit.csv",
            "task_720_decision.csv",
            "task_720_pass_fail_matrix.csv",
            "task_720_watch_bucket_interaction_diagnostics.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASK720 / name).exists(), name)

        panel = pd.read_csv(TASK720 / "task720_watch_bucket_interaction_panel.csv")
        self.assertEqual(len(panel), 345)
        self.assertEqual(panel["watch_subtype"].nunique(), 3)
        self.assertGreaterEqual(panel["layer_interaction_state"].nunique(), 5)
        self.assertGreaterEqual(panel["diagnostic_bucket_state"].nunique(), 5)
        self.assertTrue(panel["final_diagnostic_state"].astype(str).str.startswith("DIAGNOSTIC_").all())
        self.assertEqual(int(panel["new_layer_required_flag"].sum()), 0)
        self.assertEqual(int(panel["interaction_logic_upgrade_required_flag"].min()), 1)

        self.assertEqual(int(panel["translator_output_is_action_flag"].sum()), 0)
        self.assertEqual(int(panel["assignment_used_flag"].sum()), 0)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["top50_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["ticker_theme_protection_rule_flag"].sum()), 0)
        self.assertEqual(int(panel["threshold_tuned_from_outcome_flag"].sum()), 0)
        self.assertEqual(int(panel["buy_sell_or_sizing_instruction_flag"].sum()), 0)
        self.assertEqual(int(panel["missing_source_used_as_negative_flag"].sum()), 0)
        self.assertEqual(set(panel["real_capital_status"]), {"FORBIDDEN"})

    def test_matrix_queue_and_context(self) -> None:
        panel = pd.read_csv(TASK720 / "task720_watch_bucket_interaction_panel.csv")
        matrix = pd.read_csv(TASK720 / "task720_bucket_interaction_matrix.csv")
        queue = pd.read_csv(TASK720 / "task720_human_review_queue.csv")
        context = pd.read_csv(TASK720 / "task720_institutional_context_pack.csv")

        self.assertGreaterEqual(len(matrix), 5)
        self.assertEqual(int(matrix["new_layer_required_flag"].sum()), 0)
        self.assertEqual(int(matrix["interaction_logic_upgrade_required_flag"].min()), 1)
        self.assertEqual(int(matrix["outcome_used_for_assignment_flag"].sum()), 0)

        self.assertEqual(len(queue), len(panel))
        self.assertTrue(queue["manual_review_questions"].astype(str).str.len().gt(0).all())
        self.assertGreaterEqual(len(context), 4)
        self.assertTrue(context["source_url"].astype(str).str.startswith("https://").all())

    def test_guardrails(self) -> None:
        eval_guardrail = pd.read_csv(TASK720 / "task720_eval_guardrail.csv")
        leakage = pd.read_csv(TASK720 / "task720_leakage_guardrail.csv")
        governance = pd.read_csv(TASK720 / "task720_governance_audit.csv")
        pass_fail = pd.read_csv(TASK720 / "task_720_pass_fail_matrix.csv")
        decision = pd.read_csv(TASK720 / "task_720_decision.csv").iloc[0]

        self.assertEqual(int(eval_guardrail["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(eval_guardrail["outcome_used_for_evaluation_flag"].min()), 1)
        self.assertEqual(int(leakage["pass_flag"].min()), 1)
        self.assertEqual(int(governance["pass_flag"].min()), 1)
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
