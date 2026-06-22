from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_intraday_evaluation_fix_338 import (
    ENTRY_ONLY,
    _evaluate_subset_corrected,
    _missing_reason,
    _split_coverage_summary,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import _evaluate_subset as _evaluate_subset_336


class TestAnalysisStructuralBreakoutIntradayEvaluationFix338(unittest.TestCase):
    def test_missing_reason_maps_insufficient_window(self) -> None:
        self.assertEqual(_missing_reason("covered"), "")
        self.assertEqual(_missing_reason("missing_date"), "missing_date")
        self.assertEqual(_missing_reason("insufficient_window"), "incomplete_intraday_window")

    def test_split_coverage_summary_is_deterministic(self) -> None:
        coverage_df = pd.DataFrame(
            [
                {"split": "train", "is_covered": True},
                {"split": "train", "is_covered": False},
                {"split": "anchored_oos", "is_covered": True},
                {"split": "full_period", "is_covered": True},
                {"split": "full_period", "is_covered": True},
            ]
        )
        summary = _split_coverage_summary(coverage_df)
        self.assertEqual(int(summary.loc[summary["split"] == "train", "covered_trades"].iloc[0]), 1)
        self.assertEqual(int(summary.loc[summary["split"] == "anchored_oos", "covered_trades"].iloc[0]), 1)
        self.assertEqual(int(summary.loc[summary["split"] == "full_period", "covered_trades"].iloc[0]), 2)

    def test_evaluate_subset_marks_insufficient_sample_below_threshold(self) -> None:
        train_df = pd.DataFrame(
            {
                "scope": ["train"] * 2,
                "cluster_label_base": ["clean_continuation", "dead_breakout"],
                "ret_20d_pre": [0.1, -0.2],
                "realized_R": [1.0, -1.0],
            }
        )
        eval_df = pd.DataFrame(
            {
                "scope": ["anchored_oos"] * 1,
                "cluster_label_base": ["dead_breakout"],
                "ret_20d_pre": [-0.1],
                "realized_R": [-0.5],
            }
        )
        row = _evaluate_subset_corrected(
            train_df=train_df,
            eval_df=eval_df,
            split_name="anchored_oos",
            target_name="bad_state",
            feature_set="core_only",
            window_mode=ENTRY_ONLY,
            model_name="majority",
            total_split_trades=5,
            min_trades_per_split=2,
        )
        self.assertEqual(str(row["status"]), "insufficient_sample")

    def test_corrected_metrics_match_task336_on_same_subset(self) -> None:
        train_df = pd.DataFrame(
            {
                "scope": ["train"] * 4,
                "cluster_label_base": [
                    "clean_continuation",
                    "dead_breakout",
                    "clean_continuation",
                    "dead_breakout",
                ],
                "ret_20d_pre": [0.2, -0.2, 0.3, -0.1],
                "realized_R": [1.2, -0.8, 1.0, -0.6],
            }
        )
        eval_df = pd.DataFrame(
            {
                "scope": ["anchored_oos"] * 2,
                "cluster_label_base": ["clean_continuation", "dead_breakout"],
                "ret_20d_pre": [0.25, -0.15],
                "realized_R": [0.9, -0.4],
            }
        )
        old_row = _evaluate_subset_336(train_df, eval_df, "bad_state", "core_only", ENTRY_ONLY, "majority")
        new_row = _evaluate_subset_corrected(
            train_df=train_df,
            eval_df=eval_df,
            split_name="anchored_oos",
            target_name="bad_state",
            feature_set="core_only",
            window_mode=ENTRY_ONLY,
            model_name="majority",
            total_split_trades=2,
            min_trades_per_split=1,
        )
        self.assertEqual(float(old_row["accuracy"]), float(new_row["accuracy"]))
        self.assertEqual(float(old_row["lift_vs_baseline"]), float(new_row["lift_vs_baseline"]))
        self.assertEqual(str(new_row["status"]), "ok")


if __name__ == "__main__":
    unittest.main()
