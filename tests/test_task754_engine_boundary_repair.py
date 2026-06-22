from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestTask754EngineBoundaryRepair(unittest.TestCase):
    def test_engine_source_no_longer_reads_next_open_during_signal_generation(self) -> None:
        import backtest.engine as engine

        source = inspect.getsource(engine)
        self.assertNotIn("next_open", source)
        self.assertNotIn("opens[i + 1]", source)

    def test_entry_gap_is_execution_bar_calculation(self) -> None:
        from backtest.engine import _entry_execution_gap_pct

        self.assertAlmostEqual(
            _entry_execution_gap_pct(open_price=103.0, signal_close=100.0),
            0.03,
            places=12,
        )

    def test_pending_exit_next_open_proxy_resolves_on_execution_bar(self) -> None:
        from backtest.engine import PendingExitOrder, _pending_exit_execution_price

        pending_exit = PendingExitOrder(
            signal_index=10,
            signal_time=__import__("datetime").datetime(2026, 1, 1),
            start_index=11,
            limit_price=None,
            exit_rule="TIME_EXIT",
        )

        self.assertEqual(
            _pending_exit_execution_price(pending_exit=pending_exit, open_price=101.25),
            101.25,
        )

    def test_canonical_lifecycle_writer_is_lazy_imported(self) -> None:
        sys.modules.pop("backtest.canonical_position_lifecycle_event_sourcing", None)
        sys.modules.pop("state.store", None)

        import backtest.engine  # noqa: F401

        self.assertNotIn("backtest.canonical_position_lifecycle_event_sourcing", sys.modules)
        self.assertNotIn("state.store", sys.modules)


if __name__ == "__main__":
    unittest.main()
