from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task539_market_cap_shares_source import (
    build_market_cap_factor_readiness,
    build_market_cap_panel,
    extract_shares_outstanding_panel,
)


class Task539MarketCapSharesSourceTest(unittest.TestCase):
    def test_market_cap_panel_uses_reported_shares_and_daily_close(self) -> None:
        shares = pd.DataFrame(
            {
                "symbol": ["AAA"],
                "period_end": pd.to_datetime(["2024-01-01"]),
                "shares_outstanding": [100.0],
                "concept": ["CommonStockSharesOutstanding"],
            }
        )
        prices = pd.DataFrame(
            {
                "symbol": ["AAA"],
                "date": pd.to_datetime(["2024-01-02"]),
                "close": [12.0],
            }
        )
        panel = build_market_cap_panel(shares, prices)
        self.assertEqual(float(panel.iloc[0]["market_cap"]), 1200.0)
        self.assertEqual(str(panel.iloc[0]["market_cap_source_grade"]), "SEC_companyfacts_shares_x_daily_close")

    def test_factor_readiness_marks_not_crsp_grade(self) -> None:
        join = pd.DataFrame({"market_cap_available_flag": [1, 1, 0]})
        readiness = build_market_cap_factor_readiness(pd.DataFrame({"x": [1]}), join)
        self.assertEqual(int(readiness["ready_for_crsp_compustat_grade_flag"].max()), 0)


if __name__ == "__main__":
    unittest.main()
