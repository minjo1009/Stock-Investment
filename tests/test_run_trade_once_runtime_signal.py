from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from app import run_trade_once
from state.store import initialize_store


class TestRunTradeOnceRuntimeSignal(unittest.TestCase):
    def test_runtime_snapshot_without_candidate_marks_skipped_no_signal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
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
            try:
                run_trade_once.os.environ["TRADING_DB_PATH"] = str(db_path)
                run_trade_once.run()
            finally:
                if old_db is None:
                    run_trade_once.os.environ.pop("TRADING_DB_PATH", None)
                else:
                    run_trade_once.os.environ["TRADING_DB_PATH"] = old_db

            con = sqlite3.connect(str(db_path))
            con.row_factory = sqlite3.Row
            try:
                row = con.execute(
                    """
                    SELECT symbol, side, result_status
                    FROM trade_runs
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                ).fetchone()
            finally:
                con.close()

            self.assertIsNotNone(row)
            self.assertEqual(str(row["symbol"]), "NO_SIGNAL")
            self.assertEqual(str(row["side"]), "NONE")
            self.assertEqual(str(row["result_status"]), "SKIPPED_NO_SIGNAL")

    def test_missing_control_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            initialize_store(str(db_path))

            old_db = run_trade_once.os.environ.get("TRADING_DB_PATH")
            try:
                run_trade_once.os.environ["TRADING_DB_PATH"] = str(db_path)
                with self.assertRaisesRegex(RuntimeError, "control_state table is missing"):
                    run_trade_once.run()
            finally:
                if old_db is None:
                    run_trade_once.os.environ.pop("TRADING_DB_PATH", None)
                else:
                    run_trade_once.os.environ["TRADING_DB_PATH"] = old_db

    def test_no_runtime_snapshot_skips_without_dummy_order(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "trading.db"
            initialize_store(str(db_path))
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
                con.commit()
            finally:
                con.close()

            old_db = run_trade_once.os.environ.get("TRADING_DB_PATH")
            try:
                run_trade_once.os.environ["TRADING_DB_PATH"] = str(db_path)
                with patch("app.run_trade_once.KISClient.from_env") as kis_mock:
                    run_trade_once.run()
                kis_mock.assert_not_called()
            finally:
                if old_db is None:
                    run_trade_once.os.environ.pop("TRADING_DB_PATH", None)
                else:
                    run_trade_once.os.environ["TRADING_DB_PATH"] = old_db

            con = sqlite3.connect(str(db_path))
            con.row_factory = sqlite3.Row
            try:
                row = con.execute(
                    """
                    SELECT symbol, side, result_status
                    FROM trade_runs
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                ).fetchone()
            finally:
                con.close()

            self.assertIsNotNone(row)
            self.assertEqual(str(row["symbol"]), "NO_RUNTIME_SNAPSHOT")
            self.assertEqual(str(row["side"]), "NONE")
            self.assertEqual(str(row["result_status"]), "SKIPPED_NO_RUNTIME_SNAPSHOT")


if __name__ == "__main__":
    unittest.main()
