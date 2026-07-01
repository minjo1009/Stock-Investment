from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.brain.l3_diagnostic_strategy_view_bootstrap.contracts import DirectionReview
from src.brain.l3_diagnostic_strategy_view_bootstrap.coverage_policy import load_coverage_gaps
from src.brain.l3_diagnostic_strategy_view_bootstrap.economic_meaning_classifier import classify_economic_meaning
from src.brain.l3_diagnostic_strategy_view_bootstrap.l2_read_view_bridge import normalize_article_features


class L3DiagnosticStrategyViewBootstrapTests(unittest.TestCase):
    def test_l1_blocked_row_excluded_from_active(self) -> None:
        l2 = [{"diagnostic_feature_id": "l2a", "l1_article_packet_id": "p1", "symbol": "AAPL", "diagnostic_only": "1", "trading_eligible": "0", "signal_order_export_allowed": "0", "broker_mutation_permitted": "0"}]
        l1 = {"p1": {"l1_status": "BLOCKED", "mapping_status": "HIGH_CONFIDENCE_DETERMINISTIC", "mapping_scope": "TICKER", "source_time_certified": "1"}}
        active, rejected = normalize_article_features(l2, l1)
        self.assertEqual(active, [])
        self.assertIn("L1_BLOCKED_OR_NOT_READY", rejected[0]["rejection_reasons"])

    def test_unknown_mapping_routes_to_review_queue(self) -> None:
        l2 = [{"diagnostic_feature_id": "l2a", "l1_article_packet_id": "p1", "symbol": "AAPL", "diagnostic_only": "1", "trading_eligible": "0", "signal_order_export_allowed": "0", "broker_mutation_permitted": "0"}]
        l1 = {"p1": {"l1_status": "READY", "mapping_status": "UNKNOWN", "mapping_scope": "UNKNOWN", "source_time_certified": "1"}}
        active, rejected = normalize_article_features(l2, l1)
        self.assertEqual(active, [])
        self.assertIn("UNKNOWN_MAPPING", rejected[0]["rejection_reasons"])

    def test_duplicate_noncanonical_suppressed(self) -> None:
        row = {"diagnostic_feature_id": "l2a", "l1_article_packet_id": "p1", "symbol": "AAPL", "feature_name": "presence", "diagnostic_only": "1", "trading_eligible": "0", "signal_order_export_allowed": "0", "broker_mutation_permitted": "0"}
        l1 = {"p1": {"l1_status": "READY", "mapping_status": "HIGH_CONFIDENCE_DETERMINISTIC", "mapping_scope": "TICKER", "source_time_certified": "1"}}
        active, rejected = normalize_article_features([row, {**row, "diagnostic_feature_id": "l2b"}], l1)
        self.assertEqual(len(active), 1)
        self.assertIn("DUPLICATE_NON_CANONICAL_SUPPRESSED", rejected[0]["rejection_reasons"])

    def test_incomplete_backfill_creates_non_negative_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "status.json"
            path.write_text(json.dumps({"public_newswire_backfill": {"status": "RUNNING", "progress_pct": 42, "provider": "public_newswire_feeds"}, "public_market_macro_news_backfill": {"status": "RUNNING", "progress_pct": 29, "provider": "public_market_macro_news_feeds"}}), encoding="utf-8")
            gaps = load_coverage_gaps(path)
        self.assertEqual(len(gaps), 2)
        self.assertTrue(all(gap["negative_evidence_allowed"] == 0 for gap in gaps))

    def test_rule_classifier_does_not_emit_buy_sell(self) -> None:
        l2 = [{"diagnostic_feature_id": "l2a", "l1_article_packet_id": "p1", "symbol": "AAPL", "feature_name": "presence", "diagnostic_only": "1", "trading_eligible": "0", "signal_order_export_allowed": "0", "broker_mutation_permitted": "0"}]
        l1 = {"p1": {"l1_status": "READY", "mapping_status": "HIGH_CONFIDENCE_DETERMINISTIC", "mapping_scope": "TICKER", "source_time_certified": "1", "title": "Company receives regulatory approval"}}
        active, _ = normalize_article_features(l2, l1)
        _, _, direction, _, _ = classify_economic_meaning(active[0])
        self.assertIn(direction, {DirectionReview.SUPPORT_REVIEW, DirectionReview.RISK_REVIEW, DirectionReview.CONTEXT_ONLY})
        self.assertNotIn(direction.value, {"BUY", "SELL"})


if __name__ == "__main__":
    unittest.main()

