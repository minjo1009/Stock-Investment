from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK702_DIR = Path("docs/reports/task_702_full_source_packet_axis_rule")


class Task702FullSourcePacketAxisRuleTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task702_axis_freeze_panel.csv",
            "task702_axis_eval_panel.csv",
            "task702_action_summary.csv",
            "task702_portfolio_comparison.csv",
            "task702_integrity_audit.csv",
            "task_702_pass_fail_matrix.csv",
            "task_702_decision.csv",
            "task_702_full_source_packet_axis_rule.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK702_DIR / name).exists(), name)

    def test_scope_and_axes(self) -> None:
        freeze = pd.read_csv(TASK702_DIR / "task702_axis_freeze_panel.csv")

        self.assertEqual(len(freeze), 435)
        self.assertEqual(int(freeze["source_event_available_flag"].sum()), 19)
        self.assertEqual(int(freeze["full_source_axis_eligible_flag"].sum()), 5)
        for col in [
            "financing_overhang_flag",
            "guidance_quality_axis",
            "information_novelty_axis",
            "high_noise_thin_signal_flag",
            "price_absorption_confirmation_flag",
        ]:
            self.assertIn(col, freeze.columns)

    def test_eligible_symbols_and_asts_snow_blocked(self) -> None:
        freeze = pd.read_csv(TASK702_DIR / "task702_axis_freeze_panel.csv")

        eligible_symbols = list(freeze[freeze["full_source_axis_eligible_flag"].eq(1)]["symbol"])
        self.assertEqual(eligible_symbols, ["CEG", "CEG", "TER", "PH", "DDOG"])
        self.assertEqual(int(freeze[freeze["symbol"].isin(["ASTS", "SNOW"])]["full_source_axis_eligible_flag"].sum()), 0)

    def test_eval_and_action_summary(self) -> None:
        eval_panel = pd.read_csv(TASK702_DIR / "task702_axis_eval_panel.csv")
        summary = pd.read_csv(TASK702_DIR / "task702_action_summary.csv")

        self.assertEqual(len(eval_panel), 435)
        self.assertEqual(int(eval_panel["outcome_used_for_evaluation_flag"].sum()), 435)
        self.assertIn("ELIGIBLE_RULE_CANDIDATE", set(summary["full_source_axis_action"]))
        eligible = summary[summary["full_source_axis_action"].eq("ELIGIBLE_RULE_CANDIDATE")].iloc[0]
        self.assertEqual(int(eligible["candidate_count"]), 5)
        self.assertGreater(float(eligible["avg_costed_return_pct"]), 0.0)

    def test_portfolio_and_no_promotion(self) -> None:
        portfolio = pd.read_csv(TASK702_DIR / "task702_portfolio_comparison.csv")
        decision = pd.read_csv(TASK702_DIR / "task_702_decision.csv").iloc[0]

        self.assertEqual(set(portfolio["portfolio_cohort"]), {"source_packet_available_19", "full_axis_eligible_5"})
        self.assertEqual(set(portfolio["max_positions"]), {1, 3, 5, 10})
        self.assertGreater(float(decision["eligible_max5_final_capital_usd"]), 1000.0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_integrity_audit_passes(self) -> None:
        audit = pd.read_csv(TASK702_DIR / "task702_integrity_audit.csv")
        self.assertEqual(int(audit["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
