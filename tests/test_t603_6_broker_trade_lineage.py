from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.execution.broker_fill_reconciliation import reconcile_broker_trade_lineage
from src.execution.validate_broker_trade_lineage import validate_broker_trade_lineage_db


class T6036BrokerTradeLineageTest(unittest.TestCase):
    def _create_lifecycle_table(self, con: sqlite3.Connection) -> None:
        con.execute(
            """
            CREATE TABLE position_lifecycle (
                position_id TEXT,
                symbol TEXT,
                entry_order_id TEXT,
                entry_fill_id TEXT,
                exit_order_id TEXT,
                exit_fill_id TEXT,
                state TEXT
            )
            """
        )

    def _create_fills_table(self, con: sqlite3.Connection) -> None:
        con.execute(
            """
            CREATE TABLE fills (
                fill_id TEXT PRIMARY KEY,
                order_id TEXT,
                run_id TEXT,
                symbol TEXT,
                side TEXT,
                filled_quantity REAL,
                fill_price REAL,
                filled_at TEXT,
                source TEXT,
                dedupe_key TEXT
            )
            """
        )

    def _create_orders_table(self, con: sqlite3.Connection) -> None:
        con.execute(
            """
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                run_id TEXT,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                intent_key TEXT,
                submitted_at TEXT,
                status TEXT,
                raw_status TEXT,
                environment TEXT
            )
            """
        )

    def _insert_lifecycle(
        self,
        con: sqlite3.Connection,
        *,
        position_id: str = "life-1",
        symbol: str = "AMD",
        exit_order_id: str = "broker-sell-order-1",
        exit_fill_id: str = "runtime-sell-fill-1",
    ) -> None:
        con.execute(
            "INSERT INTO position_lifecycle VALUES (?,?,?,?,?,?,?)",
            (
                position_id,
                symbol,
                f"entry-order-{position_id}",
                f"entry-fill-{position_id}",
                exit_order_id,
                exit_fill_id,
                "CLOSED",
            ),
        )

    def _insert_order(self, con: sqlite3.Connection, *, order_id: str, signal_id: str, symbol: str = "AMD") -> None:
        con.execute(
            "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                order_id,
                "run-1",
                symbol,
                "SELL",
                1.0,
                signal_id,
                "2026-06-03T15:00:00Z",
                "FILLED",
                "FILLED",
                "paper",
            ),
        )

    def _insert_fill(
        self,
        con: sqlite3.Connection,
        *,
        fill_id: str,
        order_id: str,
        source: str,
        symbol: str = "AMD",
        price: float = 111.0,
    ) -> None:
        con.execute(
            "INSERT INTO fills VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                fill_id,
                order_id,
                "run-1",
                symbol,
                "SELL",
                1.0,
                price,
                "2026-06-03T15:01:00Z",
                source,
                f"dedupe-{fill_id}",
            ),
        )

    def test_pass_fixture_links_only_exact_broker_truth_sell_fill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "pass.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                self._create_orders_table(con)
                self._insert_lifecycle(con)
                self._insert_order(con, order_id="broker-sell-order-1", signal_id="signal-1")
                self._insert_fill(
                    con,
                    fill_id="runtime-sell-fill-1",
                    order_id="runtime-sell-order-1",
                    source="PAPER_RUNTIME_SYNTHETIC_EXIT",
                )
                self._insert_fill(
                    con,
                    fill_id="broker-sell-fill-1",
                    order_id="broker-sell-order-1",
                    source="ORDER_STATUS",
                )
                con.commit()
            finally:
                con.close()

            artifacts = reconcile_broker_trade_lineage(db_path)
            validation = validate_broker_trade_lineage_db(db_path)

            con = sqlite3.connect(db_path)
            try:
                lineage = pd.read_sql_query("SELECT * FROM broker_trade_lineage", con)
            finally:
                con.close()

        row = validation.iloc[0]
        self.assertEqual(row["acceptance_status"], "PASS")
        self.assertEqual(int(row["broker_truth_sell_fills"]), 1)
        self.assertEqual(float(row["lineage_coverage"]), 100.0)
        self.assertEqual(float(row["broker_fill_linkage"]), 100.0)
        self.assertEqual(lineage.iloc[0]["signal_id"], "signal-1")
        self.assertEqual(lineage.iloc[0]["fill_id"], "runtime-sell-fill-1")
        self.assertEqual(lineage.iloc[0]["broker_fill_id"], "broker-sell-fill-1")
        self.assertEqual(lineage.iloc[0]["broker_status"], "FILLED")
        self.assertEqual(len(artifacts["broker_trade_lineage"]), 1)

    def test_broker_truth_zero_fixture_fails_without_promoting_synthetic_sell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fail.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                self._create_orders_table(con)
                self._insert_lifecycle(
                    con,
                    position_id="life-2",
                    symbol="MSFT",
                    exit_order_id="runtime-sell-order-2",
                    exit_fill_id="runtime-sell-fill-2",
                )
                self._insert_order(con, order_id="runtime-sell-order-2", signal_id="signal-2", symbol="MSFT")
                self._insert_fill(
                    con,
                    fill_id="runtime-sell-fill-2",
                    order_id="runtime-sell-order-2",
                    source="PAPER_RUNTIME_SYNTHETIC_EXIT",
                    symbol="MSFT",
                )
                con.commit()
            finally:
                con.close()

            reconcile_broker_trade_lineage(db_path)
            validation = validate_broker_trade_lineage_db(db_path)

            con = sqlite3.connect(db_path)
            try:
                lineage = pd.read_sql_query("SELECT * FROM broker_trade_lineage", con)
            finally:
                con.close()

        row = validation.iloc[0]
        self.assertEqual(row["current_status"], "FAIL_BROKER_TRUTH_SELL_FILLS_ZERO")
        self.assertEqual(row["acceptance_status"], "FAIL")
        self.assertEqual(int(row["broker_truth_sell_fills"]), 0)
        self.assertEqual(float(row["lineage_coverage"]), 100.0)
        self.assertEqual(float(row["broker_fill_linkage"]), 0.0)
        self.assertEqual(lineage.iloc[0]["fill_id"], "runtime-sell-fill-2")
        self.assertIsNone(lineage.iloc[0]["broker_fill_id"])


if __name__ == "__main__":
    unittest.main()
