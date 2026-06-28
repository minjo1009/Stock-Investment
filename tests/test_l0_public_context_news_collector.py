from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.db.source_acquisition.public_context_news_collector import (
    DEFAULT_BACKFILL_SOURCES,
    DEFAULT_SOURCES,
    PublicContextNewsConfig,
    parse_cftc_archive,
    parse_federal_reserve_archive_rows,
    parse_federal_register_rows,
    parse_feed_rows,
    parse_worldbank_news_rows,
    run_backfill,
    run_collector,
)


class L0PublicContextNewsCollectorTests(unittest.TestCase):
    def test_official_expansion_sources_are_default_enabled(self) -> None:
        expected_live = {
            "ecb_press_rss",
            "ecb_statistical_press_rss",
            "bank_of_england_news_rss",
            "bank_of_england_speeches_rss",
            "eia_press_rss",
            "defense_public_press_rss",
            "defense_public_contracts_rss",
            "worldbank_news_api",
        }
        self.assertTrue(expected_live.issubset(set(DEFAULT_SOURCES)))
        self.assertIn("worldbank_news_api", DEFAULT_BACKFILL_SOURCES)

    def test_parse_feed_rows_marks_context_without_ticker_requirement(self) -> None:
        source = {
            "source_key": "federal_reserve_press_all",
            "display_name": "Federal Reserve",
            "source_class": "official_macro",
            "context_scope": ["monetary_policy"],
        }
        payload = b"""
        <rss><channel>
          <item>
            <title>Federal Reserve announces interest rate decision</title>
            <link>https://example.gov/release.htm</link>
            <pubDate>Sun, 28 Jun 2026 07:00:00 GMT</pubDate>
          </item>
        </channel></rss>
        """
        rows = parse_feed_rows(payload, source=source, source_page_url="https://example.gov/feed.xml", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["provider"], "public_context_news_feeds")
        self.assertEqual(rows[0]["ticker_mapping_required_flag"], 0)
        self.assertEqual(rows[0]["macro_context_candidate_flag"], 1)
        self.assertIn("monetary_policy", rows[0]["context_topic_candidates"])
        self.assertEqual(rows[0]["entity_mapping_status"], "NOT_REQUIRED_CONTEXT_NEWS")

    def test_parse_federal_register_api_rows(self) -> None:
        source = {
            "source_key": "federal_register_documents",
            "display_name": "Federal Register",
            "source_class": "official_regulatory",
            "context_scope": ["regulation"],
        }
        payload = json.dumps(
            {
                "results": [
                    {
                        "title": "Agency issues final rule on market regulation",
                        "html_url": "https://www.federalregister.gov/documents/example",
                        "publication_date": "2026-06-28",
                        "type": "Rule",
                        "agencies": [{"name": "Example Agency"}],
                    }
                ]
            }
        ).encode("utf-8")
        rows = parse_federal_register_rows(payload, source=source, source_page_url="https://api.example/documents.json", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["capture_method"], "official_json_api")
        self.assertIn("regulation", rows[0]["context_topic_candidates"])

    def test_parse_worldbank_news_api_rows_extracts_source_evidence(self) -> None:
        source = {
            "source_key": "worldbank_news_api",
            "display_name": "World Bank public news API",
            "source_class": "official_global_development",
            "context_scope": ["global_development", "macro", "trade"],
            "worldbank_languages": ["English"],
        }
        payload = json.dumps(
            {
                "total": 2,
                "documents": {
                    "doc1": {
                        "id": "doc1",
                        "title": {"cdata!": "World Bank warns energy inflation risk"},
                        "url": "https://www.worldbank.org/en/news/example",
                        "lnchdt": "2016-01-15T12:00:00Z",
                        "lang": "English",
                        "conttype": "Press Release",
                        "displayconttype": "Press Release",
                        "regionname": "World",
                        "country": "Global",
                        "topic": "Energy,Trade,Economic Growth",
                        "keywd": "subject:energy,subject:trade",
                        "descr": {"cdata!": "Energy market pressure matters for inflation."},
                    },
                    "doc2": {
                        "id": "doc2",
                        "title": {"cdata!": "Spanish headline excluded"},
                        "url": "https://www.worldbank.org/es/news/example",
                        "lnchdt": "2016-01-16T12:00:00Z",
                        "lang": "Spanish",
                    },
                },
            }
        ).encode("utf-8")
        rows = parse_worldbank_news_rows(
            payload,
            source=source,
            source_page_url="https://search.worldbank.org/api/v2/news?format=json&rows=2&os=0",
            captured_at="2026-06-29T00:00:00Z",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["capture_method"], "worldbank_news_json_api")
        self.assertEqual(rows[0]["published_at"], "2016-01-15T12:00:00Z")
        self.assertEqual(rows[0]["worldbank_document_id"], "doc1")
        self.assertEqual(rows[0]["ticker_mapping_required_flag"], 0)
        self.assertIn("global_development", rows[0]["context_topic_candidates"])
        self.assertIn("energy", rows[0]["context_topic_candidates"])

    def test_parse_federal_reserve_archive_rows_extracts_url_date(self) -> None:
        source = {
            "source_key": "federal_reserve_press_all",
            "display_name": "Federal Reserve",
            "source_class": "official_macro",
            "context_scope": ["monetary_policy"],
        }
        payload = b"""
        <html><body>
          <a href="/newsevents/pressreleases/monetary20260617a.htm">Federal Reserve issues FOMC statement</a>
          <a href="/newsevents/pressreleases/2026-press.htm">2026 archive</a>
        </body></html>
        """
        rows = parse_federal_reserve_archive_rows(
            payload,
            source=source,
            source_page_url="https://www.federalreserve.gov/newsevents/pressreleases/2026-press.htm",
            captured_at="2026-06-28T07:01:00Z",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["published_at"], "2026-06-17T00:00:00Z")
        self.assertEqual(rows[0]["capture_method"], "federal_reserve_year_archive")

    def test_parse_cftc_archive_pairs_date_and_release_link(self) -> None:
        source = {
            "source_key": "cftc_press_releases",
            "display_name": "CFTC",
            "source_class": "official_regulatory",
            "context_scope": ["regulation"],
        }
        payload = b"""
        <table>
          <tr>
            <td><time datetime="2016-12-01T00:00:00Z">11/30/2016</time></td>
            <td><a href="/PressRoom/PressReleases/7491-16">CFTC Grants Registration as a Derivatives Clearing Organization</a></td>
          </tr>
        </table>
        <a href="/PressRoom/PressReleases?field_press_release_type_tid=All&amp;year=2016&amp;page=1">Page 2</a>
        """
        rows, total_pages = parse_cftc_archive(
            payload,
            source=source,
            source_page_url="https://www.cftc.gov/PressRoom/PressReleases?field_press_release_type_tid=All&year=2016",
            captured_at="2026-06-28T07:01:00Z",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(total_pages, 2)
        self.assertEqual(rows[0]["published_at"], "2016-12-01T00:00:00Z")
        self.assertEqual(rows[0]["capture_method"], "cftc_year_archive")

    def test_run_collector_writes_context_event_for_mocked_feed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "mock_context",
                                "display_name": "Mock Context",
                                "source_class": "official_macro",
                                "context_scope": ["inflation"],
                                "base_url": "https://example.gov",
                                "rss_or_feed_urls": ["https://example.gov/feed.xml"],
                                "api_urls": [],
                                "page_urls": [],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicContextNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("mock_context",),
                max_items_per_source=1,
                max_fetches_per_source=1,
                request_sleep_seconds=0,
            )
            from tools.db.source_acquisition import public_context_news_collector as collector

            def fake_fetch(url: str, _config: PublicContextNewsConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"<rss><channel><item><title>Inflation report moves markets</title><link>https://example.gov/news/a</link><pubDate>2026-06-28T07:00:00Z</pubDate></item></channel></rss>"
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/rss+xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            original_fetch = collector.fetch_url
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                result = run_collector(config, smoke=True)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]
            event = json.loads(config.event_path.read_text(encoding="utf-8").splitlines()[0])
            raw_payload = json.loads(Path(event["raw_path"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "EXPORTED")
        self.assertEqual(event["l1_ready_discovery_only_count"], 1)
        self.assertEqual(event["l1_blocked_count"], 0)
        self.assertEqual(raw_payload["headlines"][0]["ticker_mapping_required_flag"], 0)

    def test_run_backfill_collects_federal_register_month_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "federal_register_documents",
                                "display_name": "Federal Register",
                                "source_class": "official_regulatory",
                                "context_scope": ["regulation"],
                                "base_url": "https://www.federalregister.gov",
                                "rss_or_feed_urls": [],
                                "api_urls": ["https://www.federalregister.gov/api/v1/documents.json?per_page=20&order=newest"],
                                "page_urls": [],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicContextNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("federal_register_documents",),
                max_items_per_source=10,
                max_fetches_per_source=2,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
                federal_register_per_page=10,
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_context_news_collector as collector

            def fake_fetch(url: str, _config: PublicContextNewsConfig) -> dict[str, object]:
                payload = json.dumps(
                    {
                        "count": 1,
                        "total_pages": 1,
                        "results": [
                            {
                                "title": "Agency issues final rule on market regulation",
                                "html_url": "https://www.federalregister.gov/documents/example",
                                "publication_date": "2016-01-04",
                                "type": "Rule",
                            }
                        ],
                    }
                ).encode("utf-8")
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/json", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            original_fetch = collector.fetch_url
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                result = run_backfill(config, smoke=False)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]
            event = json.loads(config.event_path.read_text(encoding="utf-8").splitlines()[0])
            state = json.loads(config.state_path.read_text(encoding="utf-8"))
            raw_payload = json.loads(Path(event["raw_path"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "EXPORTED")
        self.assertEqual(event["l1_ready_discovery_only_count"], 1)
        self.assertEqual(event["l1_blocked_count"], 0)
        self.assertEqual(state["backfill"]["federal_register_documents"]["completed_units"], ["2016-01"])
        self.assertEqual(raw_payload["collection_mode"], "historical_backfill")

    def test_run_backfill_collects_worldbank_offset_page_until_date_floor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "worldbank_news_api",
                                "display_name": "World Bank public news API",
                                "source_class": "official_global_development",
                                "context_scope": ["global_development", "macro", "trade"],
                                "base_url": "https://www.worldbank.org",
                                "rss_or_feed_urls": [],
                                "api_urls": ["https://search.worldbank.org/api/v2/news?format=json&rows=2&os=0"],
                                "page_urls": [],
                                "worldbank_api_endpoint": "https://search.worldbank.org/api/v2/news",
                                "worldbank_rows_per_page": 2,
                                "worldbank_languages": ["English"],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicContextNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("worldbank_news_api",),
                max_items_per_source=10,
                max_fetches_per_source=1,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_context_news_collector as collector

            def fake_fetch(url: str, _config: PublicContextNewsConfig) -> dict[str, object]:
                payload = json.dumps(
                    {
                        "total": 2,
                        "documents": {
                            "doc1": {
                                "id": "doc1",
                                "title": {"cdata!": "World Bank warns energy inflation risk"},
                                "url": "https://www.worldbank.org/en/news/example",
                                "lnchdt": "2016-01-15T12:00:00Z",
                                "lang": "English",
                            },
                            "doc2": {
                                "id": "doc2",
                                "title": {"cdata!": "Older World Bank development update"},
                                "url": "https://www.worldbank.org/en/news/older",
                                "lnchdt": "2015-12-31T12:00:00Z",
                                "lang": "English",
                            },
                        },
                    }
                ).encode("utf-8")
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/json", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            original_fetch = collector.fetch_url
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                result = run_backfill(config, smoke=False)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]
            event = json.loads(config.event_path.read_text(encoding="utf-8").splitlines()[0])
            state = json.loads(config.state_path.read_text(encoding="utf-8"))
            raw_payload = json.loads(Path(event["raw_path"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "EXPORTED")
        self.assertEqual(event["row_count"], 1)
        self.assertEqual(state["backfill"]["worldbank_news_api"]["completed_units"], ["worldbank_news_desc_cursor"])
        self.assertEqual(raw_payload["headlines"][0]["source_key"], "worldbank_news_api")
        self.assertEqual(raw_payload["headlines"][0]["capture_method"], "worldbank_news_json_api")


if __name__ == "__main__":
    unittest.main()
