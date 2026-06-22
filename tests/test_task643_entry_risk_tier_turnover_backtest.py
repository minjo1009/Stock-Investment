from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


REPORT_DIR = Path("docs/reports/task_643_entry_risk_tier_turnover_backtest")


class Task643EntryRiskTierTurnoverBacktestTest(unittest.TestCase):
    def test_task643_backtest_runs_and_keeps_task639_as_best_full_gate(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_643_decision.csv").iloc[0]

        self.assertEqual(decision["decision"], "FAIL_NO_FULL_GATE_ENTRY_RISK_TIER_TURNOVER_CANDIDATE")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(decision["best_entry_policy"], "base_delay1d_open")
        self.assertEqual(decision["best_exit_policy"], "existing_exit")
        self.assertEqual(decision["best_sizing_policy"], "equal_max5")
        self.assertAlmostEqual(float(decision["best_final_capital_usd"]), float(decision["task639_final_capital_usd"]), places=2)

    def test_entry_quality_and_risk_features_are_available(self) -> None:
        audit = pd.read_csv(REPORT_DIR / "task_643_source_audit.csv").iloc[0]
        pass_fail = pd.read_csv(REPORT_DIR / "task_643_pass_fail_matrix.csv")
        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}

        self.assertGreater(int(audit["entry_policy_variant_rows"]), int(audit["task639_source_trade_count"]))
        self.assertGreaterEqual(float(audit["atr20_available_rate"]), 0.95)
        self.assertEqual(gates["source_features_available"], 1)
        self.assertEqual(gates["no_blacklist_or_label_shortcut"], 1)

    def test_no_candidate_improves_return_and_drawdown_together(self) -> None:
        grid = pd.read_csv(REPORT_DIR / "task_643_account_grid.csv")
        decision = pd.read_csv(REPORT_DIR / "task_643_decision.csv").iloc[0]
        base_final = float(decision["task639_final_capital_usd"])
        base_dd = float(decision["task639_max_drawdown_pct"])

        both = grid[(grid["final_capital_usd"] > base_final) & (grid["max_drawdown_pct"] > base_dd)]
        self.assertTrue(both.empty)
        self.assertGreater(int((grid["max_drawdown_pct"] > base_dd).sum()), 0)

    def test_same_config_oos_baseline_still_beats_qqq(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_643_decision.csv").iloc[0]

        self.assertGreater(float(decision["best_validation_final_capital_usd"]), float(decision["best_validation_qqq_final_capital_usd"]))
        self.assertGreater(float(decision["best_recent_final_capital_usd"]), float(decision["best_recent_qqq_final_capital_usd"]))
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_gpt_review_was_captured(self) -> None:
        response = REPORT_DIR / "task_643_gpt_review_response.md"

        self.assertTrue(response.exists())
        text = response.read_text(encoding="utf-8")
        self.assertIn("conditional wrapper", text)
        self.assertIn("signal tier", text)


if __name__ == "__main__":
    unittest.main()
