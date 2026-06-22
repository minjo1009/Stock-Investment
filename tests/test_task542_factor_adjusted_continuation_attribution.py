from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task542_factor_adjusted_continuation_attribution import (
    build_decision,
    fit_factor_model,
    summarize_candidate_quality,
)


class Task542FactorAdjustedAttributionTest(unittest.TestCase):
    def test_factor_model_scores_residuals_without_trigger_use(self) -> None:
        rows = []
        for i in range(30):
            rows.append(
                {
                    "lifecycle_id": f"L{i}",
                    "return_pct": float(i),
                    "excess_return_pct": float(i),
                    "cum_Mkt_RF_pct": i / 10,
                    "cum_SMB_pct": i % 3,
                    "cum_HML_pct": i % 4,
                    "cum_RMW_pct": i % 5,
                    "cum_CMA_pct": i % 6,
                    "size_log_market_cap": 10 + i / 20,
                    "book_to_market_log": -2 + i / 30,
                }
            )
        summary, scored = fit_factor_model(pd.DataFrame(rows))
        self.assertFalse(summary.empty)
        self.assertIn("factor_adjusted_residual_pct", scored.columns)
        self.assertEqual(int(summary["factor_result_used_as_trading_trigger_flag"].max()), 0)

    def test_candidate_quality_keeps_missing_factor_data_separate(self) -> None:
        panel = pd.DataFrame(
            {
                "candidate_set": ["A", "A", "A"],
                "return_pct": [5.0, 2.0, -1.0],
                "factor_adjustment_available_flag": [1, 1, 0],
                "factor_adjusted_residual_pct": [3.0, 1.0, pd.NA],
                "win_flag": [1, 1, 0],
                "entry_reduce_failure_flag": [0, 0, 1],
                "add_scale_success_flag": [1, 1, 0],
            }
        )
        quality = summarize_candidate_quality(panel)
        self.assertEqual(int(quality.iloc[0]["factor_adjusted_count"]), 2)
        self.assertGreater(float(quality.iloc[0]["factor_adjusted_avg_residual_pct"]), 0)

    def test_decision_is_diagnostic_only(self) -> None:
        quality = pd.DataFrame({"candidate_set": ["A"], "factor_attribution_status": ["true_continuation_alpha_candidate"]})
        model = pd.DataFrame({"term": ["intercept"]})
        panel = pd.DataFrame({"factor_adjustment_available_flag": [1, 0, 1]})
        decision = build_decision(quality, model, panel)
        self.assertEqual(int(decision.iloc[0]["factor_model_run_flag"]), 1)
        self.assertEqual(int(decision.iloc[0]["factor_result_used_as_trading_trigger_flag"]), 0)
        self.assertEqual(int(decision.iloc[0]["deployment_ready_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
