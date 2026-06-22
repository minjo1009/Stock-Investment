from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.db.run_source_acquisition_once import run_once


class DbSourceAcquisitionRunnerTests(unittest.TestCase):
    def _db(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "source.db"
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
        con.commit()
        con.close()
        return path

    def _fixtures(self, root: Path) -> Path:
        fixture = root / "fixtures"
        fixture.mkdir()
        (fixture / "market_bars_5m.csv").write_text(
            "timestamp,open,high,low,close,volume,symbol\n"
            "2026-06-19T14:30:00Z,10,11,9,10.5,1000,AAPL\n"
            "2026-06-19T14:35:00Z,10.5,12,10,11.5,1200,AAPL\n",
            encoding="utf-8",
        )
        (fixture / "market_ticks_intraday.csv").write_text(
            "timestamp,open,high,low,close,volume,symbol\n"
            "2026-06-19T14:35:00Z,10.5,12,10,11.5,1200,AAPL\n",
            encoding="utf-8",
        )
        (fixture / "daily_ohlcv.csv").write_text(
            "timestamp,open,high,low,close,adj_close,volume,symbol,provider\n"
            "2026-06-18,9,12,8,11,11,5000,AAPL,fixture_daily\n",
            encoding="utf-8",
        )
        (fixture / "macro_rates.csv").write_text(
            "series_id,observation_date,value,provider,units\n"
            "DGS10,2026-06-18,4.25,fixture_macro,percent\n",
            encoding="utf-8",
        )
        (fixture / "sec_events.csv").write_text(
            "provider,cik,ticker,accession_no,form_type,filed_at,accepted_at,period_of_report,event_type,source_url\n"
            "fixture_sec,0000320193,AAPL,0000320193-26-000001,10-Q,2026-06-18,2026-06-18T21:30:00Z,2026-06-18,filing_index,https://www.sec.gov/\n",
            encoding="utf-8",
        )
        return fixture

    def test_dry_run_does_not_create_source_tables(self) -> None:
        path = self._db()
        result = run_once(db_path=path, apply=False, families=("daily_ohlcv",))
        self.assertEqual(result["status"], "DRY_RUN_OK_NO_MUTATION")
        con = sqlite3.connect(path)
        try:
            exists = con.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='daily_ohlcv'"
            ).fetchone()
            self.assertIsNone(exists)
        finally:
            con.close()

    def test_fixture_acquisition_upserts_without_duplicates(self) -> None:
        path = self._db()
        fixture = self._fixtures(path.parent)
        kwargs = {
            "db_path": path,
            "apply": True,
            "families": ("market_bars_5m", "market_ticks_intraday", "daily_ohlcv", "macro_rates", "sec_events"),
            "symbols": ("AAPL",),
            "fixture_dir": fixture,
            "bucket": "2026-06-21T00:00:00Z",
        }
        first = run_once(**kwargs)
        con = sqlite3.connect(path)
        try:
            evidence_counts_before = {
                table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("source_receipts", "reference_hashes", "data_lineage_edges", "scheduler_run_ledger")
            }
        finally:
            con.close()
        second = run_once(**kwargs)
        self.assertEqual(first["success_count"], 5)
        self.assertEqual(second["success_count"], 0)
        self.assertEqual(second["skipped_count"], 5)
        self.assertTrue(all(row["skipped_reason"] == "DUPLICATE_INPUT_HASH" for row in second["results"]))
        con = sqlite3.connect(path)
        try:
            counts = {
                table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("market_bars_5m", "market_ticks", "daily_ohlcv", "macro_rates", "sec_events")
            }
            self.assertEqual(counts["market_bars_5m"], 2)
            self.assertEqual(counts["market_ticks"], 1)
            self.assertEqual(counts["daily_ohlcv"], 1)
            self.assertEqual(counts["macro_rates"], 1)
            self.assertEqual(counts["sec_events"], 1)
            self.assertGreaterEqual(con.execute("SELECT COUNT(*) FROM source_receipts").fetchone()[0], 5)
            self.assertGreaterEqual(con.execute("SELECT COUNT(*) FROM data_lineage_edges").fetchone()[0], 5)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM source_freshness").fetchone()[0], 5)
            evidence_counts_after = {
                table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("source_receipts", "reference_hashes", "data_lineage_edges")
            }
            self.assertEqual(
                evidence_counts_after,
                {key: value for key, value in evidence_counts_before.items() if key != "scheduler_run_ledger"},
            )
            self.assertEqual(
                con.execute(
                    "SELECT COUNT(*) FROM scheduler_run_ledger WHERE skipped_reason='DUPLICATE_INPUT_HASH'"
                ).fetchone()[0],
                5,
            )
            self.assertEqual(
                con.execute("SELECT COUNT(*) FROM source_acquisition_input_fingerprints").fetchone()[0],
                5,
            )
            self.assertEqual(
                con.execute("SELECT COUNT(*) FROM source_scheduler_leases WHERE status='RELEASED'").fetchone()[0],
                5,
            )
            gates = con.execute(
                "SELECT SUM(strict_gate_allowed), SUM(proxy_allowed) FROM source_freshness"
            ).fetchone()
            self.assertEqual(gates, (0, 0))

            stale_status = con.execute(
                "SELECT freshness_status FROM source_freshness WHERE source_family='sec_events'"
            ).fetchone()[0]
            self.assertEqual(stale_status, "STALE")
        finally:
            con.close()

    def test_active_source_lease_skips_without_fetch_or_upsert(self) -> None:
        path = self._db()
        fixture = self._fixtures(path.parent)
        con = sqlite3.connect(path)
        try:
            from tools.db.apply_management_schema import _create_schema

            _create_schema(con)
            con.execute(
                """
                INSERT INTO source_scheduler_leases(
                    lease_key, owner_id, lease_token, state_hash, acquired_at,
                    heartbeat_at, expires_at, released_at, status
                )
                VALUES (
                    'source-acq:daily_ohlcv_refresh:2026-06-21T00:10:00Z',
                    'test-owner', 'held-token', 'state',
                    '2026-06-21T00:09:00Z', '2026-06-21T00:09:30Z',
                    '2999-01-01T00:00:00Z', NULL, 'HELD'
                )
                """
            )
            con.commit()
        finally:
            con.close()
        result = run_once(
            db_path=path,
            apply=True,
            families=("daily_ohlcv",),
            symbols=("AAPL",),
            fixture_dir=fixture,
            bucket="2026-06-21T00:10:00Z",
        )
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["skipped_count"], 1)
        self.assertEqual(result["results"][0]["skipped_reason"], "LEASE_HELD")
        con = sqlite3.connect(path)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM daily_ohlcv").fetchone()[0], 0)
            ledger = con.execute(
                "SELECT status, skipped_reason FROM scheduler_run_ledger WHERE cadence='daily_ohlcv_refresh'"
            ).fetchone()
            self.assertEqual(ledger, ("SKIPPED", "LEASE_HELD"))
        finally:
            con.close()

    def test_sec_live_without_user_agent_skips_without_mutation_claim(self) -> None:
        path = self._db()
        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:05:00Z",
        )
        self.assertEqual(result["status"], "APPLIED_DIAGNOSTIC_ONLY")
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["skipped_count"], 1)
        self.assertEqual(result["results"][0]["skipped_reason"], "SEC_USER_AGENT_MISSING")
        con = sqlite3.connect(path)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM source_receipts").fetchone()[0], 0)
            ledger = con.execute(
                """
                SELECT status, skipped_reason, validation_refs_json
                FROM scheduler_run_ledger
                WHERE cadence='sec_events_refresh'
                """
            ).fetchone()
            self.assertEqual(ledger[0], "SKIPPED")
            self.assertEqual(ledger[1], "SEC_USER_AGENT_MISSING")
            self.assertIn('"missing_source_is_negative": 0', ledger[2])
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
