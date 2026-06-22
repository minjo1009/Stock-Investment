from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_information_layer_expansion_335 import (
    FORBIDDEN_POST_ENTRY_FEATURES,
    PHASE1_FAMILIES,
    _add_train_only_bands,
    _derive_target,
    _diagnostic_overlay,
    _feature_family_ablation,
    _family_definition_rows,
    _holdout_rows_for_group,
    _resolve_feature_set_features,
)


class TestAnalysisStructuralBreakoutInformationLayerExpansion335(unittest.TestCase):
    def _frame(self) -> pd.DataFrame:
        rows = []
        labels = [
            ("dead_breakout", "dead_breakout"),
            ("clean_continuation", "clean_continuation"),
            ("weak_breakout", "weak_breakout"),
            ("uneven_continuation", "uneven_continuation"),
        ]
        for idx in range(60):
            label, base = labels[idx % len(labels)]
            rows.append(
                {
                    "scope": "train",
                    "cluster_label": label,
                    "cluster_label_base": base,
                    "ret_20d_pre": float(idx) / 100.0,
                    "dist_to_sma200_pct": float(idx) / 200.0,
                    "rs_percentile_20d": float((idx % 10) / 10),
                    "sector_breadth": float((idx % 6) / 6),
                    "vol_contraction_ratio": 0.8 + idx / 100.0,
                    "breakout_strength_pct": 0.01 + idx / 1000.0,
                    "extension_pressure_state": "medium",
                    "trend_quality_state": "neutral",
                    "participation_quality_state": "broad" if idx % 2 == 0 else "narrow",
                    "noise_pressure_state": "balanced",
                    "gap_over_planned_entry_pct": float(idx % 5) / 100.0,
                    "pre_breakout_distance_pct": float(idx % 7) / 100.0,
                    "close_location_pre": float(idx % 9) / 10.0,
                    "range_width_10_pre": float(idx % 11) / 100.0,
                    "squeeze_quality": float(idx % 13) / 10.0,
                    "volume_confirmation_pre": float(idx % 4) / 10.0,
                    "dollar_volume_pre": 1_000_000 + idx,
                    "turnover_pre": 10_000 + idx,
                    "breadth_above_sma20": float(idx % 12) / 12.0,
                    "breadth_above_sma50": float(idx % 10) / 10.0,
                    "breadth_positive_20d": float(idx % 8) / 8.0,
                    "dispersion_20d": float(idx % 15) / 10.0,
                    "mean_pairwise_corr": float(idx % 7) / 10.0,
                    "recent_failed_breakouts_20d": float(idx % 3),
                    "top_sector_dominance_score": float(idx % 5) / 5.0,
                    "semis_concentration_ratio": float(idx % 6) / 6.0,
                    "tech_concentration_ratio": float(idx % 7) / 7.0,
                    "sector_crowding_high": bool(idx % 2),
                    "sector_rs_percentile": float(idx % 9) / 9.0,
                    "symbol": "AAPL" if idx < 30 else "MSFT",
                    "sector_bucket": "tech" if idx < 30 else "software",
                    "scenario_family": "RANGE_COMPRESSION",
                    "entry_date": f"2024-01-{(idx % 28) + 1:02d}",
                    "scenario": "s",
                    "trade_id": f"t{idx}",
                    "realized_R": -1.0 if base in {"dead_breakout", "weak_breakout"} else 1.0,
                    "path_type": "early_failure" if base in {"dead_breakout", "weak_breakout"} else "strong_continuation",
                }
            )
        return pd.DataFrame(rows)

    def test_family_definitions_never_include_post_entry_features(self) -> None:
        for features in PHASE1_FAMILIES.values():
            self.assertTrue(set(features).isdisjoint(FORBIDDEN_POST_ENTRY_FEATURES))

    def test_train_only_band_edges_are_reused_on_oos(self) -> None:
        train = self._frame().iloc[:40].copy()
        oos = self._frame().iloc[40:].copy()
        oos.loc[:, "ret_20d_pre"] = 999.0
        full = self._frame().copy()
        train_b, oos_b, _, edges = _add_train_only_bands(train, oos, full, ["ret_20d_pre"])
        self.assertIn("ret_20d_pre", edges)
        self.assertTrue((train_b["ret_20d_pre_task335_band"].isin(["low", "mid", "high"])).all())
        self.assertEqual(str(oos_b["ret_20d_pre_task335_band"].iloc[0]), "high")

    def test_target_derivation_for_rank_is_deterministic(self) -> None:
        df = pd.DataFrame({"cluster_label": ["a"], "cluster_label_base": ["clean_continuation"]})
        self.assertEqual(_derive_target(df, "continuation_quality_rank").iloc[0], 2)

    def test_feature_family_ablation_is_deterministic(self) -> None:
        train = self._frame().copy()
        oos = self._frame().copy()
        oos["scope"] = "anchored_oos"
        full = self._frame().copy()
        full["scope"] = "full_period"
        train_b, oos_b, full_b, _ = _add_train_only_bands(train, oos, full, sorted({f for fs in PHASE1_FAMILIES.values() for f in fs}))
        first = _feature_family_ablation(train_b, oos_b, full_b)
        second = _feature_family_ablation(train_b, oos_b, full_b)
        self.assertTrue(first.equals(second))

    def test_diagnostic_overlay_does_not_mutate_base_frame(self) -> None:
        df = self._frame().iloc[:4].copy()
        original_cols = list(df.columns)
        payload_bad = ("band_probability", ["ret_20d_pre_task335_band"], {"ret_20d_pre_task335_band": {"low": {"1": 1.0}, "mid": {"0": 1.0}, "high": {"0": 1.0}}}, None)
        payload_clean = ("band_probability", ["ret_20d_pre_task335_band"], {"ret_20d_pre_task335_band": {"low": {"0": 1.0}, "mid": {"1": 1.0}, "high": {"0": 1.0}}}, None)
        work, _, _, _ = _add_train_only_bands(df, df, df, ["ret_20d_pre"])
        _, delta_df = _diagnostic_overlay(work, payload_bad, payload_clean, "policy", "train")
        self.assertEqual(list(df.columns), original_cols)
        self.assertIn("diagnostic_adjusted_R", delta_df.columns)

    def test_holdout_rows_mark_insufficient_density(self) -> None:
        df = self._frame().iloc[:20].copy()
        rows = _holdout_rows_for_group(df, "bad_state", "core_only", "band_probability", "symbol", ["ret_20d_pre"])
        self.assertTrue((rows["status"] == "insufficient_density").all() or (rows["status"] == "unavailable").all())

    def test_resolve_feature_set_features_handles_best_aggregate(self) -> None:
        train = self._frame().copy()
        ablation_df = pd.DataFrame(
            [{"feature_set": "core_plus_best_2_families", "selected_best_2_members": "core_plus_market_structure|core_plus_setup_context"}]
        )
        features = _resolve_feature_set_features(train, "core_plus_best_2_families", ablation_df)
        self.assertIn("ret_20d_pre", features)
        self.assertIn("breadth_above_sma20", features)


if __name__ == "__main__":
    unittest.main()
