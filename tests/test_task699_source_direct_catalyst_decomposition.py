from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK699_DIR = Path("docs/reports/task_699_source_direct_catalyst_decomposition")
FORBIDDEN_FREEZE_COLUMNS = {
    "entry_price",
    "simulated_exit_ts",
    "simulated_exit_price",
    "exit_reason",
    "net_return_from_entry",
    "costed_return_pct",
    "qqq_costed_return_pct",
    "holding_days",
    "win_flag",
}


class Task699SourceDirectCatalystDecompositionTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task699_source_direct_feature_freeze.csv",
            "task699_source_direct_eval_comparison.csv",
            "task699_signal_family_summary.csv",
            "task699_failure_success_contrast.csv",
            "task699_integrity_audit.csv",
            "task_699_pass_fail_matrix.csv",
            "task_699_decision.csv",
            "task_699_source_direct_catalyst_decomposition.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK699_DIR / name).exists(), name)

    def test_source_direct_scope_and_freeze_integrity(self) -> None:
        freeze = pd.read_csv(TASK699_DIR / "task699_source_direct_feature_freeze.csv")

        self.assertEqual(len(freeze), 9)
        self.assertEqual(set(freeze["symbol"]), {"ASTS", "BA", "CEG", "DDOG", "PH", "SNOW", "TER"})
        self.assertFalse(FORBIDDEN_FREEZE_COLUMNS.intersection(freeze.columns))
        self.assertEqual(int(freeze["outcome_used_for_selection_flag"].sum()), 0)
        self.assertEqual(int(freeze["future_price_used_for_selection_flag"].sum()), 0)
        self.assertTrue(freeze["catalyst_structure_bucket"].notna().all())
        self.assertTrue(freeze["quality_risk_bucket"].notna().all())

    def test_eval_contains_failure_and_large_winner_groups(self) -> None:
        eval_panel = pd.read_csv(TASK699_DIR / "task699_source_direct_eval_comparison.csv")

        self.assertEqual(len(eval_panel), 9)
        self.assertIn("failure_loss_gt_10pct", set(eval_panel["outcome_group"]))
        self.assertIn("large_winner", set(eval_panel["outcome_group"]))
        self.assertEqual(int(eval_panel["outcome_used_for_evaluation_flag"].sum()), 9)
        self.assertEqual(int(eval_panel["outcome_used_for_selection_flag"].sum()), 0)

    def test_failure_success_contrast_is_present(self) -> None:
        contrast = pd.read_csv(TASK699_DIR / "task699_failure_success_contrast.csv")

        self.assertEqual(set(contrast["contrast_group"]), {"failures_asts_snow", "large_winners_ter_ddog", "middle_ba_ceg_ph"})
        failures = contrast[contrast["contrast_group"].eq("failures_asts_snow")].iloc[0]
        winners = contrast[contrast["contrast_group"].eq("large_winners_ter_ddog")].iloc[0]
        self.assertLess(float(failures["avg_costed_return_pct"]), 0.0)
        self.assertGreater(float(winners["avg_costed_return_pct"]), 0.0)

    def test_family_summary_and_no_promotion(self) -> None:
        summary = pd.read_csv(TASK699_DIR / "task699_signal_family_summary.csv")
        decision = pd.read_csv(TASK699_DIR / "task_699_decision.csv").iloc[0]

        self.assertIn("catalyst_structure_bucket", set(summary["dimension"]))
        self.assertIn("quality_risk_bucket", set(summary["dimension"]))
        self.assertIn("direct_economic_signature", set(summary["dimension"]))
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_integrity_audit_passes(self) -> None:
        audit = pd.read_csv(TASK699_DIR / "task699_integrity_audit.csv")
        self.assertEqual(int(audit["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
