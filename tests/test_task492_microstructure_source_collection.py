from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task492_microstructure_source_collection import (
    build_microstructure_entry_features,
    build_source_availability_audit,
    normalize_quote_rows,
)


class Task492MicrostructureSourceCollectionTest(unittest.TestCase):
    def test_quote_features_are_exact_and_missing_sources_are_reported(self) -> None:
        base = pd.DataFrame(
            {
                "lifecycle_id": ["L1"],
                "symbol": ["AAPL"],
                "entry_ts": [pd.Timestamp("2024-01-02T14:31:00Z")],
                "split_name": ["validation"],
                "theme_id": ["mega_cap"],
            }
        )
        raw = normalize_quote_rows(
            "L1",
            "AAPL",
            pd.Timestamp("2024-01-02T14:31:00Z"),
            [{"t": "2024-01-02T14:30:59Z", "bp": 100.0, "ap": 100.05, "bs": 10, "as": 12, "bx": "Q", "ax": "Q", "c": ["R"], "z": "C"}],
            "sip",
        )
        features = build_microstructure_entry_features(base, raw)
        self.assertEqual(int(features.iloc[0]["microstructure_feature_available_flag"]), 1)
        self.assertGreater(float(features.iloc[0]["spread_bps"]), 0)
        audit = build_source_availability_audit(raw, features)
        self.assertIn("not_available_in_historical_api_live_archive_required", set(audit["source_status"]))
        self.assertIn("available_exact_from_bid_ask", set(audit["source_status"]))


if __name__ == "__main__":
    unittest.main()
