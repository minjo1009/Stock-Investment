from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task544_sample_expansion_quarter_failure import (
    build_expansion_masks,
    decompose_failure_quarters,
)


class Task544SampleExpansionFailureTest(unittest.TestCase):
    def test_expansion_masks_use_entry_safe_states(self) -> None:
        frame = pd.DataFrame(
            {
                "symbol_multiday_setup_state": ["trend_persistence_near_high", "volume_confirmed_reclaim"],
                "multi_day_market_state_v4": ["constructive_risk_on", "constructive_risk_on"],
                "theme_regime_state_v4": ["persistent_theme_leader", "theme_participation"],
                "entry_close_pos_in_bar": [0.96, 0.99],
                "range_pos": [0.8, 0.6],
                "volume_ratio_prev": [1.2, 1.3],
                "timing_state": ["opening_drive", "late_day"],
                "entry_reduce_failure_flag": [1, 0],
                "factor_adjusted_residual_pct": [-5.0, 3.0],
            }
        )
        masks = build_expansion_masks(frame)
        self.assertTrue(bool(masks["base_trend_closepos_097"].iloc[0]))
        self.assertTrue(bool(masks["strict_regime_volume_confirmed"].iloc[1]))

    def test_failure_decomposition_focuses_2025q1_q3(self) -> None:
        panel = pd.DataFrame(
            {
                "candidate_set": ["task505_selected_two_year_strategy"] * 3,
                "quarter": ["2025Q1", "2025Q2", "2024Q4"],
                "multi_day_market_state_v4": ["weak", "weak", "strong"],
                "theme_regime_state_v4": ["weak_theme", "weak_theme", "leader"],
                "symbol_multiday_setup_state": ["trend", "trend", "trend"],
                "intraday_entry_state_v4": ["late", "late", "good"],
                "timing_state": ["late", "late", "open"],
                "exit_reason": ["stop", "stop", "time"],
                "factor_adjustment_available_flag": [1, 1, 1],
                "factor_adjusted_residual_pct": [-3.0, -5.0, 10.0],
                "return_pct": [-2.0, -4.0, 11.0],
                "entry_reduce_failure_flag": [1, 1, 0],
                "add_scale_success_flag": [0, 0, 1],
            }
        )
        result = decompose_failure_quarters(panel)
        self.assertFalse(result.empty)
        self.assertNotIn("strong", set(result["value"]))


if __name__ == "__main__":
    unittest.main()
