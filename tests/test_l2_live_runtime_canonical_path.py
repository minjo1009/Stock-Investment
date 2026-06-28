from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.validate_l2_canonical_primitive_contract import validate as validate_contract
from scripts.validate_l2_historical_live_separation import validate as validate_separation
from scripts.validate_l2_live_runtime_canonical_path import validate as validate_live_runtime
from scripts.validate_l2_no_trade_outputs import validate as validate_no_trade_outputs
from scripts.validate_l3_inputs_are_l2_canonical import validate as validate_l3_inputs
from src.app.task_089_market_data_signal_refresh import _init_tables, _upsert_indicator_snapshots
from src.l2.live_runtime import write_live_runtime_l2_primitives_from_db
from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC


class L2LiveRuntimeCanonicalPathTest(unittest.TestCase):
    def test_task089_snapshot_writes_live_l2_receipts_batches_and_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "runtime.db"
            _init_tables(str(db_path))
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    INSERT INTO market_bars_5m(
                        bar_id, symbol, bar_start_ts, bar_end_ts, open, high, low, close, volume, tick_count, source, last_updated_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        "AAPL:2026-06-01T10:00:00Z",
                        "AAPL",
                        "2026-06-01T10:00:00Z",
                        "2026-06-01T10:05:00Z",
                        100.0,
                        101.0,
                        99.0,
                        100.5,
                        1000.0,
                        10,
                        "KIS_QUOTE",
                        "2026-06-01T10:05:00Z",
                    ),
                )
                conn.commit()
            finally:
                conn.close()
            created_at = "2026-06-01T10:10:00Z"
            ranked = [
                {
                    "symbol": "AAPL",
                    "bar_end_ts": "2026-06-01T10:05:00Z",
                    "close": 100.5,
                    "ma20": 99.0,
                    "ma50": 98.0,
                    "ma200": 97.0,
                    "breakout_high_20": 100.0,
                    "breakout_condition": True,
                    "ma_condition": True,
                    "entry_allowed": True,
                    "data_fresh": True,
                    "insufficient_history": False,
                    "action": "ENTER",
                    "side": "BUY",
                    "reason": "BREAKOUT",
                    "score": 1.23,
                    "source_price_ts": "2026-06-01T10:05:00Z",
                    "source_price": 100.5,
                    "source_type": "KIS_CURRENT_PRICE_APPENDED",
                    "freshness_age_sec": 300.0,
                    "stale_reason": "",
                    "selected_for_portfolio": True,
                }
            ]
            _upsert_indicator_snapshots(str(db_path), created_at=created_at, ranked=ranked)
            summary = write_live_runtime_l2_primitives_from_db(
                db_path,
                capture_ts=created_at,
                symbols=["AAPL"],
                indicator_rows=ranked,
            )
            self.assertEqual(summary["runtime_context"], LIVE_INTRADAY_DIAGNOSTIC)
            self.assertEqual(summary["market_fact_count"], 1)
            self.assertEqual(summary["indicator_fact_count"], 1)
            self.assertEqual(validate_contract(db_path), [])
            self.assertEqual(validate_separation(db_path), [])
            self.assertEqual(validate_no_trade_outputs(db_path), [])
            self.assertEqual(validate_l3_inputs(db_path), [])
            self.assertEqual(validate_live_runtime(db_path), [])
            conn = sqlite3.connect(db_path)
            try:
                payload = conn.execute(
                    "SELECT primitive_payload_json FROM l2_primitive_facts WHERE source_family = 'indicator'"
                ).fetchone()[0]
            finally:
                conn.close()
            self.assertNotIn("BUY", payload)
            self.assertNotIn("score", payload)
            self.assertNotIn("entry_allowed", payload)

    def test_missing_live_source_is_blocker_not_l3_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "runtime.db"
            _init_tables(str(db_path))
            created_at = "2026-06-01T10:10:00Z"
            ranked = [
                {
                    "symbol": "MSFT",
                    "bar_end_ts": "2026-06-01T10:10:00Z",
                    "close": 0.0,
                    "ma20": 0.0,
                    "ma50": 0.0,
                    "ma200": 0.0,
                    "breakout_high_20": 0.0,
                    "breakout_condition": False,
                    "ma_condition": False,
                    "entry_allowed": False,
                    "data_fresh": False,
                    "insufficient_history": True,
                    "action": "HOLD",
                    "side": "NONE",
                    "reason": "MISSING_SOURCE",
                    "score": -999.0,
                    "source_price_ts": "",
                    "source_price": 0.0,
                    "source_type": "MISSING_SOURCE",
                    "freshness_age_sec": 0.0,
                    "stale_reason": "MISSING_SOURCE",
                    "selected_for_portfolio": False,
                }
            ]
            _upsert_indicator_snapshots(str(db_path), created_at=created_at, ranked=ranked)
            summary = write_live_runtime_l2_primitives_from_db(
                db_path,
                capture_ts=created_at,
                symbols=["MSFT"],
                indicator_rows=ranked,
            )
            self.assertEqual(summary["parent_freshness_by_symbol"]["MSFT"], "MISSING")
            self.assertEqual(validate_contract(db_path), [])
            self.assertEqual(validate_live_runtime(db_path), [])
            conn = sqlite3.connect(db_path)
            try:
                l3_count = conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM l2_primitive_facts
                    WHERE source_family = 'indicator'
                      AND source_time_certified = 1
                      AND freshness_status IN ('FRESH', 'CURRENT_OR_RECENT')
                    """
                ).fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(int(l3_count), 0)


if __name__ == "__main__":
    unittest.main()
