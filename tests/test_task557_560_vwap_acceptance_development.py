from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task557_560_vwap_acceptance_development import (
    assign_vwap_acceptance_ontology,
    build_task557,
    build_task558,
    build_task559,
    build_task560,
)


class Task557To560VwapAcceptanceDevelopmentTest(unittest.TestCase):
    def _fixture(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "lifecycle_id": "L1",
                    "symbol": "AAA",
                    "theme_id": "ai_semiconductors",
                    "open": 98.5,
                    "high": 103.0,
                    "low": 96.0,
                    "close": 98.0,
                    "vwap": 99.0,
                    "entry_close_vs_vwap": -0.0101,
                    "entry_close_pos_in_bar": 0.2857,
                    "range_pos": 0.88,
                    "volume_ratio_prev": 0.9,
                    "multi_day_market_state_v4": "constructive_risk_on",
                    "theme_regime_state_v4": "persistent_theme_leader",
                    "symbol_multiday_setup_state": "trend_persistence_near_high",
                    "split_name": "validation",
                    "quarter": "2025Q1",
                    "net_return_from_entry": 0.10,
                    "entry_reduce_failure_flag": 0,
                    "add_scale_success_flag": 1,
                    "false_positive_flag": 0,
                    "holding_days": 8,
                },
                {
                    "lifecycle_id": "L2",
                    "symbol": "BBB",
                    "theme_id": "cloud",
                    "open": 100.0,
                    "high": 104.0,
                    "low": 99.0,
                    "close": 99.5,
                    "vwap": 100.5,
                    "entry_close_vs_vwap": -0.0100,
                    "entry_close_pos_in_bar": 0.10,
                    "range_pos": 0.95,
                    "volume_ratio_prev": 2.5,
                    "multi_day_market_state_v4": "weak_risk_off",
                    "theme_regime_state_v4": "weak_theme",
                    "symbol_multiday_setup_state": "weak_setup",
                    "split_name": "recent_oos",
                    "quarter": "2025Q1",
                    "net_return_from_entry": -0.05,
                    "entry_reduce_failure_flag": 1,
                    "add_scale_success_flag": 0,
                    "false_positive_flag": 1,
                    "holding_days": 0,
                },
                {
                    "lifecycle_id": "L3",
                    "symbol": "CCC",
                    "theme_id": "power_grid",
                    "open": 100.0,
                    "high": 102.0,
                    "low": 98.0,
                    "close": 101.2,
                    "vwap": 100.0,
                    "entry_close_vs_vwap": 0.0120,
                    "entry_close_pos_in_bar": 0.80,
                    "range_pos": 0.93,
                    "volume_ratio_prev": 1.3,
                    "multi_day_market_state_v4": "constructive_risk_on",
                    "theme_regime_state_v4": "persistent_theme_leader",
                    "symbol_multiday_setup_state": "trend_persistence_near_high",
                    "split_name": "train_design",
                    "quarter": "2025Q1",
                    "net_return_from_entry": 0.03,
                    "entry_reduce_failure_flag": 0,
                    "add_scale_success_flag": 1,
                    "false_positive_flag": 0,
                    "holding_days": 5,
                },
            ]
        )

    def test_task557_rebuilds_ontology_without_legacy_failed_name(self) -> None:
        artifacts = build_task557(self._fixture())
        panel = artifacts["vwap_acceptance_ontology_v3_panel"]
        self.assertTrue(
            {"below_vwap_controlled_pullback", "near_high_absorption"}.intersection(set(panel["vwap_acceptance_state_v3"]))
        )
        self.assertNotIn("failed_vwap_reclaim", set(panel["vwap_acceptance_state_v3"]))
        self.assertEqual(int(panel["label_used_in_assignment_flag_v3"].max()), 0)
        self.assertEqual(int(panel["inferred_matching_used_flag_v3"].max()), 0)

    def test_task558_separates_pullback_acceptance_from_true_failure(self) -> None:
        panel = assign_vwap_acceptance_ontology(self._fixture())
        artifacts = build_task558(panel)
        quality = artifacts["pullback_acceptance_true_failure_quality"]
        self.assertIn("pullback_acceptance_state_v3", quality.columns)
        self.assertIn("controlled_pullback_or_absorption", set(quality["pullback_acceptance_state_v3"]))
        self.assertIn("true_failure_or_rejection", set(quality["pullback_acceptance_state_v3"]))

    def test_task559_reattaches_market_theme_symbol_context(self) -> None:
        artifacts = build_task559(self._fixture())
        panel = artifacts["context_gate_v3_panel"]
        self.assertIn("context_gate_v3", panel.columns)
        self.assertIn("regime_theme_symbol_intraday_aligned", set(panel["context_gate_v3"]))
        self.assertEqual(int(panel["label_used_in_context_assignment_flag"].max()), 0)

    def test_task560_blocks_missing_microstructure_without_approximation(self) -> None:
        artifacts = build_task560()
        contract = artifacts["microstructure_confirmation_feature_contract"]
        self.assertGreater(int(contract["blocked_missing_source_flag"].sum()), 0)
        self.assertEqual(int(contract["approximation_allowed_flag"].max()), 0)
        decision = artifacts["task_560_decision"].iloc[0]
        self.assertEqual(decision["strategy_acceptance_status"], "DATA_BLOCKED_MICROSTRUCTURE_CONFIRMATION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
