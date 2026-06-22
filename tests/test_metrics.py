from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@dataclass
class TradeStub:
    actual_pnl: float


@dataclass
class ResultStub:
    trade: TradeStub
    net_pnl: float
    regime: str = "BULL"
    metadata: dict[str, object] | None = None


class TestMetrics(unittest.TestCase):
    def test_profit_factor_mdd_sharpe_win_rate(self) -> None:
        from analytics.metrics import summarize_full_results

        results = [
            ResultStub(trade=TradeStub(actual_pnl=100.0), net_pnl=100.0),
            ResultStub(trade=TradeStub(actual_pnl=-50.0), net_pnl=-50.0),
            ResultStub(trade=TradeStub(actual_pnl=30.0), net_pnl=30.0),
            ResultStub(trade=TradeStub(actual_pnl=-20.0), net_pnl=-20.0),
        ]

        summary = summarize_full_results(results, initial_equity=1_000.0)
        self.assertEqual(summary.trade_count, 4)
        self.assertAlmostEqual(summary.total_pnl, 60.0, places=9)
        self.assertAlmostEqual(summary.net_pnl, 60.0, places=9)
        self.assertAlmostEqual(summary.win_rate, 50.0, places=9)
        self.assertAlmostEqual(summary.profit_factor, 130.0 / 70.0, places=12)
        self.assertAlmostEqual(summary.max_drawdown, 50.0, places=9)
        self.assertGreater(summary.sharpe_ratio, 0.0)


if __name__ == "__main__":
    unittest.main()
