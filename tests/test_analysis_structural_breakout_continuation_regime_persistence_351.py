from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_continuation_regime_persistence_351 import (
    _artifact_vs_structure,
    _candidate_rows,
    _final_decision,
    _positive_tail_ratio,
    _prepare_continuation_master,
    _surviving_regimes,
)


class TestAnalysisStructuralBreakoutContinuationRegimePersistence351(unittest.TestCase):
    def _sample_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "trade_id": [str(i) for i in range(1, 13)],
                "symbol": [f"S{i}" for i in range(1, 13)],
                "current_split": ["train"] * 4 + ["anchored_oos"] * 8,
                "entry_ts": pd.to_datetime(
                    [
                        "2024-01-02T14:35:00Z",
                        "2024-01-03T14:35:00Z",
                        "2024-01-04T14:35:00Z",
                        "2024-01-05T14:35:00Z",
                        "2025-01-02T14:35:00Z",
                        "2025-02-02T14:35:00Z",
                        "2025-03-02T14:35:00Z",
                        "2025-04-02T14:35:00Z",
                        "2025-05-02T14:35:00Z",
                        "2025-06-02T14:35:00Z",
                        "2025-07-02T19:10:00Z",
                        "2025-08-02T19:10:00Z",
                    ],
                    utc=True,
                ),
                "exit_ts": pd.to_datetime(
                    [
                        "2024-01-05T14:35:00Z",
                        "2024-01-06T14:35:00Z",
                        "2024-01-07T14:35:00Z",
                        "2024-01-08T14:35:00Z",
                        "2025-01-05T14:35:00Z",
                        "2025-02-05T14:35:00Z",
                        "2025-03-05T14:35:00Z",
                        "2025-04-05T14:35:00Z",
                        "2025-05-05T14:35:00Z",
                        "2025-06-05T14:35:00Z",
                        "2025-07-05T19:10:00Z",
                        "2025-08-05T19:10:00Z",
                    ],
                    utc=True,
                ),
                "realized_R": [0.8, 1.2, 0.6, 0.4, 2.2, 1.8, 2.5, 1.6, -0.2, 0.9, -0.5, 0.3],
                "sector_group": ["software_internet"] * 6 + ["others"] * 6,
                "volatility_state": ["high_vol"] * 8 + ["low_vol"] * 4,
                "liquidity_state": ["liquidity_expanding"] * 8 + ["liquidity_contracting"] * 4,
                "market_breadth_state": ["broad"] * 10 + ["narrow"] * 2,
                "broad_participation_state": ["broad_participation"] * 9 + ["narrow_participation"] * 3,
                "sector_leadership_state": ["tech_led"] * 6 + ["broad_led"] * 6,
                "post_risk_off_state": ["post_risk_off"] * 5 + ["normal"] * 7,
                "session_timing_bucket": ["first_30m"] * 5 + ["mid_session"] * 5 + ["last_hour"] * 2,
                "execution_quality_bucket": ["strong"] * 6 + ["mixed"] * 4 + ["weak"] * 2,
                "covered_execution_available": [True] * 10 + [False] * 2,
                "same_day_candidate_count": [6, 5, 5, 4, 3, 3, 2, 2, 1, 1, 1, 1],
            }
        )

    def test_positive_tail_ratio_is_tail_sensitive(self) -> None:
        series = pd.Series([0.1, 0.2, 0.3, 3.0, -0.1])
        ratio = _positive_tail_ratio(series)
        self.assertGreater(ratio, 0.7)

    def test_candidate_rows_only_use_allowed_axes_and_interactions(self) -> None:
        candidates = _candidate_rows(self._sample_master())
        self.assertTrue(candidates["axes"].astype(str).str.contains("volatility_state").any())
        self.assertTrue(
            candidates["axes"].astype(str).eq("volatility_state|liquidity_state").any()
        )
        self.assertFalse(candidates["axes"].astype(str).eq("sector_group|execution_quality_bucket").any())

    def test_survivor_artifact_and_final_decision_are_deterministic(self) -> None:
        master = self._sample_master()
        candidates = _candidate_rows(master)
        self.assertFalse(candidates.empty)
        top_candidate = candidates.head(1).copy()
        artifact_df = _artifact_vs_structure(master, top_candidate)
        structural_only = artifact_df[artifact_df["scenario"] == "structural_only"]
        self.assertIn("structural_share", structural_only.columns)

        viability_df = pd.DataFrame(
            [
                {
                    "regime_id": "volatility_state=high_vol",
                    "trade_count": 12,
                    "annual_trade_frequency": 20.0,
                    "cost_adjusted_expectancy": 0.22,
                    "convex_payoff_score": 0.72,
                    "rolling_robustness": 0.75,
                    "artifact_dependence": 0.35,
                    "economic_viability": "offensive_tactical_alpha",
                }
            ]
        )
        rolling_df = pd.DataFrame(
            [
                {"regime_id": "volatility_state=high_vol", "window_id": "w1", "status": "positive_convexity"},
                {"regime_id": "volatility_state=high_vol", "window_id": "w2", "status": "positive_convexity"},
                {"regime_id": "volatility_state=high_vol", "window_id": "w3", "status": "positive_convexity"},
            ]
        )
        final_df = _final_decision(viability_df, structural_only.assign(regime_id="volatility_state=high_vol", structural_share=0.45), rolling_df)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "REGIME_DEPENDENT_CONTINUATION_ALPHA")


if __name__ == "__main__":
    unittest.main()
