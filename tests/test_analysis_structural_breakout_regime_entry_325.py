from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    PreEntryFilterConfig,
    StructuralConfig,
    _prepare_preloaded_frames,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_regime_entry_325 import (
    DUAL_MAP_FRAME,
    _apply_outcome_groups,
    _score_entry_quality_for_metadata,
    _variant_pre_entry_filter,
)


class TestAnalysisStructuralBreakoutRegimeEntry325(unittest.TestCase):
    def test_off_mode_pre_entry_filter_reproduces_baseline(self) -> None:
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
        filtered = run_structural_backtest(
            cfg,
            base_dir,
            preloaded_frames=frames,
            preloaded_timestamps=timestamps,
            preloaded_symbols=symbols,
            pre_entry_filter=PreEntryFilterConfig(regime_filter_mode="off", entry_quality_filter_mode="off", metadata_lookup={}),
        )
        self.assertEqual(baseline["metrics"]["trade_count"], filtered["metrics"]["trade_count"])
        self.assertEqual(baseline["metrics"]["total_return_pct"], filtered["metrics"]["total_return_pct"])

    def test_score_entry_quality_assigns_bands(self) -> None:
        metadata = {
            "AAA|2026-01-02": {"dist_to_sma20_pct": 0.01, "vol_contraction_ratio": 0.7, "recent_failed_breakouts_20d": 0.0},
            "BBB|2026-01-02": {"dist_to_sma20_pct": 0.03, "vol_contraction_ratio": 1.0, "recent_failed_breakouts_20d": 1.0},
            "CCC|2026-01-02": {"dist_to_sma20_pct": 0.08, "vol_contraction_ratio": 1.4, "recent_failed_breakouts_20d": 3.0},
        }
        separation = pd.DataFrame(
            [
                {"feature": "dist_to_sma20_pct", "direction": "lower_is_better"},
                {"feature": "vol_contraction_ratio", "direction": "lower_is_better"},
                {"feature": "recent_failed_breakouts_20d", "direction": "lower_is_better"},
            ]
        )
        scored, bands = _score_entry_quality_for_metadata(metadata, separation)
        self.assertIn("low", bands)
        self.assertIn("high", bands)
        self.assertEqual(scored["AAA|2026-01-02"]["entry_quality_band"], "high")
        self.assertEqual(scored["CCC|2026-01-02"]["entry_quality_band"], "low")

    def test_outcome_groups_split_expected_rows(self) -> None:
        df = pd.DataFrame({"realized_R": [-3, -1, -0.5, 0.2, 0.7, 1.0, 2.0, 3.0, 4.0, 5.0]})
        grouped = _apply_outcome_groups(df)
        self.assertEqual(int((grouped["outcome_group"] == "winners").sum()), 3)
        self.assertEqual(int((grouped["outcome_group"] == "losers").sum()), 3)
        self.assertTrue(grouped["is_best_decile"].any())
        self.assertTrue(grouped["is_worst_decile"].any())

    def test_variant_pre_entry_filter_modes(self) -> None:
        config = _variant_pre_entry_filter(
            "regime_plus_entry_filter",
            metadata_lookup={"AAA|2026-01-02": {}},
            entry_bands={"low": 0.3, "high": 1.3},
            bad_regimes=["failed_recovery"],
            weak_regimes=["rebound_chop"],
        )
        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.regime_filter_mode, "diagnostic_filter")
        self.assertEqual(config.entry_quality_filter_mode, "diagnostic_filter")

    def test_dual_map_frame_exists_for_validation_bands(self) -> None:
        self.assertTrue(Path(DUAL_MAP_FRAME).exists())


if __name__ == "__main__":
    unittest.main()
