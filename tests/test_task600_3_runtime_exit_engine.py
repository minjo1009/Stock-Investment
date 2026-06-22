from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.app.task_600_3_runtime_exit_engine import apply_runtime_exit_engine


class Task6003RuntimeExitEngineTest(unittest.TestCase):
    def _seed_runtime_db(self, db_path: Path) -> pd.DataFrame:
        con = sqlite3.connect(db_path)
        try:
            con.execute(
                """
                CREATE TABLE position_lifecycle (
                    position_id TEXT,
                    symbol TEXT,
                    entry_order_id TEXT,
                    entry_fill_id TEXT,
                    exit_order_id TEXT,
                    exit_fill_id TEXT,
                    entry_time TEXT,
                    exit_time TEXT,
                    holding_minutes REAL,
                    realized_pnl REAL,
                    exit_reason TEXT,
                    state TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    entry_qty REAL,
                    open_qty REAL,
                    closed_qty REAL,
                    matching_policy TEXT,
                    acceptance_status TEXT,
                    proxy_pnl_used_flag INTEGER,
                    proximity_fallback_used_flag INTEGER,
                    atr REAL
                )
                """
            )
            positions = [
                (
                    "life-stop",
                    "MSFT",
                    "entry-stop-order",
                    "entry-stop-fill",
                    "",
                    "",
                    "2026-06-03T13:00:00Z",
                    "",
                    None,
                    None,
                    "",
                    "OPEN",
                    100.0,
                    None,
                    1.0,
                    1.0,
                    0.0,
                    "EXACT_LIFECYCLE_ID_AND_ORDER_FILL_ID_ONLY",
                    "OPEN_ACCEPTED_EXACT_ENTRY",
                    0,
                    0,
                    2.0,
                ),
                (
                    "life-take-profit",
                    "AMD",
                    "entry-tp-order",
                    "entry-tp-fill",
                    "",
                    "",
                    "2026-06-03T13:00:00Z",
                    "",
                    None,
                    None,
                    "",
                    "OPEN",
                    100.0,
                    None,
                    1.0,
                    1.0,
                    0.0,
                    "EXACT_LIFECYCLE_ID_AND_ORDER_FILL_ID_ONLY",
                    "OPEN_ACCEPTED_EXACT_ENTRY",
                    0,
                    0,
                    2.0,
                ),
                (
                    "life-timeout",
                    "AMZN",
                    "entry-timeout-order",
                    "entry-timeout-fill",
                    "",
                    "",
                    "2026-06-03T13:00:00Z",
                    "",
                    None,
                    None,
                    "",
                    "OPEN",
                    100.0,
                    None,
                    1.0,
                    1.0,
                    0.0,
                    "EXACT_LIFECYCLE_ID_AND_ORDER_FILL_ID_ONLY",
                    "OPEN_ACCEPTED_EXACT_ENTRY",
                    0,
                    0,
                    2.0,
                ),
            ]
            con.executemany(
                """
                INSERT INTO position_lifecycle VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
                """,
                positions,
            )
            con.execute(
                """
                CREATE TABLE indicator_snapshots (
                    snapshot_id TEXT,
                    created_at TEXT,
                    symbol TEXT,
                    source_price REAL,
                    source_price_ts TEXT,
                    source_type TEXT
                )
                """
            )
            con.executemany(
                "INSERT INTO indicator_snapshots VALUES (?,?,?,?,?,?)",
                [
                    ("snap-stop", "2026-06-03T13:10:00Z", "MSFT", 95.0, "2026-06-03T13:10:00Z", "UNIT_TEST"),
                    ("snap-tp", "2026-06-03T13:20:00Z", "AMD", 108.5, "2026-06-03T13:20:00Z", "UNIT_TEST"),
                    ("snap-timeout", "2026-06-03T19:31:00Z", "AMZN", 101.0, "2026-06-03T19:31:00Z", "UNIT_TEST"),
                ],
            )
            con.execute(
                """
                CREATE TABLE runtime_strategy_decisions (
                    decision_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    decision_status TEXT,
                    symbol TEXT,
                    side TEXT,
                    quantity INTEGER,
                    limit_price REAL,
                    reason_code TEXT,
                    entry_allowed INTEGER,
                    created_by_task TEXT
                )
                """
            )
            con.executemany(
                "INSERT INTO runtime_strategy_decisions VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    ("decision-stop", "2026-06-03T12:59:00Z", "PAPER_ORDER_CANDIDATE", "MSFT", "BUY", 1, 100.0, "ENTRY", 1, "UNIT_TEST"),
                    ("decision-tp", "2026-06-03T12:59:00Z", "PAPER_ORDER_CANDIDATE", "AMD", "BUY", 1, 100.0, "ENTRY", 1, "UNIT_TEST"),
                    ("decision-timeout", "2026-06-03T12:59:00Z", "PAPER_ORDER_CANDIDATE", "AMZN", "BUY", 1, 100.0, "ENTRY", 1, "UNIT_TEST"),
                ],
            )
            con.commit()
            return pd.read_sql_query("SELECT * FROM runtime_strategy_decisions ORDER BY decision_id", con)
        finally:
            con.close()

    def test_runtime_exit_engine_creates_exact_paper_sell_fills_and_closes_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "runtime_exit.db"
            decisions_before = self._seed_runtime_db(db_path)

            artifacts = apply_runtime_exit_engine(db_path)

            con = sqlite3.connect(db_path)
            try:
                sell_fills = pd.read_sql_query("SELECT * FROM fills WHERE side='SELL' ORDER BY symbol", con)
                lifecycle = pd.read_sql_query("SELECT * FROM position_lifecycle ORDER BY position_id", con)
                events = pd.read_sql_query("SELECT * FROM paper_order_execution_events ORDER BY symbol", con)
                decisions_after = pd.read_sql_query("SELECT * FROM runtime_strategy_decisions ORDER BY decision_id", con)
            finally:
                con.close()

        summary = artifacts["runtime_exit_summary"].iloc[0]
        self.assertGreater(int(summary["sell_fill_count"]), 0)
        self.assertGreater(int(summary["closed_positions"]), 0)
        self.assertEqual(int(summary["inferred_matching_used_flag"]), 0)
        self.assertEqual(len(sell_fills), 3)
        self.assertEqual(set(sell_fills["source"]), {"PAPER_RUNTIME_SYNTHETIC_EXIT"})
        self.assertEqual(set(events["fill_confirmation_source"]), {"PAPER_RUNTIME_SYNTHETIC_EXIT"})
        self.assertEqual(set(events["broker_truth_fill_flag"].astype(int)), {0})
        self.assertEqual(set(lifecycle["state"]), {"CLOSED"})
        self.assertEqual(set(lifecycle["exit_reason"]), {"STOP", "TAKE_PROFIT", "TIMEOUT"})
        self.assertTrue(lifecycle["exit_order_id"].astype(str).str.len().gt(0).all())
        self.assertTrue(lifecycle["exit_fill_id"].astype(str).str.len().gt(0).all())
        self.assertTrue(lifecycle["realized_pnl"].notna().all())
        self.assertTrue(lifecycle["holding_minutes"].notna().all())
        self.assertEqual(set(lifecycle["proximity_fallback_used_flag"].astype(int)), {0})
        pd.testing.assert_frame_equal(decisions_before, decisions_after)

    def test_runtime_exit_engine_rejects_non_paper_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "runtime_exit.db"
            self._seed_runtime_db(db_path)
            with self.assertRaisesRegex(RuntimeError, "paper-only"):
                apply_runtime_exit_engine(db_path, environment="real")


if __name__ == "__main__":
    unittest.main()
