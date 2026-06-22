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
class PendingEntryStub:
    limit_price: float
    chase_bps: float = 0.0
    market_like: bool = False


class TestExecutionPolicies(unittest.TestCase):
    def test_baseline_fill_condition(self) -> None:
        from execution.policies import resolve_entry_fill_price

        pending = PendingEntryStub(limit_price=100.0)
        filled, fill_price = resolve_entry_fill_price(low=99.0, high=101.0, open_px=100.5, pending=pending)
        self.assertTrue(filled)
        self.assertEqual(fill_price, 100.0)

    def test_baseline_unfilled_condition(self) -> None:
        from execution.policies import resolve_entry_fill_price

        pending = PendingEntryStub(limit_price=100.0)
        filled, fill_price = resolve_entry_fill_price(low=100.2, high=101.0, open_px=100.6, pending=pending)
        self.assertFalse(filled)
        self.assertIsNone(fill_price)

    def test_limited_chase_fill_condition(self) -> None:
        from execution.policies import get_entry_policy, resolve_entry_fill_price

        policy = get_entry_policy("LIMITED_CHASE")
        pending = PendingEntryStub(limit_price=100.0, chase_bps=float(policy["chase_bps"]))
        filled, fill_price = resolve_entry_fill_price(low=100.25, high=100.50, open_px=100.30, pending=pending)
        self.assertTrue(filled)
        self.assertAlmostEqual(fill_price, 100.30, places=6)

    def test_expired_and_max_wait_bars_behavior(self) -> None:
        from execution.policies import get_entry_policy

        policy = get_entry_policy("BASELINE")
        wait_bars = int(policy["wait_bars"])
        self.assertEqual(wait_bars, 3)

        pending_wait = 0
        expired = False
        for _ in range(wait_bars):
            pending_wait += 1
            if pending_wait > wait_bars:
                expired = True

        self.assertFalse(expired)
        pending_wait += 1
        if pending_wait > wait_bars:
            expired = True
        self.assertTrue(expired)


if __name__ == "__main__":
    unittest.main()
