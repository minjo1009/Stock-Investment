from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_alpha_family_viability_350 import (
    _add_universe_environment_labels,
    _assign_failure_classes,
    _filter_actions,
    _final_decision,
)


class TestAnalysisStructuralBreakoutAlphaFamilyViability350(unittest.TestCase):
    def _sample_master(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "trade_id": ["a", "b", "c", "d", "e", "f"],
                "current_split": ["train", "train", "train", "anchored_oos", "anchored_oos", "anchored_oos"],
                "entry_ts": pd.to_datetime(
                    [
                        "2024-01-02T14:35:00Z",
                        "2024-01-02T19:10:00Z",
                        "2024-01-03T15:20:00Z",
                        "2025-01-06T14:35:00Z",
                        "2025-01-06T20:05:00Z",
                        "2025-01-07T17:00:00Z",
                    ],
                    utc=True,
                ),
                "exit_ts": pd.to_datetime(
                    [
                        "2024-01-05T14:35:00Z",
                        "2024-01-06T19:10:00Z",
                        "2024-01-08T15:20:00Z",
                        "2025-01-10T14:35:00Z",
                        "2025-01-10T20:05:00Z",
                        "2025-01-10T17:00:00Z",
                    ],
                    utc=True,
                ),
                "realized_R": [1.2, -1.4, -0.6, -0.9, -1.1, 0.4],
                "sector_group": ["software_internet", "software_internet", "semis", "software_internet", "others", "others"],
                "cluster_label_base": ["clean_continuation", "failed_pop", "dead_breakout", "failed_pop", "dead_breakout", "clean_continuation"],
                "range_width_10_pre": [0.04, 0.05, 0.02, 0.06, 0.03, 0.01],
                "ret_20d_pre": [0.12, 0.1, -0.03, 0.09, -0.01, 0.02],
                "ret_10d_pre": [0.08, 0.07, -0.01, 0.06, -0.02, 0.01],
                "dist_to_sma20_pct": [0.05, 0.02, -0.01, 0.03, -0.02, 0.01],
                "breadth_above_sma20": [0.7, 0.68, 0.3, 0.32, 0.4, 0.6],
                "breadth_above_sma50": [0.71, 0.69, 0.35, 0.34, 0.42, 0.62],
                "breadth_positive_20d": [0.72, 0.66, 0.38, 0.31, 0.43, 0.61],
                "top_sector_dominance_score": [0.75, 0.78, 0.4, 0.8, 0.45, 0.5],
                "tech_concentration_ratio": [0.8, 0.76, 0.3, 0.78, 0.35, 0.4],
                "semis_concentration_ratio": [0.2, 0.22, 0.5, 0.24, 0.4, 0.45],
                "dollar_volume_pre": [4e7, 5e7, 2e7, 4.5e7, 2.5e7, 3e7],
                "turnover_pre": [1.4, 1.5, 0.7, 1.3, 0.8, 0.9],
                "vol_contraction_ratio": [1.3, 1.4, 0.8, 1.2, 0.9, 1.0],
                "dispersion_20d": [0.45, 0.5, 0.2, 0.35, 0.3, 0.25],
                "mean_pairwise_corr": [0.65, 0.7, 0.32, 0.5, 0.4, 0.35],
                "gap_over_planned_entry_pct": [0.01, 0.05, 0.02, 0.03, 0.04, 0.01],
                "sector_rs_percentile": [0.85, 0.82, 0.45, 0.8, 0.55, 0.5],
                "sector_crowding_high": [1, 1, 0, 1, 0, 0],
                "recent_failed_breakouts_20d": [2, 5, 1, 4, 2, 1],
                "breakout_strength_pct": [0.06, 0.03, 0.02, 0.04, 0.02, 0.03],
                "window_mode": ["entry_only", "entry_only", "entry_only", "entry_only", None, None],
                "covered_execution_available": [True, True, True, True, False, False],
                "session_timing_bucket": ["mid_session", "first_30m", "mid_session", "last_hour", "mid_session", "mid_session"],
                "breakout_response": ["breakout_hold", "immediate_failure", "immediate_failure", "immediate_failure", "", ""],
                "breakout_hold_duration_bars": [3, 0, 0, 0, None, None],
                "volume_persistence_3bars_band348": ["high", "low", "low", "low", None, None],
                "return_next_3bars": [0.02, -0.03, -0.01, -0.02, None, None],
                "return_next_5bars": [0.03, -0.05, -0.02, -0.03, None, None],
                "breakout_bar_close_location": [0.8, 0.2, 0.45, 0.3, None, None],
                "multi_bar_follow_through_3bars": [0.03, -0.02, -0.01, -0.01, None, None],
                "false_break_attempts_prebreak_band348": ["low", "high", "high", "low", None, None],
                "failed_break_count_prebreak": [1, 3, 4, 2, None, None],
                "execution_quality_bucket": ["strong", "weak", "mixed", "weak", None, None],
                "is_base_subset": [True, True, False, True, False, False],
                "symbol": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
            }
        )

    def test_environment_labels_are_added_deterministically(self) -> None:
        labeled = _add_universe_environment_labels(self._sample_master())
        self.assertIn("crowding_state", labeled.columns)
        self.assertIn("post_risk_off_state", labeled.columns)
        self.assertEqual(str(labeled.loc[0, "volatility_state"]), "low_vol")
        self.assertEqual(str(labeled.loc[1, "crowding_state"]), "crowded")

    def test_failure_class_assignment_handles_covered_and_uncovered(self) -> None:
        labeled = _add_universe_environment_labels(self._sample_master())
        failed = _assign_failure_classes(labeled)
        self.assertEqual(str(failed.loc[1, "primary_failure_class"]), "crowded_continuation_failure")
        self.assertEqual(str(failed.loc[3, "primary_failure_class"]), "crowded_continuation_failure")
        self.assertEqual(str(failed.loc[4, "primary_failure_class"]), "weak_breadth_continuation")

    def test_dynamic_filter_and_final_decision_are_deterministic(self) -> None:
        labeled = _add_universe_environment_labels(self._sample_master())
        failed = _assign_failure_classes(labeled)
        actions = _filter_actions(failed, "dynamic_participation_suppression")
        self.assertEqual(str(actions.loc[1]), "suppress")
        self.assertIn(str(actions.loc[4]), {"keep", "reduce", "suppress"})

        cross_df = pd.DataFrame(
            [
                {"environment_axis": "sector_group", "positive_bucket_share": 0.3, "positive_window_share": 0.2},
                {"environment_axis": "crowding_state", "positive_bucket_share": 0.2, "positive_window_share": 0.1},
            ]
        )
        identity_df = pd.DataFrame(
            [
                {"identity_type": "participation_suppressor", "score": 0.9},
                {"identity_type": "crowding_avoidance_mechanism", "score": 0.8},
            ]
        )
        suppression_df = pd.DataFrame(
            [
                {"approach": "dynamic_participation_suppression", "expectancy_improvement": 0.12, "mdd_relief": 5.0, "total_loss_avoided": 3.0},
                {"approach": "adaptive_intraday_suppression", "expectancy_improvement": 0.08, "mdd_relief": 4.0, "total_loss_avoided": 2.0},
            ]
        )
        viability_df = pd.DataFrame(
            [
                {"environment_axis": "sector_group", "expectancy": -0.1},
                {"environment_axis": "crowding_state", "expectancy": 0.05},
                {"environment_axis": "macro_shock_state", "expectancy": -0.02},
            ]
        )
        final_df = _final_decision(cross_df, identity_df, suppression_df, viability_df)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "FAILURE_SUPPRESSION_ALPHA")


if __name__ == "__main__":
    unittest.main()
