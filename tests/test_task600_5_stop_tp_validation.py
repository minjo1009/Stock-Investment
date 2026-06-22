from __future__ import annotations

import unittest

import pandas as pd

from src.execution.stop_tp_validation import StopTpRules, build_runtime_price_evidence, validate_stop_tp_lifecycle


class Task6005StopTpValidationTest(unittest.TestCase):
    def test_stop_tp_and_timeout_are_detected_with_fresh_runtime_atr(self) -> None:
        lifecycle = pd.DataFrame(
            [
                self._position("life-stop", "MSFT"),
                self._position("life-tp", "AMD"),
                self._position("life-timeout", "AMZN"),
            ]
        )
        prices = pd.DataFrame(
            [
                {"symbol": "MSFT", "source_price": 95.0, "source_price_ts": "2026-06-03T13:10:00Z"},
                {"symbol": "AMD", "source_price": 108.5, "source_price_ts": "2026-06-03T13:20:00Z"},
                {"symbol": "AMZN", "source_price": 101.0, "source_price_ts": "2026-06-03T19:31:00Z"},
            ]
        )

        artifacts = validate_stop_tp_lifecycle(lifecycle, prices, rules=StopTpRules(timeout_minutes=390))
        summary = artifacts["stop_tp_validation_summary"].iloc[0]
        detail = artifacts["stop_tp_validation_detail"]

        self.assertEqual(summary["acceptance_status"], "PASS")
        self.assertEqual(int(summary["stop_count"]), 1)
        self.assertEqual(int(summary["tp_count"]), 1)
        self.assertEqual(int(summary["timeout_count"]), 1)
        self.assertEqual(summary["exit_distribution"], "STOP=1;TP=1;TIMEOUT=1")
        self.assertEqual(set(detail["validation_exit_reason"]), {"STOP", "TP", "TIMEOUT"})
        self.assertEqual(int(detail["source_blocked_flag"].sum()), 0)
        self.assertEqual(int(detail["proximity_fallback_used_flag"].sum()), 0)

    def test_missing_atr_blocks_stop_tp_without_approximating(self) -> None:
        lifecycle = pd.DataFrame(
            [
                {
                    "position_id": "life-no-atr",
                    "symbol": "MSFT",
                    "entry_order_id": "entry-order",
                    "entry_fill_id": "entry-fill",
                    "entry_time": "2026-06-03T13:00:00Z",
                    "entry_price": 100.0,
                    "entry_qty": 1.0,
                    "closed_qty": 1.0,
                    "exit_time": "2026-06-03T19:31:00Z",
                    "exit_price": 101.0,
                    "exit_reason": "TIMEOUT",
                    "state": "CLOSED",
                }
            ]
        )
        prices = pd.DataFrame(
            [
                {"symbol": "MSFT", "source_price": 90.0, "source_price_ts": "2026-06-03T13:10:00Z"},
                {"symbol": "MSFT", "source_price": 101.0, "source_price_ts": "2026-06-03T19:31:00Z"},
            ]
        )

        artifacts = validate_stop_tp_lifecycle(lifecycle, prices, rules=StopTpRules(timeout_minutes=390))
        summary = artifacts["stop_tp_validation_summary"].iloc[0]
        detail = artifacts["stop_tp_validation_detail"].iloc[0]

        self.assertEqual(summary["acceptance_status"], "FAIL")
        self.assertEqual(summary["decision_status"], "FAIL_STOP_TP_ZERO_SOURCE_BLOCKED")
        self.assertEqual(int(summary["stop_count"]), 0)
        self.assertEqual(int(summary["tp_count"]), 0)
        self.assertEqual(int(summary["timeout_count"]), 1)
        self.assertEqual(int(summary["source_blocked_count"]), 1)
        self.assertEqual(detail["validation_exit_reason"], "TIMEOUT")
        self.assertEqual(detail["atr_status"], "ATR_SOURCE_MISSING_NO_APPROXIMATION")

    def test_stale_atr_status_blocks_stop_tp_even_when_price_crosses_threshold(self) -> None:
        lifecycle = pd.DataFrame(
            [
                {
                    **self._position("life-stale", "AMD"),
                    "atr_status": "STALE_INTRADAY_BAR_SOURCE_BEFORE_ENTRY",
                }
            ]
        )
        prices = pd.DataFrame(
            [
                {"symbol": "AMD", "source_price": 108.5, "source_price_ts": "2026-06-03T13:20:00Z"},
                {"symbol": "AMD", "source_price": 101.0, "source_price_ts": "2026-06-03T19:31:00Z"},
            ]
        )

        artifacts = validate_stop_tp_lifecycle(lifecycle, prices, rules=StopTpRules(timeout_minutes=390))
        summary = artifacts["stop_tp_validation_summary"].iloc[0]
        detail = artifacts["stop_tp_validation_detail"].iloc[0]

        self.assertEqual(summary["acceptance_status"], "FAIL")
        self.assertEqual(int(summary["tp_count"]), 0)
        self.assertEqual(int(summary["source_blocked_count"]), 1)
        self.assertEqual(int(summary["atr_source_stale_count"]), 1)
        self.assertEqual(detail["atr_status"], "STALE_INTRADAY_BAR_SOURCE_BEFORE_ENTRY")
        self.assertEqual(detail["validation_exit_reason"], "TIMEOUT")

    def test_market_bars_supply_runtime_atr_without_position_atr_column(self) -> None:
        lifecycle = pd.DataFrame(
            [
                {
                    "position_id": "life-bars",
                    "symbol": "MSFT",
                    "entry_order_id": "entry-order",
                    "entry_fill_id": "entry-fill",
                    "entry_time": "2026-06-03T14:15:00Z",
                    "entry_price": 100.0,
                    "entry_qty": 1.0,
                    "closed_qty": 1.0,
                    "exit_time": "2026-06-03T20:45:00Z",
                    "exit_price": 95.0,
                    "exit_reason": "TIMEOUT",
                    "state": "CLOSED",
                }
            ]
        )
        bars = pd.DataFrame(
            [
                {
                    "bar_id": f"bar-{idx}",
                    "symbol": "MSFT",
                    "bar_end_ts": f"2026-06-03T{13 + (idx // 12):02d}:{(idx % 12) * 5:02d}:00Z",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "source": "runtime_5m_bar",
                }
                for idx in range(15)
            ]
            + [
                {
                    "bar_id": "bar-stop",
                    "symbol": "MSFT",
                    "bar_end_ts": "2026-06-03T14:20:00Z",
                    "open": 100.0,
                    "high": 100.0,
                    "low": 95.0,
                    "close": 95.0,
                    "source": "runtime_5m_bar",
                }
            ]
        )
        price_evidence = build_runtime_price_evidence(market_bars_5m=bars)

        artifacts = validate_stop_tp_lifecycle(lifecycle, price_evidence, rules=StopTpRules(timeout_minutes=390))
        summary = artifacts["stop_tp_validation_summary"].iloc[0]
        detail = artifacts["stop_tp_validation_detail"].iloc[0]

        self.assertEqual(int(summary["source_blocked_count"]), 0)
        self.assertEqual(int(summary["stop_count"]), 1)
        self.assertEqual(detail["atr_status"], "ATR_FROM_RUNTIME_PRICE_EVIDENCE")
        self.assertGreater(float(detail["atr"]), 0.0)

    def _position(self, position_id: str, symbol: str) -> dict[str, object]:
        return {
            "position_id": position_id,
            "symbol": symbol,
            "entry_order_id": f"{position_id}-entry-order",
            "entry_fill_id": f"{position_id}-entry-fill",
            "entry_time": "2026-06-03T13:00:00Z",
            "entry_price": 100.0,
            "entry_qty": 1.0,
            "open_qty": 1.0,
            "closed_qty": 0.0,
            "state": "OPEN",
            "atr": 2.0,
        }


if __name__ == "__main__":
    unittest.main()
