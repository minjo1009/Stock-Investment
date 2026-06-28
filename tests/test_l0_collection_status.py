from __future__ import annotations

import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.db.source_acquisition.l0_collection_status import L0CollectionStatusConfig, write_status


class L0CollectionStatusTests(unittest.TestCase):
    def test_write_status_consolidates_progress_and_db_counts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            daily_progress = root / "daily.json"
            five_progress = root / "five.json"
            news_progress = root / "news.json"
            news_plan = root / "news_plan.json"
            news_state = root / "news_state.json"
            news_events = root / "news_events.jsonl"
            newswire_progress = root / "newswire_progress.json"
            newswire_plan = root / "newswire_plan.json"
            newswire_events = root / "newswire_events.jsonl"
            context_progress = root / "context_progress.json"
            context_plan = root / "context_plan.json"
            context_events = root / "context_events.jsonl"
            context_backfill_progress = root / "context_backfill_progress.json"
            context_backfill_plan = root / "context_backfill_plan.json"
            context_backfill_events = root / "context_backfill_events.jsonl"
            market_macro_progress = root / "market_macro_progress.json"
            market_macro_plan = root / "market_macro_plan.json"
            market_macro_events = root / "market_macro_events.jsonl"
            market_macro_backfill_progress = root / "market_macro_backfill_progress.json"
            market_macro_backfill_plan = root / "market_macro_backfill_plan.json"
            market_macro_backfill_events = root / "market_macro_backfill_events.jsonl"
            ref_progress = root / "ref.json"
            tick_progress = root / "tick.json"
            daily_progress.write_text(json.dumps({"daily_symbol_index": 2, "universe_count": 10, "overall_progress_pct": 20.0}), encoding="utf-8")
            five_progress.write_text(json.dumps({"processed_events": 3, "overall_progress_pct": 1.0, "failed_events": 0}), encoding="utf-8")
            news_progress.write_text(
                json.dumps(
                    {
                        "processed_events": 4,
                        "exported_events": 3,
                        "failed_events": 1,
                        "gdelt_cursor_ts": "20160101003000",
                        "marketaux_symbol_index": 15,
                        "marketaux_window_start": "2016-01-01",
                        "marketaux_page": 1,
                        "official_done": True,
                    }
                ),
                encoding="utf-8",
            )
            news_plan.write_text(
                json.dumps(
                    {
                        "start_date": "2016-01-01",
                        "universe_count": 50,
                        "sources": {
                            "official_public_releases": {
                                "known_enabled_source_count": 2,
                                "symbols_with_known_official_endpoint": 2,
                                "symbols_missing_official_endpoint": 48,
                                "historical_2016_full_depth_status": "BLOCKED_UNLESS_OFFICIAL_ARCHIVE_ENDPOINT_EXISTS",
                            },
                            "gdelt_news_events": {"estimated_15min_files": 4, "requests_per_minute_cap": 12},
                            "marketaux_news_free": {"estimated_symbol_batches": 10, "estimated_year_windows": 2, "daily_request_cap": 95},
                        },
                    }
                ),
                encoding="utf-8",
            )
            news_state.write_text(json.dumps({"official_done": True}), encoding="utf-8")
            news_events.write_text(
                "\n".join(
                    [
                        json.dumps({"provider": "official_public_releases", "source_id": "sec_a", "status": "EXPORTED", "row_count": 1}),
                        json.dumps({"provider": "official_public_releases", "source_id": "sec_b", "status": "FAILED_RETRYABLE", "row_count": 0}),
                        json.dumps({"provider": "gdelt_news_events", "source_id": "20160101000000", "status": "EXPORTED", "row_count": 0}),
                        json.dumps({"provider": "gdelt_news_events", "source_id": "20160101001500", "status": "EXPORTED", "row_count": 0}),
                        json.dumps({"provider": "marketaux_news_free", "source_id": "A,B,C,D,E::2016-01-01::2017-01-01::page=1", "status": "EMPTY_PROVIDER_RESPONSE", "row_count": 0}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            newswire_progress.write_text(json.dumps({"processed_events": 3, "exported_events": 3}), encoding="utf-8")
            newswire_plan.write_text(json.dumps({"source_count": 3, "sources": {"prnewswire": {}, "globenewswire": {}, "businesswire": {}}}), encoding="utf-8")
            newswire_events.write_text(
                "\n".join(
                    [
                        json.dumps({"provider": "public_newswire_feeds", "source_id": "prnewswire::rss_sitemap", "status": "EXPORTED", "row_count": 10, "l1_ready_discovery_only_count": 2, "l1_blocked_count": 8}),
                        json.dumps({"provider": "public_newswire_feeds", "source_id": "globenewswire::rss_sitemap", "status": "EXPORTED", "row_count": 8, "l1_ready_discovery_only_count": 3, "l1_blocked_count": 5}),
                        json.dumps({"provider": "public_newswire_feeds", "source_id": "businesswire::rss_sitemap", "status": "EXPORTED", "row_count": 6, "l1_ready_discovery_only_count": 1, "l1_blocked_count": 5}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            context_progress.write_text(json.dumps({"processed_events": 2, "exported_events": 2}), encoding="utf-8")
            context_plan.write_text(
                json.dumps(
                    {
                        "source_count": 2,
                        "sources": {"federal_reserve_press_all": {}, "federal_register_documents": {}},
                        "historical_backfill_status": "SOURCE_SPECIFIC_ARCHIVE_REQUIRED_NOT_CLAIMED_BY_WATCHER",
                    }
                ),
                encoding="utf-8",
            )
            context_events.write_text(
                "\n".join(
                    [
                        json.dumps({"provider": "public_context_news_feeds", "source_id": "federal_reserve_press_all::context_watch", "status": "EXPORTED", "row_count": 4, "l1_ready_discovery_only_count": 4, "l1_blocked_count": 0}),
                        json.dumps({"provider": "public_context_news_feeds", "source_id": "federal_register_documents::context_watch", "status": "EXPORTED", "row_count": 6, "l1_ready_discovery_only_count": 6, "l1_blocked_count": 0}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            context_backfill_progress.write_text(
                json.dumps(
                    {
                        "processed_events": 2,
                        "exported_events": 2,
                        "backfill": {
                            "federal_register_documents": {
                                "completed_units": ["2016-01"],
                                "total_units": 2,
                                "pending_units": 1,
                                "page_offsets": {"2016-02": 2},
                            },
                            "federal_reserve_press_all": {
                                "completed_units": ["2016"],
                                "total_units": 1,
                                "pending_units": 0,
                                "page_offsets": {},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            context_backfill_plan.write_text(
                json.dumps(
                    {
                        "source_count": 2,
                        "backfill": {
                            "start_date": "2016-01-01",
                            "end_date": "2016-02-29",
                            "supported_sources": ["federal_register_documents", "federal_reserve_press_all"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            context_backfill_events.write_text(
                "\n".join(
                    [
                        json.dumps({"provider": "public_context_news_feeds", "source_id": "federal_register_documents::historical_backfill", "status": "EXPORTED", "row_count": 20, "l1_ready_discovery_only_count": 20, "l1_blocked_count": 0}),
                        json.dumps({"provider": "public_context_news_feeds", "source_id": "federal_reserve_press_all::historical_backfill", "status": "EXPORTED", "row_count": 12, "l1_ready_discovery_only_count": 12, "l1_blocked_count": 0}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            market_macro_progress.write_text(json.dumps({"processed_events": 2, "exported_events": 2}), encoding="utf-8")
            market_macro_plan.write_text(json.dumps({"source_count": 2, "sources": {"cnbc_public_rss": {}, "investing_public_rss": {}}}), encoding="utf-8")
            market_macro_events.write_text(
                "\n".join(
                    [
                        json.dumps({"provider": "public_market_macro_news_feeds", "source_id": "cnbc_public_rss::market_macro_watch", "status": "EXPORTED", "row_count": 20, "l1_ready_discovery_only_count": 20, "l1_context_ready_count": 20, "l1_blocked_count": 0}),
                        json.dumps({"provider": "public_market_macro_news_feeds", "source_id": "investing_public_rss::market_macro_watch", "status": "EXPORTED", "row_count": 20, "l1_ready_discovery_only_count": 20, "l1_context_ready_count": 20, "l1_blocked_count": 0}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            market_macro_backfill_progress.write_text(
                json.dumps(
                    {
                        "processed_events": 1,
                        "exported_events": 1,
                        "backfill": {
                            "guardian_open_platform": {
                                "completed_units": ["2016-01"],
                                "total_units": 2,
                                "pending_units": 1,
                                "page_offsets": {"2016-02": 2},
                            },
                            "cnbc_public_rss": {
                                "completed_units": ["https://www.cnbc.com/CNBCsitemapAll1.xml"],
                                "total_units": 2,
                                "pending_units": 1,
                                "entry_offsets": {"https://www.cnbc.com/CNBCsitemapAll2.xml": 5},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            market_macro_backfill_plan.write_text(
                json.dumps({"source_count": 1, "backfill_start_date": "2016-01-01", "backfill_end_date": "2016-02-29"}),
                encoding="utf-8",
            )
            market_macro_backfill_events.write_text(
                json.dumps(
                    {
                        "provider": "public_market_macro_news_feeds",
                        "source_id": "guardian_open_platform::historical_backfill",
                        "status": "EXPORTED",
                        "row_count": 50,
                        "l1_ready_discovery_only_count": 50,
                        "l1_context_ready_count": 50,
                        "l1_blocked_count": 0,
                    }
                )
                + "\n"
                + json.dumps(
                    {
                        "provider": "public_market_macro_news_feeds",
                        "source_id": "cnbc_public_rss::historical_backfill",
                        "status": "EXPORTED",
                        "row_count": 3,
                        "l1_ready_discovery_only_count": 3,
                        "l1_context_ready_count": 3,
                        "l1_blocked_count": 0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            ref_progress.write_text(json.dumps({"status": "PRIMARY_PASS", "exported_events": 5, "failed_events": 0}), encoding="utf-8")
            tick_progress.write_text(json.dumps({"status": "STOP_REQUESTED", "processed_chunks": 7}), encoding="utf-8")
            raw_dir = root / "daily_raw"
            raw_dir.mkdir()
            (raw_dir / "AAPL.csv").write_text("timestamp,open,high,low,close,volume,symbol\n", encoding="utf-8")
            shard_dir = root / "daily_shards" / "l0_bar_daily_full_backfill_shard_0"
            shard_dir.mkdir(parents=True)
            (shard_dir / "collector_progress.json").write_text(
                json.dumps({"last_status": "EXPORTED", "exported_events": 1, "observed_requests_per_minute_this_run": 2.5}),
                encoding="utf-8",
            )
            db_path = root / "test.db"
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    CREATE TABLE market_bars_5m(
                        bar_id TEXT PRIMARY KEY,
                        symbol TEXT,
                        bar_start_ts TEXT,
                        bar_end_ts TEXT
                    )
                    """
                )
                con.execute("INSERT INTO market_bars_5m VALUES('AAPL:2025-01-02T14:30:00Z','AAPL','2025-01-02T14:30:00Z','2025-01-02T14:34:59Z')")
                con.commit()
            finally:
                con.close()
            status = write_status(
                L0CollectionStatusConfig(
                    status_json=root / "status.json",
                    status_md=root / "status.md",
                    daily_progress=daily_progress,
                    five_min_progress=five_progress,
                    news_progress=news_progress,
                    news_plan=news_plan,
                    news_state=news_state,
                    news_events=news_events,
                    public_newswire_progress=newswire_progress,
                    public_newswire_plan=newswire_plan,
                    public_newswire_events=newswire_events,
                    public_newswire_background=root / "missing_newswire_bg.json",
                    public_context_news_progress=context_progress,
                    public_context_news_plan=context_plan,
                    public_context_news_events=context_events,
                    public_context_news_background=root / "missing_context_bg.json",
                    public_context_news_backfill_progress=context_backfill_progress,
                    public_context_news_backfill_plan=context_backfill_plan,
                    public_context_news_backfill_events=context_backfill_events,
                    public_context_news_backfill_background=root / "missing_context_backfill_bg.json",
                    public_market_macro_news_progress=market_macro_progress,
                    public_market_macro_news_plan=market_macro_plan,
                    public_market_macro_news_events=market_macro_events,
                    public_market_macro_news_background=root / "missing_market_macro_bg.json",
                    public_market_macro_news_backfill_progress=market_macro_backfill_progress,
                    public_market_macro_news_backfill_plan=market_macro_backfill_plan,
                    public_market_macro_news_backfill_events=market_macro_backfill_events,
                    public_market_macro_news_backfill_background=root / "missing_market_macro_backfill_bg.json",
                    reference_progress=ref_progress,
                    tick_progress=tick_progress,
                    daily_background=root / "missing_daily_bg.json",
                    five_min_background=root / "missing_five_bg.json",
                    news_background=root / "missing_news_bg.json",
                    keep_awake_status=root / "missing_keep.json",
                    daily_raw_dir=raw_dir,
                    db_path=db_path,
                    tick_stop=root / "STOP",
                    daily_shard_progress_glob=str(root / "daily_shards" / "l0_bar_daily_full_backfill_shard_*" / "collector_progress.json"),
                )
            )
            self.assertEqual(status["daily_bars"]["raw_csv_files"], 1)
            self.assertEqual(status["daily_bars"]["completed_units"], 1)
            self.assertEqual(status["daily_bars"]["shard_count"], 1)
            self.assertEqual(status["five_min_bars"]["market_bars_5m"]["row_count"], 1)
            self.assertFalse(status["one_minute_bars"]["included"])
            self.assertEqual(status["news"]["sources"]["official_public_releases"]["completed_units"], 2)
            self.assertEqual(status["news"]["sources"]["gdelt_news_events"]["progress_pct"], 50.0)
            self.assertEqual(status["news"]["sources"]["marketaux_news_free"]["completed_units"], 3)
            self.assertEqual(status["public_newswire"]["status"], "PRIMARY_PASS")
            self.assertEqual(status["public_newswire"]["row_count"], 24)
            self.assertEqual(status["public_newswire"]["l1_ready_discovery_only_count"], 6)
            self.assertEqual(status["public_newswire"]["l1_blocked_count"], 18)
            self.assertEqual(status["public_context_news"]["row_count"], 10)
            self.assertEqual(status["public_context_news"]["l1_ready_discovery_only_count"], 10)
            self.assertEqual(status["public_context_news"]["l1_blocked_count"], 0)
            self.assertEqual(status["public_context_news_backfill"]["row_count"], 32)
            self.assertEqual(status["public_context_news_backfill"]["completed_units"], 2)
            self.assertEqual(status["public_context_news_backfill"]["total_units"], 3)
            self.assertEqual(status["public_context_news_backfill"]["active_page_offsets"], 1)
            self.assertEqual(status["public_market_macro_news"]["status"], "PRIMARY_PASS")
            self.assertEqual(status["public_market_macro_news"]["row_count"], 40)
            self.assertEqual(status["public_market_macro_news"]["l1_context_ready_count"], 40)
            self.assertEqual(status["public_market_macro_news_backfill"]["row_count"], 53)
            self.assertEqual(status["public_market_macro_news_backfill"]["completed_units"], 2)
            self.assertEqual(status["public_market_macro_news_backfill"]["total_units"], 4)
            self.assertEqual(status["public_market_macro_news_backfill"]["active_page_offsets"], 2)
            self.assertTrue((root / "status.md").exists())


if __name__ == "__main__":
    unittest.main()
