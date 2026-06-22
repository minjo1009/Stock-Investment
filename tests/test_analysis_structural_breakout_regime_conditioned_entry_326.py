from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    PreEntryFilterConfig,
    StructuralConfig,
    _pre_entry_decision,
    _prepare_preloaded_frames,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_regime_conditioned_entry_326 import (
    _extract_regime_conditioned_rules,
    _feature_regime_direction,
)


class TestAnalysisStructuralBreakoutRegimeConditionedEntry326(unittest.TestCase):
    def test_off_mode_regime_conditioned_filter_reproduces_baseline(self) -> None:
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
            pre_entry_filter=PreEntryFilterConfig(regime_conditioned_filter_mode="off", metadata_lookup={}),
        )
        self.assertEqual(baseline["metrics"]["trade_count"], filtered["metrics"]["trade_count"])
        self.assertEqual(baseline["metrics"]["total_return_pct"], filtered["metrics"]["total_return_pct"])

    def test_pre_entry_decision_applies_band_rules(self) -> None:
        metadata = {
            "AAA|2026-01-02": {
                "regime_state": "failed_recovery",
                "dist_to_sma200_pct_band": "high",
                "rs_percentile_20d_band": "mid",
            }
        }
        config = PreEntryFilterConfig(
            regime_conditioned_filter_mode="rules",
            regime_conditioned_rules=(
                {
                    "rule_id": "failed_recovery_skip_dist_high",
                    "regime_state": "failed_recovery",
                    "action": "skip",
                    "size_multiplier": 0.0,
                    "conditions": (
                        {"feature": "dist_to_sma200_pct", "operator": "band_in", "values": ("high",)},
                    ),
                },
            ),
            metadata_lookup=metadata,
        )
        decision = _pre_entry_decision("AAA", pd.Timestamp("2026-01-02", tz="UTC"), config)
        self.assertEqual(decision["action"], "skip")
        self.assertIn("rule:failed_recovery_skip_dist_high", decision["reasons"])

    def test_rule_extraction_emits_skip_rule_for_negative_band(self) -> None:
        interaction_df = pd.DataFrame(
            [
                {"regime_state": "failed_recovery", "feature": "dist_to_sma200_pct", "feature_band": "high", "trade_count": 8, "expectancy_r": -1.2},
                {"regime_state": "failed_recovery", "feature": "dist_to_sma200_pct", "feature_band": "low", "trade_count": 7, "expectancy_r": 0.3},
                {"regime_state": "failed_recovery", "feature": "ret_20d_pre", "feature_band": "mid", "trade_count": 6, "expectancy_r": -0.1},
                {"regime_state": "failed_recovery", "feature": "ret_20d_pre", "feature_band": "low", "trade_count": 6, "expectancy_r": 0.2},
            ]
        )
        regime_df = pd.DataFrame([{"regime": "failed_recovery", "expectancy_r": -0.4}])
        direction_df = _feature_regime_direction(interaction_df, regime_df)
        rules_df = _extract_regime_conditioned_rules(direction_df)
        self.assertFalse(rules_df.empty)
        self.assertIn("failed_recovery", set(rules_df["regime_state"]))
        self.assertIn("skip", set(rules_df["action"]))


if __name__ == "__main__":
    unittest.main()
