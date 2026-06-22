from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_state_space_realignment_332 import (
    _candidate_a_raw,
    _candidate_b_raw,
    _candidate_c_builder,
    _final_decision,
    _transition_rows,
)


class TestAnalysisStructuralBreakoutStateSpaceRealignment332(unittest.TestCase):
    def test_candidate_a_assignment_is_conditional(self) -> None:
        row = pd.Series(
            {
                "noise_pressure_state": "high_noise",
                "trend_quality_state": "strong",
                "extension_pressure_state": "medium",
            }
        )
        self.assertEqual(_candidate_a_raw(row), "noise:high_noise|trend:strong|extension:medium")

    def test_candidate_b_assignment_prioritizes_noise_when_trend_is_weak(self) -> None:
        row = pd.Series(
            {
                "noise_pressure_state": "balanced",
                "trend_quality_state": "weak",
                "extension_pressure_state": "high",
            }
        )
        self.assertEqual(_candidate_b_raw(row), "trend:weak|noise:balanced")

    def test_candidate_c_adds_participation_only_for_dense_parent(self) -> None:
        builder = _candidate_c_builder({"noise:balanced|extension:medium"})
        dense_row = pd.Series(
            {
                "noise_pressure_state": "balanced",
                "extension_pressure_state": "medium",
                "participation_quality_state": "broad",
                "trend_quality_state": "neutral",
            }
        )
        sparse_row = pd.Series(
            {
                "noise_pressure_state": "compressed",
                "extension_pressure_state": "low",
                "participation_quality_state": "narrow",
                "trend_quality_state": "neutral",
            }
        )
        self.assertEqual(builder(dense_row), "noise:balanced|extension:medium|participation:broad")
        self.assertEqual(builder(sparse_row), "noise:compressed|extension:low")

    def test_transition_rows_compute_expected_persistence(self) -> None:
        sequence_df = pd.DataFrame(
            [
                {"state": "s1", "payoff": 1.0},
                {"state": "s1", "payoff": 0.5},
                {"state": "s2", "payoff": -0.5},
                {"state": "s2", "payoff": 0.2},
            ]
        )
        result = _transition_rows(sequence_df, "candidate_A", "calendar_day", "state", "payoff")
        row = result[(result["state_t"] == "s1") & (result["state_t1"] == "s1")].iloc[0]
        self.assertAlmostEqual(float(row["transition_probability"]), 0.5, places=6)
        self.assertAlmostEqual(float(row["persistence_probability"]), 0.5, places=6)

    def test_final_decision_promotes_only_when_all_rules_hold(self) -> None:
        evaluation_df = pd.DataFrame(
            [
                {
                    "candidate": "task_329_state_model",
                    "between_state_expectancy_dispersion": 0.40,
                    "within_state_path_entropy_mean": 1.50,
                    "oos_linkage_retention": -0.40,
                    "sparsity_risk": 0.60,
                },
                {
                    "candidate": "candidate_A",
                    "between_state_expectancy_dispersion": 0.55,
                    "within_state_path_entropy_mean": 1.20,
                    "oos_linkage_retention": 0.20,
                    "sparsity_risk": 0.50,
                },
                {
                    "candidate": "candidate_B",
                    "between_state_expectancy_dispersion": 0.45,
                    "within_state_path_entropy_mean": 1.30,
                    "oos_linkage_retention": 0.10,
                    "sparsity_risk": 0.70,
                },
                {
                    "candidate": "candidate_C",
                    "between_state_expectancy_dispersion": 0.30,
                    "within_state_path_entropy_mean": 1.60,
                    "oos_linkage_retention": -0.10,
                    "sparsity_risk": 0.50,
                },
            ]
        )
        transition_df = pd.DataFrame(
            [
                {"candidate": "task_329_state_model", "persistence_probability": 0.40, "transition_instability": 0.60},
                {"candidate": "candidate_A", "persistence_probability": 0.60, "transition_instability": 0.40},
                {"candidate": "candidate_B", "persistence_probability": 0.30, "transition_instability": 0.70},
                {"candidate": "candidate_C", "persistence_probability": 0.50, "transition_instability": 0.50},
            ]
        )
        result = _final_decision(evaluation_df, transition_df)
        self.assertEqual(result.iloc[0]["decision"], "PROMOTE")
        self.assertEqual(result.iloc[0]["recommended_candidate"], "candidate_A")


if __name__ == "__main__":
    unittest.main()
