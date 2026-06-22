from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_tactical_sleeve_348 import (
    _add_execution_bands,
    _build_sleeve_frames,
    _capital_utilization_ratio,
    _execution_quality_score,
    _longest_inactive_period_days,
    _session_timing_bucket,
)


class TestAnalysisStructuralBreakoutTacticalSleeve348(unittest.TestCase):
    def _sample_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "trade_id": ["a", "b", "c", "d", "e", "f"],
                "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
                "sector_group": ["software_internet", "semis", "software_internet", "others", "software_internet", "semis"],
                "current_split": ["train", "train", "anchored_oos", "anchored_oos", "anchored_oos", "train"],
                "entry_ts": pd.to_datetime(
                    [
                        "2024-01-02T15:00:00Z",
                        "2024-01-03T15:10:00Z",
                        "2024-01-08T15:05:00Z",
                        "2024-01-15T15:40:00Z",
                        "2024-01-22T20:10:00Z",
                        "2024-01-25T16:00:00Z",
                    ],
                    utc=True,
                ),
                "breakout_timestamp": pd.to_datetime(
                    [
                        "2024-01-02T15:00:00Z",
                        "2024-01-03T15:10:00Z",
                        "2024-01-08T15:05:00Z",
                        "2024-01-15T15:40:00Z",
                        "2024-01-22T20:10:00Z",
                        "2024-01-25T16:00:00Z",
                    ],
                    utc=True,
                ),
                "realized_R": [1.0, -0.5, 0.8, -0.2, 1.4, 0.1],
                "atr_regime": ["high_atr", "low_atr", "high_atr", "high_atr", "high_atr", "high_atr"],
                "contraction_regime": ["vol_expanding", "vol_expanding", "vol_expanding", "vol_contracting", "vol_expanding", "vol_expanding"],
                "window_mode": ["entry_only"] * 6,
                "cluster_label_base": ["clean_continuation", "dead_breakout", "failed_pop", "dead_breakout", "clean_continuation", "clean_continuation"],
                "price_vs_session_vwap_at_breakout": [0.02, -0.01, 0.03, -0.02, 0.04, 0.01],
                "vwap_deviation_at_breakout": [0.2, -0.1, 0.3, -0.2, 0.4, 0.1],
                "vwap_slope_prebreak": [0.05, -0.02, 0.06, -0.03, 0.07, 0.02],
                "vwap_response": ["vwap_hold", "vwap_reject", "vwap_hold", "vwap_reject", "vwap_hold", "vwap_hold"],
                "breakout_hold_duration_bars": [3, 0, 2, 0, 4, 1],
                "breakout_bar_close_location": [0.8, 0.2, 0.7, 0.3, 0.9, 0.6],
                "return_next_3bars": [0.03, -0.02, 0.02, -0.01, 0.04, 0.01],
                "return_next_5bars": [0.05, -0.03, 0.03, -0.02, 0.05, 0.02],
                "adverse_excursion_next_3bars": [0.01, 0.05, 0.02, 0.06, 0.01, 0.02],
                "intraday_pullback_depth_3bars": [0.01, 0.04, 0.02, 0.05, 0.01, 0.02],
                "breakout_response": ["breakout_hold", "immediate_failure", "breakout_hold", "immediate_failure", "breakout_hold", "breakout_hold"],
                "breakout_window_volume_surge": [2.0, 0.8, 1.9, 0.7, 2.1, 1.5],
                "volume_persistence_3bars": [1.8, 0.7, 1.7, 0.8, 1.9, 1.2],
                "relative_volume_percentile": [0.9, 0.2, 0.8, 0.3, 0.95, 0.6],
                "rejection_wick_ratio": [0.1, 0.5, 0.15, 0.6, 0.1, 0.2],
                "failed_break_count_prebreak": [0, 2, 0, 3, 0, 1],
                "false_break_attempts_prebreak": [0, 1, 0, 2, 0, 1],
            }
        )

    def test_session_timing_bucket_uses_market_time(self) -> None:
        self.assertEqual(_session_timing_bucket(pd.Timestamp("2024-01-02T14:35:00Z")), "first_30m")
        self.assertEqual(_session_timing_bucket(pd.Timestamp("2024-01-02T17:30:00Z")), "mid_session")
        self.assertEqual(_session_timing_bucket(pd.Timestamp("2024-01-02T20:10:00Z")), "last_hour")

    def test_build_sleeve_frames_keeps_base_and_supported(self) -> None:
        sleeves = _build_sleeve_frames(self._sample_master())
        self.assertEqual(len(sleeves["base_tactical_sleeve"]), 4)
        self.assertEqual(len(sleeves["supported_tactical_sleeve"]), 3)

    def test_execution_quality_score_is_fixed_and_bucketed(self) -> None:
        master = self._sample_master().copy()
        master["session_timing_bucket"] = master["breakout_timestamp"].map(_session_timing_bucket)
        banded = _add_execution_bands(master)
        scored = _execution_quality_score(banded)
        self.assertIn("execution_quality_score", scored.columns)
        self.assertIn("execution_quality_bucket", scored.columns)
        self.assertIn(scored.loc[0, "execution_quality_bucket"], {"weak", "mixed", "strong"})

    def test_capital_utilization_ratio_is_deterministic(self) -> None:
        master = self._sample_master()
        sleeves = _build_sleeve_frames(master)
        ratio = _capital_utilization_ratio(sleeves["base_tactical_sleeve"], master)
        self.assertGreaterEqual(ratio, 0.0)
        self.assertLessEqual(ratio, 1.0)

    def test_longest_inactive_period_days_uses_entry_gaps(self) -> None:
        scoped = self._sample_master().iloc[[0, 2, 4]].copy()
        gap = _longest_inactive_period_days(scoped)
        self.assertGreaterEqual(gap, 7)


if __name__ == "__main__":
    unittest.main()
