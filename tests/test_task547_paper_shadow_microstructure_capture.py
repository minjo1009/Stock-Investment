from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task547_paper_shadow_microstructure_capture_run import (
    build_capture_source_audit,
    build_decision,
)
from src.data.alpaca_stock_stream_archive import JsonlArchiveWriter, normalize_stream_payload
from src.data.paper_shadow_microstructure_capture import (
    build_decision_microstructure_snapshots,
    build_latest_microstructure_state,
    build_microstructure_feature_lineage,
    load_stream_archive_records,
)


class Task547PaperShadowMicrostructureCaptureTest(unittest.TestCase):
    def test_stream_archive_builds_pre_action_microstructure_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            records = normalize_stream_payload(
                [
                    {"T": "q", "S": "AAPL", "bp": 100.0, "ap": 100.1, "bs": 10, "as": 12, "t": "2024-01-02T14:30:00Z"},
                    {"T": "b", "S": "AAPL", "o": 99.0, "h": 101.0, "l": 98.5, "c": 100.05, "v": 1000, "vw": 100.0, "n": 50, "t": "2024-01-02T14:30:00Z"},
                    {"T": "s", "S": "AAPL", "sc": "T", "t": "2024-01-02T14:30:00Z"},
                    {"T": "l", "S": "AAPL", "luld": "normal", "t": "2024-01-02T14:30:00Z"},
                ],
                recv_ts_utc="2024-01-02T14:30:01Z",
                recv_monotonic_ns=1,
            )
            JsonlArchiveWriter(root).write_records(records)
            loaded = load_stream_archive_records(root)
            state = build_latest_microstructure_state(loaded)
            decisions = pd.DataFrame(
                [
                    {
                        "decision_id": "D1",
                        "lifecycle_id": "L1",
                        "symbol": "AAPL",
                        "decision_recorded_ts_utc": "2024-01-02T14:30:02Z",
                        "order_submission_enabled_flag": 0,
                    }
                ]
            )
            snapshots = build_decision_microstructure_snapshots(decisions, state, snapshot_ts_utc="2024-01-02T14:30:02Z")
            self.assertEqual(int(snapshots.iloc[0]["microstructure_source_ready_flag"]), 1)
            self.assertEqual(int(snapshots.iloc[0]["pre_action_snapshot_flag"]), 1)
            self.assertGreater(float(snapshots.iloc[0]["spread_bps"]), 0)
            lineage = build_microstructure_feature_lineage(snapshots, state)
            self.assertEqual(int(lineage["source_available_flag"].max()), 1)

    def test_empty_stream_archive_does_not_fake_microstructure(self) -> None:
        decisions = pd.DataFrame([{"decision_id": "D1", "lifecycle_id": "L1", "symbol": "AAPL", "order_submission_enabled_flag": 0}])
        snapshots = build_decision_microstructure_snapshots(decisions, pd.DataFrame(), snapshot_ts_utc="2024-01-02T14:30:02Z")
        source = build_capture_source_audit(pd.DataFrame(), pd.DataFrame(), snapshots)
        decision = build_decision(source, snapshots, pd.DataFrame())
        self.assertEqual(int(source.iloc[0]["historical_ohlcv_used_as_microstructure_flag"]), 0)
        self.assertEqual(int(source.iloc[0]["missing_source_approximated_flag"]), 0)
        self.assertEqual(int(decision.iloc[0]["microstructure_ready_snapshot_count"]), 0)


if __name__ == "__main__":
    unittest.main()
