from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_639_oos_first_rule_lock_refinement")


class Task639OosFirstRuleLockRefinementTest(unittest.TestCase):
    def test_best_same_rule_candidate_improves_return_and_drawdown(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_639_decision.csv").iloc[0]

        self.assertEqual(decision["decision"], "PASS_SAME_RULE_RETURN_UP_DRAWDOWN_DOWN_CANDIDATE_NOT_ACCEPTED")
        self.assertEqual(decision["best_rule_name"], "positive_contract_or_supply")
        self.assertEqual(decision["best_timing_mode"], "delay1d")
        self.assertEqual(decision["best_exit_mode"], "existing_exit")
        self.assertEqual(decision["best_sizing_mode"], "equal_max5")
        self.assertGreater(float(decision["best_50bp_final_capital_usd"]), float(decision["task638_high_return_final_capital_usd"]))
        self.assertGreater(float(decision["best_50bp_max_drawdown_pct"]), float(decision["task638_high_return_max_drawdown_pct"]))
        self.assertGreater(float(decision["best_50bp_max_drawdown_pct"]), float(decision["task638_risk_controlled_max_drawdown_pct"]))

    def test_same_rule_beats_validation_and_recent_qqq(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_639_decision.csv").iloc[0]

        self.assertGreater(float(decision["best_validation_final_capital_usd"]), float(decision["best_validation_qqq_final_capital_usd"]))
        self.assertGreater(float(decision["best_recent_final_capital_usd"]), float(decision["best_recent_qqq_final_capital_usd"]))

    def test_promotion_remains_blocked(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_639_decision.csv").iloc[0]
        pass_fail = pd.read_csv(REPORT_DIR / "task_639_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(gates["gpt_review_captured"], 1)
        self.assertEqual(gates["same_rule_validation_beats_qqq"], 1)
        self.assertEqual(gates["same_rule_recent_beats_qqq"], 1)
        self.assertEqual(gates["trading_promotion"], 0)


if __name__ == "__main__":
    unittest.main()
