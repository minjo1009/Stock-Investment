from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK695_DIR = Path("docs/reports/task_695_tiny_eligibility_rule_audit")
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


class Task695TinyEligibilityRuleAuditTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task695_tiny_eligibility_rulebook.csv",
            "task695_tiny_eligibility_draft.csv",
            "task695_rule_audit.csv",
            "task_695_decision.csv",
            "task_695_pass_fail_matrix.csv",
            "task_695_tiny_eligibility_rule_audit.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK695_DIR / name).exists(), name)

    def test_eligibility_counts(self) -> None:
        draft = pd.read_csv(TASK695_DIR / "task695_tiny_eligibility_draft.csv")
        decision = pd.read_csv(TASK695_DIR / "task_695_decision.csv").iloc[0]

        self.assertEqual(len(draft), 11)
        self.assertEqual(int(draft["tiny_backtest_candidate_flag"].sum()), 3)
        self.assertEqual(int(draft["extra_confirmation_required_flag"].sum()), 8)
        self.assertEqual(int(draft["excluded_flag"].sum()), 0)
        self.assertEqual(int(decision["eligible_review_candidate_count"]), 3)
        self.assertEqual(int(decision["needs_extra_confirmation_count"]), 8)

    def test_no_allocation_or_trade_approval(self) -> None:
        draft = pd.read_csv(TASK695_DIR / "task695_tiny_eligibility_draft.csv")

        self.assertEqual(int(draft["allocation_approved_flag"].sum()), 0)
        self.assertEqual(int(draft["paper_or_live_trade_approved_flag"].sum()), 0)

    def test_no_outcome_columns_in_eligibility_outputs(self) -> None:
        draft = pd.read_csv(TASK695_DIR / "task695_tiny_eligibility_draft.csv", nrows=1)
        self.assertFalse(FORBIDDEN_COLUMNS.intersection(draft.columns))

    def test_decision_status_and_integrity_gates(self) -> None:
        audit = pd.read_csv(TASK695_DIR / "task695_rule_audit.csv")
        decision = pd.read_csv(TASK695_DIR / "task_695_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
