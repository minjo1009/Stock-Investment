from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task541_size_bm_fama_macbeth import (
    build_decision,
    build_size_bm_factor_panel,
    fit_fama_macbeth_with_size_bm,
)


class Task541SizeBookToMarketTest(unittest.TestCase):
    def test_size_bm_panel_uses_previous_close_and_filed_book_value(self) -> None:
        lifecycle = pd.DataFrame(
            {
                "lifecycle_id": ["L1"],
                "symbol": ["AAA"],
                "theme_id": ["theme"],
                "entry_ts": [pd.Timestamp("2024-01-10 14:30:00", tz="UTC")],
                "quarter": ["2024Q1"],
                "return_pct": [3.0],
            }
        )
        market_cap = pd.DataFrame(
            {
                "symbol": ["AAA", "AAA"],
                "market_cap_date": [pd.Timestamp("2024-01-09", tz="UTC"), pd.Timestamp("2024-01-10", tz="UTC")],
                "market_cap": [100.0, 999.0],
            }
        )
        book = pd.DataFrame(
            {
                "symbol": ["AAA"],
                "book_equity_filed_date": [pd.Timestamp("2024-01-05", tz="UTC")],
                "book_equity_period_end": [pd.Timestamp("2023-12-31", tz="UTC")],
                "book_equity": [25.0],
            }
        ).rename(columns={"book_equity_filed_date": "filed_date", "book_equity_period_end": "period_end"})
        panel = build_size_bm_factor_panel(lifecycle, market_cap, book)
        self.assertAlmostEqual(float(panel.iloc[0]["market_cap"]), 100.0)
        self.assertAlmostEqual(float(panel.iloc[0]["book_to_market"]), 0.25)
        self.assertEqual(int(panel.iloc[0]["factor_result_used_as_trading_trigger_flag"]), 0)
        self.assertEqual(int(panel.iloc[0]["missing_data_approximated_flag"]), 0)

    def test_fama_macbeth_includes_size_and_book_to_market_terms(self) -> None:
        rows = []
        for quarter in ["2024Q1", "2024Q2", "2024Q3"]:
            for i in range(18):
                rows.append(
                    {
                        "lifecycle_id": f"{quarter}-{i}",
                        "symbol": f"S{i}",
                        "theme_id": "theme",
                        "quarter": quarter,
                        "return_pct": float(i),
                        "size_log_market_cap": 10.0 + i / 10,
                        "book_to_market_log": -2.0 + i / 20,
                        "net_return_from_entry": 999.0,
                    }
                )
        coef, result = fit_fama_macbeth_with_size_bm(pd.DataFrame(rows))
        self.assertFalse(coef.empty)
        self.assertIn("size_log_market_cap", set(result["term"]))
        self.assertIn("book_to_market_log", set(result["term"]))
        self.assertNotIn("net_return_from_entry", set(result["term"]))
        self.assertEqual(int(result["factor_result_used_as_trading_trigger_flag"].max()), 0)

    def test_decision_remains_diagnostic_and_source_limited(self) -> None:
        coverage = pd.DataFrame(
            [
                {
                    "market_cap_coverage_rate": 1.0,
                    "book_to_market_coverage_rate": 0.9,
                    "missing_data_approximated_flag": 0,
                    "crsp_compustat_grade_flag": 0,
                }
            ]
        )
        fmb = pd.DataFrame({"term": ["size_log_market_cap", "book_to_market_log"]})
        decision = build_decision(coverage, fmb)
        self.assertEqual(int(decision.iloc[0]["fama_macbeth_size_bm_run_flag"]), 1)
        self.assertEqual(int(decision.iloc[0]["factor_result_used_as_trading_trigger_flag"]), 0)
        self.assertEqual(int(decision.iloc[0]["crsp_compustat_grade_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
