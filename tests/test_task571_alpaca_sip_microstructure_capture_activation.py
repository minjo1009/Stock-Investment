from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task571_alpaca_sip_microstructure_capture_activation import build_task571
from src.data.alpaca_stock_stream_archive import normalize_stream_payload


class Task571AlpacaSipMicrostructureCaptureActivationTest(unittest.TestCase):
    def test_missing_credentials_are_blocking_without_logging_secret_values(self) -> None:
        artifacts = build_task571(env={}, stream_archive_dir=Path("__missing__"))
        decision = artifacts["task_571_decision"].iloc[0]
        self.assertEqual(decision["strategy_acceptance_status"], "DATA_BLOCKED_CREDENTIAL_ENV_MISSING")
        self.assertEqual(int(artifacts["alpaca_credential_env_audit"]["secret_value_logged_flag"].max()), 0)

    def test_stream_client_compatibility_and_command_contract_are_generated(self) -> None:
        artifacts = build_task571(env={"APCA_API_KEY_ID": "x", "APCA_API_SECRET_KEY": "y"}, stream_archive_dir=Path("__missing__"))
        client = artifacts["alpaca_stream_client_audit"]
        commands = artifacts["alpaca_capture_command_contract"]
        self.assertTrue(client["compatibility_status"].eq("PASS").any())
        self.assertEqual(int(commands["secret_in_command_flag"].max()), 0)
        self.assertTrue(commands["command"].str.contains("--channels quotes,bars,updatedBars,statuses,lulds", regex=False).any())

    def test_archive_records_with_quote_status_luld_pass_capture_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = [
                {"T": "q", "S": "AAPL", "t": "2026-05-15T14:30:00Z", "bp": 100.0, "ap": 100.1, "bs": 10, "as": 12},
                {"T": "s", "S": "AAPL", "t": "2026-05-15T14:30:01Z", "sc": "T"},
                {"T": "l", "S": "AAPL", "t": "2026-05-15T14:30:02Z", "luld": "normal"},
            ]
            records = normalize_stream_payload(payload, recv_ts_utc="2026-05-15T14:30:03Z", recv_monotonic_ns=1)
            path = root / "trade_date=2026-05-15" / "channel=mixed" / "AAPL.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text("\n".join(json.dumps(row) for row in records), encoding="utf-8")
            artifacts = build_task571(env={"APCA_API_KEY_ID": "x", "APCA_API_SECRET_KEY": "y"}, stream_archive_dir=root)
            decision = artifacts["task_571_decision"].iloc[0]
            self.assertEqual(decision["strategy_acceptance_status"], "PAPER_SHADOW_CAPTURE_ROWS_AVAILABLE_REBUILD_TASK547")
            self.assertGreater(int(decision["quote_record_count"]), 0)
            self.assertGreater(int(decision["status_record_count"]), 0)
            self.assertGreater(int(decision["luld_record_count"]), 0)


if __name__ == "__main__":
    unittest.main()
