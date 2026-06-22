from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_regime_continuation_sleeve_353 import (
    _basket_comparison,
    _build_participation_scorecard,
    _final_decision,
    _selected_regimes,
)


class TestAnalysisStructuralBreakoutRegimeContinuationSleeve353(unittest.TestCase):
    def _sample_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "trade_id": ["t1", "t2", "t3", "t4"],
                "symbol": ["A", "B", "C", "D"],
                "entry_ts": pd.to_datetime(
                    [
                        "2024-01-02T14:30:00Z",
                        "2024-01-02T15:00:00Z",
                        "2024-07-03T14:30:00Z",
                        "2024-07-04T15:30:00Z",
                    ],
                    utc=True,
                ),
                "current_split": ["train", "train", "test", "test"],
                "sector_group": ["software_internet", "industrials", "healthcare", "software_internet"],
                "realized_R": [1.2, 0.4, 0.9, -0.3],
                "market_breadth_state": ["broad", "broad", "narrow", "broad"],
                "broad_participation_state": ["narrow_participation", "broad_participation", "narrow_participation", "narrow_participation"],
                "session_timing_bucket": ["first_30m", "mid_session", "first_30m", "first_30m"],
                "execution_quality_bucket": ["strong", "mixed", "strong", "weak"],
            }
        )

    def _sample_ranked(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "regime_id": "market_breadth_state=broad|broad_participation_state=narrow_participation",
                    "axes": "market_breadth_state|broad_participation_state",
                    "buckets": "broad|narrow_participation",
                    "candidate_type": "interaction",
                    "trade_count": 40,
                    "cost_adjusted_expectancy": 0.70,
                    "rolling_robustness": 1.0,
                    "structural_share": 0.25,
                    "artifact_dependence": 0.75,
                    "continuation_quality_score": 0.80,
                },
                {
                    "regime_id": "session_timing_bucket=first_30m",
                    "axes": "session_timing_bucket",
                    "buckets": "first_30m",
                    "candidate_type": "single_axis",
                    "trade_count": 25,
                    "cost_adjusted_expectancy": 0.55,
                    "rolling_robustness": 0.75,
                    "structural_share": 0.35,
                    "artifact_dependence": 0.65,
                    "continuation_quality_score": 0.65,
                },
            ]
        )

    def test_participation_scorecard_accumulates_regime_scores(self) -> None:
        master = self._sample_master()
        selected = _selected_regimes(self._sample_ranked())
        scorecard = _build_participation_scorecard(master, selected)

        t1 = scorecard.loc[scorecard["trade_id"] == "t1"].iloc[0]
        self.assertEqual(int(t1["matched_regime_count"]), 2)
        self.assertEqual(str(t1["participation_tier"]), "core")
        self.assertGreater(float(t1["regime_participation_score"]), 1.0)
        self.assertTrue(bool(t1["single_best_match"]))

        t2 = scorecard.loc[scorecard["trade_id"] == "t2"].iloc[0]
        self.assertEqual(int(t2["matched_regime_count"]), 0)
        self.assertEqual(str(t2["participation_tier"]), "skip")

    def test_basket_comparison_emits_expected_structure_rows(self) -> None:
        master = self._sample_master()
        selected = _selected_regimes(self._sample_ranked())
        scorecard = _build_participation_scorecard(master, selected)
        basket_df, _ = _basket_comparison(master, scorecard)

        self.assertEqual(
            basket_df["structure_name"].astype(str).tolist(),
            [
                "single_best_binary",
                "top_regime_basket_binary",
                "score_ranked_top3",
                "regime_conditioned_overlay_balanced",
            ],
        )
        self.assertTrue((pd.to_numeric(basket_df["trade_count"], errors="coerce") >= 0).all())

    def test_final_decision_prefers_offensive_sleeve_when_basket_and_oos_hold(self) -> None:
        basket_df = pd.DataFrame(
            [
                {
                    "structure_name": "top_regime_basket_binary",
                    "structure_group": "basket",
                    "trade_count": 120,
                    "annual_trade_frequency": 45.0,
                    "expectancy": 0.7,
                    "sharpe_proxy": 1.1,
                    "mdd_pct": 9.0,
                    "return_contribution": 84.0,
                    "cost_adjusted_expectancy": 0.45,
                    "cost_2x_expectancy": 0.32,
                    "turnover_proxy": 0.6,
                    "capital_utilization": 0.12,
                    "concentration": 0.41,
                    "rolling_oos_robustness": 0.75,
                    "anchored_oos_expectancy": 0.6,
                    "anchored_oos_cost_adjusted_expectancy": 0.4,
                    "monetization_score": 0.74,
                },
                {
                    "structure_name": "regime_conditioned_overlay_balanced",
                    "structure_group": "basket",
                    "trade_count": 120,
                    "annual_trade_frequency": 45.0,
                    "expectancy": 0.8,
                    "sharpe_proxy": 1.2,
                    "mdd_pct": 8.5,
                    "return_contribution": 96.0,
                    "cost_adjusted_expectancy": 0.52,
                    "cost_2x_expectancy": 0.38,
                    "turnover_proxy": 0.6,
                    "capital_utilization": 0.12,
                    "concentration": 0.39,
                    "rolling_oos_robustness": 0.75,
                    "anchored_oos_expectancy": 0.7,
                    "anchored_oos_cost_adjusted_expectancy": 0.46,
                    "monetization_score": 0.79,
                },
            ]
        )
        sizing_df = pd.DataFrame(
            [
                {
                    "structure_name": "sizing_template_balanced",
                    "structure_group": "sizing",
                    "trade_count": 120,
                    "annual_trade_frequency": 45.0,
                    "expectancy": 0.8,
                    "sharpe_proxy": 1.2,
                    "mdd_pct": 8.5,
                    "return_contribution": 96.0,
                    "cost_adjusted_expectancy": 0.50,
                    "cost_2x_expectancy": 0.36,
                    "turnover_proxy": 0.6,
                    "capital_utilization": 0.12,
                    "concentration": 0.40,
                    "rolling_oos_robustness": 0.75,
                    "anchored_oos_expectancy": 0.7,
                    "anchored_oos_cost_adjusted_expectancy": 0.45,
                    "monetization_score": 0.78,
                }
            ]
        )
        artifact_df = pd.DataFrame(
            [
                {"structure_name": "artifact_half_plus", "cost_adjusted_expectancy": 0.34, "monetization_score": 0.65},
                {"structure_name": "artifact_core", "cost_adjusted_expectancy": 0.28, "monetization_score": 0.60},
            ]
        )
        oos_df = pd.DataFrame(
            [
                {"scope": "rolling_window", "expectancy": 0.4},
                {"scope": "rolling_window", "expectancy": 0.3},
                {"scope": "rolling_window", "expectancy": 0.5},
                {"scope": "rolling_window", "expectancy": 0.2},
            ]
        )
        utility_df = pd.DataFrame(
            [
                {
                    "best_structure": "regime_conditioned_overlay_balanced",
                    "trade_count": 120,
                    "annual_trade_frequency": 45.0,
                    "capital_utilization": 0.12,
                    "usable_capital_bucket": "moderate",
                    "concentration_risk": "medium",
                    "execution_fragility": "low",
                    "expected_live_slippage": "manageable",
                    "shadow_monitor_suitability": True,
                    "likely_live_decay_risk": "medium",
                }
            ]
        )
        final_df = _final_decision(basket_df, sizing_df, artifact_df, oos_df, utility_df)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "OFFENSIVE_REGIME_SLEEVE")


if __name__ == "__main__":
    unittest.main()
