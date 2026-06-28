from __future__ import annotations

import unittest

from src.brain.l3.source_reliability import (
    classify_source_authority,
    load_source_reliability_config,
    source_reliability_score,
)


class L3SourceReliabilityTest(unittest.TestCase):
    def test_primary_source_scores_above_discovery_proxy(self) -> None:
        config = load_source_reliability_config()
        self.assertGreater(
            source_reliability_score("official_primary", config=config),
            source_reliability_score("news_discovery_proxy", config=config),
        )
        self.assertEqual(classify_source_authority("sec_event"), "sec_primary")
        self.assertEqual(classify_source_authority("gdelt"), "news_discovery_proxy")
        self.assertEqual(
            classify_source_authority("news_event", "official_public_releases"),
            "official_primary",
        )
        self.assertEqual(
            classify_source_authority("news_event", "marketaux_news_free"),
            "licensed_metadata_proxy",
        )
        self.assertEqual(
            classify_source_authority("news_event", "gdelt_news_events"),
            "news_discovery_proxy",
        )
        self.assertEqual(
            classify_source_authority("news_event", "public_newswire_feeds"),
            "news_discovery_proxy",
        )
        self.assertEqual(
            classify_source_authority("news_event", "public_context_news_feeds"),
            "news_discovery_proxy",
        )
        self.assertEqual(
            classify_source_authority("news_event", "public_market_macro_news_feeds"),
            "news_discovery_proxy",
        )


if __name__ == "__main__":
    unittest.main()
