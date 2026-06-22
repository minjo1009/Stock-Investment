from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK721 = Path("docs/reports/task_721_watch_bucket_decomposition_packets")


class Task721WatchBucketDecompositionPacketsTest(unittest.TestCase):
    def test_artifacts_and_decomposition_contract(self) -> None:
        required = [
            "task721_decomposition_panel.csv",
            "task721_interaction_edge_matrix.csv",
            "task721_human_review_packet_queue.csv",
            "task721_manual_review_samples.csv",
            "task721_bucket_review_protocol.csv",
            "task721_eval_guardrail.csv",
            "task721_leakage_guardrail.csv",
            "task721_governance_audit.csv",
            "task_721_decision.csv",
            "task_721_pass_fail_matrix.csv",
            "task_721_watch_bucket_decomposition_packets.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASK721 / name).exists(), name)

        panel = pd.read_csv(TASK721 / "task721_decomposition_panel.csv")
        self.assertEqual(len(panel), 345)
        self.assertGreaterEqual(panel["next_decomposition_state"].nunique(), 8)
        self.assertEqual(set(panel["diagnostic_only_state"]), {"DIAGNOSTIC_REVIEW_REQUIRED"})
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

    def test_edge_matrix_and_packet_queue(self) -> None:
        panel = pd.read_csv(TASK721 / "task721_decomposition_panel.csv")
        edges = pd.read_csv(TASK721 / "task721_interaction_edge_matrix.csv")
        queue = pd.read_csv(TASK721 / "task721_human_review_packet_queue.csv")
        samples = pd.read_csv(TASK721 / "task721_manual_review_samples.csv")
        protocol = pd.read_csv(TASK721 / "task721_bucket_review_protocol.csv")

        self.assertEqual(len(edges), len(panel) * 4)
        self.assertEqual(int(edges["assignment_safe_flag"].sum()), len(edges))
        self.assertEqual(int(edges["outcome_used_for_assignment_flag"].sum()), 0)

        required_packet_columns = {
            "event_title",
            "event_category",
            "source_lane",
            "evidence_quality_state",
            "cashflow_path_present",
            "customer_or_counterparty_present",
            "financing_pressure_state",
            "dilution_or_overhang_flag",
            "price_absorption_state",
            "slot_rank_state",
            "cohort_strength_state",
            "invalidation_trigger",
            "missing_evidence",
            "reviewer_decision",
            "reviewer_note",
            "leakage_guardrail_pass",
        }
        self.assertTrue(required_packet_columns.issubset(set(queue.columns)))
        self.assertEqual(len(queue), len(panel))
        self.assertTrue(queue["manual_packet_questions"].astype(str).str.len().gt(0).all())
        self.assertEqual(int(queue["leakage_guardrail_pass"].min()), 1)
        expected_samples = int(panel.groupby("next_decomposition_state").size().clip(upper=10).sum())
        self.assertEqual(len(samples), expected_samples)
        self.assertEqual(len(protocol), 5)

    def test_guardrails(self) -> None:
        eval_guardrail = pd.read_csv(TASK721 / "task721_eval_guardrail.csv")
        leakage = pd.read_csv(TASK721 / "task721_leakage_guardrail.csv")
        governance = pd.read_csv(TASK721 / "task721_governance_audit.csv")
        pass_fail = pd.read_csv(TASK721 / "task_721_pass_fail_matrix.csv")
        decision = pd.read_csv(TASK721 / "task_721_decision.csv").iloc[0]

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
