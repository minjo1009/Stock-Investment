from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.execution.exit_fill_reconciliation import reconcile_exit_fill_lineage


class Task6004BrokerTruthExitLifecycleTest(unittest.TestCase):
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
                proximity_fallback_used_flag INTEGER
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

    def _insert_lifecycle(
        self,
        con: sqlite3.Connection,
        *,
        position_id: str,
        symbol: str,
        exit_order_id: str,
        exit_fill_id: str,
        exit_time: str = "2026-06-03T15:00:00Z",
        exit_price: float = 110.0,
    ) -> None:
        con.execute(
            """
            INSERT INTO position_lifecycle VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            """,
            (
                position_id,
                symbol,
                f"entry-order-{position_id}",
                f"entry-fill-{position_id}",
                exit_order_id,
                exit_fill_id,
                "2026-06-03T13:00:00Z",
                exit_time,
                120.0,
                10.0,
                "TIMEOUT",
                "CLOSED",
                100.0,
                exit_price,
                1.0,
                0.0,
                1.0,
                "EXACT_POSITION_ID_AND_ENTRY_ORDER_FILL_ID_ONLY",
                "CLOSED_RUNTIME_PAPER_EXACT_IDS",
                0,
                0,
            ),
        )

    def _insert_fill(
        self,
        con: sqlite3.Connection,
        *,
        fill_id: str,
        order_id: str,
        symbol: str,
        source: str,
        filled_at: str = "2026-06-03T15:00:00Z",
        price: float = 110.0,
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
                filled_at,
                source,
                f"dedupe-{fill_id}",
            ),
        )

    def test_exact_broker_order_status_sell_fill_maps_without_replacing_t6003_exit_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "task6004.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                for index in range(1, 3):
                    self._insert_lifecycle(
                        con,
                        position_id=f"life-{index}",
                        symbol="AMD",
                        exit_order_id=f"broker-sell-order-{index}",
                        exit_fill_id=f"runtime-exit-fill-{index}",
                    )
                    self._insert_fill(
                        con,
                        fill_id=f"runtime-exit-fill-{index}",
                        order_id=f"runtime-sell-order-{index}",
                        symbol="AMD",
                        source="PAPER_RUNTIME_SYNTHETIC_EXIT",
                    )
                    self._insert_fill(
                        con,
                        fill_id=f"broker-sell-fill-{index}",
                        order_id=f"broker-sell-order-{index}",
                        symbol="AMD",
                        source="ORDER_STATUS",
                    )
                con.commit()
            finally:
                con.close()

            artifacts = reconcile_exit_fill_lineage(db_path)

            con = sqlite3.connect(db_path)
            try:
                lifecycle = pd.read_sql_query("SELECT * FROM position_lifecycle ORDER BY position_id", con)
            finally:
                con.close()

        summary = artifacts["broker_truth_exit_summary"].iloc[0]
        self.assertEqual(summary["acceptance_status"], "PASS")
        self.assertEqual(int(summary["broker_truth_sell_fills"]), 2)
        self.assertEqual(float(summary["exit_fill_linkage_coverage"]), 100.0)
        self.assertEqual(float(summary["closed_positions_with_fill"]), 100.0)
        self.assertEqual(set(lifecycle["exit_fill_id"]), {"runtime-exit-fill-1", "runtime-exit-fill-2"})
        self.assertEqual(set(lifecycle["broker_fill_id"]), {"broker-sell-fill-1", "broker-sell-fill-2"})
        self.assertEqual(set(lifecycle["broker_fill_price"].astype(float)), {110.0})

    def test_runtime_synthetic_and_position_delta_fallback_are_not_broker_truth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "task6004.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                self._insert_lifecycle(
                    con,
                    position_id="life-1",
                    symbol="MSFT",
                    exit_order_id="runtime-sell-order-1",
                    exit_fill_id="runtime-exit-fill-1",
                )
                self._insert_fill(
                    con,
                    fill_id="runtime-exit-fill-1",
                    order_id="runtime-sell-order-1",
                    symbol="MSFT",
                    source="PAPER_RUNTIME_SYNTHETIC_EXIT",
                )
                self._insert_fill(
                    con,
                    fill_id="position-delta-fill-1",
                    order_id="runtime-sell-order-1",
                    symbol="MSFT",
                    source="POSITION_DELTA_FALLBACK",
                )
                con.commit()
            finally:
                con.close()

            artifacts = reconcile_exit_fill_lineage(db_path)

            con = sqlite3.connect(db_path)
            try:
                broker_fill_id = con.execute("SELECT broker_fill_id FROM position_lifecycle").fetchone()[0]
            finally:
                con.close()

        summary = artifacts["broker_truth_exit_summary"].iloc[0]
        self.assertEqual(summary["current_status"], "FAIL_BROKER_TRUTH_SELL_FILLS_ZERO")
        self.assertEqual(int(summary["broker_truth_sell_fills"]), 0)
        self.assertEqual(int(summary["missing_broker_exit_count"]), 1)
        self.assertIsNone(broker_fill_id)

    def test_same_symbol_price_and_time_are_not_used_without_exact_exit_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "task6004.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                self._insert_lifecycle(
                    con,
                    position_id="life-1",
                    symbol="AMD",
                    exit_order_id="expected-exit-order",
                    exit_fill_id="runtime-exit-fill-1",
                    exit_time="2026-06-03T15:00:00Z",
                    exit_price=123.45,
                )
                self._insert_fill(
                    con,
                    fill_id="runtime-exit-fill-1",
                    order_id="runtime-exit-order",
                    symbol="AMD",
                    source="PAPER_RUNTIME_SYNTHETIC_EXIT",
                    filled_at="2026-06-03T15:00:00Z",
                    price=123.45,
                )
                self._insert_fill(
                    con,
                    fill_id="broker-fill-same-symbol-time-price",
                    order_id="different-broker-order",
                    symbol="AMD",
                    source="ORDER_STATUS",
                    filled_at="2026-06-03T15:00:00Z",
                    price=123.45,
                )
                con.commit()
            finally:
                con.close()

            artifacts = reconcile_exit_fill_lineage(db_path)

            con = sqlite3.connect(db_path)
            try:
                broker_fill_id = con.execute("SELECT broker_fill_id FROM position_lifecycle").fetchone()[0]
            finally:
                con.close()

        summary = artifacts["broker_truth_exit_summary"].iloc[0]
        mapping = artifacts["broker_truth_exit_mapping"].iloc[0]
        self.assertEqual(summary["acceptance_status"], "FAIL")
        self.assertEqual(int(summary["broker_truth_sell_fills"]), 1)
        self.assertEqual(int(summary["mapped_broker_truth_exits"]), 0)
        self.assertEqual(mapping["mapping_status"], "MISSING_EXACT_BROKER_TRUTH_EXIT")
        self.assertEqual(int(mapping["proximity_fallback_used_flag"]), 0)
        self.assertIsNone(broker_fill_id)

    def test_exact_broker_event_source_can_map_exit_when_fill_table_row_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "task6004.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                self._insert_lifecycle(
                    con,
                    position_id="life-1",
                    symbol="AMZN",
                    exit_order_id="broker-event-order-1",
                    exit_fill_id="runtime-exit-fill-1",
                )
                self._insert_fill(
                    con,
                    fill_id="runtime-exit-fill-1",
                    order_id="runtime-sell-order-1",
                    symbol="AMZN",
                    source="PAPER_RUNTIME_SYNTHETIC_EXIT",
                )
                con.execute(
                    """
                    CREATE TABLE paper_order_execution_events (
                        event_id TEXT,
                        created_at TEXT,
                        order_id TEXT,
                        lifecycle_id TEXT,
                        symbol TEXT,
                        side TEXT,
                        broker_truth_fill_flag INTEGER,
                        filled_qty REAL,
                        filled_avg_price REAL,
                        fill_confirmation_source TEXT,
                        raw_response_json TEXT
                    )
                    """
                )
                con.execute(
                    "INSERT INTO paper_order_execution_events VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        "broker-event-1",
                        "2026-06-03T15:00:00Z",
                        "broker-event-order-1",
                        "life-1",
                        "AMZN",
                        "SELL",
                        1,
                        1.0,
                        222.2,
                        "ORDER_STATUS",
                        '{"fills":[{"fill_id":"broker-event-fill-1"}]}',
                    ),
                )
                con.commit()
            finally:
                con.close()

            artifacts = reconcile_exit_fill_lineage(db_path)

            con = sqlite3.connect(db_path)
            try:
                lifecycle = pd.read_sql_query("SELECT * FROM position_lifecycle", con)
            finally:
                con.close()

        summary = artifacts["broker_truth_exit_summary"].iloc[0]
        self.assertEqual(summary["acceptance_status"], "PASS")
        self.assertEqual(lifecycle.iloc[0]["broker_fill_id"], "broker-event-fill-1")
        self.assertEqual(float(lifecycle.iloc[0]["broker_fill_price"]), 222.2)


if __name__ == "__main__":
    unittest.main()
