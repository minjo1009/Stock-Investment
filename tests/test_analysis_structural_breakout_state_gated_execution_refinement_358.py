from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_state_gated_execution_refinement_358 import (
    _add_allowed,
    _final_decision,
    _marginal_penalty,
    _stage_weights,
)


class TestAnalysisStructuralBreakoutStateGatedExecutionRefinement358(unittest.TestCase):
    def test_stage_weights_reduce_crowded_probe(self) -> None:
        probe, add = _stage_weights("reduced_dislocation_mode", "crowded_dislocation_state")
        self.assertLessEqual(probe, 0.10)
        self.assertEqual(add, 0.0)

    def test_add_allowed_blocks_unknown_uncertain(self) -> None:
        thresholds = {"same_day_candidate_high": 12.0}
        row = pd.Series(
            {
                "endogenous_state": "uncertain_transition_state",
                "execution_quality_bucket": "unknown",
                "session_timing_bucket": "unknown",
                "same_day_candidate_count": 5,
            }
        )
        self.assertFalse(_add_allowed(row, "confirmation_sensitive_mode", thresholds, True))

    def test_marginal_penalty_blocks_duplicate_symbol(self) -> None:
        selected = [pd.Series({"symbol": "AMD", "sector_group": "semis", "session_timing_bucket": "first_30m"})]
        candidate = pd.Series(
            {
                "symbol": "AMD",
                "sector_group": "semis",
                "session_timing_bucket": "mid_session",
                "same_day_candidate_count": 10,
                "same_day_sector_candidate_count": 8,
                "endogenous_state": "crowded_dislocation_state",
            }
        )
        penalty, blocked = _marginal_penalty(candidate, selected, "portfolio_utility_mode", {"same_day_candidate_high": 12.0}, 0.0, 0.6)
        self.assertTrue(blocked)
        self.assertGreater(penalty, 1e5)

    def test_final_decision_promotes_practical_when_best_practical_improves(self) -> None:
        comparison_df = pd.DataFrame(
            [
                {
                    "framework_name": "current_baseline_sleeve",
                    "anchored_oos_net_pnl_r": -1.2,
                    "rolling_oos_robustness": 0.75,
                    "capital_utilization": 0.75,
                    "semis_loss_share": 0.50,
                    "net_pnl_r": 20.0,
                },
                {
                    "framework_name": "full_dislocation_mode",
                    "anchored_oos_net_pnl_r": -0.5,
                    "rolling_oos_robustness": 0.75,
                    "capital_utilization": 0.50,
                    "semis_loss_share": 0.0,
                    "net_pnl_r": 15.0,
                },
                {
                    "framework_name": "portfolio_utility_mode",
                    "anchored_oos_net_pnl_r": -0.7,
                    "rolling_oos_robustness": 0.75,
                    "capital_utilization": 0.70,
                    "semis_loss_share": 0.20,
                    "net_pnl_r": 18.0,
                },
                {
                    "framework_name": "reduced_dislocation_mode",
                    "anchored_oos_net_pnl_r": -0.8,
                    "rolling_oos_robustness": 0.75,
                    "capital_utilization": 0.72,
                    "semis_loss_share": 0.25,
                    "net_pnl_r": 17.0,
                },
                {
                    "framework_name": "confirmation_sensitive_mode",
                    "anchored_oos_net_pnl_r": -0.9,
                    "rolling_oos_robustness": 0.75,
                    "capital_utilization": 0.70,
                    "semis_loss_share": 0.28,
                    "net_pnl_r": 17.5,
                },
            ]
        )
        final_df = _final_decision(comparison_df)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "DISLOCATION_AWARE_STAGED_SLEEVE")


if __name__ == "__main__":
    unittest.main()
