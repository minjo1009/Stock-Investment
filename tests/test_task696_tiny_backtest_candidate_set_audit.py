from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK696_DIR = Path("docs/reports/task_696_tiny_backtest_candidate_set_audit")
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
    "holding_days",
    "exit_reason",
}


class Task696TinyBacktestCandidateSetAuditTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task696_tiny_backtest_candidate_set.csv",
            "task696_candidate_set_audit.csv",
            "task_696_decision.csv",
            "task_696_pass_fail_matrix.csv",
            "task_696_tiny_backtest_candidate_set_audit.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK696_DIR / name).exists(), name)

    def test_candidate_set_contains_only_expected_symbols(self) -> None:
        candidate_set = pd.read_csv(TASK696_DIR / "task696_tiny_backtest_candidate_set.csv")
        decision = pd.read_csv(TASK696_DIR / "task_696_decision.csv").iloc[0]

        self.assertEqual(len(candidate_set), 3)
        self.assertEqual(set(candidate_set["symbol"]), {"ASTS", "BA", "TER"})
        self.assertEqual(int(decision["candidate_set_count"]), 3)
        self.assertEqual(decision["candidate_symbols"], "ASTS|BA|TER")

    def test_no_conditional_or_trade_approval(self) -> None:
        candidate_set = pd.read_csv(TASK696_DIR / "task696_tiny_backtest_candidate_set.csv")

        self.assertTrue(candidate_set["eligibility_state"].eq("eligible_review_candidate").all())
        self.assertEqual(int(candidate_set["allocation_approved_flag"].sum()), 0)
        self.assertEqual(int(candidate_set["paper_or_live_trade_approved_flag"].sum()), 0)
        self.assertEqual(int(candidate_set["pnl_not_run_flag"].sum()), 3)

    def test_no_outcome_columns_in_candidate_set(self) -> None:
        candidate_set = pd.read_csv(TASK696_DIR / "task696_tiny_backtest_candidate_set.csv", nrows=1)
        self.assertFalse(FORBIDDEN_COLUMNS.intersection(candidate_set.columns))

    def test_decision_status_and_integrity_gates(self) -> None:
        audit = pd.read_csv(TASK696_DIR / "task696_candidate_set_audit.csv")
        decision = pd.read_csv(TASK696_DIR / "task_696_decision.csv").iloc[0]

        self.assertEqual(int(audit["pass_flag"].min()), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(decision["pnl_run_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
