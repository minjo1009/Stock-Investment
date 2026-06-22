from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK708_DIR = Path("docs/reports/task_708_full_period_backtest_comparison")


class Task708FullPeriodBacktestComparisonTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task708_eval_panel.csv",
            "task708_portfolio_comparison.csv",
            "task708_cost_stress_summary.csv",
            "task708_split_summary.csv",
            "task708_accepted_trades.csv",
            "task708_equity_curves.csv",
            "task_708_decision.csv",
            "task_708_pass_fail_matrix.csv",
            "task_708_full_period_backtest_comparison.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK708_DIR / name).exists(), name)

    def test_eval_scope_and_no_assignment_leakage(self) -> None:
        panel = pd.read_csv(TASK708_DIR / "task708_eval_panel.csv")

        self.assertEqual(len(panel), 5265)
        self.assertEqual(int(panel["source_event_available_flag"].sum()), 2445)
        self.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)
        self.assertEqual(int(panel["outcome_used_for_evaluation_flag"].sum()), 5265)

    def test_portfolio_comparison(self) -> None:
        portfolio = pd.read_csv(TASK708_DIR / "task708_portfolio_comparison.csv")
        decision = pd.read_csv(TASK708_DIR / "task_708_decision.csv").iloc[0]

        self.assertEqual(set(portfolio["portfolio_cohort"]), {
            "all_5265_baseline_costed",
            "event_linked_2445_costed",
            "task703_eligible_585",
            "task707_priority_only",
            "task707_priority_plus_normal",
            "task707_priority_normal_low_alive",
            "QQQ_buy_and_hold_same_horizon",
        })
        self.assertEqual(set(portfolio[portfolio["portfolio_cohort"].ne("QQQ_buy_and_hold_same_horizon")]["max_positions"]), {5, 10, 20})
        self.assertEqual(float(portfolio["initial_capital_usd"].max()), 1000.0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_pass_fail_matrix_passes(self) -> None:
        pass_fail = pd.read_csv(TASK708_DIR / "task_708_pass_fail_matrix.csv")
        self.assertEqual(int(pass_fail["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
