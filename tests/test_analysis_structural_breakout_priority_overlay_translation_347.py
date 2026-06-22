from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_priority_overlay_translation_347 import (
    SIZE_OVERLAY_50,
    _condition_mask,
    _priority_eligible,
    _sector_cap_limit,
    _select_group,
    _select_universe,
    _sort_candidates,
)


class TestAnalysisStructuralBreakoutPriorityOverlayTranslation347(unittest.TestCase):
    def _sample_group(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "trade_id": ["a", "b", "c", "d"],
                "symbol": ["AAA", "BBB", "CCC", "DDD"],
                "sector_group": ["software_internet", "software_internet", "semis", "others"],
                "entry_day": ["2024-01-02"] * 4,
                "entry_ts": pd.to_datetime(
                    ["2024-01-02T14:30:00Z", "2024-01-02T14:30:00Z", "2024-01-02T14:30:00Z", "2024-01-02T14:30:00Z"],
                    utc=True,
                ),
                "exit_ts": pd.to_datetime(
                    ["2024-01-05T14:30:00Z", "2024-01-05T14:30:00Z", "2024-01-05T14:30:00Z", "2024-01-05T14:30:00Z"],
                    utc=True,
                ),
                "realized_R": [1.0, -0.5, 0.8, 0.2],
                "is_covered": [True, True, True, False],
                "baseline_momentum": [0.10, 0.08, 0.06, 0.02],
                "baseline_avg_dollar_volume": [40_000_000, 35_000_000, 30_000_000, 20_000_000],
                "baseline_volatility": [0.03, 0.02, 0.01, 0.04],
                "is_high_atr": [True, True, False, False],
                "is_vol_expanding": [True, False, True, False],
                "is_entry_only_component": [True, True, True, False],
                "is_software_internet_component": [True, True, False, False],
                "priority_score": [4, 3, 2, 0],
            }
        )

    def test_priority_sort_is_deterministic(self) -> None:
        ranked = _sort_candidates(self._sample_group(), by_priority=True)
        self.assertEqual(ranked["trade_id"].tolist()[:3], ["a", "b", "c"])

    def test_sector_cap_limit_uses_floor_with_min_one(self) -> None:
        self.assertEqual(_sector_cap_limit(3, "30"), 1)
        self.assertEqual(_sector_cap_limit(5, "50"), 2)
        self.assertIsNone(_sector_cap_limit(10, "none"))

    def test_priority_threshold_bucket_filters_expected_rows(self) -> None:
        eligible = _priority_eligible(self._sample_group(), "priority_threshold_ge_3")
        self.assertEqual(eligible["trade_id"].tolist(), ["a", "b"])

    def test_select_group_respects_sector_cap(self) -> None:
        selected = _select_group(self._sample_group(), "priority_top3", 3, "30")
        software_count = int((selected["sector_group"] == "software_internet").sum())
        self.assertEqual(software_count, 1)
        self.assertLessEqual(len(selected), 3)

    def test_size_overlay_keeps_uncovered_neutral_after_selection(self) -> None:
        selected = _select_universe(self._sample_group(), "hybrid_full", SIZE_OVERLAY_50.name, 4, "none")
        uncovered = selected[selected["trade_id"] == "d"].iloc[0]
        self.assertEqual(float(uncovered["size_multiplier"]), 1.0)
        self.assertFalse(bool(_condition_mask(selected[selected["trade_id"] == "d"]).iloc[0]))


if __name__ == "__main__":
    unittest.main()
