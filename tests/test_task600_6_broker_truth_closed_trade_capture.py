from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.execution.broker_truth_closed_trade_capture import (
    capture_broker_truth_closed_trade_evidence,
    write_broker_truth_closed_trade_reports,
)


class Task6006BrokerTruthClosedTradeCaptureTest(unittest.TestCase):
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
        exit_order_id: str = "broker-sell-order-1",
        exit_fill_id: str = "runtime-sell-fill-1",
    ) -> None:
        con.execute(
            "INSERT INTO position_lifecycle VALUES (?,?,?,?,?,?,?)",
            (
                position_id,
                "AMD",
                f"entry-order-{position_id}",
                f"entry-fill-{position_id}",
                exit_order_id,
                exit_fill_id,
                "CLOSED",
            ),
        )

    def _insert_fill(
        self,
        con: sqlite3.Connection,
        *,
        fill_id: str,
        order_id: str,
        side: str,
        source: str,
    ) -> None:
        con.execute(
            "INSERT INTO fills VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                fill_id,
                order_id,
                "run-1",
                "AMD",
                side,
                1.0,
                101.0,
                "2026-06-03T15:01:00Z",
                source,
                f"dedupe-{fill_id}",
            ),
        )

    def test_current_db_shape_fails_without_promoting_synthetic_sell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "task6006.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                self._create_orders_table(con)
                self._insert_lifecycle(
                    con,
                    exit_order_id="runtime-sell-order-1",
                    exit_fill_id="runtime-sell-fill-1",
                )
                self._insert_fill(
                    con,
                    fill_id="buy-order-status-fill-1",
                    order_id="buy-order-1",
                    side="BUY",
                    source="ORDER_STATUS",
                )
                self._insert_fill(
                    con,
                    fill_id="runtime-sell-fill-1",
                    order_id="runtime-sell-order-1",
                    side="SELL",
                    source="PAPER_RUNTIME_SYNTHETIC_EXIT",
                )
                con.commit()
            finally:
                con.close()

            artifacts = capture_broker_truth_closed_trade_evidence(db_path)

        summary = artifacts["broker_truth_closed_trade_summary"].iloc[0]
        rejected = artifacts["broker_truth_closed_trade_rejected_sources"]
        self.assertEqual(summary["current_status"], "FAIL_BROKER_TRUTH_SELL_SOURCE_MISSING")
        self.assertEqual(int(summary["broker_truth_sell_fills"]), 0)
        self.assertEqual(int(summary["accepted_buy_order_status_source_rows"]), 1)
        self.assertEqual(int(summary["synthetic_sell_rows"]), 1)
        self.assertEqual(rejected.iloc[0]["rejection_reason"], "SYNTHETIC_RUNTIME_SELL_NOT_BROKER_TRUTH")

    def test_exact_order_status_sell_certifies_closed_trade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "task6006.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                self._create_orders_table(con)
                self._insert_lifecycle(con)
                self._insert_fill(
                    con,
                    fill_id="runtime-sell-fill-1",
                    order_id="runtime-sell-order-1",
                    side="SELL",
                    source="PAPER_RUNTIME_SYNTHETIC_EXIT",
                )
                self._insert_fill(
                    con,
                    fill_id="broker-sell-fill-1",
                    order_id="broker-sell-order-1",
                    side="SELL",
                    source="ORDER_STATUS",
                )
                con.commit()
            finally:
                con.close()

            artifacts = capture_broker_truth_closed_trade_evidence(db_path)
            report_dir = Path(tmp) / "reports"
            write_broker_truth_closed_trade_reports(report_dir, artifacts)
            report_exists = (report_dir / "broker_truth_closed_trade_report.md").exists()

        summary = artifacts["broker_truth_closed_trade_summary"].iloc[0]
        mapping = artifacts["broker_truth_closed_trade_mapping"].iloc[0]
        self.assertEqual(summary["current_status"], "PASS_BROKER_TRUTH_CLOSED_TRADE_CERTIFIED")
        self.assertEqual(summary["acceptance_status"], "PASS")
        self.assertEqual(int(summary["broker_truth_sell_fills"]), 1)
        self.assertEqual(float(summary["broker_fill_linkage"]), 100.0)
        self.assertEqual(mapping["broker_fill_id"], "broker-sell-fill-1")
        self.assertTrue(report_exists)

    def test_broker_truth_flag_with_position_delta_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "task6006.db"
            con = sqlite3.connect(db_path)
            try:
                self._create_lifecycle_table(con)
                self._create_fills_table(con)
                self._insert_lifecycle(
                    con,
                    exit_order_id="delta-sell-order-1",
                    exit_fill_id="runtime-sell-fill-1",
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
                        "event-delta-1",
                        "2026-06-03T15:02:00Z",
                        "delta-sell-order-1",
                        "life-1",
                        "AMD",
                        "SELL",
                        1,
                        1.0,
                        None,
                        "POSITION_DELTA_FALLBACK",
                        "{}",
                    ),
                )
                con.commit()
            finally:
                con.close()

            artifacts = capture_broker_truth_closed_trade_evidence(db_path)

        summary = artifacts["broker_truth_closed_trade_summary"].iloc[0]
        rejected = artifacts["broker_truth_closed_trade_rejected_sources"].iloc[0]
        self.assertEqual(int(summary["broker_truth_sell_fills"]), 0)
        self.assertEqual(int(summary["broker_truth_flag_rejected_rows"]), 1)
        self.assertEqual(rejected["rejection_reason"], "BROKER_TRUTH_FLAG_WITH_REJECTED_SOURCE")


if __name__ == "__main__":
    unittest.main()
