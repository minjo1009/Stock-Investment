from __future__ import annotations

import unittest
from pathlib import Path

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    PostEntryOverlayConfig,
    StructuralConfig,
    _prepare_preloaded_frames,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_exit_size_324 import (
    DUAL_MAP_FRAME,
    _load_validation_bands,
    _variant_overlay,
)


class TestAnalysisStructuralBreakoutExitSize324(unittest.TestCase):
    def test_load_validation_bands_from_task323_output(self) -> None:
        bands = _load_validation_bands(Path(DUAL_MAP_FRAME))
        self.assertIn("follow_through_3d_pct", bands)
        self.assertIn("adverse_excursion_3d_pct", bands)
        self.assertIn("follow_through_5d_pct", bands)
        self.assertIn("post_breakout_retrace_5d_pct", bands)

    def test_variant_overlay_maps_expected_modes(self) -> None:
        bands = {
            "follow_through_3d_pct": {"low": 0.01, "high": 0.05},
            "adverse_excursion_3d_pct": {"low_abs": 0.01, "high_abs": 0.03},
            "follow_through_5d_pct": {"low": 0.02, "high": 0.08},
            "post_breakout_retrace_5d_pct": {"low": 0.05, "high": 0.15},
        }
        overlay = _variant_overlay("exit_plus_size_30", bands)
        self.assertIsNotNone(overlay)
        assert overlay is not None
        self.assertEqual(overlay.post_entry_rule_mode, "exit_plus_size")
        self.assertAlmostEqual(overlay.size_reduction_fraction, 0.3)

    def test_baseline_overlay_mode_reproduces_baseline(self) -> None:
        base_dir = Path(DEFAULT_BASE_DIR)
        symbols = ["AAPL", "AMD", "NVDA"]
        frames, timestamps = _prepare_preloaded_frames(base_dir, symbols)
        cfg = StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=20, atr_multiplier=2.0, max_holding_days=20)
        baseline = run_structural_backtest(
            cfg,
            base_dir,
            preloaded_frames=frames,
            preloaded_timestamps=timestamps,
            preloaded_symbols=symbols,
        )
        overlay_baseline = run_structural_backtest(
            cfg,
            base_dir,
            preloaded_frames=frames,
            preloaded_timestamps=timestamps,
            preloaded_symbols=symbols,
            overlay=PostEntryOverlayConfig(post_entry_rule_mode="baseline", size_reduction_fraction=0.5, validation_bands={}),
        )
        self.assertEqual(baseline["metrics"]["trade_count"], overlay_baseline["metrics"]["trade_count"])
        self.assertEqual(baseline["metrics"]["total_return_pct"], overlay_baseline["metrics"]["total_return_pct"])
        self.assertEqual(
            [float(row["realized_R"]) for row in baseline["trade_log"]],
            [float(row["realized_R"]) for row in overlay_baseline["trade_log"]],
        )


if __name__ == "__main__":
    unittest.main()
