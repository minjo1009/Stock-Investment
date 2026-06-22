from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestTblLifecycle(unittest.TestCase):
    def _position(self):
        from strategy.lifecycle import initialize_lifecycle_position

        return initialize_lifecycle_position(
            lifecycle_id="TBL-TEST",
            symbol="NVDA",
            entry_index=10,
            entry_price=100.0,
            initial_stop_price=90.0,
            initial_quantity=5,
            target_quantity=10,
        )

    def test_initial_r_is_fixed_after_add(self) -> None:
        from strategy.lifecycle import apply_add

        pos = self._position()
        added = apply_add(pos, add_price=112.0, add_quantity=5)
        self.assertEqual(pos.initial_r, 10.0)
        self.assertEqual(added.initial_r, 10.0)
        self.assertNotEqual(added.average_price, pos.average_price)

    def test_add_and_partial_are_idempotent(self) -> None:
        from strategy.lifecycle import apply_add, apply_partial_take_profit, should_add_position, should_take_partial_profit

        pos = self._position()
        self.assertTrue(should_add_position(pos, 110.0))
        added = apply_add(pos, add_price=110.0, add_quantity=5)
        self.assertFalse(should_add_position(added, 125.0))
        self.assertTrue(should_take_partial_profit(added, 120.0))
        partial = apply_partial_take_profit(added, exit_price=120.0, exit_quantity=5)
        self.assertFalse(should_take_partial_profit(partial, 130.0))
        self.assertTrue(partial.runner)

    def test_trailing_stop_only_moves_up_and_time_exit(self) -> None:
        from strategy.lifecycle import apply_partial_take_profit, should_exit_position, update_trailing_stop

        pos = apply_partial_take_profit(self._position(), exit_price=120.0, exit_quantity=2)
        first = update_trailing_stop(pos, close_price=130.0, atr=5.0, multiplier=3.0)
        second = update_trailing_stop(first, close_price=125.0, atr=5.0, multiplier=3.0)
        self.assertEqual(first.trailing_stop, second.trailing_stop)
        exit_now, reason = should_exit_position(second, low_price=200.0, current_index=31, max_holding_bars=20)
        self.assertTrue(exit_now)
        self.assertEqual(reason, "TIME_EXIT")


if __name__ == "__main__":
    unittest.main()
