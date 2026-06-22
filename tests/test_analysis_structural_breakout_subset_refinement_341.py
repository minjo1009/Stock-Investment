from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_subset_refinement_341 import (
    MAX_CONDITIONS_PER_CANDIDATE,
    _apply_condition,
    _build_refinement_candidates,
    _condition_specs,
    _size_overlay_test,
    _window_group,
)


class TestAnalysisStructuralBreakoutSubsetRefinement341(unittest.TestCase):
    def test_window_group_is_deterministic_from_sign(self) -> None:
        self.assertEqual(_window_group(0.01), "success_window")
        self.assertEqual(_window_group(0.0), "failure_window")
        self.assertEqual(_window_group(-0.2), "failure_window")

    def test_condition_threshold_uses_train_only_median(self) -> None:
        spec = _condition_specs()["candidate_B"][1]
        train_df = pd.DataFrame({"breakout_bar_close_location": [0.2, 0.4, 0.6, 0.8]})
        eval_df = pd.DataFrame({"breakout_bar_close_location": [0.49, 0.51]})
        mask, threshold = _apply_condition(eval_df, train_df, spec)
        self.assertAlmostEqual(float(threshold), 0.5)
        self.assertEqual(mask.tolist(), [False, True])

    def test_refinement_candidates_are_bounded(self) -> None:
        base_df = pd.DataFrame(
            {
                "current_split": ["train", "train", "anchored_oos", "anchored_oos"],
                "realized_R": [1.0, -1.0, 0.5, -0.5],
                "vwap_response": ["vwap_hold"] * 4,
                "price_vs_session_vwap_at_breakout": [0.1, 0.2, 0.3, 0.4],
                "breakout_response": ["breakout_hold", "immediate_failure", "breakout_hold", "immediate_failure"],
                "breakout_bar_close_location": [0.8, 0.2, 0.9, 0.1],
                "adverse_excursion_next_3bars": [0.1, 0.5, 0.2, 0.6],
                "intraday_pullback_depth_3bars": [0.1, 0.5, 0.2, 0.6],
                "volume_persistence_3bars": [1.5, 0.5, 1.4, 0.6],
                "breakout_window_volume_surge": [2.0, 1.0, 2.1, 0.9],
                "relative_volume_percentile": [0.9, 0.1, 0.8, 0.2],
            }
        )
        window_df = base_df.copy()
        window_df["window_group"] = ["success_window", "failure_window", "success_window", "failure_window"]
        current_train_df = base_df[base_df["current_split"] == "train"].copy()
        candidates = _build_refinement_candidates(window_df, base_df, current_train_df)
        self.assertLessEqual(len(candidates), 3)
        for conditions in candidates["refinement_conditions"].tolist():
            count = 0 if not conditions else len(str(conditions).split(" AND "))
            self.assertLessEqual(count, MAX_CONDITIONS_PER_CANDIDATE)

    def test_size_overlay_is_deterministic(self) -> None:
        base_df = pd.DataFrame(
            {
                "trade_id": ["a", "b", "c"],
                "current_split": ["anchored_oos", "anchored_oos", "anchored_oos"],
                "realized_R": [1.0, -1.0, 0.5],
                "entry_ts": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
                "sector_group": ["software_internet", "semis", "software_internet"],
            }
        )
        refined_df = base_df.iloc[[0, 2]].copy()
        regime_df = pd.DataFrame([{"regime_conditions": "sector_group=software_internet"}])
        overlay = _size_overlay_test(base_df, refined_df, regime_df)
        self.assertEqual(set(overlay["policy_name"]), {"base_subset_only", "refined_binary", "size_overlay"})
        size_row = overlay[overlay["policy_name"] == "size_overlay"].iloc[0]
        self.assertGreater(float(size_row["return_proxy"]), 0.0)


if __name__ == "__main__":
    unittest.main()
