from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_regime_sleeve_deployment_354 import (
    _allocator_score,
    _final_decision,
    _timing_long_frame,
    _timing_score_wide,
)


class TestAnalysisStructuralBreakoutRegimeSleeveDeployment354(unittest.TestCase):
    def _sample_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "event_id": [0, 1, 2],
                "trade_id": ["t1", "t2", "t3"],
                "symbol": ["A", "B", "C"],
                "entry_ts": pd.to_datetime(
                    ["2024-01-02T00:00:00Z", "2024-01-02T00:00:00Z", "2024-07-01T00:00:00Z"], utc=True
                ),
                "exit_ts": pd.to_datetime(
                    ["2024-01-03T00:00:00Z", "2024-01-03T00:00:00Z", "2024-07-02T00:00:00Z"], utc=True
                ),
                "day_key": ["2024-01-02", "2024-01-02", "2024-07-01"],
                "current_split": ["train", "train", "anchored_oos"],
                "sector_group": ["software_internet", "industrials", "healthcare"],
                "session_timing_bucket": ["first_30m", "mid_session", "first_30m"],
                "execution_quality_bucket": ["strong", "mixed", "strong"],
                "same_day_candidate_count": [2, 2, 1],
                "same_day_sector_candidate_count": [1, 1, 1],
                "realized_R": [1.2, 0.4, 0.8],
                "market_breadth_state": ["broad", "narrow", "broad"],
                "broad_participation_state": ["narrow_participation", "broad_participation", "narrow_participation"],
                "volatility_state": ["low_vol", "high_vol", "low_vol"],
                "liquidity_state": ["liquidity_contracting", "liquidity_expanding", "liquidity_contracting"],
                "sector_leadership_state": ["broad_led", "tech_led", "broad_led"],
                "post_risk_off_state": ["normal", "post_risk_off", "normal"],
            }
        )

    def _sample_selected(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "regime_id": "market_breadth_state=broad|broad_participation_state=narrow_participation",
                    "axes": "market_breadth_state|broad_participation_state",
                    "buckets": "broad|narrow_participation",
                    "continuation_quality_score": 0.8,
                    "artifact_adjusted_weight": 0.2,
                },
                {
                    "regime_id": "session_timing_bucket=first_30m|execution_quality_bucket=strong",
                    "axes": "session_timing_bucket|execution_quality_bucket",
                    "buckets": "first_30m|strong",
                    "continuation_quality_score": 0.6,
                    "artifact_adjusted_weight": 0.3,
                },
            ]
        )

    def test_timing_reconstruction_is_cumulative_and_leak_free(self) -> None:
        wide = _timing_score_wide(self._sample_master(), self._sample_selected())
        long_df = _timing_long_frame(wide)

        pre_row = long_df[(long_df["trade_id"] == "t1") & (long_df["allocator_timing"] == "pre_open_allocator")].iloc[0]
        opening_row = long_df[(long_df["trade_id"] == "t1") & (long_df["allocator_timing"] == "opening_drive_allocator")].iloc[0]
        post_row = long_df[(long_df["trade_id"] == "t1") & (long_df["allocator_timing"] == "post_confirmation_allocator")].iloc[0]

        self.assertEqual(float(pre_row["regime_score_at_decision_time"]), 0.0)
        self.assertGreater(float(opening_row["regime_score_at_decision_time"]), 0.0)
        self.assertGreater(float(post_row["regime_score_at_decision_time"]), float(opening_row["regime_score_at_decision_time"]))
        self.assertTrue(bool(post_row["delayed_signal_penalty_flag"]))

    def test_allocator_score_prefers_structural_balance_for_higher_artifact_score(self) -> None:
        frame = pd.DataFrame(
            {
                "regime_score_at_decision_time": [0.5, 0.4],
                "regime_score_percentile_at_decision_time": [0.9, 0.7],
                "artifact_score_at_decision_time": [0.2, 0.5],
                "artifact_score_percentile_at_decision_time": [0.4, 0.9],
                "top_regime_score_at_decision_time": [0.5, 0.0],
                "same_day_candidate_count": [2, 2],
                "same_day_sector_candidate_count": [1, 1],
            }
        )
        structural = _allocator_score(frame, "structural_balance_allocator")
        self.assertGreater(float(structural.iloc[1]), float(structural.iloc[0]))

    def test_final_decision_prefers_tiny_capital_when_stress_and_overlap_hold(self) -> None:
        allocator_df = pd.DataFrame(
            [
                {
                    "structure_name": "single_best_binary",
                    "allocator_name": "regime_priority_allocator",
                    "allocator_timing": "opening_drive_allocator",
                    "capital_bucket": "bucket_10pct",
                    "max_positions": 3,
                    "net_pnl_r": 150.0,
                    "anchored_oos_net_pnl_r": 60.0,
                    "rolling_oos_robustness": 0.75,
                }
            ]
        )
        stress_df = pd.DataFrame(
            [
                {"stress_scenario": "combined_stress", "pnl_retention_ratio": 0.70},
            ]
        )
        netting_df = pd.DataFrame(
            [
                {"netting_mode": "symbol_netting", "pnl_retention_ratio": 0.78},
            ]
        )
        readiness_df = pd.DataFrame(
            [
                {"gate_name": "shadow_monitor_ready", "status": True},
                {"gate_name": "tiny_capital_pilot_ready", "status": True},
            ]
        )
        final_df = _final_decision(allocator_df, stress_df, netting_df, readiness_df)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "TINY_CAPITAL_PILOT_READY")


if __name__ == "__main__":
    unittest.main()
