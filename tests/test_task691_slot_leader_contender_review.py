from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK691_DIR = Path("docs/reports/task_691_slot_leader_contender_review")
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


class Task691SlotLeaderContenderReviewTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task691_confirmation_rulebook.csv",
            "task691_slot_leader_review.csv",
            "task691_contender_confirmation_map.csv",
            "task691_cohort_review_summary.csv",
            "task691_integrity_audit.csv",
            "task_691_decision.csv",
            "task_691_pass_fail_matrix.csv",
            "task_691_slot_leader_contender_review.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK691_DIR / name).exists(), name)

    def test_leader_and_contender_counts_are_expected(self) -> None:
        leaders = pd.read_csv(TASK691_DIR / "task691_slot_leader_review.csv")
        contenders = pd.read_csv(TASK691_DIR / "task691_contender_confirmation_map.csv")
        decision = pd.read_csv(TASK691_DIR / "task_691_decision.csv").iloc[0]

        self.assertEqual(len(leaders), 28)
        self.assertEqual(len(contenders), 407)
        self.assertEqual(int(decision["slot_leader_count"]), 28)
        self.assertEqual(int(decision["slot_contender_count"]), 407)

    def test_reviews_are_decomposed(self) -> None:
        leaders = pd.read_csv(TASK691_DIR / "task691_slot_leader_review.csv")
        contenders = pd.read_csv(TASK691_DIR / "task691_contender_confirmation_map.csv")
        cohorts = pd.read_csv(TASK691_DIR / "task691_cohort_review_summary.csv")

        self.assertGreaterEqual(leaders["leader_review_status"].nunique(), 3)
        self.assertGreaterEqual(contenders["required_confirmation_type"].nunique(), 2)
        self.assertGreaterEqual(cohorts["cohort_review_state"].nunique(), 3)

    def test_no_outcome_columns_in_review_outputs(self) -> None:
        for name in [
            "task691_slot_leader_review.csv",
            "task691_contender_confirmation_map.csv",
            "task691_cohort_review_summary.csv",
        ]:
            frame = pd.read_csv(TASK691_DIR / name, nrows=1)
            self.assertFalse(FORBIDDEN_COLUMNS.intersection(frame.columns), name)

    def test_decision_status_and_integrity_gates(self) -> None:
        audit = pd.read_csv(TASK691_DIR / "task691_integrity_audit.csv")
        decision = pd.read_csv(TASK691_DIR / "task_691_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
