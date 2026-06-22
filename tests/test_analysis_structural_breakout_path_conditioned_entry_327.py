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
from src.backtest.analysis_structural_breakout_path_conditioned_entry_327 import (
    _apply_path_labels,
    _attach_probability_metadata,
    _feature_band_edges,
    _feature_regime_path_mapping,
    _joint_feature_path_mapping,
    _metric_band_edges,
)


class TestAnalysisStructuralBreakoutPathConditionedEntry327(unittest.TestCase):
    def test_off_mode_path_probability_filter_reproduces_baseline(self) -> None:
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
            pre_entry_filter=PreEntryFilterConfig(path_probability_filter_mode="off", metadata_lookup={}),
        )
        self.assertEqual(baseline["metrics"]["trade_count"], filtered["metrics"]["trade_count"])
        self.assertEqual(baseline["metrics"]["total_return_pct"], filtered["metrics"]["total_return_pct"])

    def test_path_labeling_produces_all_expected_classes(self) -> None:
        df = pd.DataFrame(
            [
                {"follow_through_3d_pct": 0.12, "follow_through_5d_pct": 0.16, "adverse_excursion_3d_pct": -0.01, "adverse_excursion_5d_pct": -0.02, "post_breakout_retrace_3d_pct": 0.02, "post_breakout_retrace_5d_pct": 0.03},
                {"follow_through_3d_pct": 0.01, "follow_through_5d_pct": 0.02, "adverse_excursion_3d_pct": -0.01, "adverse_excursion_5d_pct": -0.01, "post_breakout_retrace_3d_pct": 0.20, "post_breakout_retrace_5d_pct": 0.18},
                {"follow_through_3d_pct": 0.15, "follow_through_5d_pct": 0.18, "adverse_excursion_3d_pct": -0.11, "adverse_excursion_5d_pct": -0.10, "post_breakout_retrace_3d_pct": 0.08, "post_breakout_retrace_5d_pct": 0.09},
                {"follow_through_3d_pct": 0.02, "follow_through_5d_pct": 0.09, "adverse_excursion_3d_pct": -0.005, "adverse_excursion_5d_pct": -0.006, "post_breakout_retrace_3d_pct": 0.03, "post_breakout_retrace_5d_pct": 0.04},
                {"follow_through_3d_pct": 0.04, "follow_through_5d_pct": 0.06, "adverse_excursion_3d_pct": -0.03, "adverse_excursion_5d_pct": -0.03, "post_breakout_retrace_3d_pct": 0.06, "post_breakout_retrace_5d_pct": 0.07},
            ]
        )
        band_edges = _metric_band_edges(
            pd.DataFrame(
                [
                    {"follow_through_3d_pct": 0.01, "follow_through_5d_pct": 0.02, "mfe_3d_pct": 0.01, "mfe_5d_pct": 0.02, "retrace_3d_pct": 0.02, "retrace_5d_pct": 0.03, "mae_3d_pct": 0.005, "mae_5d_pct": 0.006},
                    {"follow_through_3d_pct": 0.05, "follow_through_5d_pct": 0.07, "mfe_3d_pct": 0.05, "mfe_5d_pct": 0.07, "retrace_3d_pct": 0.06, "retrace_5d_pct": 0.07, "mae_3d_pct": 0.03, "mae_5d_pct": 0.03},
                    {"follow_through_3d_pct": 0.10, "follow_through_5d_pct": 0.15, "mfe_3d_pct": 0.10, "mfe_5d_pct": 0.15, "retrace_3d_pct": 0.15, "retrace_5d_pct": 0.16, "mae_3d_pct": 0.10, "mae_5d_pct": 0.10},
                ]
            )
        )
        labeled = _apply_path_labels(df, band_edges)
        self.assertEqual(set(labeled["path_type"]), {"strong_continuation", "early_failure", "volatile_noise", "slow_grind", "weak_continuation"})

    def test_feature_and_joint_mapping_are_non_empty(self) -> None:
        df = pd.DataFrame(
            [
                {"regime_state": "r1", "path_type": "strong_continuation", "realized_R": 1.0, "rs_percentile_20d": 0.9, "sector_breadth": 0.8, "dist_to_sma200_pct": 0.2, "ret_20d_pre": 0.15, "vol_contraction_ratio": 0.8, "breakout_strength_pct": 0.03},
                {"regime_state": "r1", "path_type": "early_failure", "realized_R": -1.0, "rs_percentile_20d": 0.2, "sector_breadth": 0.3, "dist_to_sma200_pct": 0.05, "ret_20d_pre": 0.01, "vol_contraction_ratio": 1.2, "breakout_strength_pct": 0.01},
                {"regime_state": "r2", "path_type": "weak_continuation", "realized_R": 0.2, "rs_percentile_20d": 0.5, "sector_breadth": 0.5, "dist_to_sma200_pct": 0.1, "ret_20d_pre": 0.05, "vol_contraction_ratio": 1.0, "breakout_strength_pct": 0.02},
                {"regime_state": "r2", "path_type": "volatile_noise", "realized_R": -0.3, "rs_percentile_20d": 0.7, "sector_breadth": 0.6, "dist_to_sma200_pct": 0.18, "ret_20d_pre": 0.12, "vol_contraction_ratio": 1.3, "breakout_strength_pct": 0.04},
            ]
        )
        edges = _feature_band_edges(df, ["rs_percentile_20d", "sector_breadth", "dist_to_sma200_pct", "ret_20d_pre", "vol_contraction_ratio", "breakout_strength_pct"])
        for feature, (low, high) in edges.items():
            df[f"{feature}_band"] = pd.to_numeric(df[feature], errors="coerce").map(lambda value: "unknown" if pd.isna(value) else ("low" if value <= low else "high" if value >= high else "mid"))
        feature_mapping = _feature_regime_path_mapping(df)
        joint_mapping = _joint_feature_path_mapping(df, feature_mapping)
        self.assertFalse(feature_mapping.empty)
        self.assertFalse(joint_mapping.empty)

    def test_weighted_probability_metadata_prefers_joint_signal(self) -> None:
        metadata = {
            "AAA|2026-01-02": {
                "regime_state": "r1",
                "rs_percentile_20d_band": "high",
                "dist_to_sma200_pct_band": "high",
                "sector_breadth_band": "low",
                "vol_contraction_ratio_band": "low",
                "ret_20d_pre_band": "mid",
                "breakout_strength_pct_band": "mid",
            }
        }
        single_lookup = {
            ("rs_percentile_20d", "high", "r1", "strong_continuation"): 0.4,
            ("dist_to_sma200_pct", "high", "r1", "strong_continuation"): 0.4,
            ("sector_breadth", "low", "r1", "early_failure"): 0.4,
            ("vol_contraction_ratio", "low", "r1", "early_failure"): 0.4,
        }
        joint_lookup = {
            ("rs_extension", "rs_high__dist_high", "r1", "strong_continuation"): 0.9,
            ("breadth_vol", "breadth_low__vol_low", "r1", "early_failure"): 0.1,
        }
        prior = {"strong_continuation": 0.2, "weak_continuation": 0.2, "early_failure": 0.2, "volatile_noise": 0.2, "slow_grind": 0.2}
        scored = _attach_probability_metadata(metadata, single_lookup, joint_lookup, prior)
        self.assertEqual(scored["AAA|2026-01-02"]["expected_path"], "strong_continuation")

    def test_probability_rule_engine_applies_skip_and_reduce(self) -> None:
        metadata = {
            "AAA|2026-01-02": {"prob_early_failure": 0.7, "prob_volatile_noise": 0.1, "prob_strong_continuation": 0.2},
            "BBB|2026-01-02": {"prob_early_failure": 0.1, "prob_volatile_noise": 0.6, "prob_strong_continuation": 0.2},
        }
        config = PreEntryFilterConfig(
            path_probability_filter_mode="rules",
            path_probability_rules=(
                {"rule_id": "early_failure_skip", "probability_key": "prob_early_failure", "operator": "gt", "threshold": 0.6, "action": "skip", "size_multiplier": 0.0},
                {"rule_id": "volatile_noise_reduce", "probability_key": "prob_volatile_noise", "operator": "gt", "threshold": 0.5, "action": "reduce", "size_multiplier": 0.5},
            ),
            metadata_lookup=metadata,
        )
        decision_a = _pre_entry_decision("AAA", pd.Timestamp("2026-01-02", tz="UTC"), config)
        decision_b = _pre_entry_decision("BBB", pd.Timestamp("2026-01-02", tz="UTC"), config)
        self.assertEqual(decision_a["action"], "skip")
        self.assertEqual(decision_b["action"], "reduce")
        self.assertAlmostEqual(float(decision_b["size_multiplier"]), 0.5)


if __name__ == "__main__":
    unittest.main()
