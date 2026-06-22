from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import (
    _available_features,
    _combine_binary_candidates,
    _derive_target,
    _diagnostic_overlay,
    _family_features,
    _production_candidate_selection,
    _target_design_comparison,
)


class TestAnalysisStructuralBreakoutBehaviorStateMonetization334(unittest.TestCase):
    def test_derive_target_maps_binary_targets_deterministically(self) -> None:
        df = pd.DataFrame(
            {
                "cluster_label": ["c1", "c2", "c3"],
                "cluster_label_base": ["dead_breakout", "clean_continuation", "weak_breakout"],
            }
        )
        bad = _derive_target(df, "bad_state").tolist()
        clean = _derive_target(df, "clean_state").tolist()
        multiclass = _derive_target(df, "multiclass").tolist()
        self.assertEqual(bad, [1, 0, 1])
        self.assertEqual(clean, [0, 1, 0])
        self.assertEqual(multiclass, ["c1", "c2", "c3"])

    def test_combine_binary_candidates_preserves_expanded_family_rows(self) -> None:
        ceiling_df = pd.DataFrame(
            [
                {"target": "bad_state", "model": "logistic", "feature_family": "core_feature_set", "accuracy": 0.4, "lift_vs_baseline": 0.02, "recall_positive": 0.1},
            ]
        )
        expanded_df = pd.DataFrame(
            [
                {"target": "bad_state", "model": "logistic", "feature_family": "market_structure", "accuracy": 0.5, "lift_vs_baseline": 0.05, "recall_positive": 0.3},
            ]
        )
        combined = _combine_binary_candidates(ceiling_df, expanded_df)
        self.assertEqual(len(combined), 2)
        self.assertIn("market_structure", set(combined["feature_family"].astype(str)))

    def test_target_design_comparison_chooses_highest_recall_then_lift(self) -> None:
        candidate_df = pd.DataFrame(
            [
                {"target": "bad_state", "feature_family": "core_feature_set", "model": "logistic", "accuracy": 0.40, "lift_vs_baseline": 0.01, "recall_positive": 0.10, "precision_positive": 0.50},
                {"target": "bad_state", "feature_family": "market_structure", "model": "logistic", "accuracy": 0.39, "lift_vs_baseline": 0.02, "recall_positive": 0.30, "precision_positive": 0.45},
                {"target": "clean_state", "feature_family": "crowding", "model": "band_probability", "accuracy": 0.36, "lift_vs_baseline": 0.03, "recall_positive": 0.25, "precision_positive": 0.40},
            ]
        )
        target_df = _target_design_comparison(candidate_df)
        bad_row = target_df[target_df["target"] == "bad_state"].iloc[0]
        self.assertEqual(str(bad_row["best_feature_family"]), "market_structure")

    def test_diagnostic_overlay_does_not_mutate_input_and_applies_multipliers(self) -> None:
        df = pd.DataFrame(
            [
                {"scope": "anchored_oos", "scenario": "s", "scenario_family": "f", "trade_id": "t1", "symbol": "AAPL", "sector_bucket": "tech", "entry_date": "2024-01-01", "realized_R": -1.0, "cluster_label": "dead_breakout", "cluster_label_base": "dead_breakout"},
                {"scope": "anchored_oos", "scenario": "s", "scenario_family": "f", "trade_id": "t2", "symbol": "MSFT", "sector_bucket": "tech", "entry_date": "2024-01-02", "realized_R": 2.0, "cluster_label": "clean_continuation", "cluster_label_base": "clean_continuation"},
                {"scope": "anchored_oos", "scenario": "s", "scenario_family": "f", "trade_id": "t3", "symbol": "NVDA", "sector_bucket": "semis", "entry_date": "2024-01-03", "realized_R": 1.0, "cluster_label": "weak_breakout", "cluster_label_base": "weak_breakout"},
            ]
        )
        original_cols = list(df.columns)
        metrics, delta_df = _diagnostic_overlay(df, np.asarray(["1", "0", "0"], dtype=object), np.asarray(["0", "1", "0"], dtype=object), "policy", "anchored_oos")
        self.assertEqual(list(df.columns), original_cols)
        self.assertAlmostEqual(float(metrics["saved_loss"]), 1.0, places=6)
        self.assertAlmostEqual(float(delta_df.loc[delta_df["trade_id"] == "t2", "diagnostic_multiplier"].iloc[0]), 1.25, places=6)

    def test_production_candidate_selection_returns_partial_edge_when_all_gates_pass(self) -> None:
        ceiling_df = pd.DataFrame(
            [
                {"target": "bad_state", "model": "logistic", "feature_family": "core_feature_set", "accuracy": 0.40, "lift_vs_baseline": 0.02, "recall_positive": 0.10},
            ]
        )
        expanded_df = pd.DataFrame(
            [
                {"target": "bad_state", "model": "logistic", "feature_family": "market_structure", "accuracy": 0.45, "lift_vs_baseline": 0.05, "recall_positive": 0.35},
            ]
        )
        holdout_df = pd.DataFrame([{"lift_vs_baseline": 0.02}])
        diagnostic_df = pd.DataFrame(
            [
                {"scope": "anchored_oos", "diagnostic_expectancy": -0.10, "baseline_expectancy": -0.20, "saved_loss": 3.0, "missed_gain": 1.0, "diagnostic_return_proxy": 95.0, "baseline_return_proxy": 90.0},
                {"scope": "full_period", "diagnostic_expectancy": 0.60, "baseline_expectancy": 0.55, "saved_loss": 10.0, "missed_gain": 8.0, "diagnostic_return_proxy": 96.0, "baseline_return_proxy": 100.0},
            ]
        )
        result = _production_candidate_selection(pd.DataFrame(), ceiling_df, expanded_df, holdout_df, diagnostic_df)
        self.assertEqual(str(result.iloc[0]["decision"]), "PARTIAL_EDGE")

    def test_family_features_exposes_expected_market_structure_members(self) -> None:
        features = _family_features("market_structure")
        self.assertIn("breadth_above_sma20", features)
        self.assertIn("ret_20d_pre", features)

    def test_available_features_deduplicates_overlapping_columns(self) -> None:
        df = pd.DataFrame({"a": [1], "b": [2]})
        features = _available_features(df, ["a", "b", "a", "c"])
        self.assertEqual(features, ["a", "b"])


if __name__ == "__main__":
    unittest.main()
