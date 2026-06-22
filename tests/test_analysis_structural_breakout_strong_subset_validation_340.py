from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import (
    ROLLING_WINDOWS,
    _apply_cost_to_r,
    _current_subset_mask,
    _engine_integration_spec,
    _rolling_label,
)


class TestAnalysisStructuralBreakoutStrongSubsetValidation340(unittest.TestCase):
    def test_rolling_windows_are_deterministic(self) -> None:
        self.assertEqual(len(ROLLING_WINDOWS), 4)
        self.assertEqual(ROLLING_WINDOWS[0].train_start, "2021-06-01")
        self.assertEqual(ROLLING_WINDOWS[-1].oos_end, "2026-04-30")

    def test_rolling_label_uses_train_thresholds_only(self) -> None:
        train_df = pd.DataFrame(
            {
                "range_width_10_pre": [1.0, 2.0, 3.0, 4.0],
                "vol_contraction_ratio": [0.1, 0.2, 0.3, 0.4],
            }
        )
        eval_df = pd.DataFrame(
            {
                "range_width_10_pre": [2.5, 3.5],
                "vol_contraction_ratio": [0.25, 0.45],
            }
        )
        labeled = _rolling_label(train_df, eval_df)
        self.assertEqual(labeled["atr_regime"].tolist(), ["low_atr", "high_atr"])
        self.assertEqual(labeled["contraction_regime"].tolist(), ["vol_contracting", "vol_expanding"])

    def test_cost_application_is_monotonic(self) -> None:
        df = pd.DataFrame({"realized_R": [1.0, 0.5, -0.2]})
        base = _apply_cost_to_r(df, 0.0, 0.0)
        stressed = _apply_cost_to_r(df, 0.001, 0.0005)
        self.assertTrue((stressed < base).all())

    def test_current_subset_mask_is_fixed(self) -> None:
        df = pd.DataFrame(
            {
                "atr_regime": ["high_atr", "low_atr", "high_atr"],
                "contraction_regime": ["vol_expanding", "vol_expanding", "vol_contracting"],
            }
        )
        self.assertEqual(_current_subset_mask(df).tolist(), [True, False, False])

    def test_engine_integration_spec_marks_no_lookahead(self) -> None:
        spec = _engine_integration_spec()
        self.assertTrue(spec["real_time_available"].all())
        self.assertTrue((~spec["lookahead_risk"]).all())


if __name__ == "__main__":
    unittest.main()
