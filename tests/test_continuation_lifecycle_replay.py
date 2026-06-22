from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.continuation_lifecycle_replay import (
    build_continuation_lifecycle_replay,
    normalize_lifecycle_rows,
    replay_state_machine,
)


class TestContinuationLifecycleReplay(unittest.TestCase):
    def _sample_shadow_log(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "timestamp": "2026-01-03T14:30:00Z",
                    "signal_id": "evt-1",
                    "trade_id": "t1",
                    "symbol": "NVDA",
                    "strategy_id": "continuation_sleeve",
                    "day_key": "2026-01-03",
                    "current_split": "anchored_oos",
                    "state_label": "NORMAL",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "continuation_risk_score": 0.2,
                    "participation_confidence": 0.8,
                    "allow_new_entry": True,
                    "allow_add": True,
                    "factor_exposure_violated": False,
                    "violated_factors": "",
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "quality_aware_policy_stage": "ADD_ALLOWED",
                    "quality_aware_add_allowed": True,
                    "quality_aware_size_multiplier": 0.7,
                    "healthy_aggressive_policy_label": "RELAX_SIZE_AND_ADD",
                    "healthy_aggressive_final_add_allowed": True,
                    "healthy_aggressive_final_size_multiplier": 0.9,
                    "baseline_realized_R": 1.0,
                    "shadow_realized_R_proxy": 0.2,
                    "quality_aware_realized_R_proxy": 0.7,
                    "healthy_aggressive_realized_R_proxy": 0.9,
                    "shadow_reasons": "shadow_full_participation_allowed",
                    "participation_reasons": "healthy_expansion",
                    "quality_aware_reasons": "healthy_expansion_relaxed_add",
                    "healthy_aggressive_reasons": "aggressive_add",
                },
                {
                    "timestamp": "2026-01-03T14:35:00Z",
                    "signal_id": "evt-2",
                    "trade_id": "t2",
                    "symbol": "AMD",
                    "strategy_id": "continuation_sleeve",
                    "day_key": "2026-01-03",
                    "current_split": "anchored_oos",
                    "state_label": "CROWDED",
                    "participation_quality_label": "FRAGILE_CROWDING",
                    "continuation_risk_score": 0.8,
                    "participation_confidence": 0.9,
                    "allow_new_entry": True,
                    "allow_add": False,
                    "factor_exposure_violated": False,
                    "violated_factors": "",
                    "staged_gate_stage": "stage_1_probe",
                    "staged_add_allowed": False,
                    "quality_aware_policy_stage": "PROBE_ONLY",
                    "quality_aware_add_allowed": False,
                    "quality_aware_size_multiplier": 0.15,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.1,
                    "baseline_realized_R": -1.0,
                    "shadow_realized_R_proxy": -0.1,
                    "quality_aware_realized_R_proxy": -0.15,
                    "healthy_aggressive_realized_R_proxy": -0.1,
                    "shadow_reasons": "crowded_state_add_restricted",
                    "participation_reasons": "fragile_crowding",
                    "quality_aware_reasons": "fragile_crowding_strict_suppression",
                    "healthy_aggressive_reasons": "keep_suppressed",
                },
                {
                    "timestamp": "2026-01-03T14:40:00Z",
                    "signal_id": "evt-3",
                    "trade_id": "t3",
                    "symbol": "MSFT",
                    "strategy_id": "continuation_sleeve",
                    "day_key": "2026-01-03",
                    "current_split": "anchored_oos",
                    "state_label": "NORMAL",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                    "continuation_risk_score": 0.3,
                    "participation_confidence": 0.7,
                    "allow_new_entry": True,
                    "allow_add": True,
                    "factor_exposure_violated": True,
                    "violated_factors": "semis",
                    "staged_gate_stage": "stage_2_add",
                    "staged_add_allowed": True,
                    "quality_aware_policy_stage": "BLOCK",
                    "quality_aware_add_allowed": False,
                    "quality_aware_size_multiplier": 0.0,
                    "healthy_aggressive_policy_label": "KEEP_SUPPRESSED",
                    "healthy_aggressive_final_add_allowed": False,
                    "healthy_aggressive_final_size_multiplier": 0.0,
                    "baseline_realized_R": 0.5,
                    "shadow_realized_R_proxy": 0.0,
                    "quality_aware_realized_R_proxy": 0.0,
                    "healthy_aggressive_realized_R_proxy": 0.0,
                    "shadow_reasons": "factor_budget_blocked_entry",
                    "participation_reasons": "healthy_expansion",
                    "quality_aware_reasons": "factor_or_entry_block_preserved",
                    "healthy_aggressive_reasons": "keep_suppressed",
                },
            ]
        )

    def test_normalization_is_deterministic_and_sequenced(self) -> None:
        normalized_df = normalize_lifecycle_rows(self._sample_shadow_log())
        self.assertEqual(normalized_df["sequence_in_day"].tolist(), [1, 2, 3])
        self.assertEqual(str(normalized_df.loc[0, "lifecycle_id"]), "evt-1")
        self.assertTrue(normalized_df["group_key"].astype(str).str.contains("2026-01-03").all())

    def test_replay_state_machine_maps_add_probe_and_entry_block(self) -> None:
        normalized_df = normalize_lifecycle_rows(self._sample_shadow_log())
        add_decision = replay_state_machine(normalized_df.iloc[0])
        probe_decision = replay_state_machine(normalized_df.iloc[1])
        blocked_decision = replay_state_machine(normalized_df.iloc[2])
        self.assertEqual(add_decision.replay_state, "ADD_RELAY_PASS")
        self.assertEqual(probe_decision.final_add_relay_block_stage, "exposure_add_gate")
        self.assertEqual(blocked_decision.final_add_relay_block_stage, "factor_budget")

    def test_build_replay_outputs_group_and_reason_aggregates(self) -> None:
        replay_df, group_df, reasons_df = build_continuation_lifecycle_replay(self._sample_shadow_log())
        self.assertIn("final_add_relay_outcome", replay_df.columns)
        self.assertIn("baseline_realized_R_sum", group_df.columns)
        self.assertIn("block_stage", reasons_df.columns)
        self.assertEqual(len(group_df), 3)
        self.assertTrue(reasons_df["reason"].astype(str).eq("factor_budget_violation=semis").any())


if __name__ == "__main__":
    unittest.main()
