from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task556_vwap_bandwalk_portfolio_revalidation import build_task556


class Task556VwapBandwalkPortfolioRevalidationTest(unittest.TestCase):
    def _fixture(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "lifecycle_id": "L1",
                    "symbol": "AAA",
                    "theme_id": "ai",
                    "entry_ts": "2025-01-02T10:00:00Z",
                    "simulated_exit_ts": "2025-01-06T10:00:00Z",
                    "split_name": "validation",
                    "quarter": "2025Q1",
                    "vwap_reclaim_state_v2": "strong_vwap_acceptance",
                    "relative_volume_state_v2": "volume_confirmed",
                    "band_walk_state_v2": "upper_band_walk_proxy",
                    "overextension_state_v2": "accepted_overextension",
                    "net_return_from_entry": 0.08,
                    "entry_reduce_failure_flag": 0,
                    "add_scale_success_flag": 1,
                    "false_positive_flag": 0,
                    "holding_days": 4,
                    "label_used_in_assignment_flag": 0,
                    "inferred_lifecycle_matching_used_flag": 0,
                },
                {
                    "lifecycle_id": "L2",
                    "symbol": "BBB",
                    "theme_id": "cloud",
                    "entry_ts": "2025-01-03T10:00:00Z",
                    "simulated_exit_ts": "2025-01-03T15:00:00Z",
                    "split_name": "recent_oos",
                    "quarter": "2025Q1",
                    "vwap_reclaim_state_v2": "failed_vwap_reclaim",
                    "relative_volume_state_v2": "normal_or_thin_volume",
                    "band_walk_state_v2": "lower_range",
                    "overextension_state_v2": "exhaustion_overextension",
                    "net_return_from_entry": -0.04,
                    "entry_reduce_failure_flag": 1,
                    "add_scale_success_flag": 0,
                    "false_positive_flag": 1,
                    "holding_days": 0,
                    "label_used_in_assignment_flag": 0,
                    "inferred_lifecycle_matching_used_flag": 0,
                },
                {
                    "lifecycle_id": "L3",
                    "symbol": "CCC",
                    "theme_id": "ai",
                    "entry_ts": "2025-01-04T10:00:00Z",
                    "simulated_exit_ts": "2025-01-08T10:00:00Z",
                    "split_name": "recent_oos",
                    "quarter": "2025Q1",
                    "vwap_reclaim_state_v2": "early_vwap_reclaim",
                    "relative_volume_state_v2": "volume_climax",
                    "band_walk_state_v2": "middle_range",
                    "overextension_state_v2": "not_overextended",
                    "net_return_from_entry": 0.05,
                    "entry_reduce_failure_flag": 0,
                    "add_scale_success_flag": 1,
                    "false_positive_flag": 0,
                    "holding_days": 4,
                    "label_used_in_assignment_flag": 0,
                    "inferred_lifecycle_matching_used_flag": 0,
                },
            ]
        )

    def test_assignment_uses_entry_safe_vwap_structure_only(self) -> None:
        artifacts = build_task556(self._fixture())
        assignment = artifacts["vwap_bandwalk_assignment_panel"]
        self.assertGreaterEqual(assignment["candidate_set"].nunique(), 5)
        self.assertEqual(int(assignment["assignment_used_label_flag"].max()), 0)
        self.assertEqual(int(assignment["assignment_used_outcome_flag"].max()), 0)
        self.assertEqual(int(assignment["inferred_matching_used_flag"].max()), 0)

    def test_quality_and_portfolio_outputs_are_generated(self) -> None:
        artifacts = build_task556(self._fixture())
        self.assertIn("entry_reduce_failure_rate", artifacts["vwap_bandwalk_candidate_set_quality"].columns)
        self.assertIn("max_drawdown_dollar_proxy", artifacts["vwap_bandwalk_portfolio_quality"].columns)
        self.assertIn("entry_reduce_improvement_pp", artifacts["vwap_bandwalk_entry_reduce_audit"].columns)
        self.assertIn("validation", set(artifacts["vwap_bandwalk_split_quality"]["split_name"]))
        self.assertIn("recent_oos", set(artifacts["vwap_bandwalk_split_quality"]["split_name"]))

    def test_leakage_audit_blocks_outcome_fields(self) -> None:
        artifacts = build_task556(self._fixture())
        leakage = artifacts["vwap_bandwalk_leakage_audit"]
        blocked = leakage[leakage["check"].str.contains("net_return_from_entry")]
        self.assertEqual(blocked.iloc[0]["status"], "PASS")
        self.assertEqual(int(blocked.iloc[0]["used_in_assignment_flag"]), 0)
        decision = artifacts["task_556_decision"].iloc[0]
        self.assertEqual(int(decision["deployment_ready_flag"]), 0)
        self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
