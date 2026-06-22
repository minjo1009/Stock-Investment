from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.app import task_583_live_signal_refresh_repair as task583
from src.app.task_089_market_data_signal_refresh import _init_tables


class Task583LiveSignalRefreshRepairTest(unittest.TestCase):
    def test_report_keeps_stale_rows_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            _init_tables(str(db_path))
            with (
                patch.object(task583, "_run_task089", return_value=("ok", "", 0)),
                patch.object(task583, "REPORT_DIR", Path(tmp) / "reports"),
            ):
                artifacts = task583.run_task583(db_path=db_path, env_file=Path(tmp) / "missing.env")
            decision = artifacts["task_583_decision.csv"].iloc[0].to_dict()
            self.assertEqual(decision["decision_status"], "DATA_BLOCKED_NO_INDICATOR_SNAPSHOT")
            self.assertEqual(int(decision["paper_order_candidate_rows"]), 0)
            self.assertEqual(decision["universe_scope"], "theme_10x7")
            self.assertGreater(int(decision["expected_universe_count"]), 0)
            self.assertEqual(decision["coverage_status"], "UNIVERSE_COVERAGE_GAP")

    def test_runtime_candidate_audit_marks_fresh_entry_candidate(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "snapshot_id": "s1",
                    "created_at": "2026-05-20T01:00:00Z",
                    "symbol": "AAPL",
                    "data_fresh": 1,
                    "entry_allowed": 1,
                    "selected_for_portfolio": 1,
                    "side": "BUY",
                    "score": 1.0,
                }
            ]
        )
        audit = task583._runtime_candidates(frame, expected_symbols=["AAPL", "MSFT"], universe_scope="theme_10x7")
        self.assertEqual(audit.iloc[0]["candidate_status"], "PAPER_ORDER_CANDIDATE")
        self.assertEqual(audit.iloc[0]["symbol_status"], "ENTRY_ALLOWED")
        self.assertIn("MISSING_SOURCE", set(audit["symbol_status"].astype(str)))
        self.assertEqual(audit.iloc[0]["universe_scope"], "theme_10x7")

    def test_stale_source_scoreboard_names_unblock_conditions(self) -> None:
        inventory = pd.DataFrame(
            [
                {
                    "symbol": "AAPL",
                    "symbol_status": "STALE_SOURCE",
                    "data_fresh": 0,
                    "source_type": "RAW_INTRADAY_HISTORY",
                    "stale_reason": "RAW_INTRADAY_HISTORY_STALE",
                    "provider_reason": "RAW_INTRADAY_AVAILABLE",
                    "raw_intraday_exists_flag": 1,
                    "raw_daily_exists_flag": 1,
                },
                {
                    "symbol": "MSFT",
                    "symbol_status": "FRESH_EVALUATED",
                    "data_fresh": 1,
                    "source_type": "KIS_CURRENT_PRICE_APPENDED",
                    "stale_reason": "",
                    "provider_reason": "LIVE_QUOTE_ATTACHED",
                    "raw_intraday_exists_flag": 1,
                    "raw_daily_exists_flag": 1,
                },
            ]
        )
        scoreboard = task583._stale_source_closure_scoreboard(inventory)
        self.assertEqual(len(scoreboard), 1)
        row = scoreboard.iloc[0].to_dict()
        self.assertEqual(row["owner"], "윤헌")
        self.assertEqual(row["symbol"], "AAPL")
        self.assertEqual(row["status"], "OPEN_SOURCE_BLOCKER")
        self.assertIn("do not infer", row["unblock_condition"])

    def test_latest_indicator_snapshot_uses_latest_row_per_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            _init_tables(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("old-aapl", "2026-05-20T01:00:00Z", "AAPL", "2026-05-20T01:00:00Z", 100, 99, 98, 97, 101, 0, 0, 0, 0, 0, "HOLD", "NONE", "STALE", 0.0, 1, 0),
                )
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("new-aapl", "2026-05-20T02:00:00Z", "AAPL", "2026-05-20T02:00:00Z", 101, 99, 98, 97, 100, 1, 1, 1, 1, 0, "ENTER", "BUY", "BREAKOUT", 1.0, 1, 1),
                )
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("msft", "2026-05-20T01:30:00Z", "MSFT", "2026-05-20T01:30:00Z", 50, 49, 48, 47, 51, 1, 1, 0, 1, 0, "HOLD", "BUY", "NO_ENTRY", 0.5, 2, 0),
                )
                con.commit()
            finally:
                con.close()
            latest = task583._latest_indicator_snapshot_per_symbol(db_path, ["AAPL", "MSFT"])
        self.assertEqual(set(latest["snapshot_id"].astype(str)), {"new-aapl", "msft"})
        audit = task583._freshness_audit(latest, expected_symbols=["AAPL", "MSFT"], universe_scope="theme_10x7")
        self.assertEqual(int(audit.iloc[0]["fresh_symbol_count"]), 2)


if __name__ == "__main__":
    unittest.main()
