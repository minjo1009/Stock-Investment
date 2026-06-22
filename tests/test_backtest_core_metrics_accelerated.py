from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBacktestCoreMetricsAccelerated(unittest.TestCase):
    def _fixture(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "bucket": "A",
                    "regime": "up",
                    "lifecycle_id": "L1",
                    "net_return_from_entry": 0.10,
                    "win_flag": 1.0,
                    "add_scale_success_flag": 1.0,
                    "entry_reduce_failure_flag": 0.0,
                    "false_positive_flag": 0.0,
                },
                {
                    "bucket": "A",
                    "regime": "up",
                    "lifecycle_id": None,
                    "net_return_from_entry": None,
                    "win_flag": 0.0,
                    "add_scale_success_flag": None,
                    "entry_reduce_failure_flag": 1.0,
                    "false_positive_flag": 1.0,
                },
                {
                    "bucket": "B",
                    "regime": None,
                    "lifecycle_id": "L3",
                    "net_return_from_entry": -0.20,
                    "win_flag": 0.0,
                    "add_scale_success_flag": 0.0,
                    "entry_reduce_failure_flag": 1.0,
                    "false_positive_flag": 0.0,
                },
                {
                    "bucket": "C",
                    "regime": "flat",
                    "lifecycle_id": "L4",
                    "net_return_from_entry": None,
                    "win_flag": None,
                    "add_scale_success_flag": None,
                    "entry_reduce_failure_flag": None,
                    "false_positive_flag": None,
                },
            ]
        )

    def test_grouped_lifecycle_quality_matches_pandas_semantics(self) -> None:
        from src.backtest.core.metrics import grouped_lifecycle_quality

        frame = self._fixture()
        expected = (
            frame.groupby(["bucket", "regime"], dropna=False)
            .agg(
                lifecycle_count=("lifecycle_id", "count"),
                avg_net_return_pct=("net_return_from_entry", lambda s: float(s.mean() * 100.0)),
                win_rate=("win_flag", "mean"),
                add_scale_success_rate=("add_scale_success_flag", "mean"),
                entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
                false_positive_rate=("false_positive_flag", "mean"),
            )
            .reset_index()
        )
        actual = grouped_lifecycle_quality(frame, ["bucket", "regime"])
        expected = expected.astype(object).where(pd.notna(expected), None)
        actual = actual.astype(object).where(pd.notna(actual), None)

        pd.testing.assert_frame_equal(actual, expected, check_dtype=False, check_exact=False)
        group_a = actual[(actual["bucket"] == "A") & (actual["regime"] == "up")].iloc[0]
        self.assertEqual(int(group_a["lifecycle_count"]), 1)
        self.assertAlmostEqual(float(group_a["avg_net_return_pct"]), 10.0)
        self.assertAlmostEqual(float(group_a["win_rate"]), 0.5)
        self.assertTrue(actual["regime"].isna().any())

    def test_empty_and_ungrouped_paths_remain_unchanged(self) -> None:
        from src.backtest.core.metrics import grouped_lifecycle_quality

        self.assertTrue(grouped_lifecycle_quality(pd.DataFrame(), ["bucket"]).empty)
        ungrouped = grouped_lifecycle_quality(self._fixture(), [])
        self.assertEqual(len(ungrouped), 1)
        self.assertIn("lifecycle_count", ungrouped.columns)

    def test_grouped_path_still_requires_false_positive_flag(self) -> None:
        from src.backtest.core.metrics import grouped_lifecycle_quality

        frame = self._fixture().drop(columns=["false_positive_flag"])
        with self.assertRaises(KeyError):
            grouped_lifecycle_quality(frame, ["bucket"])


if __name__ == "__main__":
    unittest.main()
