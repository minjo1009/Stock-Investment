from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.continuation_event_identity import (
    build_continuation_event_identity,
    build_continuation_event_type_summary,
    normalize_continuation_event_rows,
)


class TestContinuationEventIdentity(unittest.TestCase):
    def _sample_replay_trace(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "lifecycle_id": "AMD|2026-01-03",
                    "trade_id": "a1",
                    "signal_id": "sig-a1",
                    "symbol": "AMD",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:00:00Z",
                    "sequence_in_lifecycle": 1,
                    "previous_replay_state": "IDLE",
                    "replay_state": "REDUCING",
                    "transition_reason": "fragility_increase",
                    "add_activated": False,
                    "size_multiplier": 0.1,
                    "concentration_step": 0.1,
                    "is_live_position": True,
                    "size_increased_vs_prev": True,
                    "state_label": "CROWDED",
                    "participation_quality_label": "FRAGILE_CROWDING",
                },
                {
                    "lifecycle_id": "AMD|2026-01-03",
                    "trade_id": "a2",
                    "signal_id": "sig-a2",
                    "symbol": "AMD",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:01:00Z",
                    "sequence_in_lifecycle": 2,
                    "previous_replay_state": "REDUCING",
                    "replay_state": "EXITED",
                    "transition_reason": "fragile_exit",
                    "add_activated": False,
                    "size_multiplier": 0.0,
                    "concentration_step": -0.1,
                    "is_live_position": False,
                    "size_increased_vs_prev": False,
                    "state_label": "DISLOCATION",
                    "participation_quality_label": "FRAGILE_CROWDING",
                },
                {
                    "lifecycle_id": "NVDA|2026-01-03",
                    "trade_id": "t1",
                    "signal_id": "sig-1",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:30:00Z",
                    "sequence_in_lifecycle": 1,
                    "previous_replay_state": "IDLE",
                    "replay_state": "PROBE",
                    "transition_reason": "initial_live_probe",
                    "add_activated": False,
                    "size_multiplier": 0.5,
                    "concentration_step": 0.5,
                    "is_live_position": True,
                    "size_increased_vs_prev": True,
                    "state_label": "NORMAL",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                },
                {
                    "lifecycle_id": "NVDA|2026-01-03",
                    "trade_id": "t2",
                    "signal_id": "sig-2",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:31:00Z",
                    "sequence_in_lifecycle": 2,
                    "previous_replay_state": "PROBE",
                    "replay_state": "BUILDING",
                    "transition_reason": "probe_to_build",
                    "add_activated": True,
                    "size_multiplier": 0.9,
                    "concentration_step": 0.4,
                    "is_live_position": True,
                    "size_increased_vs_prev": True,
                    "state_label": "NORMAL",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                },
                {
                    "lifecycle_id": "NVDA|2026-01-03",
                    "trade_id": "t3",
                    "signal_id": "sig-3",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:32:00Z",
                    "sequence_in_lifecycle": 3,
                    "previous_replay_state": "BUILDING",
                    "replay_state": "PERSISTING",
                    "transition_reason": "build_to_persist",
                    "add_activated": False,
                    "size_multiplier": 0.9,
                    "concentration_step": 0.0,
                    "is_live_position": True,
                    "size_increased_vs_prev": False,
                    "state_label": "NORMAL",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                },
            ]
        )

    def test_normalization_assigns_deterministic_event_index_and_id(self) -> None:
        event_df = normalize_continuation_event_rows(self._sample_replay_trace())
        nvda = event_df[event_df["continuation_id"].eq("NVDA|2026-01-03")].reset_index(drop=True)
        self.assertEqual(nvda["event_index"].tolist(), [1, 2, 3])
        self.assertEqual(nvda["trade_id"].tolist(), ["t1", "t2", "t3"])
        self.assertEqual(nvda["event_id"].tolist()[0], "NVDA|2026-01-03|001|probe_entry")

    def test_event_type_assignment_maps_replay_states_to_task365_events(self) -> None:
        event_df = normalize_continuation_event_rows(self._sample_replay_trace())
        self.assertEqual(
            event_df["event_type"].tolist(),
            ["REDUCE", "EXIT", "PROBE_ENTRY", "ADD", "PERSIST"],
        )

    def test_build_returns_summary_with_activation_counts(self) -> None:
        event_df, summary_df = build_continuation_event_identity(self._sample_replay_trace())
        self.assertEqual(len(event_df), 5)
        add_row = summary_df[summary_df["event_type"].eq("ADD")].iloc[0]
        self.assertEqual(int(add_row["event_count"]), 1)
        self.assertEqual(int(add_row["add_activation_count"]), 1)
        self.assertAlmostEqual(float(add_row["avg_size_multiplier"]), 0.9, places=6)

    def test_empty_input_returns_empty_shapes(self) -> None:
        empty_df = pd.DataFrame()
        event_df = normalize_continuation_event_rows(empty_df)
        summary_df = build_continuation_event_type_summary(event_df)
        self.assertTrue(event_df.empty)
        self.assertTrue(summary_df.empty)


if __name__ == "__main__":
    unittest.main()
