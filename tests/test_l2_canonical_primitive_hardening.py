from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.ingest_task740_task741_artifacts_to_l2 import ingest_artifacts_to_l2
from scripts.validate_l2_canonical_primitive_contract import validate as validate_contract
from scripts.validate_l2_historical_live_separation import validate as validate_separation
from scripts.validate_l2_no_trade_outputs import validate as validate_no_trade_outputs
from scripts.validate_l3_inputs_are_l2_canonical import validate as validate_l3_inputs
from src.brain.l2_to_meaning_adapter import load_canonical_l2_meaning_inputs
from src.l2.builders.indicator_primitives import build_indicator_primitives
from src.l2.builders.market_bar_primitives import build_market_bar_primitives
from src.l2.contracts import L2PrimitiveBatch
from src.l2.freshness import STALE
from src.l2.registry import L2_BUILDER_VERSION
from src.l2.runtime_context import HISTORICAL_RESEARCH, LIVE_INTRADAY_DIAGNOSTIC
from src.l2.stores.primitive_reader import load_l3_inputs
from src.l2.stores.primitive_writer import write_l2_batch, write_l2_primitives
from src.l2.stores.sqlite_l2_store import ensure_l2_schema


class L2CanonicalPrimitiveHardeningTest(unittest.TestCase):
    def test_schema_and_contract_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                ensure_l2_schema(conn)
            finally:
                conn.close()
            self.assertEqual(validate_contract(db_path), [])

    def test_market_bar_builder_excludes_open_bars(self) -> None:
        rows = pd.DataFrame(
            [
                {
                    "bar_id": "AAPL:1",
                    "symbol": "AAPL",
                    "bar_start_ts": "2026-06-01T10:00:00Z",
                    "bar_end_ts": "2026-06-01T10:05:00Z",
                    "open": 1,
                    "high": 2,
                    "low": 1,
                    "close": 2,
                    "volume": 100,
                    "tick_count": 3,
                    "source": "KIS_QUOTE",
                },
                {
                    "bar_id": "AAPL:2",
                    "symbol": "AAPL",
                    "bar_start_ts": "2026-06-01T10:05:00Z",
                    "bar_end_ts": "2026-06-01T10:15:00Z",
                    "open": 2,
                    "high": 3,
                    "low": 2,
                    "close": 3,
                    "volume": 100,
                    "tick_count": 3,
                    "source": "KIS_QUOTE",
                },
            ]
        )
        facts = build_market_bar_primitives(
            rows,
            source_receipt_id="receipt-1",
            primitive_batch_id="batch-1",
            capture_ts="2026-06-01T10:10:00Z",
        )
        self.assertEqual(len(facts), 1)
        self.assertTrue(facts[0].closed_bar_only)
        self.assertEqual(facts[0].symbol, "AAPL")

    def test_indicator_builder_inherits_stale_parent_and_removes_trade_outputs(self) -> None:
        rows = [
            {
                "snapshot_id": "snap-1",
                "created_at": "2026-06-01T10:10:00Z",
                "symbol": "AAPL",
                "bar_end_ts": "2026-06-01T10:05:00Z",
                "close": 10,
                "ma20": 9,
                "ma50": 8,
                "ma200": 7,
                "breakout_high_20": 9,
                "breakout_condition": 1,
                "ma_condition": 1,
                "entry_allowed": 1,
                "side": "BUY",
                "score": 0.99,
                "data_fresh": 1,
                "source_price_ts": "2026-06-01T10:05:00Z",
            }
        ]
        facts = build_indicator_primitives(
            rows,
            source_receipt_id="receipt-2",
            primitive_batch_id="batch-2",
            capture_ts="2026-06-01T10:10:00Z",
            parent_freshness_by_symbol={"AAPL": STALE},
        )
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].freshness_status, STALE)
        self.assertNotIn("score", facts[0].primitive_payload_json)
        self.assertNotIn("BUY", facts[0].primitive_payload_json)
        self.assertEqual(facts[0].trade_output_flag, 0)
        self.assertEqual(facts[0].score_output_flag, 0)
        self.assertEqual(facts[0].order_intent_flag, 0)

    def test_writer_reader_and_validators(self) -> None:
        conn = sqlite3.connect(":memory:")
        try:
            ensure_l2_schema(conn)
            facts = build_indicator_primitives(
                [
                    {
                        "snapshot_id": "snap-1",
                        "created_at": "2026-06-01T10:10:00Z",
                        "symbol": "AAPL",
                        "bar_end_ts": "2026-06-01T10:05:00Z",
                        "close": 10,
                        "data_fresh": 1,
                        "source_price_ts": "2026-06-01T10:05:00Z",
                    }
                ],
                source_receipt_id="receipt-3",
                primitive_batch_id="batch-3",
                capture_ts="2026-06-01T10:10:00Z",
            )
            batch = L2PrimitiveBatch(
                primitive_batch_id="batch-3",
                runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                builder_name="unit_test",
                builder_version=L2_BUILDER_VERSION,
                asof_ts="2026-06-01T10:10:00Z",
                created_at="2026-06-01T10:10:00Z",
                source_family_set="indicator",
                symbol_set='["AAPL"]',
                row_count=len(facts),
                input_hash="input",
                output_hash="output",
            )
            write_l2_batch(conn, batch)
            write_l2_primitives(conn, facts)
            loaded = load_l3_inputs(conn, asof_ts="2026-06-01T10:10:00Z", runtime_context=LIVE_INTRADAY_DIAGNOSTIC)
            adapter_loaded = load_canonical_l2_meaning_inputs(
                conn,
                asof_ts="2026-06-01T10:10:00Z",
                runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
            )
            self.assertEqual(len(loaded), 1)
            self.assertEqual(len(adapter_loaded), 1)
            with tempfile.TemporaryDirectory() as tmp:
                db_path = Path(tmp) / "l2.db"
                disk = sqlite3.connect(db_path)
                try:
                    conn.backup(disk)
                finally:
                    disk.close()
                self.assertEqual(validate_contract(db_path), [])
                self.assertEqual(validate_separation(db_path), [])
                self.assertEqual(validate_no_trade_outputs(db_path), [])
                self.assertEqual(validate_l3_inputs(db_path), [])
        finally:
            conn.close()

    def test_historical_artifact_ingest_is_historical_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "task740_extracted_primitives.csv"
            artifact.write_text("symbol,event_time,value\nAAPL,2026-06-01T10:00:00Z,1\n", encoding="utf-8")
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = ingest_artifacts_to_l2(conn, [artifact], asof_ts="2026-06-01T10:00:00Z")
                self.assertEqual(result["ingested_rows"], 1)
                context = conn.execute("SELECT DISTINCT runtime_context FROM l2_primitive_facts").fetchone()[0]
                family = conn.execute("SELECT DISTINCT source_family FROM l2_primitive_facts").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(context, HISTORICAL_RESEARCH)
            self.assertEqual(family, "historical_artifact")
            self.assertEqual(validate_separation(db_path), [])


if __name__ == "__main__":
    unittest.main()
