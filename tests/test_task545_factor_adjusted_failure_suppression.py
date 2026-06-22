from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task545_factor_adjusted_failure_suppression import (
    build_failure_masks,
    build_suppression_rules,
)


class Task545FailureSuppressionTest(unittest.TestCase):
    def test_failure_masks_use_entry_safe_fields(self) -> None:
        frame = pd.DataFrame(
            {
                "timing_state": ["opening_drive", "midday_continuation"],
                "intraday_entry_state_v4": ["intraday_breakout_acceptance", "other"],
                "symbol_multiday_setup_state": ["volume_confirmed_reclaim", "trend_persistence_near_high"],
                "theme_regime_state_v4": ["narrow_theme_leader", "persistent_theme_leader"],
                "entry_close_pos_in_bar": [0.95, 0.7],
                "entry_close_vs_vwap": [0.001, 0.01],
                "theme_breadth20_prev": [0.5, 0.9],
                "volume_ratio_prev": [2.5, 1.0],
                "range_pos": [0.95, 0.8],
                "exit_reason": ["trailing_stop_exit", "time_exit"],
                "factor_adjusted_residual_pct": [-20.0, 10.0],
            }
        )
        masks = build_failure_masks(frame)
        self.assertTrue(bool(masks["opening_high_close_low_vwap"].iloc[0]))
        self.assertTrue(bool(masks["volume_reclaim_weak_theme"].iloc[0]))

    def test_suppression_rule_removes_detected_failure_state(self) -> None:
        frame = pd.DataFrame(
            {
                "timing_state": ["opening_drive", "midday_continuation"],
                "intraday_entry_state_v4": ["intraday_breakout_acceptance", "other"],
                "symbol_multiday_setup_state": ["volume_confirmed_reclaim", "trend_persistence_near_high"],
                "theme_regime_state_v4": ["narrow_theme_leader", "persistent_theme_leader"],
                "entry_close_pos_in_bar": [0.95, 0.7],
                "entry_close_vs_vwap": [0.001, 0.01],
                "theme_breadth20_prev": [0.5, 0.9],
                "volume_ratio_prev": [2.5, 1.0],
                "range_pos": [0.95, 0.8],
            }
        )
        rules = build_suppression_rules(frame)
        self.assertFalse(bool(rules["combined_failure_suppression_v1"].iloc[0]))
        self.assertTrue(bool(rules["combined_failure_suppression_v1"].iloc[1]))


if __name__ == "__main__":
    unittest.main()
