from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_637_content_signal_account_backtest")


class Task637ContentSignalAccountBacktestTest(unittest.TestCase):
    def test_full_period_account_candidate_beats_qqq_and_existing_max5(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_637_decision.csv").iloc[0]

        self.assertEqual(decision["decision"], "PASS_CONTENT_SIGNAL_CANDIDATE_NEEDS_LIVE_RULE_LOCK")
        self.assertGreater(float(decision["best_50bp_final_capital_usd"]), 5000)
        self.assertEqual(int(decision["best_50bp_beats_qqq_flag"]), 1)
        self.assertEqual(int(decision["best_50bp_beats_task617_original_max5_flag"]), 1)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_validation_and_recent_oos_accounts_beat_same_period_qqq(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_637_decision.csv").iloc[0]

        self.assertGreater(float(decision["validation_best_50bp_final_capital_usd"]), float(decision["validation_best_50bp_qqq_final_capital_usd"]))
        self.assertGreater(float(decision["recent_best_50bp_final_capital_usd"]), float(decision["recent_best_50bp_qqq_final_capital_usd"]))

    def test_pass_fail_keeps_trading_promotion_blocked(self) -> None:
        pass_fail = pd.read_csv(REPORT_DIR / "task_637_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(gates["best_50bp_beats_qqq"], 1)
        self.assertEqual(gates["best_50bp_beats_task617_original_max5"], 1)
        self.assertEqual(gates["validation_oos_50bp_account_beats_qqq"], 1)
        self.assertEqual(gates["recent_oos_50bp_account_beats_qqq"], 1)
        self.assertEqual(gates["presence_fields_not_used"], 1)
        self.assertEqual(gates["trading_promotion"], 0)


if __name__ == "__main__":
    unittest.main()
