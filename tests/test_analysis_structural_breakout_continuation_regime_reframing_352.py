from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_continuation_regime_reframing_352 import (
    _final_decision,
    _percentile_rank,
    _positive_vs_convex_vs_structural,
    _relative_ranking,
)


class TestAnalysisStructuralBreakoutContinuationRegimeReframing352(unittest.TestCase):
    def _sample_candidates(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "regime_id": ["r1", "r2", "r3", "r4"],
                "axes": ["volatility_state", "liquidity_state", "volatility_state|liquidity_state", "market_breadth_state"],
                "buckets": ["high_vol", "liquidity_expanding", "high_vol|liquidity_expanding", "broad"],
                "trade_count": [30, 25, 14, 40],
                "expectancy": [0.7, 0.5, 0.9, 0.3],
                "positive_tail_ratio": [0.28, 0.41, 0.36, 0.18],
                "convex_payoff_score": [0.52, 0.48, 0.59, 0.33],
                "cost_adjusted_expectancy": [0.55, 0.42, 0.68, 0.12],
                "rolling_robustness": [0.75, 0.75, 0.5, 0.25],
                "participation_durability": [0.12, 0.08, 0.06, 0.25],
            }
        )

    def test_percentile_rank_is_deterministic(self) -> None:
        ranked = _percentile_rank(pd.Series([1.0, 2.0, 3.0]))
        self.assertAlmostEqual(float(ranked.iloc[0]), 1 / 3, places=6)
        self.assertAlmostEqual(float(ranked.iloc[-1]), 1.0, places=6)

    def test_relative_ranking_uses_positive_tail_as_component_not_gate(self) -> None:
        candidates = self._sample_candidates()
        artifact_df = pd.DataFrame(
            [
                {"regime_id": "r1", "scenario": "structural_only", "structural_share": 0.45},
                {"regime_id": "r2", "scenario": "structural_only", "structural_share": 0.20},
                {"regime_id": "r3", "scenario": "structural_only", "structural_share": 0.55},
                {"regime_id": "r4", "scenario": "structural_only", "structural_share": 0.10},
            ]
        )
        tail_df = pd.DataFrame(
            [
                {"regime_id": "r1", "top_decile_contribution": 0.65, "positive_skew_proxy": 2.2, "rolling_tail_survival": 0.75},
                {"regime_id": "r2", "top_decile_contribution": 0.70, "positive_skew_proxy": 2.4, "rolling_tail_survival": 0.50},
                {"regime_id": "r3", "top_decile_contribution": 0.80, "positive_skew_proxy": 2.8, "rolling_tail_survival": 0.75},
                {"regime_id": "r4", "top_decile_contribution": 0.55, "positive_skew_proxy": 1.6, "rolling_tail_survival": 0.25},
            ]
        )
        ranked = _relative_ranking(candidates, artifact_df, tail_df)
        self.assertIn("continuation_quality_score", ranked.columns)
        self.assertTrue((ranked["positive_tail_ratio"] < 0.45).any())
        self.assertTrue((ranked["continuation_quality_score"] > 0).all())

    def test_layer_separation_and_final_decision_are_deterministic(self) -> None:
        ranked = pd.DataFrame(
            [
                {
                    "regime_id": "r1",
                    "candidate_type": "single_axis",
                    "trade_count": 30,
                    "cost_adjusted_expectancy": 0.55,
                    "rolling_robustness": 0.75,
                    "positive_tail_ratio": 0.28,
                    "top_decile_contribution": 0.65,
                    "structural_share": 0.45,
                    "continuation_quality_score": 0.82,
                    "positive_tail_ratio_pct": 0.7,
                    "top_decile_contribution_pct": 0.8,
                    "rolling_tail_survival": 0.75,
                },
                {
                    "regime_id": "r2",
                    "candidate_type": "interaction",
                    "trade_count": 20,
                    "cost_adjusted_expectancy": 0.20,
                    "rolling_robustness": 0.50,
                    "positive_tail_ratio": 0.15,
                    "top_decile_contribution": 0.30,
                    "structural_share": 0.12,
                    "continuation_quality_score": 0.41,
                    "positive_tail_ratio_pct": 0.2,
                    "top_decile_contribution_pct": 0.2,
                    "rolling_tail_survival": 0.25,
                },
            ]
        )
        layers = _positive_vs_convex_vs_structural(ranked)
        self.assertTrue(bool(layers.loc[layers["regime_id"] == "r1", "positive_drift_continuation"].iloc[0]))
        self.assertTrue(bool(layers.loc[layers["regime_id"] == "r1", "offensive_convex_continuation"].iloc[0]))
        self.assertTrue(bool(layers.loc[layers["regime_id"] == "r1", "structural_continuation"].iloc[0]))

        utility = pd.DataFrame(
            [
                {
                    "selection_bucket": "top5_overall",
                    "regime_id": "r1",
                    "trade_count": 30,
                    "annual_trade_frequency": 18.0,
                    "cost_adjusted_expectancy": 0.55,
                    "rolling_robustness": 0.75,
                    "structural_share": 0.45,
                    "tail_profile_strength": "high",
                    "economic_usefulness": "high",
                }
            ]
        )
        final_df = _final_decision(ranked, layers, utility)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "PERSISTENT_CONVEX_CONTINUATION_ALPHA")


if __name__ == "__main__":
    unittest.main()
