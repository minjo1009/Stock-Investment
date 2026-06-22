from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK724 = Path("docs/reports/task_724_queue_deep_dive_review")


class Task724QueueDeepDiveReviewTest(unittest.TestCase):
    def test_artifacts_and_scope(self) -> None:
        required = [
            "task724_queue_deep_dive_panel.csv",
            "task724_queue_summary.csv",
            "task724_subtype_summary.csv",
            "task724_queue1_cashflow_packets.csv",
            "task724_queue2_semantic_gap_packets.csv",
            "task724_queue3_noise_qa_packets.csv",
            "task724_manual_review_sample_packets.csv",
            "task724_institutional_review_protocol.csv",
            "task724_leakage_guardrail.csv",
            "task724_governance_audit.csv",
            "task_724_decision.csv",
            "task_724_pass_fail_matrix.csv",
            "task_724_queue_deep_dive_review.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASK724 / name).exists(), name)

        panel = pd.read_csv(TASK724 / "task724_queue_deep_dive_panel.csv")
        self.assertEqual(len(panel), 345)
        self.assertEqual(int((panel["review_queue"] == "queue_1_cashflow_packet_review").sum()), 0)
        self.assertEqual(int((panel["review_queue"] == "queue_2_semantic_enrichment_review").sum()), 25)
        self.assertEqual(int((panel["review_queue"] == "queue_3_noise_taxonomy_qa").sum()), 320)
        self.assertTrue(panel["manual_subtype"].astype(str).str.len().gt(0).all())
        self.assertTrue(panel["review_reason"].astype(str).str.len().gt(0).all())
        self.assertTrue(panel["minimum_evidence_needed"].astype(str).str.len().gt(0).all())

    def test_queue_decomposition_contract(self) -> None:
        panel = pd.read_csv(TASK724 / "task724_queue_deep_dive_panel.csv")
        summary = pd.read_csv(TASK724 / "task724_subtype_summary.csv")
        queue1 = pd.read_csv(TASK724 / "task724_queue1_cashflow_packets.csv")
        queue2 = pd.read_csv(TASK724 / "task724_queue2_semantic_gap_packets.csv")
        queue3 = pd.read_csv(TASK724 / "task724_queue3_noise_qa_packets.csv")
        samples = pd.read_csv(TASK724 / "task724_manual_review_sample_packets.csv")
        protocol = pd.read_csv(TASK724 / "task724_institutional_review_protocol.csv")

        self.assertEqual(len(queue1), 0)
        self.assertEqual(len(queue2), 25)
        self.assertIn("true_semantic_empty_ownership_filing", set(queue2["manual_subtype"]))
        self.assertEqual(len(queue3), 320)
        self.assertGreaterEqual(queue3["manual_subtype"].nunique(), 2)
        self.assertGreaterEqual(len(samples), len(summary))
        self.assertEqual(len(protocol), 3)
        self.assertEqual(set(panel["manual_review_decision"]), {"manual_review_pending"})

    def test_guardrails(self) -> None:
        panel = pd.read_csv(TASK724 / "task724_queue_deep_dive_panel.csv")
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
        cols = [col.lower() for col in panel.columns]
        self.assertFalse(any(token in col for token in forbidden_tokens for col in cols))
        self.assertEqual(int(panel["assignment_used_flag"].sum()), 0)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["buy_sell_or_sizing_instruction_flag"].sum()), 0)
        self.assertEqual(set(panel["strategy_acceptance_status"]), {"NOT_ACCEPTED"})
        self.assertEqual(set(panel["real_capital_status"]), {"FORBIDDEN"})

        leakage = pd.read_csv(TASK724 / "task724_leakage_guardrail.csv")
        governance = pd.read_csv(TASK724 / "task724_governance_audit.csv")
        pass_fail = pd.read_csv(TASK724 / "task_724_pass_fail_matrix.csv")
        decision = pd.read_csv(TASK724 / "task_724_decision.csv").iloc[0]
        self.assertEqual(int(leakage["pass_flag"].min()), 1)
        self.assertEqual(int(governance["pass_flag"].min()), 1)
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
