from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASK697_DIR = Path("docs/reports/task_697_tiny_candidate_pnl_test")


class Task697TinyCandidatePnlTest(unittest.TestCase):
    def test_required_artifacts_exist(self) -> None:
        for name in [
            "task697_tiny_trade_pnl.csv",
            "task697_tiny_capital_comparison.csv",
            "task697_cost_model.csv",
            "task697_benchmark_availability_audit.csv",
            "task_697_pass_fail_matrix.csv",
            "task_697_decision.csv",
            "task_697_tiny_candidate_pnl_test.md",
            "artifact_manifest.csv",
        ]:
            self.assertTrue((TASK697_DIR / name).exists(), name)

    def test_tiny_scope_and_exact_candidate_count(self) -> None:
        trade_pnl = pd.read_csv(TASK697_DIR / "task697_tiny_trade_pnl.csv")
        decision = pd.read_csv(TASK697_DIR / "task_697_decision.csv").iloc[0]

        self.assertEqual(len(trade_pnl), 3)
        self.assertEqual(set(trade_pnl["symbol"]), {"ASTS", "BA", "TER"})
        self.assertEqual(int(decision["candidate_count"]), 3)
        self.assertEqual(decision["candidate_symbols"], "ASTS|BA|TER")

    def test_cost_and_qqq_comparison_are_present(self) -> None:
        trade_pnl = pd.read_csv(TASK697_DIR / "task697_tiny_trade_pnl.csv")
        comparison = pd.read_csv(TASK697_DIR / "task697_tiny_capital_comparison.csv")
        cost_model = pd.read_csv(TASK697_DIR / "task697_cost_model.csv").iloc[0]

        self.assertTrue(trade_pnl["round_trip_cost_bps"].eq(50).all())
        self.assertTrue((trade_pnl["costed_return_pct"] <= trade_pnl["gross_return_pct"]).all())
        self.assertTrue((trade_pnl["qqq_costed_return_pct"] <= trade_pnl["qqq_gross_return_pct"]).all())
        self.assertEqual(int(cost_model["round_trip_cost_bps"]), 50)
        self.assertIn("QQQ_matched_trade_windows_sequential", set(comparison["comparison_name"]))
        self.assertIn("QQQ_buy_and_hold_tiny_window_costed", set(comparison["comparison_name"]))

    def test_capital_starts_at_1000_and_benchmark_available(self) -> None:
        comparison = pd.read_csv(TASK697_DIR / "task697_tiny_capital_comparison.csv")
        audit = pd.read_csv(TASK697_DIR / "task697_benchmark_availability_audit.csv")

        self.assertTrue(comparison["initial_capital_usd"].eq(1000.0).all())
        self.assertTrue(comparison["final_capital_usd"].notna().all())
        self.assertEqual(int(audit[audit["gate_name"].eq("qqq_benchmark_available")].iloc[0]["pass_flag"]), 1)
        self.assertEqual(int(audit["pass_flag"].min()), 1)

    def test_outcomes_are_evaluation_only_and_no_promotion(self) -> None:
        trade_pnl = pd.read_csv(TASK697_DIR / "task697_tiny_trade_pnl.csv")
        decision = pd.read_csv(TASK697_DIR / "task_697_decision.csv").iloc[0]

        self.assertEqual(int(trade_pnl["outcome_used_for_selection_flag"].sum()), 0)
        self.assertEqual(int(trade_pnl["future_price_used_for_selection_flag"].sum()), 0)
        self.assertEqual(int(trade_pnl["outcome_used_for_evaluation_flag"].sum()), 3)
        self.assertEqual(int(trade_pnl["allocation_approved_flag"].sum()), 0)
        self.assertEqual(int(trade_pnl["paper_or_live_trade_approved_flag"].sum()), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_tiny_strategy_beats_qqq_but_stays_research_only(self) -> None:
        decision = pd.read_csv(TASK697_DIR / "task_697_decision.csv").iloc[0]

        self.assertGreater(float(decision["tiny_strategy_final_capital_usd"]), 1000.0)
        self.assertEqual(int(decision["beats_qqq_matched_flag"]), 1)
        self.assertEqual(int(decision["beats_qqq_buyhold_costed_flag"]), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")


if __name__ == "__main__":
    unittest.main()
