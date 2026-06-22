from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK723 = Path("docs/reports/task_723_five_stage_decision_contract")


class Task723FiveStageDecisionContractTest(unittest.TestCase):
    def test_artifacts_and_object_counts(self) -> None:
        required = [
            "task723_stage_contract.csv",
            "task723_evidence_objects.csv",
            "task723_economic_interpretation_objects.csv",
            "task723_relation_edge_objects.csv",
            "task723_candidate_context_bundles.csv",
            "task723_slot_judgment_objects.csv",
            "task723_manual_review_queue.csv",
            "task723_leakage_guardrail.csv",
            "task723_governance_audit.csv",
            "task_723_decision.csv",
            "task_723_pass_fail_matrix.csv",
            "task_723_five_stage_decision_contract.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASK723 / name).exists(), name)

        evidence = pd.read_csv(TASK723 / "task723_evidence_objects.csv")
        interpretations = pd.read_csv(TASK723 / "task723_economic_interpretation_objects.csv")
        edges = pd.read_csv(TASK723 / "task723_relation_edge_objects.csv")
        bundles = pd.read_csv(TASK723 / "task723_candidate_context_bundles.csv")
        slots = pd.read_csv(TASK723 / "task723_slot_judgment_objects.csv")
        queue = pd.read_csv(TASK723 / "task723_manual_review_queue.csv")

        self.assertEqual(len(evidence), 345)
        self.assertEqual(len(interpretations), 345)
        self.assertEqual(len(edges), 1380)
        self.assertEqual(len(bundles), 345)
        self.assertEqual(len(slots), 345)
        self.assertEqual(len(queue), 345)
        self.assertEqual(set(queue["queue_priority"]), {2, 3})

    def test_id_linkage_and_slot_scope(self) -> None:
        evidence = pd.read_csv(TASK723 / "task723_evidence_objects.csv")
        interpretations = pd.read_csv(TASK723 / "task723_economic_interpretation_objects.csv")
        edges = pd.read_csv(TASK723 / "task723_relation_edge_objects.csv")
        bundles = pd.read_csv(TASK723 / "task723_candidate_context_bundles.csv")
        slots = pd.read_csv(TASK723 / "task723_slot_judgment_objects.csv")

        self.assertTrue(set(interpretations["evidence_id"]).issubset(set(evidence["evidence_id"])))
        self.assertTrue(set(bundles["evidence_object_ids"]).issubset(set(evidence["evidence_id"])))
        self.assertTrue(set(bundles["interpretation_object_ids"]).issubset(set(interpretations["interpretation_id"])))
        self.assertTrue(set(slots["bundle_id"]).issubset(set(bundles["bundle_id"])))
        self.assertTrue(set(edges["from_object_id"]).issubset(set(evidence["evidence_id"]) | set(interpretations["interpretation_id"])))
        self.assertEqual(int(slots["cohort_only_flag"].min()), 1)
        self.assertTrue(slots["slot_explanation"].astype(str).str.contains("cohort_only_same_timestamp").all())

    def test_stage_contract_and_review_queues(self) -> None:
        contract = pd.read_csv(TASK723 / "task723_stage_contract.csv")
        bundles = pd.read_csv(TASK723 / "task723_candidate_context_bundles.csv")
        queue = pd.read_csv(TASK723 / "task723_manual_review_queue.csv")

        self.assertEqual(
            set(contract["stage_name"]),
            {
                "evidence_object",
                "economic_interpretation_object",
                "relation_edge_object",
                "candidate_context_bundle",
                "slot_judgment_object",
            },
        )
        self.assertTrue(bundles["weakest_layer"].astype(str).str.len().gt(0).all())
        self.assertEqual(int((queue["review_queue"] == "queue_1_cashflow_packet_review").sum()), 0)
        self.assertEqual(int((queue["review_queue"] == "queue_2_semantic_enrichment_review").sum()), 25)
        self.assertEqual(int((queue["review_queue"] == "queue_3_noise_taxonomy_qa").sum()), 320)

    def test_no_action_and_leakage_guardrails(self) -> None:
        frames = [
            pd.read_csv(TASK723 / "task723_evidence_objects.csv"),
            pd.read_csv(TASK723 / "task723_economic_interpretation_objects.csv"),
            pd.read_csv(TASK723 / "task723_relation_edge_objects.csv"),
            pd.read_csv(TASK723 / "task723_candidate_context_bundles.csv"),
            pd.read_csv(TASK723 / "task723_slot_judgment_objects.csv"),
            pd.read_csv(TASK723 / "task723_manual_review_queue.csv"),
        ]
        forbidden_tokens = [
            "future_return",
            "net_return",
            "realized_outcome",
            "top50",
            "winner",
            "loser",
            "future_price",
            "post_event",
            "backtest_target",
            "selection_result",
            "costed_return",
        ]
        for frame in frames:
            cols = [col.lower() for col in frame.columns]
            self.assertFalse(any(token in col for token in forbidden_tokens for col in cols))
            if "assignment_used_flag" in frame.columns:
                self.assertEqual(int(frame["assignment_used_flag"].sum()), 0)
            if "outcome_used_for_assignment_flag" in frame.columns:
                self.assertEqual(int(frame["outcome_used_for_assignment_flag"].sum()), 0)

        leakage = pd.read_csv(TASK723 / "task723_leakage_guardrail.csv")
        governance = pd.read_csv(TASK723 / "task723_governance_audit.csv")
        pass_fail = pd.read_csv(TASK723 / "task_723_pass_fail_matrix.csv")
        decision = pd.read_csv(TASK723 / "task_723_decision.csv").iloc[0]
        self.assertEqual(int(leakage["pass_flag"].min()), 1)
        self.assertEqual(int(governance["pass_flag"].min()), 1)
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
