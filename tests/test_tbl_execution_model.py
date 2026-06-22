from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestTblExecutionModel(unittest.TestCase):
    def test_limit_fill_and_miss(self) -> None:
        from backtest.tbl_execution import BarExecutionView, resolve_limit_fill

        bar = BarExecutionView(open=101.0, high=103.0, low=99.0, close=102.0, volume=1000)
        fill = resolve_limit_fill(
            side="BUY",
            limit_price=100.0,
            bar=bar,
            requested_quantity=10,
            fee_rate=0.001,
            slippage_bps=10,
            max_volume_participation=1.0,
        )
        self.assertTrue(fill.filled)
        self.assertAlmostEqual(fill.fill_price or 0.0, 100.1)

        miss = resolve_limit_fill(
            side="BUY",
            limit_price=98.0,
            bar=bar,
            requested_quantity=10,
            fee_rate=0.001,
            slippage_bps=10,
            max_volume_participation=1.0,
        )
        self.assertFalse(miss.filled)

    def test_partial_fill_and_same_bar_stop_first(self) -> None:
        from backtest.tbl_execution import BarExecutionView, entry_bar_stop_first, resolve_limit_fill

        bar = BarExecutionView(open=101.0, high=105.0, low=95.0, close=102.0, volume=100)
        fill = resolve_limit_fill(
            side="BUY",
            limit_price=100.0,
            bar=bar,
            requested_quantity=10,
            fee_rate=0.0,
            slippage_bps=0.0,
            max_volume_participation=0.05,
        )
        self.assertTrue(fill.filled)
        self.assertEqual(fill.status, "PARTIAL")
        self.assertEqual(fill.filled_quantity, 5)
        self.assertTrue(entry_bar_stop_first(fill_price=100.0, stop_price=96.0, bar=bar))


if __name__ == "__main__":
    unittest.main()
