from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task537_factor_premium_validation import (
    fit_fama_french_trade_regression,
    fit_fama_macbeth_entry_safe_panel,
    parse_fama_french_daily,
)


class Task537FactorPremiumValidationTest(unittest.TestCase):
    def test_parse_fama_french_daily(self) -> None:
        raw = "ignore\n,Mkt-RF,SMB,HML,RMW,CMA,RF\n20240102, 0.1, 0.2, -0.3, 0.4, 0.5, 0.01\n\nAnnual Factors:"
        parsed = parse_fama_french_daily(raw)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(float(parsed.iloc[0]["Mkt_RF"]), 0.1)

    def test_fama_french_regression_is_diagnostic_only(self) -> None:
        panel = pd.DataFrame(
            {
                "excess_return_pct": [1, 2, 3, 4, 5, 6, 7, 8],
                "cum_Mkt_RF_pct": [1, 1, 2, 2, 3, 3, 4, 4],
                "cum_SMB_pct": [0, 1, 0, 1, 0, 1, 0, 1],
                "cum_HML_pct": [1, 0, 1, 0, 1, 0, 1, 0],
                "cum_RMW_pct": [0, 0, 1, 1, 2, 2, 3, 3],
                "cum_CMA_pct": [3, 2, 1, 0, 3, 2, 1, 0],
            }
        )
        result = fit_fama_french_trade_regression(panel)
        self.assertIn("alpha_pct", set(result["term"]))
        self.assertEqual(int(result["factor_result_used_as_trading_trigger_flag"].max()), 0)

    def test_fama_macbeth_uses_entry_safe_features_only(self) -> None:
        rows = []
        for q in ["2024Q1", "2024Q2", "2024Q3"]:
            for i in range(12):
                rows.append(
                    {
                        "lifecycle_id": f"{q}-{i}",
                        "symbol": f"S{i}",
                        "theme_id": "theme",
                        "quarter": q,
                        "return_pct": float(i),
                        "ret_5d_prev": float(i) / 10,
                        "breadth_20d": 0.5 + i / 100,
                        "net_return_from_entry": 999.0,
                    }
                )
        coef_panel, result = fit_fama_macbeth_entry_safe_panel(pd.DataFrame(rows))
        self.assertFalse(coef_panel.empty)
        self.assertNotIn("net_return_from_entry", set(coef_panel["term"]))
        self.assertEqual(int(result["factor_result_used_as_trading_trigger_flag"].max()), 0)


if __name__ == "__main__":
    unittest.main()
