from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK694_DIR = Path("docs/reports/task_694_candidate_packet_manual_review")
FORBIDDEN_COLUMNS = {
    "net_return_from_entry",
    "net_return_pct",
    "return_pct",
    "win_flag",
    "win_eval_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "simulated_exit_price",
    "simulated_exit_ts",
}


class Task694CandidatePacketManualReviewTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task694_packet_review_rulebook.csv",
            "task694_candidate_packet_review.csv",
            "task694_packet_review_summary.csv",
            "task694_integrity_audit.csv",
            "task_694_decision.csv",
            "task_694_pass_fail_matrix.csv",
            "task_694_candidate_packet_manual_review.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK694_DIR / name).exists(), name)

    def test_candidate_packet_counts(self) -> None:
        packets = pd.read_csv(TASK694_DIR / "task694_candidate_packet_review.csv")
        decision = pd.read_csv(TASK694_DIR / "task_694_decision.csv").iloc[0]

        self.assertEqual(len(packets), 11)
        self.assertEqual(int(decision["candidate_packet_count"]), 11)
        self.assertEqual(int(decision["source_packet_candidate_count"]), 9)
        self.assertEqual(int(decision["price_packet_candidate_count"]), 2)

    def test_review_states_are_present(self) -> None:
        packets = pd.read_csv(TASK694_DIR / "task694_candidate_packet_review.csv")

        self.assertGreaterEqual(packets["packet_review_state"].nunique(), 2)
        self.assertTrue(
            packets["packet_review_verdict"].isin(
                [
                    "manual_review_pass_not_allocation_approved",
                    "manual_review_conditional",
                    "manual_review_reject",
                ]
            ).all()
        )

    def test_no_outcome_columns_in_packet_outputs(self) -> None:
        packets = pd.read_csv(TASK694_DIR / "task694_candidate_packet_review.csv", nrows=1)
        self.assertFalse(FORBIDDEN_COLUMNS.intersection(packets.columns))

    def test_decision_status_and_integrity_gates(self) -> None:
        audit = pd.read_csv(TASK694_DIR / "task694_integrity_audit.csv")
        decision = pd.read_csv(TASK694_DIR / "task_694_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
