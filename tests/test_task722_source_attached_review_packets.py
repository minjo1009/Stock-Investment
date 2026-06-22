from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK722 = Path("docs/reports/task_722_source_attached_review_packets")


class Task722SourceAttachedReviewPacketsTest(unittest.TestCase):
    def test_artifacts_and_source_join_contract(self) -> None:
        required = [
            "task722_source_attached_packet_panel.csv",
            "task722_packet_event_detail.csv",
            "task722_source_readiness_audit.csv",
            "task722_source_attached_sample_packets.csv",
            "task722_eval_guardrail.csv",
            "task722_leakage_guardrail.csv",
            "task722_governance_audit.csv",
            "task_722_decision.csv",
            "task_722_pass_fail_matrix.csv",
            "task_722_source_attached_review_packets.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASK722 / name).exists(), name)

        panel = pd.read_csv(TASK722 / "task722_source_attached_packet_panel.csv")
        self.assertEqual(len(panel), 345)
        self.assertTrue(panel["source_linked_event_count"].gt(0).all())
        self.assertTrue(panel["best_event_id_for_review"].astype(str).str.strip().ne("").all())
        self.assertTrue(panel["best_event_title_for_review"].astype(str).str.strip().ne("").all())
        self.assertTrue(panel["best_event_timestamp_for_review"].astype(str).str.strip().ne("").all())
        self.assertTrue(panel["event_priority_reason"].astype(str).str.strip().ne("").all())
        self.assertGreaterEqual(panel["source_review_readiness_state"].nunique(), 2)
        self.assertTrue(panel["source_noise_type"].astype(str).str.len().gt(0).all())
        self.assertTrue(panel["source_strength_state"].astype(str).str.len().gt(0).all())
        self.assertTrue(panel["economic_path_state"].astype(str).str.len().gt(0).all())
        self.assertTrue(panel["company_specificity_state"].astype(str).str.len().gt(0).all())
        self.assertTrue(panel["aggregate_event_count"].gt(0).all())
        self.assertTrue(panel["raw_text_path_status"].astype(str).str.len().gt(0).all())
        self.assertTrue(panel["evidence_span_status"].astype(str).str.len().gt(0).all())
        self.assertTrue(panel["review_question"].astype(str).str.len().gt(0).all())

    def test_review_readiness_and_event_detail(self) -> None:
        panel = pd.read_csv(TASK722 / "task722_source_attached_packet_panel.csv")
        detail = pd.read_csv(TASK722 / "task722_packet_event_detail.csv")
        readiness = pd.read_csv(TASK722 / "task722_source_readiness_audit.csv")
        samples = pd.read_csv(TASK722 / "task722_source_attached_sample_packets.csv")

        self.assertGreater(len(detail), len(panel))
        self.assertEqual(int(detail["assignment_used_flag"].sum()), 0)
        self.assertEqual(int(detail["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(set(panel["source_review_readiness_state"]), set(readiness["source_review_readiness_state"]))
        self.assertGreaterEqual(len(samples), panel["source_review_readiness_state"].nunique())
        self.assertEqual(int((panel["source_review_readiness_state"] == "source_review_ready_cashflow_packet").sum()), 0)
        self.assertGreater(int((panel["source_review_readiness_state"] == "source_review_noise_triage_required").sum()), 0)

    def test_guardrails(self) -> None:
        panel = pd.read_csv(TASK722 / "task722_source_attached_packet_panel.csv")
        eval_guardrail = pd.read_csv(TASK722 / "task722_eval_guardrail.csv")
        leakage = pd.read_csv(TASK722 / "task722_leakage_guardrail.csv")
        governance = pd.read_csv(TASK722 / "task722_governance_audit.csv")
        pass_fail = pd.read_csv(TASK722 / "task_722_pass_fail_matrix.csv")
        decision = pd.read_csv(TASK722 / "task_722_decision.csv").iloc[0]

        self.assertEqual(int(panel["translator_output_is_action_flag"].sum()), 0)
        self.assertEqual(int(panel["assignment_used_flag"].sum()), 0)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["top50_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["buy_sell_or_sizing_instruction_flag"].sum()), 0)
        self.assertEqual(set(panel["real_capital_status"]), {"FORBIDDEN"})

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
