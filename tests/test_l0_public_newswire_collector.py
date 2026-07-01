from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path

from tools.db.source_acquisition.public_newswire_collector import (
    PublicNewswireConfig,
    apply_entity_mapping,
    build_row,
    build_entity_mapper,
    is_probable_article_url,
    parse_article_metadata,
    parse_feed_rows,
    parse_sitemap,
    parse_sitemap_entries,
    run_backfill,
    run_collector,
)


class L0PublicNewswireCollectorTests(unittest.TestCase):
    def _mapper(self, root: Path):
        universe = root / "universe.csv"
        universe.write_text(
            "\n".join(
                [
                    "symbol,name,exchange,status,tradable,marginable,shortable,fractionable",
                    "BMI,Badger Meter Inc.,NYSE,active,True,True,True,True",
                    "FUTU,Futu Holdings Limited American Depositary Shares,NASDAQ,active,True,True,True,True",
                    "NDAQ,Nasdaq Inc.,NASDAQ,active,True,True,True,True",
                    "ORBS,Eightco Holdings Inc.,NASDAQ,active,True,True,True,True",
                    "ABC,Example Holdings Inc.,NYSE,active,True,True,True,True",
                    "XYZ,Example Holdings Corp.,NASDAQ,active,True,True,True,True",
                    "POET,POET Technologies Inc. Common Shares,NASDAQ,active,True,True,True,True",
                    "BBBY,Bed Bath & Beyond Inc.,NYSE,active,True,True,True,True",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return build_entity_mapper(universe)

    def test_parse_feed_rows_extracts_title_link_and_time(self) -> None:
        payload = b"""
        <rss><channel>
          <item>
            <title>Example company announces public update</title>
            <link>https://example.com/news-release/example.html</link>
            <pubDate>Sun, 28 Jun 2026 07:00:00 GMT</pubDate>
          </item>
        </channel></rss>
        """
        rows = parse_feed_rows(payload, source_key="example", source_page_url="https://example.com/rss.xml", captured_at="2026-06-28T07:00:00Z")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["provider"], "public_newswire_feeds")
        self.assertEqual(rows[0]["capture_method"], "rss_or_atom")
        self.assertEqual(rows[0]["source_time_certified_flag"], 1)

    def test_parse_article_metadata_preserves_description_evidence(self) -> None:
        payload = b"""
        <html><head>
          <meta property="og:title" content="AK Steel Reports Financial Results">
          <meta name="description" content="/PRNewswire/ -- AK Steel (NYSE: AKS) today reported results.">
          <meta property="article:published_time" content="2016-01-26T08:30:00-05:00">
        </head></html>
        """
        metadata = parse_article_metadata(payload, source_key="prnewswire")
        self.assertEqual(metadata["title"], "AK Steel Reports Financial Results")
        self.assertIn("(NYSE: AKS)", metadata["description"])
        self.assertEqual(metadata["published_at"], "2016-01-26T13:30:00Z")

    def test_prnewswire_registry_prioritizes_paginated_news_sitemaps(self) -> None:
        registry = json.loads(Path("configs/source_registry/l0_public_news_capability_sources.json").read_text(encoding="utf-8-sig"))
        prnewswire = next(source for source in registry["sources"] if source["source_key"] == "prnewswire")
        sitemap_urls = prnewswire["sitemap_urls"]
        self.assertIn("https://www.prnewswire.com/sitemap-news.xml?page=1", sitemap_urls)
        self.assertLess(
            sitemap_urls.index("https://www.prnewswire.com/sitemap-news.xml?page=1"),
            sitemap_urls.index("https://www.prnewswire.com/sitemap.xml"),
        )

    def test_parse_news_sitemap_extracts_news_title(self) -> None:
        payload = b"""
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
          <url>
            <loc>https://example.com/news-release/example.html</loc>
            <news:news>
              <news:publication_date>2026-06-28T07:00:00Z</news:publication_date>
              <news:title>Example source releases headline</news:title>
            </news:news>
          </url>
        </urlset>
        """
        rows, follow = parse_sitemap(payload, source_key="example", source_page_url="https://example.com/sitemap-news.xml", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(follow, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["capture_method"], "news_sitemap")

    def test_parse_gzip_news_sitemap_extracts_news_title(self) -> None:
        payload = gzip.compress(
            b"""
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                    xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
              <url>
                <loc>https://example.com/news-release/example.html</loc>
                <news:news>
                  <news:publication_date>2026-06-28T07:00:00Z</news:publication_date>
                  <news:title>Example gzip source releases headline</news:title>
                </news:news>
              </url>
            </urlset>
            """
        )
        rows, follow = parse_sitemap(payload, source_key="example", source_page_url="https://example.com/sitemap-news.xml.gz", captured_at="2026-06-28T07:01:00Z")
        self.assertEqual(follow, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Example gzip source releases headline")

    def test_truncated_gzip_sitemap_is_retryable_parse_failure(self) -> None:
        payload = gzip.compress(b"<urlset><url><loc>https://example.com/news.html</loc></url></urlset>")[:20]
        entries, follow, parse_ok = parse_sitemap_entries(payload)
        self.assertEqual(entries, [])
        self.assertEqual(follow, [])
        self.assertFalse(parse_ok)

    def test_run_collector_writes_event_for_mocked_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "mockwire",
                                "display_name": "Mock wire",
                                "base_url": "https://example.com",
                                "rss_or_feed_urls": ["https://example.com/rss.xml"],
                                "sitemap_urls": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            config = PublicNewswireConfig(
                registry_path=registry,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("mockwire",),
                max_items_per_source=1,
                max_fetches_per_source=1,
                request_sleep_seconds=0,
            )
            from tools.db.source_acquisition import public_newswire_collector as collector

            def fake_fetch(url: str, _config: PublicNewswireConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"<rss><channel><item><title>Mock headline long enough</title><link>https://example.com/news-release/mock.html</link><pubDate>2026-06-28T07:00:00Z</pubDate></item></channel></rss>"
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/rss+xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            original_fetch = collector.fetch_url
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                result = run_collector(config, smoke=True)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]

            events = config.event_path.read_text(encoding="utf-8")
            raw_event = json.loads(events.splitlines()[0])
            raw_payload = Path(raw_event["raw_path"]).read_text(encoding="utf-8")

        self.assertEqual(result["status"], "EXPORTED")
        self.assertIn("public_newswire_feeds", events)
        self.assertIn("Mock headline", raw_payload)

    def test_source_declared_exchange_tag_maps_symbol_outside_active_universe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            row = build_row(
                source_key="prnewswire",
                title="AK Steel Reports Financial Results For Fourth Quarter And Full-Year 2015",
                source_url="https://www.prnewswire.com/news-releases/ak-steel-reports-financial-results.html",
                published_at="2016-01-26T13:30:00Z",
                published_at_text="2016-01-26T08:30:00-05:00",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://www.prnewswire.com/archive.xml",
                capture_method="historical_archive_sitemap",
                evidence_text="/PRNewswire/ -- AK Steel (NYSE: AKS) today reported its financial results.",
            )
            mapped = apply_entity_mapping(row, mapper)
        self.assertEqual(mapped["symbols"], ["AKS"])
        self.assertEqual(mapped["entity_mapping_status"], "MAPPED_EXCHANGE_TAG")
        self.assertEqual(mapped["entity_mapping_methods"], ["exchange_tag"])
        self.assertEqual(mapped["entity_map"][0]["entity_source"], "public_newswire_source_declared_exchange_tag")
        self.assertEqual(mapped["entity_map"][0]["active_universe_match_flag"], 0)
        self.assertEqual(mapped["entity_mapping_inferred_flag"], 0)

    def test_run_backfill_collects_monthly_news_sitemap_with_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "globenewswire",
                                "display_name": "Mock GlobeNewswire",
                                "base_url": "https://www.globenewswire.com",
                                "rss_or_feed_urls": [],
                                "sitemap_urls": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            universe = root / "universe.csv"
            universe.write_text(
                "symbol,name,exchange,status,tradable,marginable,shortable,fractionable\nBMI,Badger Meter Inc.,NYSE,active,True,True,True,True\n",
                encoding="utf-8",
            )
            config = PublicNewswireConfig(
                registry_path=registry,
                universe_path=universe,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("globenewswire",),
                max_items_per_source=5,
                max_fetches_per_source=4,
                request_sleep_seconds=0,
                backfill_start_date="2026-06-01",
                backfill_end_date="2026-06-30",
            )
            from tools.db.source_acquisition import public_newswire_collector as collector

            def fake_fetch(url: str, _config: PublicNewswireConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"""
                <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
                  <url>
                    <loc>https://www.globenewswire.com/news-release/2026/06/15/example.html</loc>
                    <news:news>
                      <news:publication_date>2026-06-15T12:00:00Z</news:publication_date>
                      <news:title>Badger Meter Inc. announces archive update</news:title>
                    </news:news>
                  </url>
                </urlset>
                """
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            original_fetch = collector.fetch_url
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                result = run_backfill(config, smoke=True)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]
            raw_event = json.loads(config.event_path.read_text(encoding="utf-8").splitlines()[0])
            raw_payload = json.loads(Path(raw_event["raw_path"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "EXPORTED")
        self.assertEqual(raw_payload["collection_mode"], "historical_backfill")
        self.assertEqual(raw_payload["headlines"][0]["symbols"], ["BMI"])
        self.assertEqual(raw_payload["headlines"][0]["source_time_certified_flag"], 1)

    def test_run_backfill_fetches_article_title_for_url_only_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "businesswire",
                                "display_name": "Mock BusinessWire",
                                "base_url": "https://www.businesswire.com",
                                "rss_or_feed_urls": [],
                                "sitemap_urls": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            universe = root / "universe.csv"
            universe.write_text(
                "symbol,name,exchange,status,tradable,marginable,shortable,fractionable\nBMI,Badger Meter Inc.,NYSE,active,True,True,True,True\n",
                encoding="utf-8",
            )
            config = PublicNewswireConfig(
                registry_path=registry,
                universe_path=universe,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("businesswire",),
                max_items_per_source=1,
                max_fetches_per_source=4,
                request_sleep_seconds=0,
                backfill_start_date="2026-06-26",
                backfill_end_date="2026-06-26",
            )
            from tools.db.source_acquisition import public_newswire_collector as collector

            def fake_fetch(url: str, _config: PublicNewswireConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                if url.endswith(".xml.gz"):
                    payload = gzip.compress(
                        b"""
                        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                          <url>
                            <loc>https://www.businesswire.com/news/home/20260626142107/en/example</loc>
                            <lastmod>2026-06-26T14:22:00Z</lastmod>
                          </url>
                        </urlset>
                        """
                    )
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"<html><head><meta property='og:title' content='Badger Meter Inc. announces BusinessWire archive update'><meta property='article:published_time' content='2026-06-26T14:21:07Z'></head></html>"
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/html", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            original_fetch = collector.fetch_url
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                result = run_backfill(config, smoke=True)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]
            raw_event = json.loads(config.event_path.read_text(encoding="utf-8").splitlines()[0])
            raw_payload = json.loads(Path(raw_event["raw_path"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "EXPORTED")
        self.assertEqual(raw_payload["headlines"][0]["title_source"], "article_html_meta")
        self.assertEqual(raw_payload["headlines"][0]["symbols"], ["BMI"])

    def test_run_backfill_enriches_sitemap_title_with_article_metadata_exchange_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "globenewswire",
                                "display_name": "Mock GlobeNewswire",
                                "base_url": "https://www.globenewswire.com",
                                "rss_or_feed_urls": [],
                                "sitemap_urls": [],
                                "fetch_article_metadata_for_mapping": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            universe = root / "universe.csv"
            universe.write_text(
                "symbol,name,exchange,status,tradable,marginable,shortable,fractionable\nBMI,Badger Meter Inc.,NYSE,active,True,True,True,True\n",
                encoding="utf-8",
            )
            config = PublicNewswireConfig(
                registry_path=registry,
                universe_path=universe,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("globenewswire",),
                max_items_per_source=1,
                max_fetches_per_source=4,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-31",
            )
            from tools.db.source_acquisition import public_newswire_collector as collector

            def fake_fetch(url: str, _config: PublicNewswireConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                if url.endswith("2016-01.xml"):
                    payload = b"""
                    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                            xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
                      <url>
                        <loc>https://www.globenewswire.com/news-release/2016/01/12/example.html</loc>
                        <news:news>
                          <news:publication_date>2016-01-12T12:00:00Z</news:publication_date>
                          <news:title>American Power Group Announces Private Placement</news:title>
                        </news:news>
                      </url>
                    </urlset>
                    """
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "application/xml", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                payload = b"<html><head><meta property='og:title' content='American Power Group Announces Private Placement'><meta name='description' content='American Power Group Corporation (OTCQB: APGI) today announced the completion of a private placement.'></head></html>"
                return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/html", "bytes": payload, "truncated": False, "elapsed_ms": 1}

            original_fetch = collector.fetch_url
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                result = run_backfill(config, smoke=True)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]
            raw_event = json.loads(config.event_path.read_text(encoding="utf-8").splitlines()[0])
            raw_payload = json.loads(Path(raw_event["raw_path"]).read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "EXPORTED")
        self.assertEqual(raw_payload["headlines"][0]["symbols"], ["APGI"])
        self.assertEqual(raw_payload["headlines"][0]["entity_map"][0]["entity_source"], "public_newswire_source_declared_exchange_tag")
        self.assertIn("metadata_enrichment_fetches=1", raw_event["notes"])

    def test_run_backfill_marks_businesswire_s3_403_archive_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_key": "businesswire",
                                "display_name": "Mock BusinessWire",
                                "base_url": "https://www.businesswire.com",
                                "rss_or_feed_urls": [],
                                "sitemap_urls": [],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            universe = root / "universe.csv"
            universe.write_text(
                "symbol,name,exchange,status,tradable,marginable,shortable,fractionable\nBMI,Badger Meter Inc.,NYSE,active,True,True,True,True\n",
                encoding="utf-8",
            )
            config = PublicNewswireConfig(
                registry_path=registry,
                universe_path=universe,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                plan_path=root / "plan.json",
                stop_path=root / "STOP",
                log_path=root / "collector.log",
                sources=("businesswire",),
                max_items_per_source=1,
                max_fetches_per_source=4,
                request_sleep_seconds=0,
                backfill_start_date="2016-01-01",
                backfill_end_date="2016-01-01",
            )
            from tools.db.source_acquisition import public_newswire_collector as collector

            def fake_fetch(url: str, _config: PublicNewswireConfig) -> dict[str, object]:
                if url.endswith("robots.txt"):
                    payload = b"User-agent: *\nAllow: /\n"
                    return {"ok": True, "requested_url": url, "resolved_url": url, "status_code": 200, "content_type": "text/plain", "bytes": payload, "truncated": False, "elapsed_ms": 1}
                return {
                    "ok": False,
                    "requested_url": url,
                    "resolved_url": url,
                    "status_code": 403,
                    "content_type": "",
                    "bytes": b"",
                    "truncated": False,
                    "elapsed_ms": 1,
                    "error_category": "HTTPError",
                    "error_message": "HTTP Error 403: Forbidden",
                }

            original_fetch = collector.fetch_url
            try:
                collector.fetch_url = fake_fetch  # type: ignore[assignment]
                result = run_backfill(config, smoke=True)
            finally:
                collector.fetch_url = original_fetch  # type: ignore[assignment]
            state = json.loads(config.state_path.read_text(encoding="utf-8"))
            raw_event = json.loads(config.event_path.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(result["status"], "BACKFILL_COMPLETE")
        self.assertEqual(raw_event["status"], "BACKFILL_COMPLETE")
        self.assertEqual(len(state["backfill"]["businesswire"]["completed_archive_urls"]), 1)
        self.assertEqual(len(state["backfill"]["businesswire"]["unavailable_archive_urls"]), 1)

    def test_entity_mapping_accepts_exchange_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            row = build_row(
                source_key="example",
                title="Company announces update (NASDAQ: FUTU)",
                source_url="https://example.com/a.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            mapped = apply_entity_mapping(row, mapper)
        self.assertEqual(mapped["symbols"], ["FUTU"])
        self.assertEqual(mapped["entity_mapping_status"], "MAPPED_EXCHANGE_TAG")
        self.assertEqual(mapped["entity_mapping_inferred_flag"], 0)

    def test_entity_mapping_does_not_treat_exchange_name_as_company_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            row = build_row(
                source_key="example",
                title="Eightco Holdings (NASDAQ: ORBS) announces public update",
                source_url="https://example.com/a.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            mapped = apply_entity_mapping(row, mapper)
        self.assertEqual(mapped["symbols"], ["ORBS"])
        self.assertNotIn("NDAQ", mapped["symbols"])

    def test_entity_mapping_accepts_exact_alias_but_blocks_symbol_token_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            symbol_only = build_row(
                source_key="example",
                title="BMI Investors Have Opportunity to Lead Securities Fraud Lawsuit",
                source_url="https://example.com/a.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            exact_alias = dict(symbol_only)
            exact_alias["title"] = "BMI Investors Have Opportunity to Lead Badger Meter, Inc. Securities Fraud Lawsuit"
            blocked = apply_entity_mapping(symbol_only, mapper)
            mapped = apply_entity_mapping(exact_alias, mapper)
        self.assertEqual(blocked["symbols"], [])
        self.assertEqual(blocked["entity_mapping_status"], "BLOCKED_UNMAPPED")
        self.assertEqual(blocked["ticker_mapping_required_flag"], 1)
        self.assertEqual(mapped["symbols"], ["BMI"])
        self.assertEqual(mapped["entity_mapping_status"], "MAPPED_EXACT_ALIAS")

    def test_entity_mapping_unescapes_html_entities_and_common_shares_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            poet = build_row(
                source_key="example",
                title="POET DEADLINE: Law Firm Encourages POET Technologies Inc. Investors to Act",
                source_url="https://example.com/a.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            bed_bath = build_row(
                source_key="example",
                title="Bed Bath &amp; Beyond Launches Legendary Coupon Hunt",
                source_url="https://example.com/b.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            mapped_poet = apply_entity_mapping(poet, mapper)
            mapped_bed_bath = apply_entity_mapping(bed_bath, mapper)
        self.assertEqual(mapped_poet["symbols"], ["POET"])
        self.assertEqual(mapped_poet["entity_mapping_status"], "MAPPED_EXACT_ALIAS")
        self.assertEqual(mapped_bed_bath["symbols"], ["BBBY"])
        self.assertEqual(mapped_bed_bath["entity_mapping_status"], "MAPPED_EXACT_ALIAS")

    def test_entity_mapping_blocks_ambiguous_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            row = build_row(
                source_key="example",
                title="Example Holdings announces public update",
                source_url="https://example.com/a.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            mapped = apply_entity_mapping(row, mapper)
        self.assertEqual(mapped["symbols"], [])
        self.assertEqual(mapped["entity_mapping_status"], "BLOCKED_AMBIGUOUS_ENTITY")
        self.assertEqual(mapped["entity_mapping_ambiguous_aliases"], ["example holdings"])

    def test_build_row_keeps_historical_backtest_gate_closed(self) -> None:
        row = build_row(
            source_key="example",
            title="A source headline",
            source_url="https://example.com/a.html",
            published_at="",
            published_at_text="",
            captured_at="2026-06-28T07:00:00Z",
            source_page_url="https://example.com",
            capture_method="static_html_article_link",
        )
        self.assertEqual(row["source_time_certified_flag"], 0)
        self.assertEqual(row["usable_for_historical_backtest_flag"], 0)

    def test_unmapped_macro_context_newswire_row_does_not_require_ticker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            row = build_row(
                source_key="example",
                title="Federal Reserve policy and artificial intelligence reshape commerce trends",
                source_url="https://example.com/a.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            mapped = apply_entity_mapping(row, mapper)
        self.assertEqual(mapped["symbols"], [])
        self.assertEqual(mapped["entity_mapping_status"], "NOT_REQUIRED_CONTEXT_NEWSWIRE")
        self.assertEqual(mapped["ticker_mapping_required_flag"], 0)
        self.assertEqual(mapped["macro_context_candidate_flag"], 1)
        self.assertIn("monetary_policy", mapped["context_topic_candidates"])
        self.assertIn("ai_infrastructure", mapped["context_topic_candidates"])

    def test_lawsuit_newswire_row_remains_mapping_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            row = build_row(
                source_key="example",
                title="XYZ Investors Have Opportunity to Lead Securities Fraud Lawsuit",
                source_url="https://example.com/a.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            mapped = apply_entity_mapping(row, mapper)
        self.assertEqual(mapped["entity_mapping_status"], "BLOCKED_UNMAPPED")
        self.assertEqual(mapped["ticker_mapping_required_flag"], 1)

    def test_unmapped_material_company_rows_become_non_authority_recall_candidates(self) -> None:
        titles = [
            ("TrueCar Forecasts Industry Retail Sales Soar 34% for the 4th Quarter", "industry_market_report"),
            ("Willbros Reports Fourth Quarter and Full Year 2017 Results", "earnings_results"),
            ("Merus' Interim Data on Petosemtamab Presented at Medical Meeting", "clinical_regulatory"),
            ("LAVA Medtech Acquisition Corp. Announces Liquidation", "corporate_actions"),
            ("Oak Woods Acquisition Corporation Announces Receipt of Nasdaq Notice", "listing_compliance"),
            ("Fentura Financial, Inc. Announces Fourth Quarter 2024 Earnings", "earnings_results"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            for title, topic in titles:
                row = build_row(
                    source_key="globenewswire",
                    title=title,
                    source_url="https://www.globenewswire.com/news-release/example.html",
                    published_at="2026-06-28T07:00:00Z",
                    published_at_text="2026-06-28T07:00:00Z",
                    captured_at="2026-06-28T07:00:00Z",
                    source_page_url="https://sitemaps.globenewswire.com/news/en/2026-06.xml",
                    capture_method="historical_archive_sitemap",
                )
                mapped = apply_entity_mapping(row, mapper)
                self.assertEqual(mapped["symbols"], [])
                self.assertEqual(mapped["entity_mapping_status"], "ENTITY_CANDIDATE_REVIEW")
                self.assertEqual(mapped["ticker_mapping_required_flag"], 0)
                self.assertEqual(mapped["entity_mapping_inferred_flag"], 0)
                self.assertEqual(mapped["newswire_recall_review_flag"], 1)
                self.assertEqual(mapped["newswire_recall_candidate_authority_flag"], 0)
                self.assertIn(topic, mapped["newswire_recall_topics"])

    def test_context_keyword_matching_uses_word_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            row = build_row(
                source_key="example",
                title="Locus Robotics Wins 2026 AI Breakthrough Award",
                source_url="https://example.com/a.html",
                published_at="2026-06-28T07:00:00Z",
                published_at_text="2026-06-28T07:00:00Z",
                captured_at="2026-06-28T07:00:00Z",
                source_page_url="https://example.com",
                capture_method="news_sitemap",
            )
            mapped = apply_entity_mapping(row, mapper)
        self.assertEqual(mapped["entity_mapping_status"], "NOT_REQUIRED_CONTEXT_NEWSWIRE")
        self.assertIn("ai_infrastructure", mapped["context_topic_candidates"])
        self.assertNotIn("geopolitics", mapped["context_topic_candidates"])

    def test_newswire_thematic_context_rows_are_not_forced_to_tickers(self) -> None:
        titles_and_topics = [
            ("AGIBOT's 15,000th Robot Rolls Off the Production Line, Marking a New Milestone in Embodied AI Deployment", "ai_infrastructure"),
            ("The SpaceX IPO Lifted the Whole Space Economy Including Public Companies Building the Road Back to the Moon", "space_satellite"),
            ("American EV Jobs Alliance Applauds Landmark First-Time EV Buyer Incentive", "energy_transition"),
            ("INTURAI Advances Drone, Defence and In-Home Intelligence With New Technology", "defense_drones"),
            ("Acetic Acid Market Size to Hit $34.96 Billion by 2035 Fueled by Rising VAM Demand", "industry_market_report"),
            ("Ping An Ranks No. 26 on Forbes 2026 Global 2000 List Among Global Insurers", "capital_markets"),
            ("LBank Introduces LBank Card with 100,000 USDT Rewards Pool Unlocking Seamless Crypto Payments Worldwide", "crypto_digital_assets"),
            ("One in Three Western Consumers Now Buy Products Discovered on Social Platforms as AI Reshapes Commerce", "consumer_trends"),
            ("Andreessen Horowitz Leads Netris Series A to Accelerate Adoption of GPU Network Automation Across AI Cloud Operators", "capital_markets"),
            ("Solar Backsheet Market Size to Hit USD 6.91 Billion by 2035 Research by SNS Insider", "energy_transition"),
            ("Maryland Digital Asset and Blockchain Technology Task Force to Convene at State Blockchain Bootcamp", "crypto_digital_assets"),
            ("HistoSonics Announces Financing with Participation from Yosemite Among Other Strategic Investors", "capital_markets"),
            ("BridgeBio Announces Publication in the New England Journal of Medicine of Phase 3 PROPEL 3 Trial", "healthcare_innovation"),
            ("ZTE and GSMA Announce MWC Shanghai 2026 Global Summit", "telecom_infrastructure"),
            ("WISEcode Sets Out to Transform the Food Industry Ushering In the Era of FoodTruth", "food_supply_chain"),
            ("Democratic Republic of Congo Launches Landmark Invest in the DRC Advertising Campaign in United States", "economic_development"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            for title, topic in titles_and_topics:
                row = build_row(
                    source_key="example",
                    title=title,
                    source_url="https://example.com/a.html",
                    published_at="2026-06-28T07:00:00Z",
                    published_at_text="2026-06-28T07:00:00Z",
                    captured_at="2026-06-28T07:00:00Z",
                    source_page_url="https://example.com",
                    capture_method="news_sitemap",
                )
                mapped = apply_entity_mapping(row, mapper)
                self.assertEqual(mapped["symbols"], [])
                self.assertIn(mapped["entity_mapping_status"], {"NOT_REQUIRED_CONTEXT_NEWSWIRE", "ENTITY_CANDIDATE_REVIEW"})
                self.assertEqual(mapped["ticker_mapping_required_flag"], 0)
                topics = set(mapped.get("context_topic_candidates", [])) | set(mapped.get("newswire_recall_topics", []))
                self.assertIn(topic, topics)

    def test_recent_blocked_market_structure_and_results_rows_become_context_only(self) -> None:
        titles_and_topics = [
            ("Result of Riksbank reversed auctions SEK bonds", "monetary_policy"),
            ("Procedure for listing of AS Rietumu Banka bonds initiated", "capital_markets"),
            ("Listing of Covered warrants issued by Svenska Handelsbanken AB", "market_structure"),
            ("Traiana and Trax Form Business Alliance to Offer Repo Matching Service", "market_structure"),
            ("SolarCity Announces Date and Conference Call Details for Fourth Quarter and Full Year 2015 Earnings Report", "corporate_results"),
            ("Raytheon kill vehicle succeeds in developmental flight test", "defense_drones"),
            ("ARC Document Solutions Survey Identifies Current Construction Technology Trends", "infrastructure_construction"),
            ("Dahabshiil Invests in Agri and Emergency Power Projects for Youth Entrepreneurship Programme", "infrastructure_construction"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            for title, topic in titles_and_topics:
                row = build_row(
                    source_key="example",
                    title=title,
                    source_url="https://example.com/a.html",
                    published_at="2026-06-28T07:00:00Z",
                    published_at_text="2026-06-28T07:00:00Z",
                    captured_at="2026-06-28T07:00:00Z",
                    source_page_url="https://example.com",
                    capture_method="news_sitemap",
                )
                mapped = apply_entity_mapping(row, mapper)
                self.assertEqual(mapped["symbols"], [])
                self.assertIn(mapped["entity_mapping_status"], {"NOT_REQUIRED_CONTEXT_NEWSWIRE", "ENTITY_CANDIDATE_REVIEW"})
                self.assertEqual(mapped["ticker_mapping_required_flag"], 0)
                topics = set(mapped.get("context_topic_candidates", [])) | set(mapped.get("newswire_recall_topics", []))
                self.assertIn(topic, topics)

    def test_newswire_low_signal_exclusions_remain_blocked(self) -> None:
        titles = [
            "Landscape Design Expert Breaks Down Pool Style Options for HelloNation",
            "Leading Maritime Disaster Lawyers Urge Duck-Boat Ban After Today's Incident",
            "SENIX Announces Prime Day Deal on 21-Inch Self-Propelled Gas Lawn Mower",
            "BurnTide Official Announces Effective Formula Gummies For Weight Loss in Markets",
            "GradGuard Celebrates Scholarship Program on National Insurance Awareness Day",
            "Augusta Tops Best Gold IRA Companies List By Gold Advisor",
            "AiraBreeze Announces Entry into the Portable Cooling Products Industry",
            "Monster Energy Riders Claim Key Victories on Day 2 of X Games Sacramento 2026",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            mapper = self._mapper(Path(tmp))
            for title in titles:
                row = build_row(
                    source_key="example",
                    title=title,
                    source_url="https://example.com/a.html",
                    published_at="2026-06-28T07:00:00Z",
                    published_at_text="2026-06-28T07:00:00Z",
                    captured_at="2026-06-28T07:00:00Z",
                    source_page_url="https://example.com",
                    capture_method="news_sitemap",
                )
                mapped = apply_entity_mapping(row, mapper)
                self.assertEqual(mapped["entity_mapping_status"], "BLOCKED_UNMAPPED")
                self.assertEqual(mapped["ticker_mapping_required_flag"], 1)

    def test_static_html_article_filter_blocks_overview_pages(self) -> None:
        self.assertFalse(is_probable_article_url("https://www.prnewswire.com/news-releases/"))
        self.assertFalse(is_probable_article_url("https://www.prnewswire.com/news-releases/multimedia/"))
        self.assertTrue(is_probable_article_url("https://www.prnewswire.com/news-releases/company-announces-update-302809999.html"))


if __name__ == "__main__":
    unittest.main()
