from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestGoldenS4KisRealistic(unittest.TestCase):
    def test_golden_regression_s4_kis_realistic(self) -> None:
        from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
        from backtest.engine_full import run_full_backtest_universe, summarize

        results = run_full_backtest_universe(
            symbols=list(DEFAULT_US_UNIVERSE),
            base_dir=DEFAULT_BASE_DIR,
            initial_equity=100_000.0,
            fee_rate=0.0025,
            slippage_rate=0.001,
            entry_policy="LIMITED_CHASE",
            risk_policy="BASELINE",
        )
        summary = summarize(results, initial_equity=100_000.0)

        self.assertEqual(summary.trade_count, 182)
        self.assertAlmostEqual(summary.profit_factor, 1.0834642819511264, places=9)
        self.assertAlmostEqual(summary.net_pnl, 4582.873640776714, places=6)
        self.assertAlmostEqual(summary.max_drawdown, 9885.240817217753, places=6)
        self.assertAlmostEqual(summary.sharpe_ratio, 0.38926634377514224, places=9)


if __name__ == "__main__":
    unittest.main()
