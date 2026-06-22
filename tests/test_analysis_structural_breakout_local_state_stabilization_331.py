from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_local_state_stabilization_331 import (
    _best_split_plan,
    _decision_df,
    _merge_sparse_states,
    _vulnerable_bucket_split_analysis,
)


class TestAnalysisStructuralBreakoutLocalStateStabilization331(unittest.TestCase):
    def test_best_split_plan_picks_highest_score_per_target(self) -> None:
        df = pd.DataFrame(
            [
                {"target_state": "s1", "split_condition": "noise_pressure_state", "split_score": 1.0, "after_retention": 0.2},
                {"target_state": "s1", "split_condition": "ret_20d_pre_band", "split_score": 0.5, "after_retention": 0.3},
                {"target_state": "s2", "split_condition": "strong_trend_subtype", "split_score": 0.8, "after_retention": 0.1},
            ]
        )
        result = _best_split_plan(df)
        self.assertEqual(result["s1"], "noise_pressure_state")
        self.assertEqual(result["s2"], "strong_trend_subtype")

    def test_merge_sparse_states_maps_marked_children_to_parent(self) -> None:
        df = pd.DataFrame(
            [
                {"proposed_state_model": "base|local:a"},
                {"proposed_state_model": "base|local:b"},
                {"proposed_state_model": "base"},
            ]
        )
        sparse_df = pd.DataFrame(
            [
                {"state": "base|local:a", "merge_candidate": "base", "merge_justification": "merge"},
                {"state": "base|local:b", "merge_candidate": "base", "merge_justification": "keep_if_structurally_distinct"},
            ]
        )
        result = _merge_sparse_states(df, sparse_df)
        self.assertEqual(result.iloc[0]["proposed_state_model"], "base")
        self.assertEqual(result.iloc[1]["proposed_state_model"], "base|local:b")

    def test_decision_applies_local_stabilization_when_metrics_improve(self) -> None:
        comparison_df = pd.DataFrame(
            [
                {"candidate": "current_task_329", "oos_linkage_retention": -0.4, "vulnerable_bucket_concentration": 0.8, "sparsity_risk": 0.6, "within_state_path_entropy_mean": 1.5},
                {"candidate": "local_A", "oos_linkage_retention": 0.1, "vulnerable_bucket_concentration": 0.7, "sparsity_risk": 0.65, "within_state_path_entropy_mean": 1.4},
            ]
        )
        result = _decision_df(comparison_df)
        self.assertEqual(result.iloc[0]["decision"], "apply_limited_local_stabilization")


if __name__ == "__main__":
    unittest.main()
