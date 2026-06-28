from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.db.source_acquisition.public_market_macro_news_collector import (
    DEFAULT_BACKFILL_SOURCES,
    DEFAULT_LIVE_SOURCES,
    DEFAULT_REGISTRY_PATH,
    PublicMarketMacroNewsConfig,
    canonicalize_news_url,
    parse_feed_rows,
    parse_guardian_api_rows,
    parse_html_headline_rows,
    parse_datetime_value,
    parse_wordpress_rest_rows,
    row_date_within_window,
    run_backfill,
    run_collector,
)


class L0PublicMarketMacroNewsCollectorTests(unittest.TestCase):
    def test_default_live_sources_are_registered(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        registered = {str(source["source_key"]) for source in registry["sources"]}
        missing = sorted(set(DEFAULT_LIVE_SOURCES) - registered)
        self.assertEqual(missing, [])
        self.assertGreaterEqual(len(DEFAULT_LIVE_SOURCES), 22)

    def test_default_backfill_sources_are_registered(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        registered = {str(source["source_key"]) for source in registry["sources"]}
        missing = sorted(set(DEFAULT_BACKFILL_SOURCES) - registered)
        self.assertEqual(missing, [])
        self.assertGreaterEqual(len(DEFAULT_BACKFILL_SOURCES), 13)

    def test_external_news_expansion_sources_are_promoted_after_smoke(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        sources = {str(source["source_key"]): source for source in registry["sources"]}
        for source_key in (
            "cointelegraph_public_rss",
            "decrypt_public_rss",
            "cryptoslate_public_rss",
            "oilprice_public_rss",
            "mining_copper_public_rss",
            "bleepingcomputer_public_rss",
            "krebsonsecurity_public_rss",
            "semiengineering_public_rss",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_LIVE_SOURCES)
                self.assertIn(source_key, sources)
                self.assertGreaterEqual(len(sources[source_key].get("rss_or_feed_urls", [])), 1)
                self.assertIn("no_login", str(sources[source_key].get("terms_posture", "")))

    def test_external_wordpress_backfill_sources_are_promoted_after_smoke(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        sources = {str(source["source_key"]): source for source in registry["sources"]}
        for source_key in (
            "semiengineering_public_wp",
            "bitcoinmagazine_public_wp",
            "nine_to_five_mac_public_wp",
            "nine_to_five_google_public_wp",
            "pv_magazine_usa_public_wp",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_BACKFILL_SOURCES)
                self.assertEqual(sources[source_key].get("historical_backfill_mode"), "wordpress_rest_posts")
                self.assertTrue(sources[source_key].get("wordpress_required_title_term_match"))
                self.assertGreaterEqual(len(sources[source_key].get("wordpress_required_title_terms", [])), 5)

    def test_non_newswire_v2_sources_are_promoted_after_probe(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        sources = {str(source["source_key"]): source for source in registry["sources"]}
        for source_key in (
            "axios_public_rss",
            "the_verge_public_rss",
            "wired_business_public_rss",
            "siliconangle_public_rss",
            "securityweek_public_rss",
            "utilitydive_public_rss",
            "supplychaindive_public_rss",
            "biopharmadive_public_rss",
            "constructiondive_public_rss",
            "cfodive_public_rss",
            "restaurantdive_public_rss",
            "grocerydive_public_rss",
            "marketingdive_public_rss",
            "hrdive_public_rss",
            "medtechdive_public_rss",
            "highereddive_public_rss",
            "k12dive_public_rss",
            "smartcitiesdive_public_rss",
            "fiercebiotech_public_rss",
            "stat_public_rss",
            "breakingdefense_public_rss",
            "defensenews_global_public_rss",
            "spacenews_public_rss",
            "freightwaves_public_rss",
            "loadstar_public_rss",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_LIVE_SOURCES)
                self.assertIn(source_key, sources)
                self.assertGreaterEqual(len(sources[source_key].get("rss_or_feed_urls", [])), 1)
                self.assertIn("no_login", str(sources[source_key].get("terms_posture", "")))
        for source_key in (
            "ap_news_monthly_sitemap",
            "spacenews_public_wp",
            "carbonbrief_public_wp",
            "robotreport_public_wp",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_BACKFILL_SOURCES)
                self.assertIn(source_key, sources)
                self.assertTrue(str(sources[source_key].get("historical_backfill_mode", "")))

    def test_market_macro_v4_more_industry_dive_archives_are_promoted(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        sources = {str(source["source_key"]): source for source in registry["sources"]}
        for source_key in (
            "utilitydive_public_rss",
            "supplychaindive_public_rss",
            "biopharmadive_public_rss",
            "constructiondive_public_rss",
            "cfodive_public_rss",
            "restaurantdive_public_rss",
            "grocerydive_public_rss",
            "marketingdive_public_rss",
            "hrdive_public_rss",
            "medtechdive_public_rss",
            "highereddive_public_rss",
            "k12dive_public_rss",
            "smartcitiesdive_public_rss",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_LIVE_SOURCES)
                self.assertIn(source_key, DEFAULT_BACKFILL_SOURCES)
                self.assertIn(source_key, sources)
                self.assertEqual(sources[source_key].get("historical_backfill_mode"), "monthly_sitemap_article_meta")
                self.assertIn("{month_name_lower}", str(sources[source_key].get("monthly_sitemap_template", "")))
                self.assertRegex(str(sources[source_key].get("backfill_start_date", "")), r"^\d{4}-\d{2}-\d{2}$")

    def test_market_macro_v3_industry_dive_and_aggregator_sources_are_promoted(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        sources = {str(source["source_key"]): source for source in registry["sources"]}
        for source_key in (
            "seekingalpha_market_currents_rss",
            "finviz_public_news_html",
            "bankingdive_public_rss",
            "retaildive_public_rss",
            "ciodive_public_rss",
            "cybersecuritydive_public_rss",
            "paymentsdive_public_rss",
            "manufacturingdive_public_rss",
            "fooddive_public_rss",
            "healthcaredive_public_rss",
            "pharmavoice_public_rss",
            "stocktitan_public_rss",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_LIVE_SOURCES)
                self.assertIn(source_key, sources)
                self.assertTrue(sources[source_key].get("rss_or_feed_urls") or sources[source_key].get("html_page_urls"))
        for source_key in (
            "bankingdive_public_rss",
            "retaildive_public_rss",
            "ciodive_public_rss",
            "cybersecuritydive_public_rss",
            "paymentsdive_public_rss",
            "manufacturingdive_public_rss",
            "fooddive_public_rss",
            "healthcaredive_public_rss",
            "pharmavoice_public_rss",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_BACKFILL_SOURCES)
                self.assertEqual(sources[source_key].get("historical_backfill_mode"), "monthly_sitemap_article_meta")
                self.assertIn("{month_name_lower}", str(sources[source_key].get("monthly_sitemap_template", "")))
                self.assertRegex(str(sources[source_key].get("backfill_start_date", "")), r"^\d{4}-\d{2}-\d{2}$")

    def test_market_macro_v0111_non_newswire_market_sources_are_promoted(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        sources = {str(source["source_key"]): source for source in registry["sources"]}
        for source_key in (
            "investors_public_rss",
            "investorplace_public_rss",
            "fxstreet_public_rss",
            "defenseone_public_rss",
            "nareit_public_rss",
            "etftrends_public_rss",
            "housingwire_public_rss",
            "americanbanker_public_rss",
            "techmeme_public_rss",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_LIVE_SOURCES)
                self.assertIn(source_key, sources)
                self.assertGreaterEqual(len(sources[source_key].get("rss_or_feed_urls", [])), 1)
                self.assertIn("no_login", str(sources[source_key].get("terms_posture", "")))
        for source_key in (
            "investors_public_wp",
            "investorplace_public_wp",
            "etftrends_public_wp",
            "housingwire_public_wp",
        ):
            with self.subTest(source_key=source_key):
                self.assertIn(source_key, DEFAULT_BACKFILL_SOURCES)
                self.assertIn(source_key, sources)
                self.assertEqual(sources[source_key].get("historical_backfill_mode"), "wordpress_rest_posts")
                self.assertGreaterEqual(len(sources[source_key].get("wordpress_required_title_terms", [])), 10)

    def test_common_crawl_registry_includes_promoted_market_archive_patterns(self) -> None:
        registry = json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))
        source = next(source for source in registry["sources"] if source["source_key"] == "common_crawl_market_news_archive")
        patterns = set(source["common_crawl_url_patterns"])
        self.assertIn("money.cnn.com/2016/*", patterns)
        self.assertIn("money.cnn.com/2018/*", patterns)
        self.assertNotIn("finance.yahoo.com/news/*", patterns)
        self.assertNotIn("www.investing.com/news/*", patterns)

    def test_backfill_rows_outside_requested_date_window_are_rejected(self) -> None:
        from datetime import date

        self.assertFalse(row_date_within_window({"published_at": "2014-08-13T15:17:48Z"}, start=date(2016, 1, 1), end=date(2016, 12, 31)))
        self.assertTrue(row_date_within_window({"published_at": "2016-01-03T16:23:10Z"}, start=date(2016, 1, 1), end=date(2016, 12, 31)))

    def test_parse_datetime_value_treats_date_only_as_utc_midnight(self) -> None:
        self.assertEqual(parse_datetime_value("2016-01-01"), "2016-01-01T00:00:00Z")

    def test_canonicalize_news_url_removes_index_query_and_fragment(self) -> None:
        self.assertEqual(
            canonicalize_news_url("http://money.cnn.com/2016/01/04/investing/china-stocks/index.html?iid=hp#section"),
            "http://money.cnn.com/2016/01/04/investing/china-stocks",
        )

    def test_parse_feed_rows_marks_macro_context_without_ticker_requirement(self) -> None:
        source = {
            "source_key": "cnbc_public_rss",
            "display_name": "CNBC",
            "source_class": "market_macro_media_context",
            "context_scope": ["macro", "markets"],
        }
        payload = b"""
        <rss><channel>
          <item>
            <title>Core inflation rate moves bond markets</title>
            <link>https://www.cnbc.com/2026/06/28/example.html</link>
            <pubDate>Sun, 28 Jun 2026 07:00:00 GMT</pubDate>
          </item>
        </channel></rss>
        """
        rows = parse_feed_rows(payload, source=source, source_page_url="https://example.com/rss.xml", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["provider"], "public_market_macro_news_feeds")
        self.assertEqual(rows[0]["ticker_mapping_required_flag"], 0)
        self.assertEqual(rows[0]["macro_context_candidate_flag"], 1)
        self.assertIn("inflation", rows[0]["context_topic_candidates"])
        self.assertEqual(rows[0]["entity_mapping_status"], "NOT_REQUIRED_MARKET_MACRO_CONTEXT")

    def test_parse_feed_rows_supports_nested_title_markup(self) -> None:
        source = {
            "source_key": "fiercebiotech_public_rss",
            "display_name": "Fierce Biotech",
            "source_class": "healthcare_biotech_media_context",
            "context_scope": ["healthcare_biotech"],
        }
        payload = b"""
        <rss><channel>
          <item>
            <title><a href="/biotech/example">Biotech drug trial lifts healthcare outlook</a></title>
            <link>https://www.fiercebiotech.com/biotech/example</link>
            <pubDate>Jun 26, 2026 10:33am</pubDate>
          </item>
        </channel></rss>
        """
        rows = parse_feed_rows(payload, source=source, source_page_url="https://example.com/rss.xml", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Biotech drug trial lifts healthcare outlook")
        self.assertIn("healthcare_biotech", rows[0]["context_topic_candidates"])

    def test_parse_stocktitan_rss_rows_use_explicit_url_ticker_only(self) -> None:
        source = {
            "source_key": "stocktitan_public_rss",
            "display_name": "StockTitan",
            "source_class": "market_equity_news_aggregator_context",
            "context_scope": ["markets"],
            "stocktitan_ticker_from_url": True,
            "stocktitan_require_source_ticker": True,
        }
        payload = b"""
        <rss><channel>
          <item>
            <title>Apple announces new AI infrastructure investment</title>
            <link>https://www.stocktitan.net/news/AAPL/apple-announces-new-ai-infrastructure-investment.html</link>
            <pubDate>Sun, 28 Jun 2026 07:00:00 GMT</pubDate>
          </item>
          <item>
            <title>Generic market news without explicit symbol path</title>
            <link>https://www.stocktitan.net/news/live.html</link>
            <pubDate>Sun, 28 Jun 2026 07:05:00 GMT</pubDate>
          </item>
        </channel></rss>
        """
        rows = parse_feed_rows(payload, source=source, source_page_url="https://www.stocktitan.net/rss", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbols"], ["AAPL"])
        self.assertEqual(rows[0]["ticker_mapping_required_flag"], 1)
        self.assertEqual(rows[0]["entity_mapping_status"], "MAPPED_EXPLICIT_SOURCE_TICKER")
        self.assertEqual(rows[0]["entity_mapping_methods"], ["stocktitan_url_path_symbol"])
        self.assertEqual(rows[0]["entity_mapping_inferred_flag"], 0)
        self.assertEqual(rows[0]["stocktitan_source_ticker_flag"], 1)

    def test_parse_html_headline_rows_collects_finviz_external_links(self) -> None:
        source = {
            "source_key": "finviz_public_news_html",
            "display_name": "Finviz News",
            "source_class": "market_news_aggregator_context",
            "context_scope": ["markets", "risk_appetite"],
            "html_required_url_terms": ["bloomberg.com", "marketwatch.com"],
            "html_min_title_length": 18,
        }
        payload = b"""
        <html><body>
          <a href="https://www.bloomberg.com/news/articles/2026-06-28/bond-heavyweights-target-a-market-sweet-spot">Bond Heavyweights Target a Market Sweet Spot for New Warsh Era</a>
          <a href="/maps">Markets</a>
        </body></html>
        """
        rows = parse_html_headline_rows(payload, source=source, source_page_url="https://finviz.com/news", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["capture_method"], "public_html_anchor_headline")
        self.assertEqual(rows[0]["source_time_certified_flag"], 0)
        self.assertEqual(rows[0]["html_discovery_only_flag"], 1)

    def test_parse_guardian_api_rows_supports_2016_backfill(self) -> None:
        source = {
            "source_key": "guardian_open_platform",
            "display_name": "Guardian",
            "source_class": "macro_world_media_context",
            "context_scope": ["macro", "geopolitics"],
        }
        payload = json.dumps(
            {
                "response": {
                    "status": "ok",
                    "total": 1,
                    "currentPage": 1,
                    "pages": 1,
                    "pageSize": 50,
                    "results": [
                        {
                            "webTitle": "Oil prices rise after geopolitical tensions",
                            "webUrl": "https://www.theguardian.com/business/2016/jan/02/oil-example",
                            "webPublicationDate": "2016-01-02T10:00:00Z",
                            "sectionId": "business",
                            "type": "article",
                            "fields": {"trailText": "Summary"},
                        }
                    ],
                }
            }
        ).encode("utf-8")
        rows, metadata = parse_guardian_api_rows(payload, source=source, source_page_url="https://content.guardianapis.com/search", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(metadata["pages"], 1)
        self.assertEqual(rows[0]["published_at"], "2016-01-02T10:00:00Z")
        self.assertEqual(rows[0]["section_id"], "business")
        self.assertIn("energy", rows[0]["context_topic_candidates"])

    def test_parse_wordpress_rest_rows_filters_to_source_terms(self) -> None:
        source = {
            "source_key": "thehill_public_wp",
            "display_name": "The Hill",
            "source_class": "macro_policy_media_context",
            "context_scope": ["macro", "policy"],
            "wordpress_required_topic_match": True,
            "wordpress_required_title_terms": ["iran", "tax"],
        }
        payload = json.dumps(
            [
                {
                    "id": 1,
                    "date_gmt": "2016-01-03T02:05:48",
                    "link": "https://thehill.com/example/iran-deal/",
                    "title": {"rendered": "Trump: Iran deal was so bad it is suspicious"},
                    "excerpt": {"rendered": "<p>Policy context</p>"},
                    "categories": [1],
                    "slug": "iran-deal",
                },
                {
                    "id": 2,
                    "date_gmt": "2016-01-03T02:10:00",
                    "link": "https://thehill.com/example/lifestyle/",
                    "title": {"rendered": "Weekend media notes"},
                    "excerpt": {"rendered": "<p>Low signal</p>"},
                    "categories": [1],
                    "slug": "lifestyle",
                },
            ]
        ).encode("utf-8")
        rows, metadata = parse_wordpress_rest_rows(payload, source=source, source_page_url="https://thehill.com/wp-json/wp/v2/posts", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(metadata["item_count"], 2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["capture_method"], "wordpress_rest_posts_api")
        self.assertEqual(rows[0]["ticker_mapping_required_flag"], 0)
        self.assertEqual(rows[0]["usable_for_historical_backtest_flag"], 1)
        self.assertIn("geopolitics", rows[0]["context_topic_candidates"])

    def test_parse_wordpress_rest_rows_can_require_source_title_term(self) -> None:
        source = {
            "source_key": "techcrunch_public_wp",
            "display_name": "TechCrunch",
            "source_class": "technology_industry_media_context",
            "context_scope": ["technology", "industry"],
            "wordpress_required_topic_match": True,
            "wordpress_required_title_term_match": True,
            "wordpress_required_title_terms": ["bitcoin"],
        }
        payload = json.dumps(
            [
                {
                    "id": 1,
                    "date_gmt": "2016-01-02T05:00:18",
                    "link": "https://techcrunch.com/2016/01/02/bitcoin/",
                    "title": {"rendered": "Why Bitcoin Matters"},
                    "excerpt": {"rendered": "<p>Crypto context</p>"},
                },
                {
                    "id": 2,
                    "date_gmt": "2016-01-02T06:00:18",
                    "link": "https://techcrunch.com/2016/01/02/growth/",
                    "title": {"rendered": "Startup growth plan"},
                    "excerpt": {"rendered": "<p>Broad tech</p>"},
                },
            ]
        ).encode("utf-8")
        rows, _metadata = parse_wordpress_rest_rows(payload, source=source, source_page_url="https://techcrunch.com/wp-json/wp/v2/posts", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual([row["title"] for row in rows], ["Why Bitcoin Matters"])

    def test_parse_wordpress_rest_rows_supports_ev_energy_title_gate(self) -> None:
        source = {
            "source_key": "electrek_public_wp",
            "display_name": "Electrek",
            "source_class": "ev_energy_transition_media_context",
            "context_scope": ["energy", "industry", "ev_autonomy_mobility"],
            "wordpress_required_topic_match": True,
            "wordpress_required_title_term_match": True,
            "wordpress_required_title_terms": ["tesla", "battery", "charging"],
        }
        payload = json.dumps(
            [
                {
                    "id": 1,
                    "date_gmt": "2016-01-03T17:55:51",
                    "link": "https://electrek.co/2016/01/03/tesla-deliveries/",
                    "title": {"rendered": "Tesla delivered 17,400 vehicles in Q4"},
                    "excerpt": {"rendered": "<p>EV context</p>"},
                },
                {
                    "id": 2,
                    "date_gmt": "2016-01-03T18:00:00",
                    "link": "https://electrek.co/2016/01/03/consumer-gadgets/",
                    "title": {"rendered": "CES gadget roundup"},
                    "excerpt": {"rendered": "<p>Low signal</p>"},
                },
            ]
        ).encode("utf-8")
        rows, _metadata = parse_wordpress_rest_rows(payload, source=source, source_page_url="https://electrek.co/wp-json/wp/v2/posts", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual([row["title"] for row in rows], ["Tesla delivered 17,400 vehicles in Q4"])

    def test_run_collector_writes_market_macro_event_for_mocked_feed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "mock_market_macro",
                                "display_name": "Mock Market Macro",
                                "source_class": "market_macro_media_context",
                                "context_scope": ["markets"],
                                "base_url": "https://example.com",
                                "rss_or_feed_urls": ["https://example.com/feed.xml"],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicMarketMacroNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("mock_market_macro",),
                max_items_per_source=1,
                max_fetches_per_source=1,
                request_sleep_seconds=0,
            )
            from tools.db.source_acquisition import public_market_macro_news_collector as collector

            def fake_fetch(url: str, _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"<rss><channel><item><title>Stocks rally as rate cut hopes grow</title><link>https://example.com/a</link><pubDate>2026-06-28T07:00:00Z</pubDate></item></channel></rss>"
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
        self.assertEqual(event["l1_context_ready_count"], 1)
        self.assertEqual(event["l1_blocked_count"], 0)
        self.assertEqual(raw_payload["headlines"][0]["ticker_mapping_required_flag"], 0)

    def test_run_backfill_collects_guardian_month_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "guardian_open_platform",
                                "display_name": "Guardian",
                                "source_class": "macro_world_media_context",
                                "context_scope": ["macro", "geopolitics"],
                                "base_url": "https://content.guardianapis.com",
                                "api_urls": ["https://content.guardianapis.com/search?api-key=test"],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicMarketMacroNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("guardian_open_platform",),
                max_items_per_source=10,
                max_fetches_per_source=2,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_market_macro_news_collector as collector

            def fake_fetch(url: str, _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                payload = json.dumps(
                    {
                        "response": {
                            "status": "ok",
                            "total": 1,
                            "currentPage": 1,
                            "pages": 1,
                            "pageSize": 50,
                            "results": [
                                {
                                    "webTitle": "Markets react to world policy shock",
                                    "webUrl": "https://www.theguardian.com/business/2016/jan/02/example",
                                    "webPublicationDate": "2016-01-02T10:00:00Z",
                                    "sectionId": "business",
                                    "type": "article",
                                }
                            ],
                        }
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
        self.assertEqual(state["backfill"]["guardian_open_platform"]["completed_units"], ["2016-01"])
        self.assertEqual(raw_payload["collection_mode"], "historical_backfill")
        self.assertEqual(raw_payload["headlines"][0]["usable_for_historical_backtest_flag"], 1)

    def test_run_backfill_collects_wordpress_rest_month_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "thehill_public_wp",
                                "display_name": "The Hill",
                                "source_class": "macro_policy_media_context",
                                "context_scope": ["macro", "policy"],
                                "base_url": "https://thehill.com",
                                "api_urls": ["https://thehill.com/wp-json/wp/v2/posts"],
                                "historical_backfill_mode": "wordpress_rest_posts",
                                "wordpress_required_topic_match": True,
                                "wordpress_required_title_terms": ["iran"],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicMarketMacroNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("thehill_public_wp",),
                max_items_per_source=10,
                max_fetches_per_source=2,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_market_macro_news_collector as collector

            def fake_fetch(url: str, _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                payload = json.dumps(
                    [
                        {
                            "id": 1,
                            "date_gmt": "2016-01-03T02:05:48",
                            "link": "https://thehill.com/example/iran-deal/",
                            "title": {"rendered": "Trump: Iran deal was so bad it is suspicious"},
                            "excerpt": {"rendered": "<p>Policy context</p>"},
                            "categories": [1],
                            "slug": "iran-deal",
                        }
                    ]
                ).encode("utf-8")
                return {
                    "ok": True,
                    "requested_url": url,
                    "resolved_url": url,
                    "status_code": 200,
                    "content_type": "application/json",
                    "headers": {"X-WP-TotalPages": "1"},
                    "bytes": payload,
                    "truncated": False,
                    "elapsed_ms": 1,
                }

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
        self.assertEqual(state["backfill"]["thehill_public_wp"]["completed_units"], ["2016-01"])
        self.assertEqual(raw_payload["headlines"][0]["source_key"], "thehill_public_wp")
        self.assertEqual(raw_payload["headlines"][0]["capture_method"], "wordpress_rest_posts_api")

    def test_run_backfill_collects_monthly_sitemap_article_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "retaildive_public_rss",
                                "display_name": "Retail Dive",
                                "source_class": "retail_consumer_industry_media_context",
                                "context_scope": ["industry", "consumer_spending"],
                                "base_url": "https://www.retaildive.com",
                                "historical_backfill_mode": "monthly_sitemap_article_meta",
                                "monthly_sitemap_template": "https://www.retaildive.com/news/archive/{year}/{month_name_lower}.xml",
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicMarketMacroNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("retaildive_public_rss",),
                max_items_per_source=10,
                max_fetches_per_source=4,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_market_macro_news_collector as collector

            def fake_fetch(url: str, _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\nCrawl-delay: 5\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                if url.endswith("/news/archive/2016/january.xml"):
                    payload = b"""
                    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                      <url><loc>https://www.retaildive.com/news/under-armour-calms-investor-fears-with-strong-q4/413003/</loc><lastmod>2016-01-29</lastmod></url>
                    </urlset>
                    """
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"<html><head><meta property='og:title' content='Under Armour calms investor fears with strong Q4'><meta property='article:published_time' content='2016-01-29T12:00:00Z'><meta property='og:description' content='Retail earnings context'></head></html>"
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/html", "bytes": payload, "truncated": False, "elapsed_ms": 1}

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
        self.assertEqual(state["backfill"]["retaildive_public_rss"]["completed_units"], ["2016-01"])
        self.assertEqual(raw_payload["headlines"][0]["capture_method"], "monthly_sitemap_article_meta")
        self.assertEqual(raw_payload["headlines"][0]["usable_for_historical_backtest_flag"], 0)

    def test_run_backfill_collects_ap_monthly_sitemap_article_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "ap_news_monthly_sitemap",
                                "display_name": "AP News",
                                "source_class": "broad_macro_world_media_context",
                                "context_scope": ["macro", "policy", "geopolitics"],
                                "base_url": "https://apnews.com",
                                "historical_backfill_mode": "ap_monthly_sitemap_article_meta",
                                "ap_monthly_sitemap_template": "https://apnews.com/ap-sitemap-{yyyymm}.xml",
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicMarketMacroNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("ap_news_monthly_sitemap",),
                max_items_per_source=10,
                max_fetches_per_source=5,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_market_macro_news_collector as collector

            def fake_fetch(url: str, _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                if url.endswith("ap-sitemap-201601.xml"):
                    payload = b"""
                    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                      <url><loc>https://apnews.com/article/sports-ignored</loc></url>
                      <url><loc>https://apnews.com/article/market-policy-shock</loc></url>
                    </urlset>
                    """
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                if url.endswith("sports-ignored"):
                    payload = b"""
                    <html><head>
                      <meta property="og:title" content="Local sports team wins again">
                      <meta property="og:description" content="Sports recap">
                      <meta property="article:published_time" content="2016-01-03T10:00:00">
                    </head></html>
                    """
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/html", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"""
                <html><head>
                  <meta property="og:title" content="Fed rate path shakes stock market and bond yields">
                  <meta property="og:description" content="Federal Reserve policy drove market volatility.">
                  <meta property="article:published_time" content="2016-01-04T15:30:00">
                  <meta property="article:modified_time" content="2021-01-04T15:30:00">
                </head></html>
                """
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/html", "bytes": payload, "truncated": False, "elapsed_ms": 1}

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
        self.assertEqual(state["backfill"]["ap_news_monthly_sitemap"]["completed_units"], ["2016-01"])
        self.assertEqual(raw_payload["headlines"][0]["source_key"], "ap_news_monthly_sitemap")
        self.assertEqual(raw_payload["headlines"][0]["capture_method"], "ap_monthly_sitemap_article_meta")
        self.assertEqual(raw_payload["headlines"][0]["usable_for_historical_backtest_flag"], 0)

    def test_run_backfill_collects_cnbc_sitemap_article_meta_without_backtest_certification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "cnbc_public_rss",
                                "display_name": "CNBC",
                                "source_class": "market_macro_media_context",
                                "context_scope": ["macro", "markets"],
                                "base_url": "https://www.cnbc.com",
                                "rss_or_feed_urls": [],
                                "sitemap_urls": ["https://www.cnbc.com/sitemapAll.xml"],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicMarketMacroNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("cnbc_public_rss",),
                max_items_per_source=10,
                max_fetches_per_source=6,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_market_macro_news_collector as collector

            def fake_fetch(url: str, _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                if url.endswith("sitemapAll.xml"):
                    payload = b"""
                    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                      <sitemap><loc>https://www.cnbc.com/CNBCsitemapAll1.xml</loc><lastmod>2026-06-28T00:00:00Z</lastmod></sitemap>
                    </sitemapindex>
                    """
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                if url.endswith("CNBCsitemapAll1.xml"):
                    payload = b"""
                    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                      <url><loc>https://www.cnbc.com/2016/01/04/us-markets.html</loc><lastmod>2016-01-04T18:00:00Z</lastmod></url>
                      <url><loc>https://www.cnbc.com/2015/12/31/old-markets.html</loc><lastmod>2015-12-31T18:00:00Z</lastmod></url>
                    </urlset>
                    """
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"""
                <html><head>
                  <meta property="og:title" content="Dow closes down triple digits, posts worst opening day in 8 years">
                  <meta property="og:description" content="Market context summary">
                </head><body></body></html>
                """
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/html", "bytes": payload, "truncated": False, "elapsed_ms": 1}

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
        self.assertEqual(raw_payload["headlines"][0]["source_key"], "cnbc_public_rss")
        self.assertEqual(raw_payload["headlines"][0]["title_source"], "article_meta_og_title")
        self.assertEqual(raw_payload["headlines"][0]["source_time_certified_flag"], 0)
        self.assertEqual(raw_payload["headlines"][0]["usable_for_historical_backtest_flag"], 0)
        self.assertEqual(len(state["backfill"]["cnbc_public_rss"]["completed_units"]), 1)

    def test_run_backfill_collects_wikimedia_current_events_without_backtest_certification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "wikimedia_current_events",
                                "display_name": "Wikimedia Current Events",
                                "source_class": "macro_world_event_context",
                                "context_scope": ["macro", "geopolitics", "policy"],
                                "base_url": "https://en.wikipedia.org",
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicMarketMacroNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("wikimedia_current_events",),
                max_items_per_source=2,
                max_fetches_per_source=3,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_market_macro_news_collector as collector

            def fake_fetch(url: str, _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"""
                <html><body>
                  <div role="region" aria-label="January 1" id="2016_January_1" class="current-events-main vevent">
                    <span class="bday dtstart published updated itvstart">2016-01-01</span>
                    <div class="current-events-content description">
                      <div class="current-events-content-heading" role="heading">Armed conflicts and attacks</div>
                      <ul><li>Market-moving geopolitical event affects oil supply. <a rel="nofollow" class="external text" href="https://example.com/source">(Source)</a></li></ul>
                    </div>
                  </div>
                </body></html>
                """
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/html", "bytes": payload, "truncated": False, "elapsed_ms": 1}

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
        self.assertEqual(raw_payload["headlines"][0]["source_key"], "wikimedia_current_events")
        self.assertEqual(raw_payload["headlines"][0]["section_id"], "Armed conflicts and attacks")
        self.assertEqual(raw_payload["headlines"][0]["source_time_certified_flag"], 0)
        self.assertEqual(raw_payload["headlines"][0]["usable_for_historical_backtest_flag"], 0)
        self.assertEqual(state["backfill"]["wikimedia_current_events"]["completed_units"], ["2016-01"])

    def test_run_backfill_collects_common_crawl_archive_without_backtest_certification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "common_crawl_market_news_archive",
                                "display_name": "Common Crawl Market News Archive",
                                "source_class": "market_macro_media_archive_context",
                                "context_scope": ["macro", "markets"],
                                "base_url": "https://index.commoncrawl.org",
                                "api_urls": ["https://index.commoncrawl.org/collinfo.json"],
                                "common_crawl_url_patterns": ["finance.yahoo.com/news/*"],
                                "enabled": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicMarketMacroNewsConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("common_crawl_market_news_archive",),
                max_items_per_source=2,
                max_fetches_per_source=4,
                request_sleep_seconds=0,
                backfill_start_date="2016-02-01",
                backfill_end_date="2016-02-29",
                max_cycles=1,
            )
            from tools.db.source_acquisition import public_market_macro_news_collector as collector

            def fake_fetch(url: str, _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                if url.endswith("collinfo.json"):
                    payload = json.dumps(
                        [
                            {
                                "id": "CC-MAIN-2016-07",
                                "name": "February 2016 Index",
                                "from": "2016-02-05T21:49:27",
                                "to": "2016-02-15T00:47:02",
                                "cdx-api": "https://index.commoncrawl.org/CC-MAIN-2016-07-index",
                            }
                        ]
                    ).encode("utf-8")
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/json", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"""
                {"url":"http://finance.yahoo.com/news/fed-rate-cut-hopes-boost-stocks.html","timestamp":"20160214101300","status":"200","mime":"text/html","digest":"ABC","filename":"crawl-data/example.warc.gz","offset":"10","length":"200"}
                """
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/x-ndjson", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            def fake_warc(_record: dict[str, str], _config: PublicMarketMacroNewsConfig) -> dict[str, object]:
                payload = b"""
                WARC/1.0\r\nContent-Type: application/http; msgtype=response\r\n\r\n
                HTTP/1.1 200 OK\r\n\r\n
                <html><head>
                  <title>Fed rate cut hopes boost stocks</title>
                  <meta name="description" content="Archived market context">
                </head><body></body></html>
                """
                return {"ok": True, "requested_url": "https://data.commoncrawl.org/crawl-data/example.warc.gz", "resolved_url": "https://data.commoncrawl.org/crawl-data/example.warc.gz", "status_code": 206, "content_type": "application/octet-stream", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            original_fetch = collector.fetch_url
            original_warc = collector.fetch_common_crawl_warc_record
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                collector.fetch_common_crawl_warc_record = fake_warc  # type: ignore[assignment]
                result = run_backfill(config, smoke=False)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]
                collector.fetch_common_crawl_warc_record = original_warc  # type: ignore[assignment]
            event = json.loads(config.event_path.read_text(encoding="utf-8").splitlines()[0])
            state = json.loads(config.state_path.read_text(encoding="utf-8"))
            raw_payload = json.loads(Path(event["raw_path"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "EXPORTED")
        self.assertEqual(event["l1_ready_discovery_only_count"], 1)
        self.assertEqual(event["l1_blocked_count"], 0)
        self.assertEqual(raw_payload["headlines"][0]["source_key"], "common_crawl_market_news_archive")
        self.assertEqual(raw_payload["headlines"][0]["capture_method"], "common_crawl_warc_article_meta")
        self.assertEqual(raw_payload["headlines"][0]["archive_provider"], "Common Crawl")
        self.assertEqual(raw_payload["headlines"][0]["source_time_certified_flag"], 0)
        self.assertEqual(raw_payload["headlines"][0]["usable_for_historical_backtest_flag"], 0)
        self.assertEqual(state["backfill"]["common_crawl_market_news_archive"]["completed_units"], ["CC-MAIN-2016-07::finance.yahoo.com/news/*"])


if __name__ == "__main__":
    unittest.main()
