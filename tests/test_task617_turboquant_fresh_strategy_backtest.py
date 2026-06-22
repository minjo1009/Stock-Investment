from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task617_turboquant_fresh_strategy_backtest import (
    build_task617_turboquant_fresh_strategy_backtest,
)


class Task617TurboQuantFreshStrategyBacktestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task617_turboquant_fresh_strategy_backtest()

    def test_fresh_strategy_is_not_refilter_of_existing_89(self) -> None:
        decision = self.artifacts["task_617_decision"].iloc[0]
        baseline = self.artifacts["fresh_baseline_all_candidate_backtest_panel"]
        strategy = self.artifacts["fresh_turboquant_strategy_backtest_panel"]

        self.assertGreater(int(decision["baseline_candidate_count"]), 300)
        self.assertEqual(int(decision["baseline_candidate_count"]), len(baseline))
        self.assertEqual(int(decision["strategy_trade_count"]), len(strategy))
        self.assertGreater(int(decision["strategy_trade_count"]), 50)
        self.assertNotEqual(int(decision["strategy_trade_count"]), 89)
        self.assertTrue(strategy["lifecycle_id"].astype(str).str.startswith("TASK617|").all())

    def test_fresh_strategy_improves_baseline_but_blocks_promotion(self) -> None:
        decision = self.artifacts["task_617_decision"].iloc[0]

        self.assertEqual(decision["decision"], "PASS_FRESH_TURBOQUANT_DIAGNOSTIC_FAIL_PORTFOLIO_CAPACITY_AND_RECENT_OOS")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertGreater(float(decision["strategy_avg_delta_vs_baseline_pct_point"]), 2.0)
        self.assertLessEqual(
            float(decision["strategy_entry_reduce_failure_rate"]),
            float(decision["baseline_entry_reduce_failure_rate"]),
        )
        self.assertEqual(int(decision["gpt_review_pass_flag"]), 1)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_recent_oos_gap_is_visible(self) -> None:
        split = self.artifacts["fresh_turboquant_split_summary"]
        recent = split[split["split_name"].astype(str).eq("recent_oos")].iloc[0]

        self.assertEqual(int(recent["positive_split_flag"]), 0)
        self.assertLess(float(recent["avg_net_return_pct"]), 3.0)

    def test_gpt_review_status_is_captured_not_used_as_source(self) -> None:
        gpt = self.artifacts["gpt_fresh_backtest_design_review_status"].iloc[0]
        decision = self.artifacts["task_617_decision"].iloc[0]

        self.assertEqual(gpt["captured_status"], "CAPTURED_NEW_ALLOWED_TAB")
        self.assertEqual(int(gpt["gpt_output_used_as_source_flag"]), 0)
        self.assertEqual(int(decision["gpt_or_plugin_used_as_source_flag"]), 0)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task617_turboquant_fresh_strategy_backtest(out_dir=out_dir)

            self.assertTrue((out_dir / "task_617_turboquant_fresh_strategy_backtest.md").exists())
            self.assertTrue((out_dir / "fresh_turboquant_strategy_backtest_panel.csv").exists())
            self.assertTrue((out_dir / "task_617_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["fresh_turboquant_strategy_backtest_panel"]), 50)


if __name__ == "__main__":
    unittest.main()
