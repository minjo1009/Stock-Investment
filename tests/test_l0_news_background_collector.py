from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.db.source_acquisition.news_background_collector import (
    NewsCollectorConfig,
    collect_marketaux,
    next_batch,
    parse_rss_rows,
    gdelt_query_text,
    source_event,
    write_raw,
)


class L0NewsBackgroundCollectorTest(unittest.TestCase):
    def test_parse_rss_rows_produces_official_l1_ready_input(self) -> None:
        rss = b"""
        <rss><channel><item>
          <title>Official release</title>
          <link>https://example.com/release</link>
          <pubDate>Fri, 26 Jun 2026 13:30:00 GMT</pubDate>
        </item></channel></rss>
        """

        rows = parse_rss_rows(
            {
                "source_id": "official_example",
                "url": "https://example.com/rss",
                "symbol_scope": ["AAPL"],
            },
            rss,
        )
        event = source_event(provider="official_public_releases", source_id="official_example", status="EXPORTED", row_count=len(rows), l1_rows=rows)

        self.assertEqual(len(rows), 1)
        self.assertEqual(event["l1_ready_diagnostic_only_count"], 1)
        self.assertEqual(event["trade_authority_flag"], 0)

    def test_marketaux_missing_token_records_credential_blocker_without_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = NewsCollectorConfig(raw_dir=Path(tmp) / "raw")

            with patch("tools.db.source_acquisition.news_background_collector.load_marketaux_token", return_value=""):
                event = collect_marketaux(config, ["AAPL", "MSFT"])

        self.assertEqual(event["status"], "CREDENTIAL_BLOCKED")
        self.assertEqual(event["secret_logged_flag"], 0)
        self.assertNotIn("api_token", event["error_message_redacted"].lower())

    def test_next_batch_wraps_without_losing_symbols(self) -> None:
        batch, next_index = next_batch(["A", "B", "C"], 2, 2)

        self.assertEqual(batch, ["C"])
        self.assertEqual(next_index, 0)

    def test_gdelt_query_prefers_company_name_over_short_symbol(self) -> None:
        self.assertEqual(gdelt_query_text("A", "Agilent Technologies Inc."), '"Agilent Technologies"')
        self.assertEqual(gdelt_query_text("A", ""), "")

    def test_write_raw_hash_event_has_no_trading_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = write_raw(Path(tmp), provider="gdelt_news_events", key="AAPL", payload={"data": []})
            event = source_event(provider="gdelt_news_events", source_id="AAPL", status="EMPTY_PROVIDER_RESPONSE", row_count=0, raw_path=path)

        self.assertTrue(event["raw_sha256"])
        self.assertEqual(event["broker_mutation_permitted_flag"], 0)
        self.assertEqual(event["real_capital_permitted_flag"], 0)


if __name__ == "__main__":
    unittest.main()
