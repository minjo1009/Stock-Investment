from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@dataclass
class PositionStub:
    stop_price: float
    entry_fill_price: float
    entry_index: int
    max_high_since_entry: float


class TestRiskPolicies(unittest.TestCase):
    def test_stop_hit_condition(self) -> None:
        from risk.policies import evaluate_risk_exit, get_risk_policy

        pos = PositionStub(stop_price=95.0, entry_fill_price=100.0, entry_index=0, max_high_since_entry=104.0)
        decision = evaluate_risk_exit(i=3, close=98.0, low=94.5, position=pos, risk_policy=get_risk_policy("BREAK_EVEN_STOP"))
        self.assertIsNotNone(decision)
        self.assertEqual(decision["kind"], "stop")
        self.assertEqual(decision["stop_price"], 100.0)

    def test_time_stop_condition(self) -> None:
        from risk.policies import evaluate_risk_exit, get_risk_policy

        pos = PositionStub(stop_price=90.0, entry_fill_price=100.0, entry_index=0, max_high_since_entry=101.0)
        decision = evaluate_risk_exit(i=9, close=100.5, low=99.0, position=pos, risk_policy=get_risk_policy("TIME_STOP"))
        self.assertIsNotNone(decision)
        self.assertEqual(decision["kind"], "exit")
        self.assertEqual(decision["rule"], "RISK_TIME_STOP")

    def test_trend_break_2bar_condition(self) -> None:
        from strategy.conditions import is_exit_condition

        frame = pd.DataFrame(
            {
                "close": [100.0, 97.0, 96.0],
                "sma20": [98.0, 98.5, 98.2],
                "ma20": [98.0, 98.5, 98.2],
            }
        )
        self.assertFalse(is_exit_condition(frame, 1))
        self.assertTrue(is_exit_condition(frame, 2))

    def test_state_flag_like_payload_shape(self) -> None:
        from risk.policies import evaluate_risk_exit, get_risk_policy

        pos = PositionStub(stop_price=96.0, entry_fill_price=100.0, entry_index=0, max_high_since_entry=105.0)
        decision = evaluate_risk_exit(i=2, close=100.0, low=97.0, position=pos, risk_policy=get_risk_policy("MFE_GIVEBACK_50"))
        self.assertIsNotNone(decision)
        self.assertIn("kind", decision)
        self.assertIn(decision["kind"], ("stop", "exit"))
        if decision["kind"] == "exit":
            self.assertIn("rule", decision)


if __name__ == "__main__":
    unittest.main()
