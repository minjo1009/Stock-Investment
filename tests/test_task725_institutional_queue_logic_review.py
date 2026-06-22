from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK725 = Path("docs/reports/task_725_institutional_queue_logic_review")


class Task725InstitutionalQueueLogicReviewTest(unittest.TestCase):
    def test_artifacts_and_scope(self) -> None:
        required = [
            "task725_manual_logic_review_packet.csv",
            "task725_queue1_deep_review.csv",
            "task725_queue2_semantic_gap_review.csv",
            "task725_queue3_noise_qa.csv",
            "task725_exception_deep_review.csv",
            "task725_review_decision_summary.csv",
            "task725_review_decision_summary.json",
            "task725_logic_error_audit.csv",
            "task725_logic_error_audit.json",
            "task725_leakage_guardrail.csv",
            "task725_leakage_audit.json",
            "task725_governance_audit.csv",
            "task_725_decision.csv",
            "task_725_pass_fail_matrix.csv",
            "task_725_institutional_queue_logic_review.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASK725 / name).exists(), name)

        packet = pd.read_csv(TASK725 / "task725_manual_logic_review_packet.csv")
        self.assertEqual(len(packet), 345)
        self.assertTrue(packet["review_depth"].astype(str).str.len().gt(0).all())
        self.assertTrue(packet["review_decision_state"].astype(str).str.len().gt(0).all())
        self.assertTrue(packet["evidence_span_used"].astype(str).str.len().gt(0).all())
        self.assertTrue(packet["review_reason"].astype(str).str.len().gt(0).all())
        self.assertTrue(packet["logic_error_risk"].astype(str).str.len().gt(0).all())

    def test_queue_review_depths_and_decisions(self) -> None:
        queue1 = pd.read_csv(TASK725 / "task725_queue1_deep_review.csv")
        queue2 = pd.read_csv(TASK725 / "task725_queue2_semantic_gap_review.csv")
        queue3 = pd.read_csv(TASK725 / "task725_queue3_noise_qa.csv")
        exceptions = pd.read_csv(TASK725 / "task725_exception_deep_review.csv")

        self.assertEqual(len(queue1), 0)

        self.assertEqual(len(queue2), 25)
        self.assertEqual(set(queue2["review_depth"]), {"full_text_semantic_gap_review"})
        self.assertIn("ownership_filing_empty_confirmed", set(queue2["review_decision_state"]))
        self.assertIn("parser_miss_policy_transmission_confirmed", set(queue2["review_decision_state"]))

        self.assertEqual(len(queue3), 320)
        self.assertEqual(len(exceptions), 3)
        self.assertEqual(set(exceptions["review_depth"]), {"deep_exception_review"})
        self.assertEqual(int(exceptions["second_reviewer_required_flag"].sum()), 3)

    def test_logic_error_audit_and_guardrails(self) -> None:
        packet = pd.read_csv(TASK725 / "task725_manual_logic_review_packet.csv")
        logic = pd.read_csv(TASK725 / "task725_logic_error_audit.csv")
        leakage = pd.read_csv(TASK725 / "task725_leakage_guardrail.csv")
        governance = pd.read_csv(TASK725 / "task725_governance_audit.csv")
        pass_fail = pd.read_csv(TASK725 / "task_725_pass_fail_matrix.csv")
        decision = pd.read_csv(TASK725 / "task_725_decision.csv").iloc[0]

        self.assertEqual(len(logic), 2)
        self.assertEqual(set(logic["backtest_permission"]), {"FAIL"})
        self.assertEqual(int(packet["assignment_used_flag"].sum()), 0)
        self.assertEqual(int(packet["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(packet["buy_sell_or_sizing_instruction_flag"].sum()), 0)
        self.assertEqual(set(packet["strategy_acceptance_status"]), {"NOT_ACCEPTED"})
        self.assertEqual(set(packet["real_capital_status"]), {"FORBIDDEN"})
        self.assertEqual(int(leakage["pass_flag"].min()), 1)
        self.assertEqual(int(governance["pass_flag"].min()), 1)
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(decision["backtest_permission"], "FAIL")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
