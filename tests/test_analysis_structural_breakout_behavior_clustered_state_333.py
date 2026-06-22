from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_clustered_state_333 import (
    BEHAVIOR_CLUSTER_FEATURES,
    PRE_ENTRY_PREDICTOR_FEATURES,
    _diagnostic_action_test,
    _fit_behavior_scaler,
    _label_cluster_rows,
    _majority_baseline,
    _probability_metrics,
    _select_best_cluster_candidate,
    _transform_behavior_features,
)


class TestAnalysisStructuralBreakoutBehaviorClusteredState333(unittest.TestCase):
    def _behavior_frame(self) -> pd.DataFrame:
        rows = []
        for idx in range(6):
            rows.append(
                {
                    "follow_through_3d_pct": 0.01 * idx,
                    "follow_through_5d_pct": 0.02 * idx,
                    "retrace_3d_pct": 0.03 * idx,
                    "retrace_5d_pct": 0.04 * idx,
                    "mae_3d_pct": 0.05 * idx,
                    "mae_5d_pct": 0.06 * idx,
                    "mfe_3d_pct": 0.07 * idx,
                    "mfe_5d_pct": 0.08 * idx,
                    "realized_R": float(idx - 2),
                    "holding_days": float(5 + idx),
                }
            )
        return pd.DataFrame(rows)

    def test_behavior_feature_standardization_uses_train_only(self) -> None:
        train_df = self._behavior_frame().iloc[:3].copy()
        oos_df = self._behavior_frame().iloc[3:].copy()
        scaler = _fit_behavior_scaler(train_df)
        expected_mean = train_df[BEHAVIOR_CLUSTER_FEATURES].astype(float).mean().to_numpy()
        np.testing.assert_allclose(scaler.mean_, expected_mean)
        before_mean = scaler.mean_.copy()
        _transform_behavior_features(oos_df, scaler)
        np.testing.assert_allclose(scaler.mean_, before_mean)

    def test_clustering_model_selection_is_deterministic(self) -> None:
        candidate_df = pd.DataFrame(
            [
                {"method": "kmeans", "k": 4, "oos_linkage_retention": 0.1, "between_cluster_expectancy_dispersion": 0.3, "within_cluster_behavior_variance": 1.0, "path_entropy": 1.1, "min_train_cluster_count": 50, "oos_cluster_assignment_stability": 0.8, "sparsity_risk": 0.2},
                {"method": "agglomerative", "k": 5, "oos_linkage_retention": 0.2, "between_cluster_expectancy_dispersion": 0.25, "within_cluster_behavior_variance": 1.1, "path_entropy": 1.2, "min_train_cluster_count": 40, "oos_cluster_assignment_stability": 0.7, "sparsity_risk": 0.3},
            ]
        )
        first = _select_best_cluster_candidate(candidate_df)
        second = _select_best_cluster_candidate(candidate_df)
        self.assertEqual(first["method"], second["method"])
        self.assertEqual(first["k"], second["k"])

    def test_cluster_label_assignment_is_deterministic(self) -> None:
        diag_df = pd.DataFrame(
            [
                {"behavior_cluster_id": 0, "avg_follow_through_3d": 0.01, "avg_follow_through_5d": 0.20, "avg_retrace_5d": 0.01, "avg_MAE": 0.01, "avg_MFE": 0.30, "avg_holding_days": 10, "expectancy_R": 1.0},
                {"behavior_cluster_id": 1, "avg_follow_through_3d": 0.00, "avg_follow_through_5d": 0.01, "avg_retrace_5d": 0.50, "avg_MAE": 0.50, "avg_MFE": 0.01, "avg_holding_days": 4, "expectancy_R": -1.0},
            ]
        )
        first = _label_cluster_rows(diag_df)
        second = _label_cluster_rows(diag_df)
        self.assertTrue(first.equals(second))

    def test_prediction_metrics_include_majority_baseline(self) -> None:
        y_true = pd.Series(["a", "a", "b", "a"])
        y_pred = np.asarray(["a", "a", "a", "a"], dtype=object)
        probs = [{"a": 1.0, "b": 0.0} for _ in range(4)]
        label_bases = pd.Series(["clean_continuation", "clean_continuation", "early_failure", "clean_continuation"])
        row, _ = _probability_metrics(y_true, y_pred, probs, label_bases, "majority_baseline", "train")
        self.assertIn("majority_baseline_accuracy", row)

    def test_no_pre_entry_feature_is_used_in_clustering(self) -> None:
        self.assertTrue(set(BEHAVIOR_CLUSTER_FEATURES).isdisjoint(set(PRE_ENTRY_PREDICTOR_FEATURES)))

    def test_diagnostic_action_test_does_not_mutate_input(self) -> None:
        df = pd.DataFrame(
            [
                {"scope": "anchored_oos", "scenario": "s", "scenario_family": "f", "trade_id": "t1", "symbol": "AAPL", "entry_date": "2024-01-01", "realized_R": -1.0},
                {"scope": "anchored_oos", "scenario": "s", "scenario_family": "f", "trade_id": "t2", "symbol": "MSFT", "entry_date": "2024-01-02", "realized_R": 1.0},
            ]
        )
        original_cols = list(df.columns)
        y_pred = np.asarray(["early_failure", "clean_continuation"], dtype=object)
        label_lookup = {"early_failure": "early_failure", "clean_continuation": "clean_continuation"}
        _, delta_df = _diagnostic_action_test(df, y_pred, label_lookup, "m", "anchored_oos")
        self.assertEqual(list(df.columns), original_cols)
        self.assertIn("diagnostic_adjusted_R", delta_df.columns)

    def test_majority_baseline_is_deterministic(self) -> None:
        train_y = pd.Series(["a", "a", "b"])
        df = pd.DataFrame({"x": [1, 2]})
        preds1, _ = _majority_baseline(train_y, df)
        preds2, _ = _majority_baseline(train_y, df)
        self.assertTrue((preds1 == preds2).all())


if __name__ == "__main__":
    unittest.main()
