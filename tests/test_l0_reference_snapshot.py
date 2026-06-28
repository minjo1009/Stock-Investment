from __future__ import annotations

import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.db.source_acquisition.reference_snapshot import ReferenceSnapshotConfig, build_plan, write_assets_csv, write_calendar_csv


class L0ReferenceSnapshotTests(unittest.TestCase):
    def test_write_assets_csv_keeps_status_fields(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "assets.csv"
            count = write_assets_csv(
                path,
                [
                    {
                        "id": "asset-1",
                        "class": "us_equity",
                        "exchange": "NASDAQ",
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "status": "active",
                        "tradable": True,
                    }
                ],
            )
            self.assertEqual(count, 1)
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["symbol"], "AAPL")
            self.assertEqual(rows[0]["status"], "active")

    def test_write_calendar_csv_keeps_date_key(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "calendar.csv"
            count = write_calendar_csv(
                path,
                [
                    {"date": "2025-01-02", "open": "09:30", "close": "16:00"},
                    {"date": "2025-01-02", "open": "09:30", "close": "16:00"},
                ],
            )
            self.assertEqual(count, 1)
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["date"], "2025-01-02")

    def test_build_plan_writes_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = ReferenceSnapshotConfig(
                raw_dir=root / "raw",
                progress_path=root / "progress.json",
                event_path=root / "events.jsonl",
                plan_path=root / "plan.json",
                contract_path=root / "contract.json",
                start_date="2016-01-01",
                end_date="2026-06-26",
            )
            plan = build_plan(config)
            self.assertIn("alpaca_calendar", plan["sources"])
            self.assertTrue((root / "contract.json").exists())


if __name__ == "__main__":
    unittest.main()
