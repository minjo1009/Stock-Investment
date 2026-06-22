from __future__ import annotations

import sqlite3
import tempfile
import unittest
import os
import json
from datetime import UTC, datetime
from pathlib import Path

from tools.db.apply_management_schema import _create_schema, _seed
from tools.db.run_registered_loop_once import run_once


class DbRegisteredLoopRunnerTests(unittest.TestCase):
    def _db(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "loop.db"
        con = sqlite3.connect(path)
        con.executescript(
            """
            CREATE TABLE control_state(
                control_key TEXT PRIMARY KEY,
                run_mode TEXT NOT NULL,
                kill_switch_active INTEGER NOT NULL
            );
            INSERT INTO control_state VALUES('default', 'DIAGNOSTIC_ONLY', 1);

            CREATE TABLE db_authority_manifest(
                authority_id TEXT PRIMARY KEY,
                db_path TEXT NOT NULL,
                status TEXT NOT NULL
            );
            INSERT INTO db_authority_manifest VALUES('active', 'trading.db', 'ACTIVE');

            CREATE TABLE schema_migrations(
                migration_id TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL,
                checksum TEXT NOT NULL,
                owning_module TEXT NOT NULL,
                description TEXT NOT NULL
            );
            CREATE TABLE source_receipts(
                receipt_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                source_family TEXT NOT NULL,
                source_key TEXT NOT NULL,
                source_ts TEXT,
                capture_ts TEXT NOT NULL,
                available_to_brain_ts TEXT,
                raw_path TEXT NOT NULL,
                raw_sha256 TEXT NOT NULL,
                source_time_basis TEXT NOT NULL,
                strict_gate_allowed INTEGER NOT NULL,
                proxy_allowed INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE source_freshness(
                source_family TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                storage_ref TEXT NOT NULL,
                max_source_ts TEXT,
                max_capture_ts TEXT,
                max_available_to_brain_ts TEXT,
                freshness_sla_minutes INTEGER NOT NULL,
                freshness_status TEXT NOT NULL,
                strict_gate_allowed INTEGER NOT NULL,
                proxy_allowed INTEGER NOT NULL,
                evidence_ref TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                notes TEXT NOT NULL
            );
            CREATE TABLE scheduler_run_ledger(
                run_ledger_id TEXT PRIMARY KEY,
                cadence TEXT NOT NULL,
                expected_bucket_ts TEXT NOT NULL,
                actual_start_at TEXT,
                actual_finish_at TEXT,
                owner_id TEXT NOT NULL,
                lease_token TEXT,
                status TEXT NOT NULL,
                lag_seconds REAL,
                skipped_reason TEXT,
                validation_refs_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        _create_schema(con)
        _seed(con, "2026-06-20T00:00:00Z")
        con.commit()
        con.close()
        return path

    def test_dry_run_does_not_mutate(self) -> None:
        path = self._db()
        result = run_once(db_path=path, apply=False, bucket="2026-06-20T00:00:00Z")
        self.assertEqual(result["status"], "DRY_RUN_OK_NO_MUTATION")
        con = sqlite3.connect(path)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM scheduler_run_ledger").fetchone()[0], 0)
        finally:
            con.close()

    def test_apply_writes_heartbeat_and_skips_unadapted_jobs(self) -> None:
        path = self._db()
        raw_dir = path.parent / "raw"
        result = run_once(db_path=path, apply=True, bucket="2026-06-20T00:00:00Z", raw_dir=raw_dir)
        self.assertEqual(result["status"], "APPLIED_DIAGNOSTIC_ONLY")
        self.assertEqual(result["success_count"], 4)
        self.assertEqual(result["skipped_count"], 8)
        con = sqlite3.connect(path)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM source_receipts").fetchone()[0], 4)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM reference_hashes").fetchone()[0], 4)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM data_lineage_edges").fetchone()[0], 4)
            self.assertEqual(
                con.execute(
                    "SELECT freshness_status FROM source_freshness WHERE source_family='diagnostic_runtime_heartbeats'"
                ).fetchone()[0],
                "CURRENT_OR_RECENT",
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE status='SKIPPED' AND skipped_reason='NO_ADAPTER_REGISTERED_DIAGNOSTIC_ONLY'"
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE status='SKIPPED' AND skipped_reason='NO_CACHED_MARKET_BARS_5M_SOURCE'"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE status='SKIPPED' AND skipped_reason='NO_CACHED_MARKET_TICKS_INTRADAY_SOURCE'"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE cadence='broker_truth_reconciliation_refresh' AND status='SUCCESS'"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE status='SKIPPED' AND skipped_reason='NO_RUNTIME_STRATEGY_DECISIONS_SOURCE'"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE status='SKIPPED' AND skipped_reason='NO_INDICATOR_SNAPSHOTS_SOURCE_FOR_RUNTIME_DECISIONS'"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE status='SKIPPED' AND skipped_reason='NO_MARKET_BARS_5M_SOURCE_FOR_INDICATORS'"
                ).fetchone()[0],
                1,
            )
            for reason in ("NO_CACHED_DAILY_OHLCV_SOURCE", "NO_CACHED_MACRO_RATES_SOURCE", "NO_CACHED_SEC_EVENTS_SOURCE"):
                self.assertEqual(
                    con.execute(
                        "SELECT COUNT(*) FROM scheduler_run_ledger WHERE status='SKIPPED' AND skipped_reason=?",
                        (reason,),
                    ).fetchone()[0],
                    1,
                )
            for family in ("frontend_read_models", "catalog_report_artifacts"):
                self.assertEqual(
                    con.execute(
                        "SELECT COUNT(*) FROM data_lineage_edges WHERE source_family=?",
                        (family,),
                    ).fetchone()[0],
                    1,
                )
        finally:
            con.close()

    def test_apply_writes_cached_market_bars_evidence_without_opening_gates(self) -> None:
        path = self._db()
        raw_dir = path.parent / "raw"
        market_raw_dir = path.parent / "market_raw"
        con = sqlite3.connect(path)
        try:
            con.executescript(
                """
                CREATE TABLE market_bars_5m(
                    bar_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    bar_start_ts TEXT NOT NULL,
                    bar_end_ts TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    tick_count INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    last_updated_at TEXT NOT NULL
                );
                INSERT INTO market_bars_5m VALUES
                ('AAPL:2026-06-01T14:30:00Z','AAPL','2026-06-01T14:30:00Z','2026-06-01T14:34:59Z',10,11,9,10.5,1000,12,'fixture','2026-06-01T14:35:10Z'),
                ('MSFT:2026-06-01T14:30:00Z','MSFT','2026-06-01T14:30:00Z','2026-06-01T14:34:59Z',20,21,19,20.5,2000,14,'fixture','2026-06-01T14:35:11Z');
                """
            )
            con.commit()
        finally:
            con.close()

        result = run_once(
            db_path=path,
            apply=True,
            bucket="2026-06-20T00:00:00Z",
            raw_dir=raw_dir,
            market_bars_raw_dir=market_raw_dir,
        )
        self.assertEqual(result["status"], "APPLIED_DIAGNOSTIC_ONLY")
        self.assertEqual(result["success_count"], 7)
        self.assertEqual(result["skipped_count"], 5)
        con = sqlite3.connect(path)
        try:
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM source_receipts WHERE source_family='market_bars_5m'"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM reference_hashes WHERE source_family='market_bars_5m'"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM data_lineage_edges WHERE source_family='market_bars_5m'"
                ).fetchone()[0],
                1,
            )
            fresh = con.execute(
                """
                SELECT freshness_status, strict_gate_allowed, proxy_allowed
                FROM source_freshness
                WHERE source_family='market_bars_5m'
                """
            ).fetchone()
            self.assertEqual(fresh, ("STALE", 0, 0))
            indicator = con.execute(
                """
                SELECT COUNT(*), SUM(entry_allowed), SUM(selected_for_portfolio)
                FROM indicator_snapshots
                WHERE reason='DIAGNOSTIC_INDICATOR_REFRESH_NO_TRADE'
                """
            ).fetchone()
            self.assertEqual(indicator, (2, 0, 0))
            runtime = con.execute(
                """
                SELECT COUNT(*), SUM(quantity), SUM(entry_allowed)
                FROM runtime_strategy_decisions
                WHERE created_by_task='Task3761_3800'
                """
            ).fetchone()
            self.assertEqual(runtime, (2, 0, 0))
            validation = con.execute(
                """
                SELECT validation_refs_json FROM scheduler_run_ledger
                WHERE cadence='market_bars_5m_refresh' AND status='SUCCESS'
                """
            ).fetchone()[0]
            self.assertIn('"cached_source_only": 1', validation)
            self.assertIn('"live_fetch": 0', validation)
            self.assertTrue(any(market_raw_dir.glob("market_bars_5m_cached_*.json")))
        finally:
            con.close()

    def test_current_market_bars_can_be_fresh_without_opening_gates(self) -> None:
        path = self._db()
        raw_dir = path.parent / "raw"
        market_raw_dir = path.parent / "market_raw"
        now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        con = sqlite3.connect(path)
        try:
            con.executescript(
                f"""
                CREATE TABLE market_bars_5m(
                    bar_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    bar_start_ts TEXT NOT NULL,
                    bar_end_ts TEXT NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    tick_count INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    last_updated_at TEXT NOT NULL
                );
                INSERT INTO market_bars_5m VALUES
                ('AAPL:{now}','AAPL','{now}','{now}',10,11,9,10.5,1000,12,'fixture','{now}');
                """
            )
            con.commit()
        finally:
            con.close()

        result = run_once(
            db_path=path,
            apply=True,
            only_job="market_bars_5m_refresh",
            bucket="2026-06-20T00:15:00Z",
            raw_dir=raw_dir,
            market_bars_raw_dir=market_raw_dir,
        )
        self.assertEqual(result["success_count"], 1)
        con = sqlite3.connect(path)
        try:
            fresh = con.execute(
                """
                SELECT freshness_status, strict_gate_allowed, proxy_allowed
                FROM source_freshness
                WHERE source_family='market_bars_5m'
                """
            ).fetchone()
            self.assertEqual(fresh, ("CURRENT_OR_RECENT", 0, 0))
            ledger = con.execute(
                """
                SELECT validation_refs_json
                FROM scheduler_run_ledger
                WHERE cadence='market_bars_5m_refresh'
                """
            ).fetchone()[0]
            self.assertIn('"freshness_recovered": 1', ledger)
            self.assertIn('"strict_gate_allowed": 0', ledger)
        finally:
            con.close()

    def test_apply_writes_cached_ticks_and_broker_truth_without_live_fetch(self) -> None:
        path = self._db()
        raw_dir = path.parent / "raw"
        market_raw_dir = path.parent / "market_raw"
        con = sqlite3.connect(path)
        try:
            con.executescript(
                """
                CREATE TABLE market_ticks(
                    tick_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    last_price REAL NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                INSERT INTO market_ticks VALUES
                ('AAPL:2026-06-01T14:30:00Z','2026-06-01T14:30:00Z','AAPL',10.5,'fixture','2026-06-01T14:30:01Z'),
                ('MSFT:2026-06-01T14:30:00Z','2026-06-01T14:30:00Z','MSFT',20.5,'fixture','2026-06-01T14:30:01Z');

                CREATE TABLE reconciliation_runs(
                    reconciliation_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    max_severity TEXT NOT NULL,
                    block_new_orders INTEGER NOT NULL,
                    summary_text TEXT NOT NULL,
                    raw_snapshot_json TEXT
                );
                INSERT INTO reconciliation_runs VALUES
                ('recon-1','run-1','2026-06-01T14:31:00Z','2026-06-01T14:31:05Z','CLEAN','INFO',0,'fixture clean','{}');

                CREATE TABLE runtime_authority_evidence_ledger(
                    authority_hash TEXT PRIMARY KEY,
                    authority_id TEXT NOT NULL,
                    runtime_decision_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            con.commit()
        finally:
            con.close()

        result = run_once(
            db_path=path,
            apply=True,
            bucket="2026-06-20T00:00:00Z",
            raw_dir=raw_dir,
            market_bars_raw_dir=market_raw_dir,
        )
        self.assertEqual(result["status"], "APPLIED_DIAGNOSTIC_ONLY")
        self.assertEqual(result["success_count"], 5)
        self.assertEqual(result["skipped_count"], 7)
        con = sqlite3.connect(path)
        try:
            for family in ("market_ticks_intraday", "broker_truth_reconciliation"):
                self.assertEqual(
                    con.execute(
                        "SELECT COUNT(*) FROM source_receipts WHERE source_family=?",
                        (family,),
                    ).fetchone()[0],
                    1,
                )
                fresh = con.execute(
                    """
                    SELECT freshness_status, strict_gate_allowed, proxy_allowed
                    FROM source_freshness
                    WHERE source_family=?
                    """,
                    (family,),
                ).fetchone()
                if family == "broker_truth_reconciliation":
                    self.assertEqual(fresh, ("CURRENT_OR_RECENT", 0, 0))
                else:
                    self.assertEqual(fresh, ("STALE", 0, 0))
            broker_block = con.execute(
                """
                SELECT status, max_severity, block_new_orders, raw_snapshot_json
                FROM reconciliation_runs
                WHERE reconciliation_id='diag-broker-truth:2026-06-20T00:00:00Z'
                """
            ).fetchone()
            self.assertEqual(broker_block[:3], ("BLOCKED", "CRITICAL", 1))
            self.assertIn('"broker_api_called": false', broker_block[3])
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE skipped_reason='NO_RUNTIME_STRATEGY_DECISIONS_SOURCE'"
                ).fetchone()[0],
                1,
            )
            validation = con.execute(
                """
                SELECT validation_refs_json FROM scheduler_run_ledger
                WHERE cadence='broker_truth_reconciliation_refresh' AND status='SUCCESS'
                """
            ).fetchone()[0]
            self.assertIn('"broker_api_called": 0', validation)
            self.assertIn('"broker_mutation": 0', validation)
            self.assertIn('"block_new_orders": 1', validation)
        finally:
            con.close()

    def test_operator_broker_truth_fixture_source_connects_without_broker_api(self) -> None:
        path = self._db()
        raw_dir = path.parent / "raw"
        fixture = path.parent / "broker_truth_fixture.json"
        now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        fixture.write_text(
            json.dumps(
                {
                    "snapshot_ts": now,
                    "reconciliation_status": "CLEAN",
                    "max_severity": "INFO",
                    "broker_orders": [
                        {
                            "broker_order_id": "fixture-order-1",
                            "symbol": "AAPL",
                            "side": "BUY",
                            "status": "FILLED",
                            "filled_qty": 1,
                        }
                    ],
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        previous = os.environ.get("TRADER_BRAIN_BROKER_TRUTH_FIXTURE_JSON")
        os.environ["TRADER_BRAIN_BROKER_TRUTH_FIXTURE_JSON"] = str(fixture)
        try:
            result = run_once(
                db_path=path,
                apply=True,
                only_job="broker_truth_reconciliation_refresh",
                bucket="2026-06-20T00:20:00Z",
                raw_dir=raw_dir,
            )
        finally:
            if previous is None:
                os.environ.pop("TRADER_BRAIN_BROKER_TRUTH_FIXTURE_JSON", None)
            else:
                os.environ["TRADER_BRAIN_BROKER_TRUTH_FIXTURE_JSON"] = previous
        self.assertEqual(result["success_count"], 1)
        con = sqlite3.connect(path)
        try:
            row = con.execute(
                """
                SELECT status, max_severity, block_new_orders, raw_snapshot_json
                FROM reconciliation_runs
                WHERE reconciliation_id='fixture-broker-truth:2026-06-20T00:20:00Z'
                """
            ).fetchone()
            self.assertEqual(row[:3], ("CLEAN", "INFO", 0))
            payload = json.loads(row[3])
            self.assertFalse(payload["broker_api_called"])
            self.assertFalse(payload["broker_mutation"])
            fresh = con.execute(
                """
                SELECT provider, freshness_status, strict_gate_allowed, proxy_allowed
                FROM source_freshness
                WHERE source_family='broker_truth_reconciliation'
                """
            ).fetchone()
            self.assertEqual(fresh, ("operator_broker_truth_fixture_reconciliation", "CURRENT_OR_RECENT", 0, 0))
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
