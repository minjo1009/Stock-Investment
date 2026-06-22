from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task495_microstructure_live_source_readiness import build_task495_microstructure_live_source_readiness
from src.data.alpaca_stock_stream_archive import JsonlArchiveWriter, normalize_stream_payload
from src.data.full_depth_book_archive import FullDepthBookArchive, FullDepthBookProviderUnavailable


class Task495MicrostructureLiveSourceReadinessTest(unittest.TestCase):
    def test_stream_payload_adds_raw_receive_timestamp_and_hash(self) -> None:
        records = normalize_stream_payload(
            [{"T": "q", "S": "AAPL", "bp": 100.0, "ap": 100.01, "t": "2024-01-02T14:30:00Z"}],
            recv_ts_utc="2024-01-02T14:30:01Z",
            recv_monotonic_ns=123,
        )
        self.assertEqual(records[0]["recv_ts_utc"], "2024-01-02T14:30:01Z")
        self.assertEqual(records[0]["channel"], "quotes")
        self.assertTrue(records[0]["raw_message_hash"])
        with tempfile.TemporaryDirectory() as tmp:
            writer = JsonlArchiveWriter(Path(tmp))
            self.assertEqual(writer.write_records(records), 1)
            files = list(Path(tmp).rglob("*.jsonl"))
            self.assertEqual(len(files), 1)
            payload = json.loads(files[0].read_text(encoding="utf-8").strip())
            self.assertEqual(payload["symbol"], "AAPL")

    def test_full_depth_fails_fast_without_provider(self) -> None:
        archive = FullDepthBookArchive(output_dir=Path("unused"))
        status = archive.readiness()
        self.assertEqual(status.implemented_flag, 0)
        with self.assertRaises(FullDepthBookProviderUnavailable):
            archive.run()

    def test_task495_reports_no_fake_depth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = build_task495_microstructure_live_source_readiness(out_dir=Path(tmp) / "out")
            decision = artifacts["decision"].iloc[0]
            self.assertEqual(int(decision["raw_receive_timestamp_implemented_flag"]), 1)
            self.assertEqual(int(decision["status_luld_live_archive_implemented_flag"]), 1)
            self.assertEqual(int(decision["full_depth_book_implemented_flag"]), 0)
            self.assertEqual(int(decision["fake_depth_or_luld_used_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
