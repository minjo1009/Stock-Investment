from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestTask753W2BacktestCoreBoundary(unittest.TestCase):
    def test_quick_loader_missing_raw_data_does_not_create_sample_by_default(self) -> None:
        from backtest.data_loader import load_bars_for_quick_backtest

        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                load_bars_for_quick_backtest(symbol="AAPL", base_dir=Path(td))

    def test_quick_loader_sample_fallback_requires_explicit_opt_in(self) -> None:
        from backtest.data_loader import load_bars_for_quick_backtest

        with tempfile.TemporaryDirectory() as td:
            bars = load_bars_for_quick_backtest(
                symbol="AAPL",
                base_dir=Path(td),
                years=1,
                allow_sample_fallback=True,
            )

        self.assertGreater(len(bars), 0)

    def test_w0_backtest_namespace_does_not_export_models(self) -> None:
        import backtest

        self.assertEqual(backtest.__all__, [])
        self.assertFalse(hasattr(backtest, "TradeResult"))

    def test_state_contract_is_separate_from_sqlite_store(self) -> None:
        from state.interface import StateStorePort

        self.assertEqual(StateStorePort.__name__, "StateStorePort")


if __name__ == "__main__":
    unittest.main()
