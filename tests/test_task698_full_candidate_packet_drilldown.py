from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK698_DIR = Path("docs/reports/task_698_full_candidate_packet_drilldown")
FORBIDDEN_FREEZE_COLUMNS = {
    "entry_price",
    "simulated_exit_ts",
    "simulated_exit_price",
    "exit_reason",
    "net_return_from_entry",
    "return_pct",
    "holding_days",
}


class Task698FullCandidatePacketDrilldownTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task698_full_candidate_freeze_panel.csv",
            "task698_full_candidate_eval_panel.csv",
            "task698_bucket_return_summary.csv",
            "task698_portfolio_comparison.csv",
            "task698_integrity_audit.csv",
            "task_698_pass_fail_matrix.csv",
            "task_698_decision.csv",
            "task_698_full_candidate_packet_drilldown.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK698_DIR / name).exists(), name)

    def test_freeze_scope_and_no_outcome_columns(self) -> None:
        freeze = pd.read_csv(TASK698_DIR / "task698_full_candidate_freeze_panel.csv")

        self.assertEqual(len(freeze), 435)
        self.assertEqual(int(freeze["review_role"].eq("leader").sum()), 28)
        self.assertEqual(int(freeze["review_role"].eq("contender").sum()), 407)
        self.assertFalse(FORBIDDEN_FREEZE_COLUMNS.intersection(freeze.columns))
        self.assertEqual(int(freeze["outcome_used_for_selection_flag"].sum()), 0)
        self.assertEqual(int(freeze["future_price_used_for_selection_flag"].sum()), 0)

    def test_review_ready_counts_are_frozen(self) -> None:
        freeze = pd.read_csv(TASK698_DIR / "task698_full_candidate_freeze_panel.csv")
        summary = pd.read_csv(TASK698_DIR / "task698_bucket_return_summary.csv")

        self.assertEqual(int(freeze["review_ready_packet_flag"].sum()), 11)
        self.assertEqual(int(freeze["source_direct_supported_flag"].sum()), 9)
        self.assertEqual(int(freeze["price_confirmed_flag"].sum()), 2)
        self.assertEqual(int(summary["candidate_count"].sum()), 435)
        self.assertIn("source_direct_supported", set(summary["packet_bucket"]))
        self.assertIn("price_confirmed_not_overextended", set(summary["packet_bucket"]))

    def test_eval_panel_has_cost_and_qqq_for_all_rows(self) -> None:
        eval_panel = pd.read_csv(TASK698_DIR / "task698_full_candidate_eval_panel.csv")

        self.assertEqual(len(eval_panel), 435)
        self.assertTrue(eval_panel["round_trip_cost_bps"].eq(50).all())
        self.assertTrue(eval_panel["costed_return_pct"].notna().all())
        self.assertTrue(eval_panel["qqq_costed_return_pct"].notna().all())
        self.assertEqual(int(eval_panel["outcome_used_for_evaluation_flag"].sum()), 435)
        self.assertEqual(int(eval_panel["outcome_used_for_selection_flag"].sum()), 0)

    def test_portfolio_comparison_and_no_promotion(self) -> None:
        portfolio = pd.read_csv(TASK698_DIR / "task698_portfolio_comparison.csv")
        decision = pd.read_csv(TASK698_DIR / "task_698_decision.csv").iloc[0]

        self.assertIn("source_direct_supported_9", set(portfolio["portfolio_cohort"]))
        self.assertIn("review_ready_source_or_price_11", set(portfolio["portfolio_cohort"]))
        self.assertIn("all_435", set(portfolio["portfolio_cohort"]))
        self.assertEqual(set(portfolio["max_positions"]), {1, 3, 5, 10})
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_source_direct_is_better_than_price_confirmed_on_average(self) -> None:
        summary = pd.read_csv(TASK698_DIR / "task698_bucket_return_summary.csv")
        source_direct = summary[summary["packet_bucket"].eq("source_direct_supported")].iloc[0]
        price_confirmed = summary[summary["packet_bucket"].eq("price_confirmed_not_overextended")].iloc[0]

        self.assertGreater(float(source_direct["avg_costed_return_pct"]), 0.0)
        self.assertGreater(float(source_direct["avg_costed_return_pct"]), float(price_confirmed["avg_costed_return_pct"]))

    def test_integrity_audit_passes(self) -> None:
        audit = pd.read_csv(TASK698_DIR / "task698_integrity_audit.csv")
        self.assertEqual(int(audit["pass_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
