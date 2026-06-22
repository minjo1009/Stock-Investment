from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_regime_failure_diagnosis_328 import (
    _failure_mode_attribution,
    _linkage_diagnosis,
    _regime_drift,
    _regime_internal_heterogeneity,
    _total_variation_distance,
)


class TestAnalysisStructuralBreakoutRegimeFailureDiagnosis328(unittest.TestCase):
    def test_total_variation_distance_is_deterministic(self) -> None:
        lhs = {"a": 0.7, "b": 0.3}
        rhs = {"a": 0.2, "b": 0.8}
        self.assertAlmostEqual(_total_variation_distance(lhs, rhs), 0.5)

    def test_regime_internal_heterogeneity_reports_expected_columns(self) -> None:
        df = pd.DataFrame(
            [
                {"regime_state": "r1", "entry_archetype": "a1", "path_type": "early_failure", "realized_R": -1.0, "follow_through_5d_pct": 0.01, "retrace_5d_pct": 0.20},
                {"regime_state": "r1", "entry_archetype": "a2", "path_type": "strong_continuation", "realized_R": 1.2, "follow_through_5d_pct": 0.15, "retrace_5d_pct": 0.03},
                {"regime_state": "r2", "entry_archetype": "a1", "path_type": "early_failure", "realized_R": -0.6, "follow_through_5d_pct": 0.02, "retrace_5d_pct": 0.18},
                {"regime_state": "r2", "entry_archetype": "a1", "path_type": "early_failure", "realized_R": -0.5, "follow_through_5d_pct": 0.03, "retrace_5d_pct": 0.17},
            ]
        )
        result = _regime_internal_heterogeneity(df, "train")
        self.assertIn("heterogeneity_diagnosis", result.columns)
        self.assertEqual(set(result["regime_state"]), {"r1", "r2"})

    def test_failure_mode_attribution_prefers_low_follow_through_when_oos_collapses(self) -> None:
        train_df = pd.DataFrame(
            [
                {"regime_state": "r1", "entry_archetype": "a1", "path_type": "strong_continuation", "realized_R": 1.0, "follow_through_5d_pct": 0.15, "retrace_5d_pct": 0.04, "mae_5d_pct": 0.02},
                {"regime_state": "r1", "entry_archetype": "a1", "path_type": "strong_continuation", "realized_R": 0.8, "follow_through_5d_pct": 0.14, "retrace_5d_pct": 0.05, "mae_5d_pct": 0.02},
            ]
        )
        oos_df = pd.DataFrame(
            [
                {"regime_state": "r1", "entry_archetype": "a1", "path_type": "early_failure", "realized_R": -1.0, "follow_through_5d_pct": 0.01, "retrace_5d_pct": 0.05, "mae_5d_pct": 0.02},
                {"regime_state": "r1", "entry_archetype": "a1", "path_type": "early_failure", "realized_R": -0.8, "follow_through_5d_pct": 0.02, "retrace_5d_pct": 0.06, "mae_5d_pct": 0.02},
            ]
        )
        result = _failure_mode_attribution(train_df, oos_df)
        self.assertEqual(result.iloc[0]["failure_driver"], "low_follow_through")

    def test_regime_drift_detects_entry_linkage_drift(self) -> None:
        train_df = pd.DataFrame(
            [
                {"regime_state": "r1", "path_type": "early_failure", "entry_archetype": "a1", "realized_R": -0.5, "rs_percentile_20d_band": "low", "sector_breadth_band": "low", "dist_to_sma200_pct_band": "low", "ret_20d_pre_band": "low", "vol_contraction_ratio_band": "low", "breakout_strength_pct_band": "low"},
                {"regime_state": "r1", "path_type": "early_failure", "entry_archetype": "a1", "realized_R": -0.4, "rs_percentile_20d_band": "low", "sector_breadth_band": "low", "dist_to_sma200_pct_band": "low", "ret_20d_pre_band": "low", "vol_contraction_ratio_band": "low", "breakout_strength_pct_band": "low"},
            ]
        )
        oos_df = pd.DataFrame(
            [
                {"regime_state": "r1", "path_type": "strong_continuation", "entry_archetype": "a2", "realized_R": 0.8, "rs_percentile_20d_band": "high", "sector_breadth_band": "high", "dist_to_sma200_pct_band": "high", "ret_20d_pre_band": "high", "vol_contraction_ratio_band": "high", "breakout_strength_pct_band": "high"},
                {"regime_state": "r1", "path_type": "strong_continuation", "entry_archetype": "a2", "realized_R": 0.9, "rs_percentile_20d_band": "high", "sector_breadth_band": "high", "dist_to_sma200_pct_band": "high", "ret_20d_pre_band": "high", "vol_contraction_ratio_band": "high", "breakout_strength_pct_band": "high"},
            ]
        )
        result = _regime_drift(train_df, oos_df)
        self.assertIn(result.iloc[0]["drift_type"], {"entry_linkage_drift", "mixed_drift"})

    def test_linkage_diagnosis_maps_synthetic_rows(self) -> None:
        train_sep = pd.DataFrame([{"regime_state": "r1", "expectancy_r": 0.8, "global_baseline_gap_r": 0.5, "path_mix_entropy": 0.3}])
        oos_sep = pd.DataFrame([{"regime_state": "r1", "expectancy_r": 0.5, "global_baseline_gap_r": 0.2, "path_mix_entropy": 0.4}])
        heterogeneity = pd.DataFrame([{"scope": "train", "regime_state": "r1", "heterogeneity_score": 0.2, "heterogeneity_diagnosis": "low"}])
        archetype = pd.DataFrame([{"scope": "train", "regime_state": "r1", "dominant_archetype_share": 0.3}])
        drift = pd.DataFrame([{"regime_state": "r1", "path_mix_shift": 0.1, "trade_share_delta": 0.01}])
        result = _linkage_diagnosis(train_sep, oos_sep, heterogeneity, archetype, drift)
        self.assertEqual(result.iloc[0]["diagnosis"], "strong_and_stable")


if __name__ == "__main__":
    unittest.main()
