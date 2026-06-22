from __future__ import annotations

import pandas as pd
import unittest

from src.backtest.build_task540_market_cap_coverage_gap import build_gap_decomposition


class Task540MarketCapCoverageGapTest(unittest.TestCase):
    def test_gap_decomposition_separates_share_and_price_missing(self) -> None:
        joined = pd.DataFrame(
            {
                "symbol": ["AAA", "BBB", "CCC"],
                "market_cap_available_flag": [1, 0, 0],
            }
        )
        shares = pd.DataFrame({"symbol": ["AAA", "CCC"]})
        price = pd.DataFrame({"symbol": ["AAA", "BBB"]})
        gap = build_gap_decomposition(joined, shares, price)
        reasons = dict(zip(gap["symbol"], gap["gap_reason"]))
        self.assertEqual(reasons["AAA"], "covered")
        self.assertEqual(reasons["BBB"], "shares_source_missing")
        self.assertEqual(reasons["CCC"], "daily_price_source_missing")


if __name__ == "__main__":
    unittest.main()
