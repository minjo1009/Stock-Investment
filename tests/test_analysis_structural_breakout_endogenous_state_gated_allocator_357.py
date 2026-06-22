from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_endogenous_state_gated_allocator_357 import (
    _final_decision,
    _marginal_penalty,
    _row_state,
    _staged_weight,
)


class TestAnalysisStructuralBreakoutEndogenousStateGatedAllocator357(unittest.TestCase):
    def test_row_state_marks_semis_crowding_as_dislocation(self) -> None:
        thresholds = {
            "same_day_candidate_high": 6.0,
            "same_day_sector_high": 3.0,
            "dispersion_high": 1.0,
            "corr_high": 0.5,
            "semis_concentration_high": 0.4,
        }
        row = pd.Series(
            {
                "same_day_candidate_count": 7,
                "same_day_sector_candidate_count": 4,
                "dispersion_20d": 1.5,
                "mean_pairwise_corr": 0.6,
                "semis_concentration_ratio": 0.7,
                "session_timing_bucket": "first_30m",
                "execution_quality_bucket": "strong",
                "sector_group": "semis",
                "gap_environment_state": "unstable",
                "market_breadth_state": "narrow",
                "sector_leadership_state": "tech_led",
                "crowding_state": "crowded",
                "sector_crowding_high": 1,
            }
        )
        self.assertEqual(_row_state(row, thresholds), "crowded_dislocation_state")

    def test_marginal_penalty_blocks_second_semis_when_cap_enabled(self) -> None:
        selected_rows = [
            pd.Series({"sector_group": "semis", "session_timing_bucket": "first_30m", "symbol": "AMD"}),
        ]
        candidate = pd.Series({"sector_group": "semis", "session_timing_bucket": "mid_session", "symbol": "NVDA"})
        _penalty, blocked = _marginal_penalty(candidate, selected_rows, "state_gated_allocator_plus_semis_factor_cap")
        self.assertTrue(blocked)

    def test_staged_weight_reduces_crowded_probe(self) -> None:
        row = pd.Series(
            {
                "endogenous_state": "crowded_dislocation_state",
                "execution_quality_bucket": "unknown",
                "session_timing_bucket": "first_30m",
            }
        )
        stage_name, weight = _staged_weight(row, "state_gated_allocator_plus_staged_execution")
        self.assertEqual(stage_name, "stage_1_probe")
        self.assertLess(weight, 0.5)

    def test_final_decision_promotes_dislocation_aware_when_anchored_positive(self) -> None:
        comparison_df = pd.DataFrame(
            [
                {
                    "framework_name": "current_baseline_sleeve",
                    "allocator_variant": "baseline_rank_allocator",
                    "anchored_oos_net_pnl_r": -1.0,
                    "net_pnl_r": 20.0,
                    "rolling_oos_robustness": 0.75,
                    "anchored_oos_drawdown": 3.0,
                    "semis_loss_share": 0.55,
                },
                {
                    "framework_name": "state_gated_allocator_plus_staged_execution",
                    "allocator_variant": "marginal_utility_allocator",
                    "anchored_oos_net_pnl_r": 0.5,
                    "net_pnl_r": 18.0,
                    "rolling_oos_robustness": 0.75,
                    "anchored_oos_drawdown": 2.0,
                    "semis_loss_share": 0.20,
                },
            ]
        )
        final_df = _final_decision(comparison_df)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "DISLOCATION_AWARE_SLEEVE")


if __name__ == "__main__":
    unittest.main()
