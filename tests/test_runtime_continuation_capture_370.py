from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.continuation_runtime_capture_370 import emit_continuation_capture_event
from app import run_trade_once
from state.store import initialize_store


class TestRuntimeContinuationCapture370(unittest.TestCase):
    def test_emit_continuation_capture_event_is_paper_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            capture_path = Path(td) / "capture.jsonl"
            emit_continuation_capture_event(
                db_path=str(Path(td) / "trading.db"),
                environment="live",
                run_id="run-live",
                event_type="SETUP_DETECTED",
                symbol="AAPL",
                side="BUY",
                reason="live_should_not_write",
                payload={"value": 1},
            )
            self.assertFalse(capture_path.exists())

    def test_run_trade_once_no_signal_emits_invalidation_capture(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            capture_path = Path(td) / "continuation_capture.jsonl"
            initialize_store(str(db_path))

            now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            con = sqlite3.connect(str(db_path))
            try:
                con.execute(
                    """
                    CREATE TABLE IF NOT EXISTS control_state (
                        control_key TEXT PRIMARY KEY,
                        run_mode TEXT NOT NULL,
                        kill_switch_active INTEGER NOT NULL,
                        kill_switch_reason TEXT
                    )
                    """
                )
                con.execute(
                    """
                    INSERT OR REPLACE INTO control_state(control_key, run_mode, kill_switch_active, kill_switch_reason)
                    VALUES('default', 'LIVE_ENABLED', 0, '')
                    """
                )
                con.execute(
                    """
                    CREATE TABLE IF NOT EXISTS indicator_snapshots (
                        snapshot_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        action TEXT,
                        side TEXT,
                        reason TEXT,
                        score REAL,
                        close REAL,
                        entry_allowed INTEGER NOT NULL,
                        data_fresh INTEGER NOT NULL
                    )
                    """
                )
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, action, side, reason, score, close, entry_allowed, data_fresh
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"{now}:AAPL",
                        now,
                        "AAPL",
                        "HOLD",
                        "NONE",
                        "NO_ENTRY",
                        0.0,
                        100.0,
                        0,
                        1,
                    ),
                )
                con.commit()
            finally:
                con.close()

            old_db = run_trade_once.os.environ.get("TRADING_DB_PATH")
            old_capture = run_trade_once.os.environ.get("TRADING_CONTINUATION_CAPTURE_PATH")
            old_env = run_trade_once.os.environ.get("KIS_ENVIRONMENT")
            try:
                run_trade_once.os.environ["TRADING_DB_PATH"] = str(db_path)
                run_trade_once.os.environ["TRADING_CONTINUATION_CAPTURE_PATH"] = str(capture_path)
                run_trade_once.os.environ["KIS_ENVIRONMENT"] = "paper"
                run_trade_once.run()
            finally:
                if old_db is None:
                    run_trade_once.os.environ.pop("TRADING_DB_PATH", None)
                else:
                    run_trade_once.os.environ["TRADING_DB_PATH"] = old_db
                if old_capture is None:
                    run_trade_once.os.environ.pop("TRADING_CONTINUATION_CAPTURE_PATH", None)
                else:
                    run_trade_once.os.environ["TRADING_CONTINUATION_CAPTURE_PATH"] = old_capture
                if old_env is None:
                    run_trade_once.os.environ.pop("KIS_ENVIRONMENT", None)
                else:
                    run_trade_once.os.environ["KIS_ENVIRONMENT"] = old_env

            lines = capture_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertEqual(record["event_type"], "INVALIDATION")
            self.assertEqual(record["symbol"], "NO_SIGNAL")
            self.assertEqual(record["side"], "NONE")
            self.assertEqual(record["result_status"], "SKIPPED_NO_SIGNAL")
            self.assertEqual(record["reason"], "runtime_no_candidate")


if __name__ == "__main__":
    unittest.main()
