from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestDataQuality(unittest.TestCase):
    def test_us_daily_data_quality_minimum(self) -> None:
        from data.quality import assess_csv_quality

        csv_path = ROOT / "data" / "raw" / "us_daily" / "AAPL.csv"
        self.assertTrue(csv_path.exists())

        quality = assess_csv_quality(csv_path)
        self.assertTrue(quality["exists"])
        self.assertGreater(int(quality["row_count"]), 0)
        self.assertIsNotNone(quality["start_date"])
        self.assertIsNotNone(quality["end_date"])

        df = pd.read_csv(csv_path)
        self.assertIn("timestamp", df.columns)
        dup_count = int(df.duplicated(subset=["timestamp"]).sum())
        self.assertEqual(dup_count, 0)


if __name__ == "__main__":
    unittest.main()
