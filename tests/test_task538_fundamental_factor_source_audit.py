from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.build_task538_fundamental_factor_source_audit import (
    build_cik_coverage,
    build_factor_readiness,
    extract_concept_availability,
)


class Task538FundamentalFactorSourceAuditTest(unittest.TestCase):
    def test_cik_coverage_flags_missing_symbols(self) -> None:
        cik_map = pd.DataFrame({"symbol": ["AAPL"], "cik10": ["0000320193"], "title": ["Apple Inc."]})
        coverage = build_cik_coverage(["AAPL", "NOPE"], cik_map)
        self.assertEqual(int(coverage[coverage["symbol"].eq("AAPL")]["cik_available_flag"].iloc[0]), 1)
        self.assertEqual(int(coverage[coverage["symbol"].eq("NOPE")]["cik_available_flag"].iloc[0]), 0)

    def test_concept_availability_extracts_us_gaap_facts(self) -> None:
        payload = {
            "facts": {
                "us-gaap": {
                    "Assets": {"units": {"USD": [{"val": 1}, {"val": 2}]}},
                    "NetIncomeLoss": {"units": {"USD": [{"val": 3}]}},
                }
            }
        }
        row = extract_concept_availability("AAPL", "0000320193", payload)
        self.assertEqual(int(row["assets_available_flag"]), 1)
        self.assertEqual(int(row["net_income_available_flag"]), 1)
        self.assertEqual(int(row["equity_available_flag"]), 0)

    def test_factor_readiness_does_not_approximate_market_cap_or_revisions(self) -> None:
        concepts = pd.DataFrame(
            [
                {
                    "assets_available_flag": 1,
                    "equity_available_flag": 1,
                    "net_income_available_flag": 1,
                    "operating_income_available_flag": 0,
                }
            ]
        )
        readiness = build_factor_readiness(concepts)
        size = readiness[readiness["factor_name"].eq("size_market_cap")].iloc[0]
        revision = readiness[readiness["factor_name"].eq("earnings_revision")].iloc[0]
        self.assertEqual(int(size["current_available_flag"]), 0)
        self.assertEqual(str(size["blocked_reason"]), "market_cap_raw_source_missing")
        self.assertEqual(int(revision["current_available_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
