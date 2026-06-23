from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError

from tools.db import run_source_acquisition_once as source_runner
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

    def test_news_fixtures_upsert_l0_l1_with_closed_gates(self) -> None:
        path = self._db()
        fixture = path.parent / "news_fixtures"
        fixture.mkdir()
        (fixture / "official_public_releases.csv").write_text(
            "provider,provider_item_id,source_url,title,body_or_summary,publication_ts,publisher,language,tickers,entities,event_type\n"
            "company_ir,aapl-ir-1,https://www.apple.com/newsroom/2026/06/apple-results/,Apple reports quarterly results,Official release,2026-06-21T12:00:00Z,Apple,en,AAPL,Apple Inc,earnings_release\n",
            encoding="utf-8",
        )
        (fixture / "gdelt_news_events.csv").write_text(
            "provider,provider_item_id,source_url,title,body_or_summary,seendate,publisher,language,entities,event_type\n"
            "gdelt_doc,gdelt-1,https://example.com/story,Apple supplier story,Discovery metadata,2026-06-21T12:05:00Z,Example,en,Apple Inc,news_discovery\n",
            encoding="utf-8",
        )
        (fixture / "marketaux_news_free.csv").write_text(
            "provider,provider_item_id,source_url,title,body_or_summary,published_at,publisher,language,tickers,event_type\n"
            "marketaux,marketaux-1,https://example.com/marketaux,Apple market brief,Marketaux metadata,2026-06-21T12:10:00Z,Example,en,AAPL,market_news\n",
            encoding="utf-8",
        )

        result = run_once(
            db_path=path,
            apply=True,
            families=("official_public_releases", "gdelt_news_events", "marketaux_news_free"),
            symbols=("AAPL",),
            fixture_dir=fixture,
            bucket="2026-06-21T00:40:00Z",
        )

        self.assertEqual(result["success_count"], 3)
        con = sqlite3.connect(path)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM news_event_l0").fetchone()[0], 3)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM news_event_l1_evidence").fetchone()[0], 3)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM news_event_entity_map").fetchone()[0], 4)
            official = con.execute(
                """
                SELECT promotion_status, blocker_code
                FROM news_event_l1_evidence
                WHERE source_family='official_public_releases'
                """
            ).fetchone()
            self.assertEqual(official, ("READY_DIAGNOSTIC_ONLY", ""))
            blocked = con.execute(
                """
                SELECT COUNT(*)
                FROM news_event_l1_evidence
                WHERE source_family IN ('gdelt_news_events', 'marketaux_news_free')
                  AND promotion_status='BLOCKED'
                  AND blocker_code='L1_NEWS_EVENT_QUALITY_GATE_CLOSED'
                """
            ).fetchone()[0]
            self.assertEqual(blocked, 2)
            gates = con.execute(
                """
                SELECT SUM(strict_gate_allowed), SUM(proxy_allowed)
                FROM source_freshness
                WHERE source_family IN ('official_public_releases', 'gdelt_news_events', 'marketaux_news_free')
                """
            ).fetchone()
            self.assertEqual(gates, (0, 0))
            lineage = con.execute(
                """
                SELECT COUNT(*)
                FROM news_event_l0 n
                JOIN source_receipts r ON r.receipt_id=n.raw_receipt_id
                WHERE n.source_family=r.source_family
                """
            ).fetchone()[0]
            self.assertEqual(lineage, 3)
        finally:
            con.close()

    def test_news_live_fetch_is_disabled_without_fixture(self) -> None:
        path = self._db()
        result = run_once(
            db_path=path,
            apply=True,
            families=("gdelt_news_events", "marketaux_news_free"),
            symbols=("AAPL",),
            allow_network=False,
            bucket="2026-06-21T00:45:00Z",
        )

        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["skipped_count"], 2)
        self.assertTrue(all(row["skipped_reason"] == "NETWORK_FETCH_DISABLED" for row in result["results"]))
        con = sqlite3.connect(path)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM news_event_l0").fetchone()[0], 0)
        finally:
            con.close()

    def test_official_news_live_fetch_records_call_ledger(self) -> None:
        path = self._db()
        old_urlopen = source_runner.urlopen
        old_interval = source_runner.NEWS_REQUEST_INTERVAL_SECONDS
        old_feeds = source_runner.OFFICIAL_RSS_FEEDS
        old_ir_pages = source_runner.OFFICIAL_IR_PAGES
        old_bls = source_runner.BLS_LATEST_SERIES
        old_treasury = source_runner.TREASURY_FISCALDATA_ENDPOINTS

        class FakeResponse:
            status = 200
            headers = {}

            def __init__(self, body: bytes):
                self.body = body

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return self.body

        def fake_urlopen(request, *args, **kwargs):
            body = (
                b"<?xml version='1.0'?><rss><channel><item><title>Apple official update</title>"
                b"<link>https://www.apple.com/newsroom/test</link><pubDate>Sun, 21 Jun 2026 12:00:00 GMT</pubDate>"
                b"<guid>aapl-official-1</guid><description>summary</description></item></channel></rss>"
            )
            return FakeResponse(body)

        source_runner.urlopen = fake_urlopen
        source_runner.NEWS_REQUEST_INTERVAL_SECONDS = 0.0
        source_runner.OFFICIAL_RSS_FEEDS = (
            {
                "provider": "apple_newsroom_rss",
                "endpoint": "apple_newsroom",
                "url": "https://www.apple.com/newsroom/rss-feed.rss",
                "tickers": "AAPL",
                "entities": "Apple Inc",
                "publisher": "Apple",
                "event_type": "company_ir_newsroom",
            },
        )
        source_runner.OFFICIAL_IR_PAGES = ()
        source_runner.BLS_LATEST_SERIES = ()
        source_runner.TREASURY_FISCALDATA_ENDPOINTS = ()
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "NEWS_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: setattr(source_runner, "OFFICIAL_RSS_FEEDS", old_feeds))
        self.addCleanup(lambda: setattr(source_runner, "OFFICIAL_IR_PAGES", old_ir_pages))
        self.addCleanup(lambda: setattr(source_runner, "BLS_LATEST_SERIES", old_bls))
        self.addCleanup(lambda: setattr(source_runner, "TREASURY_FISCALDATA_ENDPOINTS", old_treasury))

        result = run_once(
            db_path=path,
            apply=True,
            families=("official_public_releases",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:50:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        con = sqlite3.connect(path)
        try:
            row = con.execute(
                "SELECT provider, title, publication_ts FROM news_event_l0 WHERE source_family='official_public_releases'"
            ).fetchone()
            self.assertEqual(row, ("apple_newsroom_rss", "Apple official update", "2026-06-21T12:00:00Z"))
            raw_path = con.execute(
                "SELECT raw_path FROM source_receipts WHERE source_family='official_public_releases'"
            ).fetchone()[0]
            payload = json.loads((Path.cwd() / raw_path).read_text(encoding="utf-8"))
            self.assertEqual(payload["provider_call_ledger"][0]["status"], "SUCCESS")
            self.assertEqual(payload["provider_call_ledger"][0]["token_used"], 0)
        finally:
            con.close()

    def test_gdelt_429_records_rate_limit_without_rows(self) -> None:
        path = self._db()
        old_urlopen = source_runner.urlopen
        old_interval = source_runner.NEWS_REQUEST_INTERVAL_SECONDS
        old_gdelt_interval = source_runner.GDELT_REQUEST_INTERVAL_SECONDS
        old_block_state = source_runner.GDELT_BLOCK_STATE
        block_state = path.parent / "gdelt_block_state.json"

        def fake_urlopen(request, *args, **kwargs):
            raise HTTPError(
                request.full_url,
                429,
                "Too Many Requests",
                {},
                BytesIO(b"rate limited"),
            )

        source_runner.urlopen = fake_urlopen
        source_runner.NEWS_REQUEST_INTERVAL_SECONDS = 0.0
        source_runner.GDELT_REQUEST_INTERVAL_SECONDS = 0.0
        source_runner.GDELT_BLOCK_STATE = block_state
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "NEWS_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: setattr(source_runner, "GDELT_REQUEST_INTERVAL_SECONDS", old_gdelt_interval))
        self.addCleanup(lambda: setattr(source_runner, "GDELT_BLOCK_STATE", old_block_state))

        result = run_once(
            db_path=path,
            apply=True,
            families=("gdelt_news_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:55:00Z",
        )

        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["results"][0]["skipped_reason"], "RATE_LIMIT_OR_QUOTA_429")
        con = sqlite3.connect(path)
        try:
            ledger = con.execute(
                "SELECT validation_refs_json FROM scheduler_run_ledger WHERE cadence='gdelt_news_events_refresh'"
            ).fetchone()[0]
            self.assertIn("RATE_LIMIT_OR_QUOTA_429", ledger)
            self.assertIn("provider_call_ledger", ledger)
            self.assertTrue(block_state.exists())
            block_payload = json.loads(block_state.read_text(encoding="utf-8"))
            self.assertEqual(block_payload["status"], "GDELT_TEMPORARILY_BLOCKED")
            self.assertEqual(block_payload["cooldown_seconds"], source_runner.GDELT_COOLDOWN_SECONDS)
        finally:
            con.close()

    def test_gdelt_success_uses_single_symbol_and_upserts_rows(self) -> None:
        path = self._db()
        old_urlopen = source_runner.urlopen
        old_interval = source_runner.NEWS_REQUEST_INTERVAL_SECONDS
        old_gdelt_interval = source_runner.GDELT_REQUEST_INTERVAL_SECONDS
        old_block_state = source_runner.GDELT_BLOCK_STATE
        block_state = path.parent / "gdelt_block_state_success.json"
        captured_urls: list[str] = []

        class FakeResponse:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(
                    {
                        "articles": [
                            {
                                "url": "https://example.com/aapl-gdelt",
                                "url_mobile": "",
                                "title": "Apple GDELT story",
                                "seendate": "20260623160000",
                                "domain": "example.com",
                                "language": "English",
                            }
                        ]
                    }
                ).encode("utf-8")

        def fake_urlopen(request, *args, **kwargs):
            captured_urls.append(request.full_url)
            return FakeResponse()

        source_runner.urlopen = fake_urlopen
        source_runner.NEWS_REQUEST_INTERVAL_SECONDS = 0.0
        source_runner.GDELT_REQUEST_INTERVAL_SECONDS = 0.0
        source_runner.GDELT_BLOCK_STATE = block_state
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "NEWS_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: setattr(source_runner, "GDELT_REQUEST_INTERVAL_SECONDS", old_gdelt_interval))
        self.addCleanup(lambda: setattr(source_runner, "GDELT_BLOCK_STATE", old_block_state))

        result = run_once(
            db_path=path,
            apply=True,
            families=("gdelt_news_events",),
            symbols=("AAPL", "MSFT"),
            allow_network=True,
            bucket="2026-06-21T01:05:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        self.assertIn("query=AAPL", captured_urls[0])
        self.assertNotIn("MSFT", captured_urls[0])
        self.assertIn("maxrecords=1", captured_urls[0])
        self.assertIn("timespan=15m", captured_urls[0])
        con = sqlite3.connect(path)
        try:
            row = con.execute(
                "SELECT provider, title, source_url FROM news_event_l0 WHERE source_family='gdelt_news_events'"
            ).fetchone()
            self.assertEqual(row, ("gdelt_doc_api", "Apple GDELT story", "https://example.com/aapl-gdelt"))
            l1 = con.execute(
                "SELECT promotion_status, blocker_code FROM news_event_l1_evidence WHERE source_family='gdelt_news_events'"
            ).fetchone()
            self.assertEqual(l1, ("BLOCKED", "L1_NEWS_EVENT_QUALITY_GATE_CLOSED"))
        finally:
            con.close()

    def test_marketaux_token_is_masked_and_daily_guard_records_usage(self) -> None:
        path = self._db()
        old_urlopen = source_runner.urlopen
        old_interval = source_runner.NEWS_REQUEST_INTERVAL_SECONDS
        old_env_file = source_runner.MARKETAUX_ENV_FILE
        old_usage = source_runner.MARKETAUX_USAGE_LEDGER
        old_token = os.environ.pop("MARKETAUX_API_TOKEN", None)
        token_file = path.parent / "marketaux.env"
        usage_file = path.parent / "marketaux_usage.json"
        token_file.write_text("MARKETAUX_API_TOKEN=test-token-secret\n", encoding="utf-8")

        class FakeResponse:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps(
                    {
                        "data": [
                            {
                                "uuid": "maux-1",
                                "url": "https://example.com/aapl-news",
                                "title": "Apple market news",
                                "description": "metadata",
                                "published_at": "2026-06-21T12:15:00Z",
                                "language": "en",
                                "source": "Example",
                                "entities": [{"symbol": "AAPL", "name": "Apple Inc"}],
                            }
                        ]
                    }
                ).encode("utf-8")

        captured_urls: list[str] = []

        def fake_urlopen(request, *args, **kwargs):
            captured_urls.append(request.full_url)
            return FakeResponse()

        source_runner.urlopen = fake_urlopen
        source_runner.NEWS_REQUEST_INTERVAL_SECONDS = 0.0
        source_runner.MARKETAUX_ENV_FILE = token_file
        source_runner.MARKETAUX_USAGE_LEDGER = usage_file
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "NEWS_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: setattr(source_runner, "MARKETAUX_ENV_FILE", old_env_file))
        self.addCleanup(lambda: setattr(source_runner, "MARKETAUX_USAGE_LEDGER", old_usage))
        self.addCleanup(lambda: os.environ.update({"MARKETAUX_API_TOKEN": old_token}) if old_token else os.environ.pop("MARKETAUX_API_TOKEN", None))

        result = run_once(
            db_path=path,
            apply=True,
            families=("marketaux_news_free",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T01:00:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        self.assertIn("api_token=test-token-secret", captured_urls[0])
        self.assertEqual(json.loads(usage_file.read_text(encoding="utf-8"))["request_count"], 1)
        con = sqlite3.connect(path)
        try:
            raw_path = con.execute(
                "SELECT raw_path FROM source_receipts WHERE source_family='marketaux_news_free'"
            ).fetchone()[0]
            payload_text = (Path.cwd() / raw_path).read_text(encoding="utf-8")
            self.assertNotIn("test-token-secret", payload_text)
            self.assertIn("api_token=%2A%2A%2A", payload_text)
            row = con.execute(
                "SELECT provider, title FROM news_event_l0 WHERE source_family='marketaux_news_free'"
            ).fetchone()
            self.assertEqual(row, ("marketaux_free_api", "Apple market news"))
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

    def test_sec_without_user_agent_uses_bulk_baseline_when_available(self) -> None:
        path = self._db()
        root = path.parent
        tickers_path = root / "company_tickers.json"
        submissions_path = root / "submissions.zip"
        tickers_path.write_text(
            json.dumps({"0": {"ticker": "AAPL", "cik_str": 320193}}),
            encoding="utf-8",
        )
        with zipfile.ZipFile(submissions_path, "w") as archive:
            archive.writestr(
                "CIK0000320193.json",
                json.dumps(
                    {
                        "filings": {
                            "recent": {
                                "form": ["10-Q"],
                                "accessionNumber": ["0000320193-26-000010"],
                                "filingDate": ["2026-06-01"],
                                "acceptanceDateTime": ["2026-06-01T12:34:56.000Z"],
                                "reportDate": ["2026-03-31"],
                            }
                        }
                    }
                ),
            )
        old_tickers = source_runner.SEC_COMPANY_TICKERS_CACHE
        old_submissions = source_runner.SEC_BULK_SUBMISSIONS_ZIP
        old_user_agent = os.environ.pop("SEC_USER_AGENT", None)
        source_runner.SEC_COMPANY_TICKERS_CACHE = tickers_path
        source_runner.SEC_BULK_SUBMISSIONS_ZIP = submissions_path
        self.addCleanup(lambda: setattr(source_runner, "SEC_COMPANY_TICKERS_CACHE", old_tickers))
        self.addCleanup(lambda: setattr(source_runner, "SEC_BULK_SUBMISSIONS_ZIP", old_submissions))
        self.addCleanup(lambda: os.environ.update({"SEC_USER_AGENT": old_user_agent}) if old_user_agent else os.environ.pop("SEC_USER_AGENT", None))
        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:05:00Z",
        )
        self.assertEqual(result["status"], "APPLIED_DIAGNOSTIC_ONLY")
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["results"][0]["row_count"], 1)
        con = sqlite3.connect(path)
        try:
            self.assertEqual(con.execute("SELECT provider FROM sec_events").fetchone()[0], "sec_bulk_baseline")
            ledger = con.execute(
                """
                SELECT status, skipped_reason, validation_refs_json
                FROM scheduler_run_ledger
                WHERE cadence='sec_events_refresh'
                """
            ).fetchone()
            self.assertEqual(ledger[0], "SUCCESS")
            self.assertEqual(ledger[1], "")
            self.assertIn('"missing_source_is_negative": 0', ledger[2])
        finally:
            con.close()

    def test_sec_submission_cache_fallback_when_live_fetch_fails(self) -> None:
        path = self._db()
        root = path.parent
        tickers_path = root / "company_tickers.json"
        submissions_path = root / "submissions.zip"
        tickers_path.write_text(
            json.dumps({"0": {"ticker": "AAPL", "cik_str": 320193}}),
            encoding="utf-8",
        )
        with zipfile.ZipFile(submissions_path, "w") as archive:
            archive.writestr(
                "CIK0000320193.json",
                json.dumps(
                    {
                        "filings": {
                            "recent": {
                                "form": ["10-K"],
                                "accessionNumber": ["0000320193-26-000001"],
                                "filingDate": ["2026-02-01"],
                                "acceptanceDateTime": ["2026-02-01T12:34:56.000Z"],
                                "reportDate": ["2025-12-31"],
                            }
                        }
                    }
                ),
            )
        old_tickers = source_runner.SEC_COMPANY_TICKERS_CACHE
        old_submissions = source_runner.SEC_BULK_SUBMISSIONS_ZIP
        old_urlopen = source_runner.urlopen
        old_edgartools = source_runner._fetch_sec_json_edgartools
        old_interval = source_runner.SEC_REQUEST_INTERVAL_SECONDS
        old_user_agent = os.environ.get("SEC_USER_AGENT")
        source_runner.SEC_COMPANY_TICKERS_CACHE = tickers_path
        source_runner.SEC_BULK_SUBMISSIONS_ZIP = submissions_path
        source_runner._fetch_sec_json_edgartools = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("edgartools disabled"))
        source_runner.urlopen = lambda *args, **kwargs: (_ for _ in ()).throw(OSError("blocked"))
        source_runner.SEC_REQUEST_INTERVAL_SECONDS = 0.0
        os.environ["SEC_USER_AGENT"] = "Stock-Investment test@example.com"
        self.addCleanup(lambda: setattr(source_runner, "SEC_COMPANY_TICKERS_CACHE", old_tickers))
        self.addCleanup(lambda: setattr(source_runner, "SEC_BULK_SUBMISSIONS_ZIP", old_submissions))
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_json_edgartools", old_edgartools))
        self.addCleanup(lambda: setattr(source_runner, "SEC_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: os.environ.update({"SEC_USER_AGENT": old_user_agent}) if old_user_agent else os.environ.pop("SEC_USER_AGENT", None))

        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:15:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["results"][0]["row_count"], 1)
        con = sqlite3.connect(path)
        try:
            row = con.execute(
                "SELECT provider, source_url FROM sec_events WHERE ticker='AAPL'"
            ).fetchone()
            self.assertEqual(row[0], "sec_bulk_baseline")
            self.assertIn("submissions.zip::CIK0000320193.json", row[1])
            freshness = con.execute(
                "SELECT provider, strict_gate_allowed, proxy_allowed FROM source_freshness WHERE source_family='sec_events'"
            ).fetchone()
            self.assertEqual(freshness, ("sec_bulk_baseline", 0, 0))
        finally:
            con.close()

    def test_sec_live_success_uses_browser_compatible_headers_before_edgartools(self) -> None:
        path = self._db()
        block_state_path = path.parent / "sec_live_success_state.json"
        missing_tickers_path = path.parent / "missing_company_tickers.json"
        missing_submissions_path = path.parent / "missing_submissions.zip"
        old_tickers = source_runner.SEC_COMPANY_TICKERS_CACHE
        old_submissions = source_runner.SEC_BULK_SUBMISSIONS_ZIP
        old_edgartools = source_runner._fetch_sec_json_edgartools
        old_urlopen = source_runner.urlopen
        old_block_state = source_runner.SEC_LIVE_BLOCK_STATE
        old_interval = source_runner.SEC_REQUEST_INTERVAL_SECONDS
        old_user_agent = os.environ.get("SEC_USER_AGENT")

        captured_headers: list[dict[str, str]] = []

        class FakeUrlopenResponse:
            def __init__(self, payload: dict):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self) -> bytes:
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(request, *args, **kwargs):
            captured_headers.append(dict(request.header_items()))
            url = request.full_url
            payload = (
                {"0": {"ticker": "AAPL", "cik_str": 320193}}
                if url.endswith("/company_tickers.json")
                else {
                    "filings": {
                        "recent": {
                            "form": ["10-Q"],
                            "accessionNumber": ["0000320193-26-000004"],
                            "filingDate": ["2026-06-15"],
                            "acceptanceDateTime": ["2026-06-15T12:34:56.000Z"],
                            "reportDate": ["2026-03-31"],
                        }
                    }
                }
            )
            return FakeUrlopenResponse(payload)

        source_runner._fetch_sec_json_edgartools = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("edgartools should not be called"))
        source_runner.urlopen = fake_urlopen
        source_runner.SEC_COMPANY_TICKERS_CACHE = missing_tickers_path
        source_runner.SEC_BULK_SUBMISSIONS_ZIP = missing_submissions_path
        source_runner.SEC_LIVE_BLOCK_STATE = block_state_path
        source_runner.SEC_REQUEST_INTERVAL_SECONDS = 0.0
        os.environ["SEC_USER_AGENT"] = "Minjo Stock-Investment test@example.com"
        self.addCleanup(lambda: setattr(source_runner, "SEC_COMPANY_TICKERS_CACHE", old_tickers))
        self.addCleanup(lambda: setattr(source_runner, "SEC_BULK_SUBMISSIONS_ZIP", old_submissions))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_json_edgartools", old_edgartools))
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "SEC_LIVE_BLOCK_STATE", old_block_state))
        self.addCleanup(lambda: setattr(source_runner, "SEC_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: os.environ.update({"SEC_USER_AGENT": old_user_agent}) if old_user_agent else os.environ.pop("SEC_USER_AGENT", None))

        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:18:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["results"][0]["row_count"], 1)
        self.assertGreaterEqual(len(captured_headers), 2)
        for headers in captured_headers:
            self.assertEqual(headers.get("User-agent"), source_runner.SEC_BROWSER_COMPAT_USER_AGENT)
            self.assertEqual(headers.get("From"), "test@example.com")
            self.assertEqual(headers.get("Accept-language"), "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7")
        con = sqlite3.connect(path)
        try:
            row = con.execute(
                "SELECT provider, source_url FROM sec_events WHERE ticker='AAPL'"
            ).fetchone()
            self.assertEqual(row, ("sec_live_delta", "https://data.sec.gov/submissions/CIK0000320193.json"))
            freshness = con.execute(
                "SELECT provider, strict_gate_allowed, proxy_allowed FROM source_freshness WHERE source_family='sec_events'"
            ).fetchone()
            self.assertEqual(freshness, ("sec_live_delta", 0, 0))
        finally:
            con.close()

    def test_sec_hybrid_bulk_and_live_delta_dedupe_and_attribute_freshness(self) -> None:
        path = self._db()
        root = path.parent
        tickers_path = root / "company_tickers.json"
        submissions_path = root / "submissions.zip"
        block_state_path = root / "sec_live_mixed_state.json"
        tickers_path.write_text(
            json.dumps({"0": {"ticker": "AAPL", "cik_str": 320193}}),
            encoding="utf-8",
        )
        with zipfile.ZipFile(submissions_path, "w") as archive:
            archive.writestr(
                "CIK0000320193.json",
                json.dumps(
                    {
                        "filings": {
                            "recent": {
                                "form": ["10-Q"],
                                "accessionNumber": ["0000320193-26-000100"],
                                "filingDate": ["2026-06-01"],
                                "acceptanceDateTime": ["2026-06-01T12:34:56.000Z"],
                                "reportDate": ["2026-03-31"],
                            }
                        }
                    }
                ),
            )

        def fake_edgartools(url: str, user_agent: str) -> dict:
            if url.endswith("/CIK0000320193.json"):
                return {
                    "filings": {
                        "recent": {
                            "form": ["10-Q", "8-K"],
                            "accessionNumber": ["0000320193-26-000100", "0000320193-26-000101"],
                            "filingDate": ["2026-06-01", "2026-06-21"],
                            "acceptanceDateTime": ["2026-06-01T12:34:56.000Z", "2026-06-21T12:34:56.000Z"],
                            "reportDate": ["2026-03-31", "2026-06-21"],
                        }
                    }
                }
            return {}

        old_tickers = source_runner.SEC_COMPANY_TICKERS_CACHE
        old_submissions = source_runner.SEC_BULK_SUBMISSIONS_ZIP
        old_block_state = source_runner.SEC_LIVE_BLOCK_STATE
        old_edgartools = source_runner._fetch_sec_json_edgartools
        old_urlopen = source_runner.urlopen
        old_fetch_text = source_runner._fetch_sec_text_live
        old_interval = source_runner.SEC_REQUEST_INTERVAL_SECONDS
        old_user_agent = os.environ.get("SEC_USER_AGENT")
        source_runner.SEC_COMPANY_TICKERS_CACHE = tickers_path
        source_runner.SEC_BULK_SUBMISSIONS_ZIP = submissions_path
        source_runner.SEC_LIVE_BLOCK_STATE = block_state_path
        source_runner._fetch_sec_json_edgartools = fake_edgartools
        source_runner.urlopen = lambda *args, **kwargs: (_ for _ in ()).throw(OSError("direct disabled"))
        source_runner._fetch_sec_text_live = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("rss disabled"))
        source_runner.SEC_REQUEST_INTERVAL_SECONDS = 0.0
        os.environ["SEC_USER_AGENT"] = "Minjo Personal Research test@example.com"
        self.addCleanup(lambda: setattr(source_runner, "SEC_COMPANY_TICKERS_CACHE", old_tickers))
        self.addCleanup(lambda: setattr(source_runner, "SEC_BULK_SUBMISSIONS_ZIP", old_submissions))
        self.addCleanup(lambda: setattr(source_runner, "SEC_LIVE_BLOCK_STATE", old_block_state))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_json_edgartools", old_edgartools))
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_text_live", old_fetch_text))
        self.addCleanup(lambda: setattr(source_runner, "SEC_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: os.environ.update({"SEC_USER_AGENT": old_user_agent}) if old_user_agent else os.environ.pop("SEC_USER_AGENT", None))

        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:19:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["results"][0]["row_count"], 2)
        con = sqlite3.connect(path)
        try:
            providers = con.execute(
                "SELECT provider, COUNT(*) FROM sec_events GROUP BY provider ORDER BY provider"
            ).fetchall()
            self.assertEqual(providers, [("sec_bulk_baseline", 1), ("sec_live_delta", 1)])
            freshness = con.execute(
                "SELECT provider, strict_gate_allowed, proxy_allowed FROM source_freshness WHERE source_family='sec_events'"
            ).fetchone()
            self.assertEqual(freshness, ("sec_live_delta", 0, 0))
        finally:
            con.close()
        metadata = json.loads(Path(result["results"][0]["raw_path"]).read_text(encoding="utf-8"))
        self.assertEqual(metadata["provider"], "sec_live_delta")
        self.assertEqual(metadata["providers_seen"], ["sec_bulk_baseline", "sec_live_delta"])

    def test_sec_undeclared_tool_403_records_cooldown_before_cache_fallback(self) -> None:
        path = self._db()
        root = path.parent
        tickers_path = root / "company_tickers.json"
        submissions_path = root / "submissions.zip"
        block_state_path = root / "sec_live_access_block_state.json"
        tickers_path.write_text(
            json.dumps({"0": {"ticker": "AAPL", "cik_str": 320193}}),
            encoding="utf-8",
        )
        with zipfile.ZipFile(submissions_path, "w") as archive:
            archive.writestr(
                "CIK0000320193.json",
                json.dumps(
                    {
                        "filings": {
                            "recent": {
                                "form": ["10-Q"],
                                "accessionNumber": ["0000320193-26-000002"],
                                "filingDate": ["2026-05-01"],
                                "acceptanceDateTime": ["2026-05-01T12:34:56.000Z"],
                                "reportDate": ["2026-03-31"],
                            }
                        }
                    }
                ),
            )

        old_tickers = source_runner.SEC_COMPANY_TICKERS_CACHE
        old_submissions = source_runner.SEC_BULK_SUBMISSIONS_ZIP
        old_block_state = source_runner.SEC_LIVE_BLOCK_STATE
        old_urlopen = source_runner.urlopen
        old_edgartools = source_runner._fetch_sec_json_edgartools
        old_interval = source_runner.SEC_REQUEST_INTERVAL_SECONDS
        old_user_agent = os.environ.get("SEC_USER_AGENT")

        def blocked_urlopen(*args, **kwargs):
            body = b"<title>SEC.gov | Your Request Originates from an Undeclared Automated Tool</title>"
            raise HTTPError(
                url="https://data.sec.gov/submissions/CIK0000320193.json",
                code=403,
                msg="Forbidden",
                hdrs={},
                fp=BytesIO(body),
            )

        source_runner.SEC_COMPANY_TICKERS_CACHE = tickers_path
        source_runner.SEC_BULK_SUBMISSIONS_ZIP = submissions_path
        source_runner.SEC_LIVE_BLOCK_STATE = block_state_path
        source_runner._fetch_sec_json_edgartools = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("edgartools disabled"))
        source_runner.urlopen = blocked_urlopen
        source_runner.SEC_REQUEST_INTERVAL_SECONDS = 0.0
        os.environ["SEC_USER_AGENT"] = "Minjo Personal Research test@example.com"
        self.addCleanup(lambda: setattr(source_runner, "SEC_COMPANY_TICKERS_CACHE", old_tickers))
        self.addCleanup(lambda: setattr(source_runner, "SEC_BULK_SUBMISSIONS_ZIP", old_submissions))
        self.addCleanup(lambda: setattr(source_runner, "SEC_LIVE_BLOCK_STATE", old_block_state))
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_json_edgartools", old_edgartools))
        self.addCleanup(lambda: setattr(source_runner, "SEC_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: os.environ.update({"SEC_USER_AGENT": old_user_agent}) if old_user_agent else os.environ.pop("SEC_USER_AGENT", None))

        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:20:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        self.assertTrue(block_state_path.exists())
        block_state = json.loads(block_state_path.read_text(encoding="utf-8"))
        self.assertEqual(block_state["reason"], "SEC_UNDECLARED_AUTOMATED_TOOL_403")
        self.assertEqual(block_state["status"], "SEC_LIVE_TEMPORARILY_BLOCKED")
        self.assertEqual(block_state["cooldown_seconds"], 600)
        detected = datetime.fromisoformat(block_state["detected_at"].replace("Z", "+00:00"))
        retry_after = datetime.fromisoformat(block_state["retry_after_ts"].replace("Z", "+00:00"))
        self.assertEqual(int((retry_after - detected).total_seconds()), 600)
        con = sqlite3.connect(path)
        try:
            row = con.execute("SELECT provider FROM sec_events WHERE ticker='AAPL'").fetchone()
            self.assertEqual(row[0], "sec_bulk_baseline")
        finally:
            con.close()

    def test_sec_rate_threshold_403_records_cooldown_before_cache_fallback(self) -> None:
        path = self._db()
        root = path.parent
        tickers_path = root / "company_tickers.json"
        submissions_path = root / "submissions.zip"
        block_state_path = root / "sec_live_rate_block_state.json"
        tickers_path.write_text(
            json.dumps({"0": {"ticker": "AAPL", "cik_str": 320193}}),
            encoding="utf-8",
        )
        with zipfile.ZipFile(submissions_path, "w") as archive:
            archive.writestr(
                "CIK0000320193.json",
                json.dumps(
                    {
                        "filings": {
                            "recent": {
                                "form": ["8-K"],
                                "accessionNumber": ["0000320193-26-000003"],
                                "filingDate": ["2026-06-01"],
                                "acceptanceDateTime": ["2026-06-01T12:34:56.000Z"],
                                "reportDate": ["2026-06-01"],
                            }
                        }
                    }
                ),
            )

        old_tickers = source_runner.SEC_COMPANY_TICKERS_CACHE
        old_submissions = source_runner.SEC_BULK_SUBMISSIONS_ZIP
        old_block_state = source_runner.SEC_LIVE_BLOCK_STATE
        old_urlopen = source_runner.urlopen
        old_edgartools = source_runner._fetch_sec_json_edgartools
        old_interval = source_runner.SEC_REQUEST_INTERVAL_SECONDS
        old_user_agent = os.environ.get("SEC_USER_AGENT")

        def rate_limited_urlopen(*args, **kwargs):
            body = b"<title>SEC.gov | Request Rate Threshold Exceeded</title>"
            raise HTTPError(
                url="https://www.sec.gov/files/company_tickers.json",
                code=403,
                msg="Forbidden",
                hdrs={},
                fp=BytesIO(body),
            )

        source_runner.SEC_COMPANY_TICKERS_CACHE = tickers_path
        source_runner.SEC_BULK_SUBMISSIONS_ZIP = submissions_path
        source_runner.SEC_LIVE_BLOCK_STATE = block_state_path
        source_runner._fetch_sec_json_edgartools = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("edgartools disabled"))
        source_runner.urlopen = rate_limited_urlopen
        source_runner.SEC_REQUEST_INTERVAL_SECONDS = 0.0
        os.environ["SEC_USER_AGENT"] = "Minjo Personal Research test@example.com"
        self.addCleanup(lambda: setattr(source_runner, "SEC_COMPANY_TICKERS_CACHE", old_tickers))
        self.addCleanup(lambda: setattr(source_runner, "SEC_BULK_SUBMISSIONS_ZIP", old_submissions))
        self.addCleanup(lambda: setattr(source_runner, "SEC_LIVE_BLOCK_STATE", old_block_state))
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_json_edgartools", old_edgartools))
        self.addCleanup(lambda: setattr(source_runner, "SEC_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: os.environ.update({"SEC_USER_AGENT": old_user_agent}) if old_user_agent else os.environ.pop("SEC_USER_AGENT", None))

        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:25:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        block_state = json.loads(block_state_path.read_text(encoding="utf-8"))
        self.assertEqual(block_state["reason"], "SEC_REQUEST_RATE_THRESHOLD_403")
        self.assertEqual(block_state["status"], "SEC_LIVE_TEMPORARILY_BLOCKED")
        self.assertEqual(block_state["cooldown_seconds"], 600)

    def test_sec_edgartools_403_records_cooldown_without_urllib_retry(self) -> None:
        path = self._db()
        root = path.parent
        tickers_path = root / "company_tickers.json"
        submissions_path = root / "submissions.zip"
        block_state_path = root / "sec_live_edgartools_rate_block_state.json"
        tickers_path.write_text(
            json.dumps({"0": {"ticker": "AAPL", "cik_str": 320193}}),
            encoding="utf-8",
        )
        with zipfile.ZipFile(submissions_path, "w") as archive:
            archive.writestr(
                "CIK0000320193.json",
                json.dumps(
                    {
                        "filings": {
                            "recent": {
                                "form": ["8-K"],
                                "accessionNumber": ["0000320193-26-000005"],
                                "filingDate": ["2026-06-20"],
                                "acceptanceDateTime": ["2026-06-20T12:34:56.000Z"],
                                "reportDate": ["2026-06-20"],
                            }
                        }
                    }
                ),
            )

        class FakeResponse:
            status_code = 403
            text = "<title>SEC.gov | Request Rate Threshold Exceeded</title>"

        class FakeEdgarError(Exception):
            response = FakeResponse()

        old_tickers = source_runner.SEC_COMPANY_TICKERS_CACHE
        old_submissions = source_runner.SEC_BULK_SUBMISSIONS_ZIP
        old_block_state = source_runner.SEC_LIVE_BLOCK_STATE
        old_urlopen = source_runner.urlopen
        old_edgartools = source_runner._fetch_sec_json_edgartools
        old_interval = source_runner.SEC_REQUEST_INTERVAL_SECONDS
        old_user_agent = os.environ.get("SEC_USER_AGENT")
        source_runner.SEC_COMPANY_TICKERS_CACHE = tickers_path
        source_runner.SEC_BULK_SUBMISSIONS_ZIP = submissions_path
        source_runner.SEC_LIVE_BLOCK_STATE = block_state_path
        source_runner._fetch_sec_json_edgartools = lambda *args, **kwargs: (_ for _ in ()).throw(FakeEdgarError("403 Forbidden"))
        source_runner.urlopen = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("urllib should not retry after active cooldown"))
        source_runner.SEC_REQUEST_INTERVAL_SECONDS = 0.0
        os.environ["SEC_USER_AGENT"] = "Minjo Personal Research test@example.com"
        self.addCleanup(lambda: setattr(source_runner, "SEC_COMPANY_TICKERS_CACHE", old_tickers))
        self.addCleanup(lambda: setattr(source_runner, "SEC_BULK_SUBMISSIONS_ZIP", old_submissions))
        self.addCleanup(lambda: setattr(source_runner, "SEC_LIVE_BLOCK_STATE", old_block_state))
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_json_edgartools", old_edgartools))
        self.addCleanup(lambda: setattr(source_runner, "SEC_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: os.environ.update({"SEC_USER_AGENT": old_user_agent}) if old_user_agent else os.environ.pop("SEC_USER_AGENT", None))

        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:30:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        block_state = json.loads(block_state_path.read_text(encoding="utf-8"))
        self.assertEqual(block_state["reason"], "SEC_REQUEST_RATE_THRESHOLD_403")
        self.assertGreater(block_state["response_body_length"], 0)
        self.assertEqual(len(block_state["response_body_sha256"]), 64)
        con = sqlite3.connect(path)
        try:
            row = con.execute("SELECT provider FROM sec_events WHERE ticker='AAPL'").fetchone()
            self.assertEqual(row[0], "sec_bulk_baseline")
        finally:
            con.close()

    def test_sec_rss_delta_records_separate_provider(self) -> None:
        path = self._db()
        root = path.parent
        missing_tickers_path = root / "missing_company_tickers.json"
        missing_submissions_path = root / "missing_submissions.zip"
        block_state_path = root / "sec_live_rss_state.json"
        old_tickers = source_runner.SEC_COMPANY_TICKERS_CACHE
        old_submissions = source_runner.SEC_BULK_SUBMISSIONS_ZIP
        old_block_state = source_runner.SEC_LIVE_BLOCK_STATE
        old_edgartools = source_runner._fetch_sec_json_edgartools
        old_urlopen = source_runner.urlopen
        old_fetch_text = source_runner._fetch_sec_text_live
        old_interval = source_runner.SEC_REQUEST_INTERVAL_SECONDS
        old_user_agent = os.environ.get("SEC_USER_AGENT")

        def fake_edgartools(url: str, user_agent: str) -> dict:
            if url.endswith("/company_tickers.json"):
                return {"0": {"ticker": "AAPL", "cik_str": 320193}}
            if url.endswith("/CIK0000320193.json"):
                return {"filings": {"recent": {"form": [], "accessionNumber": []}}}
            return {}

        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>8-K - Apple Inc. (0000320193) (Filer)</title>
            <updated>2026-06-21T12:34:56Z</updated>
            <link href="https://www.sec.gov/Archives/edgar/data/320193/0000320193-26-000111-index.htm" />
          </entry>
        </feed>
        """

        source_runner.SEC_COMPANY_TICKERS_CACHE = missing_tickers_path
        source_runner.SEC_BULK_SUBMISSIONS_ZIP = missing_submissions_path
        source_runner.SEC_LIVE_BLOCK_STATE = block_state_path
        source_runner._fetch_sec_json_edgartools = fake_edgartools
        source_runner.urlopen = lambda *args, **kwargs: (_ for _ in ()).throw(OSError("direct disabled"))
        source_runner._fetch_sec_text_live = lambda *args, **kwargs: rss_xml
        source_runner.SEC_REQUEST_INTERVAL_SECONDS = 0.0
        os.environ["SEC_USER_AGENT"] = "Minjo Personal Research test@example.com"
        self.addCleanup(lambda: setattr(source_runner, "SEC_COMPANY_TICKERS_CACHE", old_tickers))
        self.addCleanup(lambda: setattr(source_runner, "SEC_BULK_SUBMISSIONS_ZIP", old_submissions))
        self.addCleanup(lambda: setattr(source_runner, "SEC_LIVE_BLOCK_STATE", old_block_state))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_json_edgartools", old_edgartools))
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_text_live", old_fetch_text))
        self.addCleanup(lambda: setattr(source_runner, "SEC_REQUEST_INTERVAL_SECONDS", old_interval))
        self.addCleanup(lambda: os.environ.update({"SEC_USER_AGENT": old_user_agent}) if old_user_agent else os.environ.pop("SEC_USER_AGENT", None))

        result = run_once(
            db_path=path,
            apply=True,
            families=("sec_events",),
            symbols=("AAPL",),
            allow_network=True,
            bucket="2026-06-21T00:32:00Z",
        )

        self.assertEqual(result["success_count"], 1)
        con = sqlite3.connect(path)
        try:
            row = con.execute(
                "SELECT provider, accession_no, form_type, event_type FROM sec_events WHERE ticker='AAPL'"
            ).fetchone()
            self.assertEqual(row, ("sec_rss_delta", "0000320193-26-000111", "8-K", "latest_filing_rss_delta"))
            freshness = con.execute(
                "SELECT provider, strict_gate_allowed, proxy_allowed FROM source_freshness WHERE source_family='sec_events'"
            ).fetchone()
            self.assertEqual(freshness, ("sec_rss_delta", 0, 0))
        finally:
            con.close()

    def test_sec_rss_403_uses_browser_compatible_text_fallback(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        block_state_path = root / "sec_live_rss_recovered_state.json"
        old_block_state = source_runner.SEC_LIVE_BLOCK_STATE
        old_urlopen = source_runner.urlopen
        old_browser_compat = source_runner._fetch_sec_text_browser_compat
        old_interval = source_runner.SEC_REQUEST_INTERVAL_SECONDS

        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>8-K - Apple Inc. (0000320193) (Filer)</title>
            <updated>2026-06-21T12:34:56Z</updated>
            <link href="https://www.sec.gov/Archives/edgar/data/320193/0000320193-26-000222-index.htm" />
          </entry>
        </feed>
        """

        def fake_urlopen(request, *args, **kwargs):
            raise HTTPError(
                request.full_url,
                403,
                "Forbidden",
                {"Content-Encoding": "identity"},
                BytesIO(b"Your Request Originates from an Undeclared Automated Tool"),
            )

        source_runner.SEC_LIVE_BLOCK_STATE = block_state_path
        source_runner.urlopen = fake_urlopen
        source_runner._fetch_sec_text_browser_compat = lambda *args, **kwargs: rss_xml
        source_runner.SEC_REQUEST_INTERVAL_SECONDS = 0.0
        self.addCleanup(lambda: setattr(source_runner, "SEC_LIVE_BLOCK_STATE", old_block_state))
        self.addCleanup(lambda: setattr(source_runner, "urlopen", old_urlopen))
        self.addCleanup(lambda: setattr(source_runner, "_fetch_sec_text_browser_compat", old_browser_compat))
        self.addCleanup(lambda: setattr(source_runner, "SEC_REQUEST_INTERVAL_SECONDS", old_interval))

        rows = source_runner._fetch_sec_rss_delta(
            ("AAPL",),
            {"0": {"ticker": "AAPL", "cik_str": 320193}},
            "Minjo Personal Research test@example.com",
            set(),
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["provider"], "sec_rss_delta")
        self.assertEqual(rows[0]["accession_no"], "0000320193-26-000222")
        state = json.loads(block_state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "SEC_LIVE_ACCESS_RECOVERED")
        self.assertEqual(state["endpoint_group"], "sec_rss_delta")

    def test_sec_live_block_cooldown_escalates_after_consecutive_blocks(self) -> None:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(root, ignore_errors=True))
        block_state_path = root / "sec_live_escalation_state.json"
        old_block_state = source_runner.SEC_LIVE_BLOCK_STATE
        source_runner.SEC_LIVE_BLOCK_STATE = block_state_path
        self.addCleanup(lambda: setattr(source_runner, "SEC_LIVE_BLOCK_STATE", old_block_state))

        source_runner._record_sec_live_block(
            url="https://www.sec.gov/files/company_tickers.json",
            reason="SEC_REQUEST_RATE_THRESHOLD_403",
            status_code=403,
            response_body="same block page",
        )
        first = json.loads(block_state_path.read_text(encoding="utf-8"))
        self.assertEqual(first["consecutive_block_count"], 1)
        self.assertEqual(first["cooldown_seconds"], 600)

        source_runner._record_sec_live_block(
            url="https://www.sec.gov/files/company_tickers.json",
            reason="SEC_REQUEST_RATE_THRESHOLD_403",
            status_code=403,
            response_body="same block page",
        )
        second = json.loads(block_state_path.read_text(encoding="utf-8"))
        self.assertEqual(second["consecutive_block_count"], 2)
        self.assertEqual(second["cooldown_seconds"], 1800)
        self.assertTrue(second["same_response_body_as_previous"])


if __name__ == "__main__":
    unittest.main()
