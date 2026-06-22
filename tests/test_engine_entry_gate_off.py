from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestEngineEntryGateOff(unittest.TestCase):
    def test_gate_disabled_is_backward_compatible(self) -> None:
        from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
        from backtest.engine_full import run_full_backtest_universe_with_stats, summarize
        from backtest.entry_gates import EntryGateConfig

        symbol = list(DEFAULT_US_UNIVERSE)[0]
        kwargs = {
            "symbols": [symbol],
            "base_dir": DEFAULT_BASE_DIR,
            "initial_equity": 100_000.0,
            "fee_rate": 0.0025,
            "slippage_rate": 0.0010,
            "entry_policy": "LIMITED_CHASE",
            "risk_policy": "BASELINE",
        }

        results_default, stats_default = run_full_backtest_universe_with_stats(**kwargs)
        results_disabled, stats_disabled = run_full_backtest_universe_with_stats(
            **kwargs,
            entry_gate_config=EntryGateConfig.disabled(),
        )

        summary_default = summarize(results_default, initial_equity=100_000.0)
        summary_disabled = summarize(results_disabled, initial_equity=100_000.0)
        self.assertEqual(summary_default.trade_count, summary_disabled.trade_count)
        self.assertAlmostEqual(summary_default.net_pnl, summary_disabled.net_pnl, places=9)
        self.assertEqual(stats_default.skipped_by_gate, 0)
        self.assertEqual(stats_disabled.skipped_by_gate, 0)


if __name__ == "__main__":
    unittest.main()
