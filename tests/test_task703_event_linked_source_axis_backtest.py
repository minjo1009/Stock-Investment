from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK703_DIR = Path("docs/reports/task_703_event_linked_source_axis_backtest")


class Task703EventLinkedSourceAxisBacktestTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "gpt_review_packet.md",
            "gpt_review_raw.md",
            "task703_axis_freeze_panel.csv",
            "task703_axis_eval_panel.csv",
            "task703_action_summary.csv",
            "task703_split_summary.csv",
            "task703_portfolio_comparison.csv",
            "task703_gpt_review_status.csv",
            "task703_integrity_audit.csv",
            "task_703_pass_fail_matrix.csv",
            "task_703_decision.csv",
            "task_703_event_linked_source_axis_backtest.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK703_DIR / name).exists(), name)

    def test_scope_and_parser_axes(self) -> None:
        freeze = pd.read_csv(TASK703_DIR / "task703_axis_freeze_panel.csv")

        self.assertEqual(len(freeze), 5265)
        self.assertEqual(int(freeze["source_event_available_flag"].sum()), 2445)
        self.assertEqual(int(freeze["price_context_available_flag"].sum()), 5265)
        self.assertEqual(int(freeze["full_event_axis_eligible_flag"].sum()), 585)
        for col in [
            "financing_overhang_flag",
            "guidance_quality_axis",
            "information_novelty_axis",
            "high_noise_thin_signal_flag",
            "price_absorption_confirmation_flag",
        ]:
            self.assertIn(col, freeze.columns)

    def test_no_selection_leakage(self) -> None:
        freeze = pd.read_csv(TASK703_DIR / "task703_axis_freeze_panel.csv")
        eval_panel = pd.read_csv(TASK703_DIR / "task703_axis_eval_panel.csv")

        self.assertEqual(int(freeze["outcome_used_for_selection_flag"].sum()), 0)
        self.assertEqual(int(freeze["future_price_used_for_selection_flag"].sum()), 0)
        self.assertEqual(len(eval_panel), 5265)
        self.assertEqual(int(eval_panel["outcome_used_for_evaluation_flag"].sum()), 5265)

    def test_gpt_review_is_design_review_only(self) -> None:
        status = pd.read_csv(TASK703_DIR / "task703_gpt_review_status.csv").iloc[0]

        self.assertEqual(int(status["gpt_review_required_flag"]), 1)
        self.assertEqual(int(status["gpt_review_complete_flag"]), 1)
        self.assertEqual(int(status["gpt_used_as_source_flag"]), 0)

    def test_portfolio_comparison_and_decision(self) -> None:
        portfolio = pd.read_csv(TASK703_DIR / "task703_portfolio_comparison.csv")
        decision = pd.read_csv(TASK703_DIR / "task_703_decision.csv").iloc[0]

        self.assertEqual(
            set(portfolio["portfolio_cohort"]),
            {
                "all_5265_baseline_costed",
                "event_linked_2445_costed",
                "full_event_axis_eligible",
                "QQQ_buy_and_hold_same_horizon",
            },
        )
        self.assertEqual(set(portfolio[portfolio["portfolio_cohort"].ne("QQQ_buy_and_hold_same_horizon")]["max_positions"]), {5, 10, 20})
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(decision["gpt_review_complete_flag"]), 1)

    def test_integrity_audit_passes(self) -> None:
        audit = pd.read_csv(TASK703_DIR / "task703_integrity_audit.csv")
        self.assertEqual(int(audit["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
