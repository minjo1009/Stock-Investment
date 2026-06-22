from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_anchored_oos_failure_uplift_355 import (
    _deployment_uplift_score,
    _final_decision,
    _uplift_scorecard,
)


class TestAnalysisStructuralBreakoutAnchoredOosFailureUplift355(unittest.TestCase):
    def test_deployment_uplift_score_prioritizes_anchored_improvement(self) -> None:
        baseline = {
            "anchored_oos_net_pnl_r": -1.0,
            "anchored_oos_cost_adjusted_expectancy": -0.05,
            "max_peak_to_trough_pnl_drawdown": 10.0,
        }
        candidate = {
            "anchored_oos_net_pnl_r": 4.0,
            "anchored_oos_cost_adjusted_expectancy": 0.10,
            "max_peak_to_trough_pnl_drawdown": 8.0,
        }
        score = _deployment_uplift_score(baseline, candidate, 0.6)
        self.assertGreater(score, 0.0)

    def test_uplift_scorecard_computes_relative_changes(self) -> None:
        uplift_df = pd.DataFrame(
            [
                {
                    "candidate_name": "baseline_task354_best",
                    "uplift_type": "baseline",
                    "anchored_oos_net_pnl_r": -1.0,
                    "anchored_oos_cost_adjusted_expectancy": -0.05,
                    "max_peak_to_trough_pnl_drawdown": 10.0,
                    "rolling_oos_robustness": 0.75,
                    "combined_stress_retention": 0.56,
                    "deployment_uplift_score": 0.0,
                },
                {
                    "candidate_name": "uplift_a",
                    "uplift_type": "single_factor",
                    "anchored_oos_net_pnl_r": 2.5,
                    "anchored_oos_cost_adjusted_expectancy": 0.03,
                    "max_peak_to_trough_pnl_drawdown": 8.0,
                    "rolling_oos_robustness": 0.75,
                    "combined_stress_retention": 0.58,
                    "deployment_uplift_score": 1.2,
                },
            ]
        )
        scorecard = _uplift_scorecard(uplift_df)
        row = scorecard.iloc[0]
        self.assertEqual(str(row["candidate_name"]), "uplift_a")
        self.assertAlmostEqual(float(row["anchored_oos_net_pnl_improvement"]), 3.5, places=6)
        self.assertTrue(bool(row["rolling_robustness_preserved"]))

    def test_final_decision_promotes_shadow_ready_when_anchored_turns_positive(self) -> None:
        uplift_df = pd.DataFrame(
            [
                {
                    "candidate_name": "baseline_task354_best",
                    "uplift_type": "baseline",
                    "anchored_oos_net_pnl_r": -1.0,
                    "anchored_oos_cost_adjusted_expectancy": -0.05,
                    "max_peak_to_trough_pnl_drawdown": 10.0,
                    "rolling_oos_robustness": 0.75,
                    "combined_stress_retention": 0.56,
                    "deployment_uplift_score": 0.0,
                },
                {
                    "candidate_name": "uplift_best",
                    "uplift_type": "single_factor",
                    "anchored_oos_net_pnl_r": 1.5,
                    "anchored_oos_cost_adjusted_expectancy": 0.02,
                    "max_peak_to_trough_pnl_drawdown": 9.0,
                    "rolling_oos_robustness": 0.75,
                    "combined_stress_retention": 0.60,
                    "deployment_uplift_score": 0.9,
                },
            ]
        )
        scorecard_df = pd.DataFrame(
            [
                {
                    "candidate_name": "uplift_best",
                    "uplift_type": "single_factor",
                    "anchored_oos_net_pnl_improvement": 2.5,
                    "anchored_oos_expectancy_improvement": 0.07,
                    "drawdown_relief": 1.0,
                    "rolling_robustness_preserved": True,
                    "stress_retention_preserved": True,
                    "deployment_uplift_score": 0.9,
                }
            ]
        )
        final_df = _final_decision(uplift_df, scorecard_df)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "SHADOW_READY_UPLIFT")


if __name__ == "__main__":
    unittest.main()
