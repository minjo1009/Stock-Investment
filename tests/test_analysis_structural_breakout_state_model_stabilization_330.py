from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_state_model_stabilization_330 import (
    _build_generic_fold_map,
    _decision_row,
    _strong_trend_subtype,
    _vulnerable_state_buckets,
)


class TestAnalysisStructuralBreakoutStateModelStabilization330(unittest.TestCase):
    def test_strong_trend_subtype_is_deterministic(self) -> None:
        row = pd.Series(
            {
                "trend_quality_state": "strong",
                "extension_pressure_state": "high",
                "participation_quality_state": "mixed",
                "ret_20d_pre_band": "high",
                "breakout_strength_pct_band": "high",
            }
        )
        self.assertEqual(_strong_trend_subtype(row), "crowded_continuation")

    def test_generic_fold_map_folds_suffix_to_parent(self) -> None:
        raw = pd.Series(
            [
                "base|noise:compressed",
            ]
            * 30
            + [
                "base|noise:high_noise",
            ]
            * 5
        )
        mapping = _build_generic_fold_map(raw, min_count=25)
        self.assertEqual(mapping["base|noise:compressed"], "base|noise:compressed")
        self.assertEqual(mapping["base|noise:high_noise"], "base")

    def test_vulnerable_buckets_rank_most_damaging_state_first(self) -> None:
        df = pd.DataFrame(
            [
                {"proposed_state_model": "s1", "oos_trade_count": 10, "oos_expectancy_r": -1.0, "expectancy_delta": -1.0, "path_mix_shift": 0.3},
                {"proposed_state_model": "s2", "oos_trade_count": 3, "oos_expectancy_r": -0.2, "expectancy_delta": -0.1, "path_mix_shift": 0.5},
            ]
        )
        result = _vulnerable_state_buckets(df)
        self.assertEqual(result.iloc[0]["proposed_state_model"], "s1")

    def test_decision_prefers_incremental_refinement_when_best_candidate_improves(self) -> None:
        comparison_df = pd.DataFrame(
            [
                {
                    "candidate": "current_task_329",
                    "oos_linkage_retention": -0.50,
                    "within_state_path_entropy_mean": 1.50,
                    "sparsity_risk": 0.40,
                },
                {
                    "candidate": "candidate_A",
                    "oos_linkage_retention": -0.10,
                    "within_state_path_entropy_mean": 1.20,
                    "sparsity_risk": 0.45,
                },
                {
                    "candidate": "candidate_B",
                    "oos_linkage_retention": -0.30,
                    "within_state_path_entropy_mean": 1.30,
                    "sparsity_risk": 0.35,
                },
            ]
        )
        result = _decision_row(comparison_df)
        self.assertEqual(result.iloc[0]["decision"], "refine_current_state_model_incrementally")


if __name__ == "__main__":
    unittest.main()
