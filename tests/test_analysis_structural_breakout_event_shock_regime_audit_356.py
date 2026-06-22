from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_event_shock_regime_audit_356 import (
    _distribution_overlap,
    _final_decision,
    _numeric_similarity,
    _shock_similarity,
)


class TestAnalysisStructuralBreakoutEventShockRegimeAudit356(unittest.TestCase):
    def test_distribution_overlap_is_one_for_identical_distributions(self) -> None:
        self.assertAlmostEqual(_distribution_overlap({"a": 0.6, "b": 0.4}, {"a": 0.6, "b": 0.4}), 1.0, places=6)

    def test_numeric_similarity_penalizes_distance(self) -> None:
        self.assertGreater(_numeric_similarity(5.0, 5.5, 0.0, 10.0), _numeric_similarity(5.0, 9.0, 0.0, 10.0))

    def test_shock_similarity_prefers_matching_profiles(self) -> None:
        base_pool = pd.DataFrame(
            {
                "dispersion_20d": [1.0, 2.0, 3.0],
                "mean_pairwise_corr": [0.2, 0.4, 0.6],
                "same_day_candidate_count": [2, 4, 6],
                "same_day_sector_candidate_count": [1, 2, 3],
            }
        )
        current = {
            "episode_name": "current_failure_window",
            "trade_count": 10,
            "dispersion_20d": 2.0,
            "mean_pairwise_corr": 0.4,
            "same_day_candidate_count": 4.0,
            "same_day_sector_candidate_count": 2.0,
            "gap_environment_state_dist": {"unstable": 1.0},
            "market_breadth_state_dist": {"narrow": 1.0},
            "sector_leadership_state_dist": {"tech_led": 1.0},
        }
        match = {
            "episode_name": "match",
            "trade_count": 8,
            "dispersion_20d": 2.1,
            "mean_pairwise_corr": 0.39,
            "same_day_candidate_count": 4.2,
            "same_day_sector_candidate_count": 2.1,
            "gap_environment_state_dist": {"unstable": 1.0},
            "market_breadth_state_dist": {"narrow": 1.0},
            "sector_leadership_state_dist": {"tech_led": 1.0},
        }
        mismatch = {
            "episode_name": "mismatch",
            "trade_count": 8,
            "dispersion_20d": 3.0,
            "mean_pairwise_corr": 0.2,
            "same_day_candidate_count": 6.0,
            "same_day_sector_candidate_count": 3.0,
            "gap_environment_state_dist": {"calm": 1.0},
            "market_breadth_state_dist": {"broad": 1.0},
            "sector_leadership_state_dist": {"broad_led": 1.0},
        }
        match_score = _shock_similarity(current, match, base_pool)["shock_regime_similarity_score"]
        mismatch_score = _shock_similarity(current, mismatch, base_pool)["shock_regime_similarity_score"]
        self.assertGreater(match_score, mismatch_score)

    def test_final_decision_promotes_shock_manageable_when_rule_restores_positive_pnl(self) -> None:
        similarity_df = pd.DataFrame(
            [
                {"comparison_episode": "russia_invasion_shock", "shock_regime_similarity_score": 0.72},
                {"comparison_episode": "banking_stress_shock", "shock_regime_similarity_score": 0.58},
            ]
        )
        deployment_df = pd.DataFrame(
            [
                {"deployment_rule": "baseline_deployment", "episode_name": "current_failure_window", "net_pnl_r": -1.0, "cost_adjusted_expectancy": -0.05},
                {"deployment_rule": "shock_skip_rule", "episode_name": "current_failure_window", "net_pnl_r": 0.0, "cost_adjusted_expectancy": 0.0},
                {"deployment_rule": "shock_timing_downgrade", "episode_name": "current_failure_window", "net_pnl_r": 0.4, "cost_adjusted_expectancy": 0.02},
            ]
        )
        final_df = _final_decision(similarity_df, deployment_df)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "SHOCK_MANAGEABLE_DEPLOYMENT")


if __name__ == "__main__":
    unittest.main()
