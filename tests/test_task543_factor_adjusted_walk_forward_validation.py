from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task543_factor_adjusted_walk_forward_validation import (
    build_walk_forward_stability,
    summarize_group,
)


class Task543FactorAdjustedWalkForwardTest(unittest.TestCase):
    def test_positive_oos_is_underpowered_when_counts_small(self) -> None:
        rows = []
        for split, n in [("validation", 10), ("recent_oos", 5), ("train_design", 30)]:
            for i in range(n):
                rows.append(
                    {
                        "candidate_set": "A",
                        "split_name": split,
                        "quarter": "2024Q1",
                        "return_pct": 1.0,
                        "win_flag": 1,
                        "factor_adjustment_available_flag": 1,
                        "factor_adjusted_residual_pct": 2.0,
                        "entry_reduce_failure_flag": 0,
                        "add_scale_success_flag": 1,
                    }
                )
        split_quality = summarize_group(pd.DataFrame(rows), ["candidate_set", "split_name"], "split")
        stability = build_walk_forward_stability(split_quality)
        self.assertEqual(stability.iloc[0]["walk_forward_status"], "positive_but_underpowered")
        self.assertEqual(int(stability.iloc[0]["oos_sample_adequate_flag"]), 0)

    def test_oos_survives_when_validation_and_recent_have_enough_positive_residuals(self) -> None:
        rows = []
        for split in ["validation", "recent_oos", "train_design"]:
            for i in range(22):
                rows.append(
                    {
                        "candidate_set": "A",
                        "split_name": split,
                        "quarter": "2024Q1",
                        "return_pct": 1.0,
                        "win_flag": 1,
                        "factor_adjustment_available_flag": 1,
                        "factor_adjusted_residual_pct": 2.0,
                        "entry_reduce_failure_flag": 0,
                        "add_scale_success_flag": 1,
                    }
                )
        split_quality = summarize_group(pd.DataFrame(rows), ["candidate_set", "split_name"], "split")
        stability = build_walk_forward_stability(split_quality)
        self.assertEqual(stability.iloc[0]["walk_forward_status"], "factor_adjusted_oos_survives")
        self.assertEqual(int(stability.iloc[0]["oos_sample_adequate_flag"]), 1)


if __name__ == "__main__":
    unittest.main()
