from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_conditional_edge_integration_342 import (
    VARIANTS,
    OverlayVariant,
    _assign_multiplier,
    _concentration_share,
    _daily_curve_from_event_returns,
    _drawdown_duration_days,
    _portfolio_metrics,
)


class TestAnalysisStructuralBreakoutConditionalEdgeIntegration342(unittest.TestCase):
    def _sample_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "trade_id": ["a", "b", "c", "d"],
                "symbol": ["AAA", "BBB", "AAA", "CCC"],
                "sector_group": ["software_internet", "semis", "software_internet", "others"],
                "entry_ts": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"], utc=True),
                "exit_ts": pd.to_datetime(["2024-01-05", "2024-01-06", "2024-01-07", "2024-01-08"], utc=True),
                "realized_R": [1.0, -1.0, 2.0, 0.5],
                "is_covered": [True, True, False, True],
                "is_condition_met": [True, False, False, False],
            }
        )

    def test_hybrid_full_uncovered_is_neutral(self) -> None:
        df = self._sample_df()
        variant = OverlayVariant("overlay_2p0_0p5", 2.0, 0.5, 1.0, "primary")
        assigned = _assign_multiplier(df, variant, "hybrid_full")
        self.assertEqual(assigned.loc[assigned["trade_id"] == "c", "size_multiplier"].iloc[0], 1.0)

    def test_filter_skip_zeroes_only_non_condition_covered(self) -> None:
        df = self._sample_df()
        variant = OverlayVariant("filter_skip", 1.0, 0.0, 1.0, "aggressive_filter")
        assigned = _assign_multiplier(df, variant, "hybrid_full")
        self.assertEqual(assigned.loc[assigned["trade_id"] == "b", "size_multiplier"].iloc[0], 0.0)
        self.assertEqual(assigned.loc[assigned["trade_id"] == "c", "size_multiplier"].iloc[0], 1.0)

    def test_baseline_metrics_match_uniform_sizing(self) -> None:
        df = self._sample_df()
        variant = OverlayVariant("baseline_equal", 1.0, 1.0, 1.0, "baseline")
        assigned = _assign_multiplier(df, variant, "hybrid_full")
        metrics = _portfolio_metrics(assigned)
        self.assertEqual(metrics["trade_count"], 4)
        self.assertAlmostEqual(float(assigned["scaled_R"].sum()), 2.5)

    def test_drawdown_duration_and_concentration_are_deterministic(self) -> None:
        df = self._sample_df()
        variant = OverlayVariant("overlay_1p5_0p5", 1.5, 0.5, 1.0, "primary")
        assigned = _assign_multiplier(df, variant, "covered_only")
        daily_curve, _ = _daily_curve_from_event_returns(assigned)
        self.assertGreaterEqual(_drawdown_duration_days(daily_curve), 0)
        share = _concentration_share(assigned, "symbol")
        self.assertGreaterEqual(share, 0.0)
        self.assertLessEqual(share, 1.0)


if __name__ == "__main__":
    unittest.main()
