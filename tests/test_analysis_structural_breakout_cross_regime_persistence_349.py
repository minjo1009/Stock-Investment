from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_cross_regime_persistence_349 import (
    _apply_regime_labels,
    _assign_failure_types,
    _final_decision,
    _regime_thresholds,
    _scorecard,
    _shadow_readiness,
)


class TestAnalysisStructuralBreakoutCrossRegimePersistence349(unittest.TestCase):
    def _sample_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "trade_id": ["a", "b", "c", "d", "e", "f"],
                "current_split": ["train", "train", "train", "anchored_oos", "anchored_oos", "anchored_oos"],
                "entry_ts": pd.to_datetime(
                    [
                        "2024-01-02T15:00:00Z",
                        "2024-01-03T15:00:00Z",
                        "2024-01-04T15:00:00Z",
                        "2024-01-05T15:00:00Z",
                        "2024-01-08T15:00:00Z",
                        "2024-01-09T20:05:00Z",
                    ],
                    utc=True,
                ),
                "realized_R": [1.0, -0.5, 0.8, -0.2, 1.4, -0.3],
                "sector_group": ["software_internet", "semis", "software_internet", "others", "software_internet", "software_internet"],
                "cluster_label_base": ["clean_continuation", "dead_breakout", "failed_pop", "dead_breakout", "clean_continuation", "failed_pop"],
                "range_width_10_pre": [0.04, 0.01, 0.05, 0.03, 0.06, 0.02],
                "ret_20d_pre": [0.15, -0.04, 0.10, 0.08, 0.12, -0.02],
                "dist_to_sma20_pct": [0.06, -0.01, 0.03, 0.02, 0.05, -0.03],
                "breadth_above_sma20": [0.7, 0.4, 0.8, 0.6, 0.7, 0.3],
                "breadth_above_sma50": [0.75, 0.45, 0.8, 0.55, 0.72, 0.35],
                "breadth_positive_20d": [0.68, 0.42, 0.73, 0.57, 0.7, 0.38],
                "top_sector_dominance_score": [0.7, 0.4, 0.8, 0.6, 0.75, 0.45],
                "tech_concentration_ratio": [0.72, 0.3, 0.76, 0.62, 0.74, 0.35],
                "semis_concentration_ratio": [0.2, 0.5, 0.22, 0.3, 0.25, 0.4],
                "dollar_volume_pre": [40e6, 20e6, 45e6, 35e6, 50e6, 18e6],
                "turnover_pre": [1.5, 0.7, 1.8, 1.2, 1.7, 0.6],
                "vol_contraction_ratio": [1.3, 0.7, 1.4, 1.1, 1.5, 0.8],
                "dispersion_20d": [0.4, 0.2, 0.45, 0.3, 0.5, 0.25],
                "mean_pairwise_corr": [0.6, 0.3, 0.7, 0.55, 0.72, 0.32],
                "gap_over_planned_entry_pct": [0.01, 0.04, 0.02, 0.03, 0.01, 0.05],
                "sector_rs_percentile": [0.82, 0.4, 0.85, 0.7, 0.88, 0.5],
                "sector_crowding_high": [1, 0, 1, 1, 1, 0],
                "breakout_response": ["breakout_hold", "immediate_failure", "breakout_hold", "immediate_failure", "breakout_hold", "immediate_failure"],
                "breakout_hold_duration_bars": [2, 0, 3, 0, 4, 0],
                "volume_persistence_3bars_band348": ["high", "low", "high", "low", "high", "low"],
                "breakout_window_volume_surge_band348": ["high", "low", "high", "mid", "high", "low"],
                "return_next_3bars": [0.03, -0.02, 0.02, -0.03, 0.04, -0.01],
                "gap_environment_state": ["calm", "unstable", "calm", "unstable", "calm", "unstable"],
                "breakout_bar_close_location": [0.8, 0.2, 0.75, 0.3, 0.9, 0.25],
                "multi_bar_follow_through_3bars": [0.02, -0.01, 0.03, -0.02, 0.04, -0.01],
                "false_break_attempts_prebreak_band348": ["low", "high", "low", "high", "low", "high"],
                "session_timing_bucket": ["first_30m", "first_30m", "mid_session", "mid_session", "mid_session", "last_hour"],
                "vwap_response": ["vwap_hold", "vwap_reject", "vwap_hold", "vwap_reject", "vwap_hold", "vwap_reject"],
                "rejection_wick_ratio_band348": ["low", "high", "low", "high", "low", "high"],
            }
        )

    def test_regime_labels_are_deterministic(self) -> None:
        master = self._sample_master()
        thresholds = _regime_thresholds(master[master["current_split"] == "train"])
        labeled = _apply_regime_labels(master, thresholds)
        self.assertIn("volatility_state", labeled.columns)
        self.assertIn("macro_shock_state", labeled.columns)
        self.assertEqual(str(labeled.loc[0, "trend_state"]), "trend")

    def test_failure_types_assign_expected_flags(self) -> None:
        master = self._sample_master()
        thresholds = _regime_thresholds(master[master["current_split"] == "train"])
        labeled = _apply_regime_labels(master, thresholds)
        failed = _assign_failure_types(labeled)
        self.assertTrue(bool(failed.loc[1, "failure_immediate_rejection"]))
        self.assertTrue(bool(failed.loc[5, "failure_late_participation_trap"]))

    def test_shadow_readiness_and_decision_are_deterministic(self) -> None:
        scorecard = pd.DataFrame(
            [
                {"dimension": "regime_robustness", "score_0_to_3": 2},
                {"dimension": "time_robustness", "score_0_to_3": 2},
                {"dimension": "cost_robustness", "score_0_to_3": 2},
                {"dimension": "sector_robustness", "score_0_to_3": 2},
                {"dimension": "execution_robustness", "score_0_to_3": 2},
                {"dimension": "concentration_fragility", "score_0_to_3": 2},
                {"dimension": "decay_sensitivity", "score_0_to_3": 2},
            ]
        )
        failure_df = pd.DataFrame(
            [
                {"failure_type": "a", "trade_count": 3},
                {"failure_type": "b", "trade_count": 2},
                {"failure_type": "c", "trade_count": 1},
                {"failure_type": "d", "trade_count": 1},
            ]
        )
        viability_df = pd.DataFrame([{"shadow_monitor_suitability": "ready"}])
        shadow = _shadow_readiness(scorecard, failure_df, viability_df)
        attribution = pd.DataFrame([{"persistent_structure_share": 0.7, "temporary_phase_share": 0.3}])
        final_df = _final_decision(attribution, scorecard, shadow)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "TACTICAL_EDGE_SHADOW_READY")


if __name__ == "__main__":
    unittest.main()
