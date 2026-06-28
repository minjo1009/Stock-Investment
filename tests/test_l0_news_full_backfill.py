from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.db.source_acquisition.news_full_backfill import (
    NewsFullBackfillConfig,
    build_plan,
    gdelt_raw_path,
    gdelt_url,
    marketaux_window_end,
    next_gdelt_ts,
    run_full_backfill,
)


class L0NewsFullBackfillTest(unittest.TestCase):
    def test_gdelt_archive_url_and_cursor_are_15_minute_chunks(self) -> None:
        self.assertEqual(gdelt_url("20160101000000"), "http://data.gdeltproject.org/gdeltv2/20160101000000.export.CSV.zip")
        self.assertEqual(next_gdelt_ts("20160101000000"), "20160101001500")
        self.assertEqual(
            gdelt_raw_path(Path("raw"), "20160101000000").as_posix(),
            "raw/provider=gdelt_news_events/year=2016/month=01/20160101000000.export.CSV.zip",
        )

    def test_marketaux_window_caps_at_end_date(self) -> None:
        self.assertEqual(marketaux_window_end("2026-01-01", days=366, max_end="2026-06-27"), "2026-06-27")

    def test_plan_writes_official_missing_endpoint_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            universe = root / "universe.csv"
            universe.write_text(
                "symbol,name,exchange,status,tradable\nAAPL,Apple Inc,NASDAQ,active,True\nZZZ,Missing Co,NASDAQ,active,True\n",
                encoding="utf-8",
            )
            config = NewsFullBackfillConfig(
                universe_path=universe,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                stop_path=root / "STOP",
                plan_path=root / "plan.json",
                official_blockers_path=root / "official_blockers.csv",
                end_date="2016-01-02",
            )

            plan = build_plan(config)
            blocker_text = config.official_blockers_path.read_text(encoding="utf-8-sig")

        self.assertEqual(plan["sources"]["official_public_releases"]["symbols_missing_official_endpoint"], 1)
        self.assertIn("OFFICIAL_ENDPOINT_NOT_VERIFIED_NOT_APPROXIMATED", blocker_text)

    def test_marketaux_smoke_without_token_records_credential_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            universe = root / "universe.csv"
            universe.write_text("symbol,name,exchange,status,tradable\nAAPL,Apple Inc,NASDAQ,active,True\n", encoding="utf-8")
            config = NewsFullBackfillConfig(
                universe_path=universe,
                raw_dir=root / "raw",
                state_path=root / "state.json",
                event_path=root / "events.jsonl",
                progress_path=root / "progress.json",
                stop_path=root / "STOP",
                plan_path=root / "plan.json",
                official_blockers_path=root / "official_blockers.csv",
                sources=("marketaux",),
                max_requests=1,
            )

            with patch("tools.db.source_acquisition.news_full_backfill.load_marketaux_token", return_value=""):
                result = run_full_backfill(config, smoke=True)
            event_text = config.event_path.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "CREDENTIAL_BLOCKED")
        self.assertIn("CREDENTIAL_BLOCKED", event_text)


if __name__ == "__main__":
    unittest.main()
