from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from tools.db.news_l0_l1 import (
    BLOCKED,
    READY_DIAGNOSTIC_ONLY,
    READY_DISCOVERY_ONLY,
    evaluate_news_l1_row,
    marketaux_token_audit,
    redact_provider_metadata,
)
from tools.db.source_acquisition.microstructure_checkpoint import MicrostructureCheckpointStore
from tools.db.source_acquisition.microstructure_coverage import build_microstructure_coverage
from tools.db.source_acquisition.scheduler_override import (
    FORCE_CLOSED_FIELDS,
    SchedulerOverrideError,
    merge_scheduler_override,
    read_json,
)


BASE_CONFIG = Path("configs/db_source_acquisition_scheduler.json")
TEMPLATE_OVERRIDE = Path("configs/local_templates/db_source_acquisition_scheduler.override.example.json")


class L0SourceAcquisitionHardeningTest(unittest.TestCase):
    def _valid_row(self, provider: str) -> dict[str, object]:
        return {
            "provider": provider,
            "published_at": "2026-06-01T12:00:00Z",
            "source_url": "https://example.com/source",
            "title": "Source release title",
            "symbols": ["AAPL"],
        }

    def test_news_l1_statuses_separate_authority_from_discovery(self) -> None:
        official = evaluate_news_l1_row(self._valid_row("official_public_releases"))
        gdelt = evaluate_news_l1_row(self._valid_row("gdelt_news_events"))
        marketaux = evaluate_news_l1_row(self._valid_row("marketaux_news_free"))
        browser = evaluate_news_l1_row(self._valid_row("public_headline_browser_watch"))
        self.assertEqual(official.promotion_status, READY_DIAGNOSTIC_ONLY)
        self.assertEqual(gdelt.promotion_status, READY_DISCOVERY_ONLY)
        self.assertEqual(marketaux.promotion_status, READY_DISCOVERY_ONLY)
        self.assertEqual(browser.promotion_status, READY_DISCOVERY_ONLY)
        self.assertEqual(gdelt.trade_authority_flag, 0)
        self.assertEqual(marketaux.trade_authority_flag, 0)
        self.assertEqual(browser.trade_authority_flag, 0)

    def test_news_missing_critical_fields_blocked(self) -> None:
        row = self._valid_row("gdelt_news_events")
        row["title"] = ""
        self.assertEqual(evaluate_news_l1_row(row).promotion_status, BLOCKED)
        row = self._valid_row("official_public_releases")
        row["source_url"] = ""
        self.assertEqual(evaluate_news_l1_row(row).promotion_status, BLOCKED)

    def test_marketaux_token_masking_and_metadata_redaction(self) -> None:
        audit = marketaux_token_audit({"MARKETAUX_API_KEY": "marketaux-secret-value"})
        self.assertEqual(audit["secret_value_logged_flag"], 0)
        self.assertNotIn("marketaux-secret-value", audit["masked"])
        metadata = redact_provider_metadata(
            {
                "api_key": "marketaux-secret-value",
                "url": "https://example.com/news?token=sk-testtokenvalue123456",
                "headline": "safe",
            }
        )
        self.assertEqual(metadata["api_key"], "***REDACTED***")
        self.assertNotIn("sk-testtokenvalue123456", metadata["url"])

    def test_scheduler_override_enables_diagnostic_collection_without_permissions(self) -> None:
        base = read_json(BASE_CONFIG)
        override = read_json(TEMPLATE_OVERRIDE)
        effective = merge_scheduler_override(base, override)
        jobs = {job["name"]: job for job in effective["jobs"]}
        self.assertTrue(jobs["official_news_sources_15m"]["enabled"])
        self.assertTrue(jobs["gdelt_news_discovery_15m"]["enabled"])
        self.assertTrue(jobs["marketaux_news_free_30m"]["enabled"])
        self.assertTrue(jobs["microstructure_backfill_batch"]["enabled"])
        self.assertEqual(jobs["microstructure_backfill_batch"]["mode"], "smoke")
        self.assertFalse(jobs["microstructure_backfill_batch"]["feature_builder_enabled"])
        for field, closed in FORCE_CLOSED_FIELDS.items():
            self.assertEqual(int(effective["permissions"][field]), closed)
            self.assertEqual(int(jobs["microstructure_backfill_batch"][field]), closed)

    def test_scheduler_override_rejects_trading_permission_opening(self) -> None:
        base = read_json(BASE_CONFIG)
        with self.assertRaises(SchedulerOverrideError):
            merge_scheduler_override(
                base,
                {
                    "permissions": {"execution_permitted": 1},
                    "jobs": [{"name": "official_news_sources_15m", "enabled": True}],
                },
            )
        with self.assertRaises(SchedulerOverrideError):
            merge_scheduler_override(base, {"strategy": "ACCEPTED"})

    def test_microstructure_default_is_disabled_and_yfinance_proxy_is_not_tick_truth(self) -> None:
        base = read_json(BASE_CONFIG)
        jobs = {job["name"]: job for job in base["jobs"]}
        micro = jobs["microstructure_backfill_batch"]
        self.assertFalse(micro["enabled"])
        self.assertFalse(micro["allow_network"])
        self.assertEqual(set(micro["families"]), {"microstructure_quotes", "microstructure_trades"})
        self.assertFalse(micro["feature_builder_enabled"])
        self.assertEqual(base["source_families"]["market_bar_proxy_intraday"]["authority_class"], "bar_proxy_not_exchange_tick_truth")

    def test_microstructure_checkpoint_records_success_and_retryable_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checkpoint.jsonl"
            store = MicrostructureCheckpointStore(path)
            success = store.record(
                provider="alpaca",
                feed="iex",
                source_type="quotes",
                symbol="AAPL",
                session_date="2026-05-15",
                chunk_start_ts="2026-05-15T14:30:00Z",
                chunk_end_ts="2026-05-15T14:31:00Z",
                status="EXPORTED",
                row_count=2,
            )
            failure = store.record(
                provider="alpaca",
                feed="iex",
                source_type="trades",
                symbol="AAPL",
                session_date="2026-05-15",
                chunk_start_ts="2026-05-15T14:30:00Z",
                chunk_end_ts="2026-05-15T14:31:00Z",
                status="FAILED_RETRYABLE",
                error_category="RateLimit",
                error_message="Bearer sk-testtokenvalue123456 failed",
            )
            rows = store.load()
            self.assertEqual(len(rows), 2)
            self.assertEqual(success["status"], "EXPORTED")
            self.assertEqual(failure["status"], "FAILED_RETRYABLE")
            self.assertNotIn("sk-testtokenvalue123456", failure["error_message_redacted"])

    def test_microstructure_coverage_audit_reports_quote_trade_coverage_without_proxy_or_feature_builder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            quotes = root / "feed=sip" / "quotes"
            trades = root / "feed=sip" / "trades"
            quotes.mkdir(parents=True)
            trades.mkdir(parents=True)
            pd.DataFrame(
                [
                    {
                        "symbol": "AAPL",
                        "quote_ts": "2026-05-15T14:30:00Z",
                        "bid": 100.0,
                        "ask": 100.1,
                        "bid_size": 10,
                        "ask_size": 12,
                    }
                ]
            ).to_csv(quotes / "AAPL.csv", index=False)
            pd.DataFrame(
                [
                    {
                        "symbol": "AAPL",
                        "trade_ts": "2026-05-15T14:30:01Z",
                        "price": 100.05,
                        "size": 100,
                        "trade_id": "T1",
                    }
                ]
            ).to_csv(trades / "AAPL.csv", index=False)
            artifacts = build_microstructure_coverage(raw_dir=root, output_dir=None, symbols=["AAPL"], session_dates=["2026-05-15"])
            by_symbol_date = artifacts["by_symbol_date"].iloc[0]
            self.assertEqual(int(by_symbol_date["quotes_available_flag"]), 1)
            self.assertEqual(int(by_symbol_date["trades_available_flag"]), 1)
            self.assertEqual(int(by_symbol_date["yfinance_proxy_used_flag"]), 0)
            self.assertEqual(int(by_symbol_date["open_bar_proxy_used_flag"]), 0)
            self.assertEqual(int(by_symbol_date["feature_builder_allowed_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
