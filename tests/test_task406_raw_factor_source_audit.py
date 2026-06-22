from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task406_raw_factor_source_audit import build_task406_raw_factor_source_audit


class TestTask406RawFactorSourceAudit(unittest.TestCase):
    def test_raw_provenance_missing_sources_and_non_regular_audit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = root / "raw"
            raw.mkdir()
            pd.DataFrame(
                [
                    {"timestamp": "2026-01-02T09:00:00Z", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100, "trade_count": 3, "vwap": 10.2},
                    {"timestamp": "2026-01-02T14:30:00Z", "open": 10.5, "high": 12, "low": 10, "close": 11.5, "volume": 200, "trade_count": 5, "vwap": 11.0},
                ]
            ).to_csv(raw / "AAA.csv", index=False)

            artifacts = build_task406_raw_factor_source_audit(intraday_dir=raw, out_dir=root / "out")

            self.assertIn("raw_bar_id", artifacts.raw_bar_provenance_panel.columns)
            self.assertIn("raw_row_hash", artifacts.raw_bar_provenance_panel.columns)
            self.assertGreater(int(artifacts.raw_session_eligibility_audit["non_regular_session_bar_count"].sum()), 0)
            missing = artifacts.raw_factor_source_audit[artifacts.raw_factor_source_audit["factor_name"].eq("spread_bps")]
            self.assertEqual(str(missing.iloc[0]["source_availability_status"]), "collectable_but_missing")
            self.assertEqual(int(artifacts.raw_factor_source_audit["inferred_matching_used_flag"].max()), 0)
            self.assertTrue((root / "out" / "task_406_raw_factor_source_audit.md").exists())


if __name__ == "__main__":
    unittest.main()
