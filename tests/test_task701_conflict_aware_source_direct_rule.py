from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK701_DIR = Path("docs/reports/task_701_conflict_aware_source_direct_rule")


class Task701ConflictAwareSourceDirectRuleTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task701_rule_freeze_panel.csv",
            "task701_rule_eval_panel.csv",
            "task701_action_summary.csv",
            "task701_portfolio_comparison.csv",
            "task701_integrity_audit.csv",
            "task_701_pass_fail_matrix.csv",
            "task_701_decision.csv",
            "task_701_conflict_aware_source_direct_rule.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK701_DIR / name).exists(), name)

    def test_scope_and_eligibility(self) -> None:
        freeze = pd.read_csv(TASK701_DIR / "task701_rule_freeze_panel.csv")

        self.assertEqual(len(freeze), 435)
        self.assertEqual(int(freeze["packet_bucket"].eq("source_direct_supported").sum()), 9)
        self.assertEqual(int(freeze["conflict_aware_eligible_flag"].sum()), 4)
        eligible_symbols = list(freeze[freeze["conflict_aware_eligible_flag"].eq(1)]["symbol"])
        self.assertEqual(eligible_symbols, ["CEG", "CEG", "TER", "DDOG"])

    def test_asts_snow_are_blocked(self) -> None:
        freeze = pd.read_csv(TASK701_DIR / "task701_rule_freeze_panel.csv")
        blocked = freeze[freeze["symbol"].isin(["ASTS", "SNOW"])]

        self.assertEqual(int(blocked["conflict_aware_eligible_flag"].sum()), 0)
        self.assertIn("CONFIRMATION_REQUIRED_FINANCING", set(blocked["conflict_aware_action"]))
        self.assertIn("CONFIRMATION_REQUIRED_REAFFIRM", set(blocked["conflict_aware_action"]))

    def test_eval_and_action_summary(self) -> None:
        eval_panel = pd.read_csv(TASK701_DIR / "task701_rule_eval_panel.csv")
        summary = pd.read_csv(TASK701_DIR / "task701_action_summary.csv")

        self.assertEqual(len(eval_panel), 435)
        self.assertEqual(int(eval_panel["outcome_used_for_evaluation_flag"].sum()), 435)
        self.assertIn("ELIGIBLE_RULE_CANDIDATE", set(summary["conflict_aware_action"]))
        eligible = summary[summary["conflict_aware_action"].eq("ELIGIBLE_RULE_CANDIDATE")].iloc[0]
        self.assertEqual(int(eligible["candidate_count"]), 4)
        self.assertGreater(float(eligible["avg_costed_return_pct"]), 0.0)

    def test_portfolio_and_no_promotion(self) -> None:
        portfolio = pd.read_csv(TASK701_DIR / "task701_portfolio_comparison.csv")
        decision = pd.read_csv(TASK701_DIR / "task_701_decision.csv").iloc[0]

        self.assertEqual(set(portfolio["portfolio_cohort"]), {"source_direct_original_9", "conflict_aware_eligible_4"})
        self.assertEqual(set(portfolio["max_positions"]), {1, 3, 5, 10})
        self.assertGreater(float(decision["eligible_max5_final_capital_usd"]), 1000.0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_integrity_audit_passes(self) -> None:
        audit = pd.read_csv(TASK701_DIR / "task701_integrity_audit.csv")
        self.assertEqual(int(audit["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
