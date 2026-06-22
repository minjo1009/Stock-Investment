from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_intraday_coverage_audit_337 import (
    build_coverage_audit,
    readiness_gate,
)


class IntradayCoverageAudit337Tests(unittest.TestCase):
    def test_coverage_statuses_are_deterministic(self) -> None:
        required = pd.DataFrame(
            [
                {"symbol": "AAPL", "trade_date": "2025-01-02"},
                {"symbol": "AAPL", "trade_date": "2025-01-03"},
                {"symbol": "MSFT", "trade_date": "2025-01-02"},
            ]
        )
        bars = pd.DataFrame(
            [{"symbol": "AAPL", "bar_date": "2025-01-02", "bar_start_ts": "x", "source": "SRC"}] * 60
            + [{"symbol": "AAPL", "bar_date": "2025-01-03", "bar_start_ts": "y", "source": "SRC"}] * 10
        )
        audit = build_coverage_audit(required, bars)
        self.assertEqual(audit["coverage_status"].tolist(), ["covered", "insufficient_window", "missing_symbol"])

    def test_readiness_gate_requires_oos_coverage_per_symbol(self) -> None:
        audit = pd.DataFrame(
            [
                {"symbol": "AAPL", "trade_date": "2025-01-02", "coverage_status": "covered"},
                {"symbol": "MSFT", "trade_date": "2025-01-03", "coverage_status": "missing_date"},
            ]
        )
        oos = pd.DataFrame(
            [
                {"symbol": "AAPL", "entry_date": "2025-01-02", "scope": "anchored_oos", "scenario": "s1"},
                {"symbol": "MSFT", "entry_date": "2025-01-03", "scope": "anchored_oos", "scenario": "s2"},
            ]
        )
        gate = readiness_gate(oos, audit)
        self.assertEqual(gate["task_336_readiness"], "phase_2_incomplete")
        self.assertFalse(gate["anchored_oos_all_symbols_have_coverage"])


if __name__ == "__main__":
    unittest.main()
