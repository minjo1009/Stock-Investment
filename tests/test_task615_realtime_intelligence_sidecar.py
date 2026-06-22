from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.app.task_615_realtime_intelligence_sidecar import (
    _stamp_runtime_temporal_contract,
    run_task615_realtime_intelligence_sidecar,
)


class Task615RealtimeIntelligenceSidecarTest(unittest.TestCase):
    def test_sidecar_collects_status_without_trading_signal(self) -> None:
        with tempfile.TemporaryDirectory() as out_tmp, tempfile.TemporaryDirectory() as artifact_tmp, tempfile.TemporaryDirectory() as raw_tmp:
            with (
                patch.dict(os.environ, {"TRADING_INTELLIGENCE_SIDECAR_ENABLED": "1"}, clear=False),
                patch(
                    "src.app.task_615_realtime_intelligence_sidecar._collect_runtime_source_snapshot",
                    return_value={"event_store_rows": 2, "attached_source_lanes": 4},
                ),
                patch("src.app.task_615_realtime_intelligence_sidecar.append_registry_rows"),
            ):
                artifacts = run_task615_realtime_intelligence_sidecar(
                    fetch_sources=False,
                    force=True,
                    out_dir=Path(out_tmp),
                    artifact_dir=Path(artifact_tmp),
                    raw_dir=Path(raw_tmp),
                )
            latest = artifacts["latest_runtime_intelligence_sidecar_status.csv"].iloc[0]
            self.assertEqual(latest["decision_status"], "INTELLIGENCE_SIDECAR_COLLECTION_OK")
            self.assertEqual(int(latest["event_store_rows"]), 2)
            self.assertEqual(int(latest["sidecar_trade_signal_used_flag"]), 0)
            self.assertEqual(latest["strategy_acceptance_status"], "NOT_ACCEPTED")
            self.assertEqual(latest["real_capital_status"], "FORBIDDEN")

    def test_sidecar_disabled_writes_disabled_status(self) -> None:
        with tempfile.TemporaryDirectory() as out_tmp, tempfile.TemporaryDirectory() as artifact_tmp:
            with patch.dict(os.environ, {"TRADING_INTELLIGENCE_SIDECAR_ENABLED": "0"}, clear=False):
                artifacts = run_task615_realtime_intelligence_sidecar(
                    out_dir=Path(out_tmp),
                    artifact_dir=Path(artifact_tmp),
                )
            latest = artifacts["latest_runtime_intelligence_sidecar_status.csv"].iloc[0]
            self.assertEqual(latest["decision_status"], "INTELLIGENCE_SIDECAR_DISABLED")
            self.assertEqual(int(latest["sidecar_trade_signal_used_flag"]), 0)

    def test_sidecar_busy_status_does_not_become_trading_signal(self) -> None:
        with tempfile.TemporaryDirectory() as out_tmp, tempfile.TemporaryDirectory() as artifact_tmp:
            lock_path = Path(out_tmp) / ".runtime_intelligence_sidecar.lock"
            lock_path.write_text('{"pid": 1, "created_at_utc": "2999-01-01T00:00:00Z"}', encoding="utf-8")
            with patch.dict(os.environ, {"TRADING_INTELLIGENCE_SIDECAR_ENABLED": "1"}, clear=False):
                artifacts = run_task615_realtime_intelligence_sidecar(
                    out_dir=Path(out_tmp),
                    artifact_dir=Path(artifact_tmp),
                )
            latest = artifacts["latest_runtime_intelligence_sidecar_status.csv"].iloc[0]
            self.assertEqual(latest["decision_status"], "INTELLIGENCE_SIDECAR_BUSY")
            self.assertEqual(int(latest["sidecar_trade_signal_used_flag"]), 0)

    def test_runtime_temporal_contract_stamps_received_and_tradable_time(self) -> None:
        events = pd.DataFrame(
            [
                {
                    "event_id": "timestamped",
                    "source_lane": "trump_major_person_political_statements",
                    "source_name": "whitehouse",
                    "event_date": "2026-01-02",
                    "event_timestamp_utc": "2026-01-02T15:00:00+00:00",
                    "time_precision": "timestamp",
                    "event_title": "Timestamped Event",
                },
                {
                    "event_id": "date_only",
                    "source_lane": "war_geopolitical_conflict_events",
                    "source_name": "ofac_recent_actions",
                    "event_date": "2026-01-02",
                    "event_timestamp_utc": "",
                    "time_precision": "date",
                    "event_title": "Date Only Event",
                },
            ]
        )

        stamped = _stamp_runtime_temporal_contract(events, received_at="2026-01-02T16:00:00Z")
        timestamped = stamped[stamped["event_id"].eq("timestamped")].iloc[0]
        date_only = stamped[stamped["event_id"].eq("date_only")].iloc[0]

        self.assertEqual(timestamped["published_at"], "2026-01-02T15:00:00+00:00")
        self.assertEqual(timestamped["received_at"], "2026-01-02T16:00:00Z")
        self.assertEqual(timestamped["tradable_after_ts"], "2026-01-02T15:00:00+00:00")
        self.assertEqual(date_only["published_at"], "")
        self.assertEqual(date_only["received_at"], "2026-01-02T16:00:00Z")
        self.assertEqual(date_only["tradable_after_ts"], "2026-01-02T16:00:00Z")


if __name__ == "__main__":
    unittest.main()
