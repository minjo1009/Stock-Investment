from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.validate_l2_canonical_primitive_contract import validate as validate_contract
from scripts.validate_l2_news_canonical_path import validate as validate_news
from scripts.validate_l2_no_trade_outputs import validate as validate_no_trade_outputs
from scripts.validate_l3_inputs_are_l2_canonical import validate as validate_l3_inputs
from src.l2.news_runtime import load_news_collector_events, write_news_l2_primitives
from src.l2.runtime_context import LIVE_INTRADAY_DIAGNOSTIC
from src.l2.stores.primitive_reader import load_l3_inputs


class L2NewsCanonicalPathTest(unittest.TestCase):
    def test_official_raw_rows_become_news_l2_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw.json"
            raw.write_text(
                json.dumps(
                    {
                        "parsed_rows": [
                            {
                                "provider": "official_public_releases",
                                "published_at": "2026-06-28T01:00:00Z",
                                "source_url": "https://example.com/aapl",
                                "title": "Official AAPL update",
                                "symbols": ["AAPL"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            events = [
                {
                    "provider": "official_public_releases",
                    "source_family": "official_public_releases",
                    "source_id": "apple_newsroom",
                    "status": "EXPORTED",
                    "row_count": 1,
                    "raw_path": str(raw),
                    "raw_sha256": "hash",
                    "updated_at": "2026-06-28T01:05:00Z",
                    "diagnostic_only_flag": 1,
                    "trade_authority_flag": 0,
                }
            ]
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = write_news_l2_primitives(
                    conn,
                    events=events,
                    capture_ts="2026-06-28T01:06:00Z",
                    runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                )
                self.assertEqual(result["news_fact_count"], 1)
                l3_rows = load_l3_inputs(conn, asof_ts="2026-06-28T01:06:00Z", runtime_context=LIVE_INTRADAY_DIAGNOSTIC)
            finally:
                conn.close()
            self.assertEqual(len([row for row in l3_rows if row.source_family == "news_event"]), 1)
            self.assertEqual(validate_contract(db_path), [])
            self.assertEqual(validate_news(db_path), [])
            self.assertEqual(validate_no_trade_outputs(db_path), [])
            self.assertEqual(validate_l3_inputs(db_path), [])

    def test_empty_provider_response_is_blocker_not_negative_or_l3_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = write_news_l2_primitives(
                    conn,
                    events=[
                        {
                            "provider": "marketaux_news_free",
                            "source_family": "marketaux_news_free",
                            "source_id": "AAPL,MSFT",
                            "status": "EMPTY_PROVIDER_RESPONSE",
                            "row_count": 0,
                            "raw_path": "",
                            "raw_sha256": "",
                            "updated_at": "2026-06-28T01:05:00Z",
                            "diagnostic_only_flag": 1,
                            "trade_authority_flag": 0,
                        }
                    ],
                    capture_ts="2026-06-28T01:06:00Z",
                    runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                )
                self.assertEqual(result["news_fact_count"], 1)
                l3_rows = load_l3_inputs(conn, asof_ts="2026-06-28T01:06:00Z", runtime_context=LIVE_INTRADAY_DIAGNOSTIC)
                status = conn.execute(
                    "SELECT freshness_status, missing_source_is_negative FROM l2_primitive_facts WHERE source_family = 'news_event'"
                ).fetchone()
            finally:
                conn.close()
            self.assertEqual(status[0], "MISSING")
            self.assertEqual(int(status[1]), 0)
            self.assertEqual(len([row for row in l3_rows if row.source_family == "news_event"]), 0)
            self.assertEqual(validate_news(db_path), [])

    def test_public_headline_browser_rows_preserve_evidence_and_block_without_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "browser_headlines.json"
            raw.write_text(
                json.dumps(
                    {
                        "provider": "public_headline_browser_watch",
                        "source_id": "prnewswire_all_news_releases",
                        "source_url": "https://www.prnewswire.com/news-releases/",
                        "captured_at": "2026-06-28T01:05:00Z",
                        "selector_version": "test-selector-v1",
                        "headlines": [
                            {
                                "provider": "public_headline_browser_watch",
                                "title": "Example public headline captured from the listing page",
                                "url": "https://www.prnewswire.com/news-releases/example-302000000.html",
                                "source_page_url": "https://www.prnewswire.com/news-releases/",
                                "detected_at": "2026-06-28T01:05:00Z",
                                "event_time": "2026-06-28T01:05:00Z",
                                "headline_hash": "headline-hash",
                                "symbols": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = write_news_l2_primitives(
                    conn,
                    events=[
                        {
                            "provider": "public_headline_browser_watch",
                            "source_family": "public_headline_browser_watch",
                            "source_id": "prnewswire_all_news_releases::latest_listing",
                            "status": "EXPORTED",
                            "row_count": 1,
                            "raw_path": str(raw),
                            "raw_sha256": "raw-hash",
                            "updated_at": "2026-06-28T01:05:00Z",
                            "diagnostic_only_flag": 1,
                            "trade_authority_flag": 0,
                        }
                    ],
                    capture_ts="2026-06-28T01:06:00Z",
                    runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                )
                payload = conn.execute(
                    "SELECT primitive_payload_json, trade_output_flag, score_output_flag FROM l2_primitive_facts WHERE provider = 'public_headline_browser_watch'"
                ).fetchone()
            finally:
                conn.close()
            self.assertEqual(result["news_fact_count"], 1)
            parsed = json.loads(payload[0])
            self.assertEqual(parsed["headline_hash"], "headline-hash")
            self.assertEqual(parsed["selector_version"], "test-selector-v1")
            self.assertEqual(parsed["promotion_status"], "BLOCKED")
            self.assertIn("missing_entity_or_ticker_mapping", parsed["quality_flags"])
            self.assertEqual(int(payload[1]), 0)
            self.assertEqual(int(payload[2]), 0)
            self.assertEqual(validate_news(db_path), [])

    def test_public_newswire_rows_preserve_entity_mapping_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "newswire_headlines.json"
            raw.write_text(
                json.dumps(
                    {
                        "provider": "public_newswire_feeds",
                        "source_key": "prnewswire",
                        "captured_at": "2026-06-28T01:05:00Z",
                        "headlines": [
                            {
                                "provider": "public_newswire_feeds",
                                "title": "BMI Investors Have Opportunity to Lead Badger Meter, Inc. Securities Fraud Lawsuit",
                                "source_url": "https://example.com/bmi.html",
                                "published_at": "2026-06-28T01:00:00Z",
                                "detected_at": "2026-06-28T01:05:00Z",
                                "headline_hash": "headline-hash",
                                "symbols": ["BMI"],
                                "entities": [{"symbol": "BMI", "match_type": "exact_universe_alias"}],
                                "entity_map": [{"symbol": "BMI", "match_type": "exact_universe_alias"}],
                                "entity_mapping_status": "MAPPED_EXACT_ALIAS",
                                "entity_mapping_methods": ["exact_universe_alias"],
                                "entity_mapping_version": "public_newswire_entity_mapper.v0.1.0",
                                "entity_mapping_inferred_flag": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = write_news_l2_primitives(
                    conn,
                    events=[
                        {
                            "provider": "public_newswire_feeds",
                            "source_family": "public_newswire_feeds",
                            "source_id": "prnewswire::rss_sitemap",
                            "status": "EXPORTED",
                            "row_count": 1,
                            "raw_path": str(raw),
                            "raw_sha256": "raw-hash",
                            "updated_at": "2026-06-28T01:05:00Z",
                            "diagnostic_only_flag": 1,
                            "trade_authority_flag": 0,
                        }
                    ],
                    capture_ts="2026-06-28T01:06:00Z",
                    runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                )
                payload = conn.execute(
                    "SELECT primitive_payload_json, symbol, trade_output_flag, score_output_flag FROM l2_primitive_facts WHERE provider = 'public_newswire_feeds'"
                ).fetchone()
            finally:
                conn.close()
            self.assertEqual(result["news_fact_count"], 1)
            parsed = json.loads(payload[0])
            self.assertEqual(payload[1], "BMI")
            self.assertEqual(parsed["entity_mapping_status"], "MAPPED_EXACT_ALIAS")
            self.assertEqual(parsed["entity_mapping_methods"], ["exact_universe_alias"])
            self.assertEqual(parsed["entity_mapping_inferred_flag"], 0)
            self.assertEqual(parsed["promotion_status"], "READY_DISCOVERY_ONLY")
            self.assertEqual(int(payload[2]), 0)
            self.assertEqual(int(payload[3]), 0)
            self.assertEqual(validate_news(db_path), [])

    def test_public_newswire_context_rows_do_not_require_ticker_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "newswire_context_headlines.json"
            raw.write_text(
                json.dumps(
                    {
                        "provider": "public_newswire_feeds",
                        "source_key": "prnewswire",
                        "captured_at": "2026-06-28T01:05:00Z",
                        "headlines": [
                            {
                                "provider": "public_newswire_feeds",
                                "title": "Federal Reserve policy and artificial intelligence reshape commerce trends",
                                "source_url": "https://example.com/context.html",
                                "published_at": "2026-06-28T01:00:00Z",
                                "detected_at": "2026-06-28T01:05:00Z",
                                "headline_hash": "context-hash",
                                "symbols": [],
                                "entities": [],
                                "entity_map": [],
                                "entity_mapping_status": "NOT_REQUIRED_CONTEXT_NEWSWIRE",
                                "context_source_class": "public_newswire_context",
                                "context_scope": ["ai_infrastructure", "monetary_policy"],
                                "context_topic_candidates": ["ai_infrastructure", "monetary_policy"],
                                "context_classification_methods": ["deterministic_newswire_context_keyword"],
                                "macro_context_candidate_flag": 1,
                                "ticker_mapping_required_flag": 0,
                                "entity_mapping_inferred_flag": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = write_news_l2_primitives(
                    conn,
                    events=[
                        {
                            "provider": "public_newswire_feeds",
                            "source_family": "public_newswire_feeds",
                            "source_id": "prnewswire::rss_sitemap",
                            "status": "EXPORTED",
                            "row_count": 1,
                            "raw_path": str(raw),
                            "raw_sha256": "raw-hash",
                            "updated_at": "2026-06-28T01:05:00Z",
                            "diagnostic_only_flag": 1,
                            "trade_authority_flag": 0,
                        }
                    ],
                    capture_ts="2026-06-28T01:06:00Z",
                    runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                )
                payload = conn.execute(
                    "SELECT primitive_payload_json, symbol, trade_output_flag, score_output_flag FROM l2_primitive_facts WHERE provider = 'public_newswire_feeds'"
                ).fetchone()
            finally:
                conn.close()
            self.assertEqual(result["news_fact_count"], 1)
            parsed = json.loads(payload[0])
            self.assertIsNone(payload[1])
            self.assertEqual(parsed["promotion_status"], "READY_DISCOVERY_ONLY")
            self.assertNotIn("missing_entity_or_ticker_mapping", parsed["quality_flags"])
            self.assertEqual(parsed["ticker_mapping_required_flag"], 0)
            self.assertEqual(parsed["entity_mapping_status"], "NOT_REQUIRED_CONTEXT_NEWSWIRE")
            self.assertEqual(int(payload[2]), 0)
            self.assertEqual(int(payload[3]), 0)
            self.assertEqual(validate_news(db_path), [])

    def test_public_context_news_rows_do_not_require_ticker_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "context_headlines.json"
            raw.write_text(
                json.dumps(
                    {
                        "provider": "public_context_news_feeds",
                        "source_key": "federal_reserve_press_all",
                        "captured_at": "2026-06-28T01:05:00Z",
                        "headlines": [
                            {
                                "provider": "public_context_news_feeds",
                                "source_key": "federal_reserve_press_all",
                                "source_display_name": "Federal Reserve",
                                "title": "Federal Reserve announces interest rate decision",
                                "source_url": "https://www.federalreserve.gov/newsevents/pressreleases/example.htm",
                                "published_at": "2026-06-28T01:00:00Z",
                                "detected_at": "2026-06-28T01:05:00Z",
                                "headline_hash": "context-hash",
                                "symbols": [],
                                "context_source_class": "official_macro",
                                "context_scope": ["monetary_policy"],
                                "context_topic_candidates": ["monetary_policy"],
                                "macro_context_candidate_flag": 1,
                                "ticker_mapping_required_flag": 0,
                                "entity_mapping_status": "NOT_REQUIRED_CONTEXT_NEWS",
                                "entity_mapping_inferred_flag": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = write_news_l2_primitives(
                    conn,
                    events=[
                        {
                            "provider": "public_context_news_feeds",
                            "source_family": "public_context_news_feeds",
                            "source_id": "federal_reserve_press_all::context_watch",
                            "status": "EXPORTED",
                            "row_count": 1,
                            "raw_path": str(raw),
                            "raw_sha256": "raw-hash",
                            "updated_at": "2026-06-28T01:05:00Z",
                            "diagnostic_only_flag": 1,
                            "trade_authority_flag": 0,
                        }
                    ],
                    capture_ts="2026-06-28T01:06:00Z",
                    runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                )
                payload = conn.execute(
                    "SELECT primitive_payload_json, symbol, trade_output_flag, score_output_flag FROM l2_primitive_facts WHERE provider = 'public_context_news_feeds'"
                ).fetchone()
            finally:
                conn.close()
            self.assertEqual(result["news_fact_count"], 1)
            parsed = json.loads(payload[0])
            self.assertIsNone(payload[1])
            self.assertEqual(parsed["promotion_status"], "READY_DISCOVERY_ONLY")
            self.assertNotIn("missing_entity_or_ticker_mapping", parsed["quality_flags"])
            self.assertEqual(parsed["ticker_mapping_required_flag"], 0)
            self.assertEqual(parsed["context_topic_candidates"], ["monetary_policy"])
            self.assertEqual(int(payload[2]), 0)
            self.assertEqual(int(payload[3]), 0)
            self.assertEqual(validate_news(db_path), [])

    def test_public_market_macro_news_rows_do_not_require_ticker_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "market_macro_headlines.json"
            raw.write_text(
                json.dumps(
                    {
                        "provider": "public_market_macro_news_feeds",
                        "source_key": "cnbc_public_rss",
                        "captured_at": "2026-06-28T01:05:00Z",
                        "headlines": [
                            {
                                "provider": "public_market_macro_news_feeds",
                                "source_key": "cnbc_public_rss",
                                "source_display_name": "CNBC",
                                "title": "Core inflation rate moves bond markets",
                                "source_url": "https://www.cnbc.com/2026/06/28/example.html",
                                "published_at": "2026-06-28T01:00:00Z",
                                "detected_at": "2026-06-28T01:05:00Z",
                                "headline_hash": "market-macro-hash",
                                "symbols": [],
                                "context_source_class": "market_macro_media_context",
                                "context_scope": ["macro", "markets"],
                                "context_topic_candidates": ["inflation", "risk_appetite"],
                                "macro_context_candidate_flag": 1,
                                "ticker_mapping_required_flag": 0,
                                "entity_mapping_status": "NOT_REQUIRED_MARKET_MACRO_CONTEXT",
                                "entity_mapping_inferred_flag": 0,
                                "section_id": "business",
                                "summary": "Summary",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = write_news_l2_primitives(
                    conn,
                    events=[
                        {
                            "provider": "public_market_macro_news_feeds",
                            "source_family": "public_market_macro_news_feeds",
                            "source_id": "cnbc_public_rss::market_macro_watch",
                            "status": "EXPORTED",
                            "row_count": 1,
                            "raw_path": str(raw),
                            "raw_sha256": "raw-hash",
                            "updated_at": "2026-06-28T01:05:00Z",
                            "diagnostic_only_flag": 1,
                            "trade_authority_flag": 0,
                        }
                    ],
                    capture_ts="2026-06-28T01:06:00Z",
                    runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                )
                payload = conn.execute(
                    "SELECT primitive_payload_json, symbol, trade_output_flag, score_output_flag FROM l2_primitive_facts WHERE provider = 'public_market_macro_news_feeds'"
                ).fetchone()
            finally:
                conn.close()
            self.assertEqual(result["news_fact_count"], 1)
            parsed = json.loads(payload[0])
            self.assertIsNone(payload[1])
            self.assertEqual(parsed["promotion_status"], "READY_DISCOVERY_ONLY")
            self.assertNotIn("missing_entity_or_ticker_mapping", parsed["quality_flags"])
            self.assertEqual(parsed["ticker_mapping_required_flag"], 0)
            self.assertEqual(parsed["summary"], "Summary")
            self.assertEqual(int(payload[2]), 0)
            self.assertEqual(int(payload[3]), 0)
            self.assertEqual(validate_news(db_path), [])

    def test_event_loader_and_empty_ingest_do_not_fail_whole_layer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event_path = root / "events.jsonl"
            event_path.write_text("", encoding="utf-8")
            events = load_news_collector_events([event_path])
            db_path = root / "l2.db"
            conn = sqlite3.connect(db_path)
            try:
                result = write_news_l2_primitives(
                    conn,
                    events=events,
                    capture_ts="2026-06-28T01:06:00Z",
                    runtime_context=LIVE_INTRADAY_DIAGNOSTIC,
                )
            finally:
                conn.close()
            self.assertEqual(result["input_event_count"], 0)
            self.assertEqual(result["news_fact_count"], 0)
            self.assertEqual(validate_news(db_path), [])


if __name__ == "__main__":
    unittest.main()
