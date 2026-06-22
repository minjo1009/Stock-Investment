from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.continuation_setup_identity import (
    build_continuation_setup_identity,
    build_continuation_setup_type_summary,
    normalize_continuation_setup_rows,
)


class TestContinuationSetupIdentity(unittest.TestCase):
    def _sample_replay_trace(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "lifecycle_id": "AMD|2026-01-03",
                    "trade_id": "a2",
                    "symbol": "AMD",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:01:00Z",
                    "sequence_in_lifecycle": 2,
                    "replay_state": "EXITED",
                    "transition_reason": "fragile_exit",
                    "add_activated": False,
                    "size_multiplier": 0.0,
                    "state_label": "DISLOCATION",
                    "participation_quality_label": "FRAGILE_CROWDING",
                },
                {
                    "lifecycle_id": "NVDA|2026-01-03",
                    "trade_id": "t2",
                    "symbol": "NVDA",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:31:00Z",
                    "sequence_in_lifecycle": 2,
                    "replay_state": "BUILDING",
                    "transition_reason": "probe_to_build",
                    "add_activated": True,
                    "size_multiplier": 0.9,
                    "state_label": "NORMAL",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                },
                {
                    "lifecycle_id": "AMD|2026-01-03",
                    "trade_id": "a1",
                    "signal_id": "sig-a1",
                    "symbol": "AMD",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:00:00Z",
                    "sequence_in_lifecycle": 1,
                    "replay_state": "REDUCING",
                    "transition_reason": "fragility_increase",
                    "add_activated": False,
                    "size_multiplier": 0.1,
                    "state_label": "CROWDED",
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
                    "replay_state": "PROBE",
                    "transition_reason": "initial_live_probe",
                    "add_activated": False,
                    "size_multiplier": 0.5,
                    "state_label": "NORMAL",
                    "participation_quality_label": "HEALTHY_EXPANSION",
                },
                {
                    "lifecycle_id": "MSFT|2026-01-03",
                    "trade_id": "m1",
                    "symbol": "MSFT",
                    "session_date": "2026-01-03",
                    "timestamp": "2026-01-03T14:10:00Z",
                    "sequence_in_lifecycle": 1,
                    "replay_state": "EXITED",
                    "transition_reason": "dislocation_exit",
                    "add_activated": False,
                    "size_multiplier": 0.0,
                    "state_label": "DISLOCATION",
                    "participation_quality_label": "UNKNOWN",
                },
            ]
        )

    def test_normalization_anchors_first_row_per_continuation(self) -> None:
        setup_df = normalize_continuation_setup_rows(self._sample_replay_trace())
        self.assertEqual(len(setup_df), 3)
        nvda = setup_df[setup_df["continuation_id"].eq("NVDA|2026-01-03")].iloc[0]
        self.assertEqual(str(nvda["setup_id"]), "NVDA|2026-01-03|setup|001")
        self.assertEqual(str(nvda["anchor_trade_id"]), "t1")
        self.assertEqual(int(nvda["anchor_sequence_in_lifecycle"]), 1)

    def test_setup_status_maps_active_fragile_and_invalidated(self) -> None:
        setup_df = normalize_continuation_setup_rows(self._sample_replay_trace())
        status_map = dict(zip(setup_df["continuation_id"], setup_df["setup_status"]))
        self.assertEqual(status_map["NVDA|2026-01-03"], "ACTIVE")
        self.assertEqual(status_map["AMD|2026-01-03"], "FRAGILE")
        self.assertEqual(status_map["MSFT|2026-01-03"], "INVALIDATED")

    def test_build_returns_status_summary(self) -> None:
        setup_df, summary_df = build_continuation_setup_identity(self._sample_replay_trace())
        self.assertEqual(len(setup_df), 3)
        active_row = summary_df[summary_df["setup_status"].eq("ACTIVE")].iloc[0]
        self.assertEqual(int(active_row["setup_count"]), 1)
        self.assertEqual(int(active_row["live_setup_count"]), 1)

    def test_empty_input_returns_empty_shapes(self) -> None:
        empty_df = pd.DataFrame()
        setup_df = normalize_continuation_setup_rows(empty_df)
        summary_df = build_continuation_setup_type_summary(setup_df)
        self.assertTrue(setup_df.empty)
        self.assertTrue(summary_df.empty)


if __name__ == "__main__":
    unittest.main()
