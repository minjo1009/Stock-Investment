from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_state_model_redesign_329 import (
    _apply_proposed_state,
    _attach_axis_states,
    _build_state_fold_map,
    _framework_comparison,
    _state_model_decision,
)


class TestAnalysisStructuralBreakoutStateModelRedesign329(unittest.TestCase):
    def test_axis_assignment_is_deterministic(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "ret_20d_pre_band": "high",
                    "dist_to_sma200_pct_band": "high",
                    "breakout_strength_pct_band": "high",
                    "sector_breadth_band": "high",
                    "vol_contraction_ratio_band": "low",
                    "regime_state": "late_extension",
                }
            ]
        )
        result = _attach_axis_states(df)
        row = result.iloc[0]
        self.assertEqual(row["trend_quality_state"], "strong")
        self.assertEqual(row["extension_pressure_state"], "high")
        self.assertEqual(row["participation_quality_state"], "broad")
        self.assertEqual(row["noise_pressure_state"], "compressed")

    def test_small_count_state_folds_to_parent(self) -> None:
        df = pd.DataFrame(
            [
                {"trend_quality_state": "strong", "extension_pressure_state": "high", "participation_quality_state": "broad"},
            ] * 30
            + [
                {"trend_quality_state": "strong", "extension_pressure_state": "high", "participation_quality_state": "mixed"},
            ] * 5
        )
        selected_axes = ["trend_quality", "extension_pressure", "participation_quality"]
        fold_map = _build_state_fold_map(df, selected_axes)
        rare_state = "trend_quality:strong|extension_pressure:high|participation_quality:mixed"
        self.assertNotEqual(fold_map[rare_state], rare_state)

    def test_framework_comparison_reports_expected_frameworks(self) -> None:
        train_df = pd.DataFrame(
            [
                {"regime_state": "r1", "proposed_state_model": "s1", "realized_R": 1.0, "path_type": "strong_continuation", "entry_archetype": "a1"},
                {"regime_state": "r2", "proposed_state_model": "s2", "realized_R": -1.0, "path_type": "early_failure", "entry_archetype": "a2"},
            ]
        )
        oos_df = pd.DataFrame(
            [
                {"regime_state": "r1", "proposed_state_model": "s1", "realized_R": 0.8, "path_type": "strong_continuation", "entry_archetype": "a1"},
                {"regime_state": "r2", "proposed_state_model": "s2", "realized_R": -0.5, "path_type": "early_failure", "entry_archetype": "a2"},
            ]
        )
        result = _framework_comparison(train_df, oos_df, train_df, oos_df)
        self.assertEqual(set(result["framework"]), {"old_regime", "new_state_model"})

    def test_decision_rule_maps_improvement_count(self) -> None:
        comparison_df = pd.DataFrame(
            [
                {
                    "framework": "old_regime",
                    "between_state_expectancy_dispersion": 0.10,
                    "within_state_realized_r_variance_mean": 0.50,
                    "within_state_path_entropy_mean": 1.20,
                    "oos_linkage_retention": 0.20,
                    "drift_sensitivity": 0.60,
                },
                {
                    "framework": "new_state_model",
                    "between_state_expectancy_dispersion": 0.25,
                    "within_state_realized_r_variance_mean": 0.30,
                    "within_state_path_entropy_mean": 0.80,
                    "oos_linkage_retention": 0.40,
                    "drift_sensitivity": 0.30,
                },
            ]
        )
        result = _state_model_decision(comparison_df, ["trend_quality", "extension_pressure", "participation_quality"])
        self.assertEqual(result.iloc[0]["decision"], "fully_replaced")


if __name__ == "__main__":
    unittest.main()
