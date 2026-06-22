from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestEntryGates(unittest.TestCase):
    def test_ker_boundary_classification(self) -> None:
        from backtest.entry_gates import EntryGateConfig, evaluate_entry_gate

        frame = pd.DataFrame(
            {
                "ker": [0.3, 0.5, 0.51],
                "volume_percentile": [0.7, 0.7, 0.7],
                "close": [101.0, 102.0, 103.0],
                "daily_sma20": [100.0, 100.0, 100.0],
                "daily_sma50": [99.0, 99.0, 99.0],
            }
        )

        blocked = evaluate_entry_gate(frame, 1, EntryGateConfig(use_ker_gate=True))
        self.assertFalse(blocked.passed)
        self.assertEqual(blocked.ker_regime, "MIXED")

        passed = evaluate_entry_gate(frame, 2, EntryGateConfig(use_ker_gate=True))
        self.assertTrue(passed.passed)
        self.assertEqual(passed.ker_regime, "TREND")

    def test_volume_threshold(self) -> None:
        from backtest.entry_gates import EntryGateConfig, evaluate_entry_gate

        frame = pd.DataFrame(
            {
                "ker": [0.8, 0.8],
                "volume_percentile": [0.59, 0.60],
                "close": [101.0, 102.0],
                "daily_sma20": [100.0, 100.0],
                "daily_sma50": [99.0, 99.0],
            }
        )

        low = evaluate_entry_gate(frame, 0, EntryGateConfig(use_volume_gate=True))
        hit = evaluate_entry_gate(frame, 1, EntryGateConfig(use_volume_gate=True))
        self.assertFalse(low.passed)
        self.assertTrue(hit.passed)

    def test_daily_bias_classification(self) -> None:
        from backtest.entry_gates import EntryGateConfig, evaluate_entry_gate

        frame = pd.DataFrame(
            {
                "ker": [0.8, 0.8],
                "volume_percentile": [0.8, 0.8],
                "close": [90.0, 110.0],
                "daily_sma20": [95.0, 108.0],
                "daily_sma50": [100.0, 100.0],
            }
        )

        bear = evaluate_entry_gate(frame, 0, EntryGateConfig(use_daily_bias_gate=True))
        bull = evaluate_entry_gate(frame, 1, EntryGateConfig(use_daily_bias_gate=True))
        self.assertFalse(bear.passed)
        self.assertEqual(bear.daily_bias, "BEARISH")
        self.assertTrue(bull.passed)
        self.assertEqual(bull.daily_bias, "STRONG_BULLISH")

    def test_prepare_entry_gate_frame_columns(self) -> None:
        from backtest.entry_gates import EntryGateConfig, prepare_entry_gate_frame

        frame = pd.DataFrame(
            {
                "close": [float(100 + i) for i in range(130)],
                "volume": [float(1_000_000 + (i % 7) * 1_000) for i in range(130)],
            }
        )
        enriched = prepare_entry_gate_frame(frame, EntryGateConfig())
        self.assertIn("ker", enriched.columns)
        self.assertIn("volume_percentile", enriched.columns)
        self.assertIn("daily_sma20", enriched.columns)
        self.assertIn("daily_sma50", enriched.columns)
        self.assertTrue(enriched["ker"].notna().any())
        self.assertTrue(enriched["volume_percentile"].notna().any())


if __name__ == "__main__":
    unittest.main()
