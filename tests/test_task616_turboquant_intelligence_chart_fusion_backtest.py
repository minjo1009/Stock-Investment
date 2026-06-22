from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task616_turboquant_intelligence_chart_fusion_backtest import (
    build_task616_turboquant_intelligence_chart_fusion_backtest,
)


class Task616TurboQuantIntelligenceChartFusionBacktestTest(unittest.TestCase):
    def test_fusion_backtest_uses_chart_and_intelligence_but_blocks_promotion(self) -> None:
        artifacts = build_task616_turboquant_intelligence_chart_fusion_backtest()
        decision = artifacts["task_616_decision"].iloc[0]

        self.assertEqual(decision["decision"], "PASS_TURBOQUANT_FUSION_DIAGNOSTIC_FAIL_TRADING_PROMOTION")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["fusion_accepted_count"]), 67)
        self.assertGreater(float(decision["fusion_accepted_return_delta_pct_point"]), 4.0)
        self.assertLess(float(decision["fusion_failure_delta_pct_point"]), -4.0)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)
        self.assertEqual(int(decision["gpt_or_plugin_used_as_source_flag"]), 0)

    def test_fusion_entry_panel_has_expected_scores(self) -> None:
        artifacts = build_task616_turboquant_intelligence_chart_fusion_backtest()
        panel = artifacts["turboquant_fusion_entry_panel"]

        for col in (
            "tq_pre_entry_chart_health_score",
            "tq_wait_window_chart_risk_score",
            "tq_intelligence_support_score",
            "tq_fusion_accept_flag",
            "tq_fusion_review_flag",
        ):
            self.assertIn(col, panel.columns)
        self.assertEqual(int(panel["tq_fusion_accept_flag"].sum()), 67)
        self.assertEqual(int(panel["tq_fusion_assignment_label_used_flag"].max()), 0)

    def test_quarter_stability_is_diagnostic_not_acceptance(self) -> None:
        artifacts = build_task616_turboquant_intelligence_chart_fusion_backtest()
        quarters = artifacts["turboquant_fusion_quarter_summary"]
        pass_fail = artifacts["task_616_pass_fail_matrix"]

        self.assertGreaterEqual(int(quarters["positive_quarter_flag"].sum()), 4)
        trading_gate = pass_fail[pass_fail["gate"].eq("trading_promotion")].iloc[0]
        self.assertEqual(int(trading_gate["pass_flag"]), 0)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            build_task616_turboquant_intelligence_chart_fusion_backtest(out_dir=out_dir)

            self.assertTrue((out_dir / "task_616_turboquant_intelligence_chart_fusion_backtest.md").exists())
            self.assertTrue((out_dir / "task_616_decision.csv").exists())
            self.assertTrue((out_dir / "turboquant_fusion_entry_panel.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
