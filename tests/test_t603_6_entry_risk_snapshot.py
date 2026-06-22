from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from src.risk.build_entry_risk_snapshot import build_entry_risk_snapshot_from_db
from src.risk.validate_entry_risk_snapshot import validate_entry_risk_snapshot_from_db


class T6036EntryRiskSnapshotTest(unittest.TestCase):
    def test_ohlc_source_fixture_populates_atr_stop_and_take_profit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.db"
            self._create_position_lifecycle(db_path)
            self._create_market_bars(db_path, include_source=True, bar_count=15)
            self._create_indicator_snapshots(db_path)

            snapshots = build_entry_risk_snapshot_from_db(db_path, report_dir=None)
            artifacts = validate_entry_risk_snapshot_from_db(db_path, report_dir=None)
            summary = artifacts["entry_risk_snapshot_validation"].iloc[0]
            snapshot = snapshots.iloc[0]

            self.assertEqual(summary["acceptance_status"], "PASS")
            self.assertEqual(float(summary["snapshot_coverage"]), 1.0)
            self.assertEqual(float(summary["stop_price_populated"]), 1.0)
            self.assertEqual(float(summary["take_profit_price_populated"]), 1.0)
            self.assertAlmostEqual(float(snapshot["atr14"]), 2.0)
            self.assertAlmostEqual(float(snapshot["stop_price"]), 96.0)
            self.assertAlmostEqual(float(snapshot["take_profit_price"]), 108.0)
            self.assertAlmostEqual(float(snapshot["vwap"]), 114.0)
            self.assertAlmostEqual(float(snapshot["volume_ratio"]), 1.5)
            self.assertEqual(snapshot["market_regime"], "RISK_ON")
            self.assertEqual(int(snapshot["source_block"]), 0)

    def test_missing_ohlc_source_blocks_stop_tp_and_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.db"
            self._create_position_lifecycle(db_path)

            snapshots = build_entry_risk_snapshot_from_db(db_path, report_dir=None)
            artifacts = validate_entry_risk_snapshot_from_db(db_path, report_dir=None)
            summary = artifacts["entry_risk_snapshot_validation"].iloc[0]
            snapshot = snapshots.iloc[0]

            self.assertEqual(summary["acceptance_status"], "FAIL")
            self.assertEqual(summary["decision_status"], "FAIL_STOP_TP_SOURCE_BLOCKED")
            self.assertEqual(float(summary["snapshot_coverage"]), 1.0)
            self.assertEqual(float(summary["stop_price_populated"]), 0.0)
            self.assertEqual(float(summary["take_profit_price_populated"]), 0.0)
            self.assertTrue(pd.isna(snapshot["atr14"]))
            self.assertTrue(pd.isna(snapshot["stop_price"]))
            self.assertTrue(pd.isna(snapshot["take_profit_price"]))
            self.assertEqual(int(snapshot["source_block"]), 1)
            self.assertEqual(snapshot["atr_source_status"], "ATR_SOURCE_BLOCK_NO_MARKET_BARS_5M_SOURCE")

    def _create_position_lifecycle(self, db_path: Path) -> None:
        con = sqlite3.connect(db_path)
        try:
            con.execute(
                """
                CREATE TABLE position_lifecycle (
                    position_id TEXT,
                    symbol TEXT,
                    entry_time TEXT,
                    entry_price REAL,
                    state TEXT
                )
                """
            )
            con.execute(
                "INSERT INTO position_lifecycle VALUES (?,?,?,?,?)",
                ("pos-1", "MSFT", "2026-06-03T14:15:00Z", 100.0, "OPEN"),
            )
            con.commit()
        finally:
            con.close()

    def _create_market_bars(self, db_path: Path, *, include_source: bool, bar_count: int) -> None:
        con = sqlite3.connect(db_path)
        try:
            if include_source:
                con.execute(
                    """
                    CREATE TABLE market_bars_5m (
                        bar_id TEXT,
                        symbol TEXT,
                        bar_end_ts TEXT,
                        open REAL,
                        high REAL,
                        low REAL,
                        close REAL,
                        volume REAL,
                        vwap REAL,
                        volume_ratio REAL
                    )
                    """
                )
                start = datetime(2026, 6, 3, 13, 0, tzinfo=UTC)
                rows = []
                for index in range(bar_count):
                    ts = start + timedelta(minutes=5 * index)
                    rows.append(
                        (
                            f"MSFT:{index}",
                            "MSFT",
                            ts.isoformat().replace("+00:00", "Z"),
                            100.0 + index,
                            101.0 + index,
                            99.0 + index,
                            100.0 + index,
                            1000.0,
                            100.0 + index,
                            1.5,
                        )
                    )
                con.executemany("INSERT INTO market_bars_5m VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
            con.commit()
        finally:
            con.close()

    def _create_indicator_snapshots(self, db_path: Path) -> None:
        con = sqlite3.connect(db_path)
        try:
            con.execute(
                """
                CREATE TABLE indicator_snapshots (
                    snapshot_id TEXT,
                    created_at TEXT,
                    symbol TEXT,
                    market_regime TEXT
                )
                """
            )
            con.execute(
                "INSERT INTO indicator_snapshots VALUES (?,?,?,?)",
                ("snap-1", "2026-06-03T14:10:00Z", "MSFT", "RISK_ON"),
            )
            con.commit()
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
