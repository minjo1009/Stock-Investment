from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.db.source_acquisition.source_capability_probe import (
    build_robot_parser,
    load_registry,
    parse_html,
    parse_xml_capability,
    robots_posture,
    robots_url_allowed,
    select_recommended_mode,
)


class L0SourceCapabilityProbeTests(unittest.TestCase):
    def test_parse_html_detects_feed_jsonld_and_article_links(self) -> None:
        html = b"""
        <html><head>
          <link rel="alternate" type="application/rss+xml" href="/rss/news.xml" />
          <meta property="article:published_time" content="2026-06-28T01:00:00Z" />
          <script type="application/ld+json">{"@type":"NewsArticle","headline":"A headline"}</script>
        </head>
        <body>
          <a href="/news-release/2026/06/28/example.html">Example company announces update</a>
        </body></html>
        """
        parsed = parse_html(html, "https://example.com/newsroom")
        self.assertEqual(parsed["feed_link_count"], 1)
        self.assertEqual(parsed["article_link_count"], 1)
        self.assertTrue(parsed["has_newsarticle_jsonld"])
        self.assertTrue(parsed["has_article_meta"])

    def test_parse_xml_capability_detects_rss_and_sitemap(self) -> None:
        rss = b"<rss><channel><item><title>A</title></item><item><title>B</title></item></channel></rss>"
        sitemap = b"""<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.com/a</loc></url></urlset>"""
        self.assertEqual(parse_xml_capability(rss)["feed_item_count"], 2)
        self.assertEqual(parse_xml_capability(sitemap)["sitemap_url_count"], 1)

    def test_recommended_mode_prefers_machine_readable_before_browser(self) -> None:
        self.assertEqual(select_recommended_mode({"feed": {"feed_ready": True}}), "rss_or_atom")
        self.assertEqual(select_recommended_mode({"sitemap": {"sitemap_ready": True}}), "sitemap_or_news_sitemap")
        self.assertEqual(select_recommended_mode({"static_html": {"article_links_ready": True}}), "static_html")
        self.assertEqual(select_recommended_mode({"browser_fallback": {"needed": True}}), "chrome_fallback_probe")

    def test_recommended_mode_does_not_promote_robots_blocked_feed_to_browser(self) -> None:
        self.assertEqual(
            select_recommended_mode(
                {
                    "feed": {"results": [{"skipped_by_robots": True, "skip_reason": "robots_disallow"}]},
                    "browser_fallback": {"needed": True},
                }
            ),
            "blocked_or_manual_review",
        )

    def test_robots_blocks_same_origin_but_not_cross_origin_sitemap_hints(self) -> None:
        robots = b"User-agent: *\nDisallow: /help\nSitemap: https://feed.example.com/rss.xml\n"
        posture = robots_posture(robots)
        parser = build_robot_parser("https://example.com", robots)

        self.assertFalse(
            robots_url_allowed(
                "https://example.com/help/feed-options",
                base_origin="https://example.com",
                robots_present=posture["robots_present"],
                robot_parser=parser,
            )
        )
        self.assertTrue(
            robots_url_allowed(
                "https://feed.example.com/rss.xml",
                base_origin="https://example.com",
                robots_present=posture["robots_present"],
                robot_parser=parser,
            )
        )

    def test_registry_loads_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sources.json"
            path.write_text(json.dumps({"sources": [{"source_key": "example", "base_url": "https://example.com"}]}), encoding="utf-8")
            sources = load_registry(path)
            self.assertEqual(sources[0]["source_key"], "example")


if __name__ == "__main__":
    unittest.main()
