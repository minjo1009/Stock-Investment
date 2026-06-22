from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_intraday_coverage_alignment_345 import (
    ALIGNMENT_RULES,
    _breakout_diagnostic,
    _coverage_under_rule,
    _failure_taxonomy,
    _recoverability_class,
    _session_metadata,
    _window_alignment_comparison,
)


def _session_df(start: str, rows: int, highs: list[float], closes: list[float]) -> pd.DataFrame:
    bar_start = pd.date_range(start=start, periods=rows, freq="5min", tz="UTC")
    return pd.DataFrame(
        {
            "bar_start_ts": bar_start,
            "bar_end_ts": bar_start + pd.Timedelta(minutes=4, seconds=59),
            "high": highs,
            "close": closes,
        }
    )


class TestAnalysisStructuralBreakoutIntradayCoverageAlignment345(unittest.TestCase):
    def test_breakout_diagnostic_is_deterministic(self) -> None:
        session = _session_df(
            "2021-07-15T13:30:00Z",
            4,
            [10.0, 10.5, 11.0, 11.5],
            [9.9, 10.2, 10.9, 11.4],
        )
        high_touch = _breakout_diagnostic(session, 10.5, "high_touch_first_touch")
        close_confirm = _breakout_diagnostic(session, 10.5, "close_confirmed_break")
        tolerant = _breakout_diagnostic(session, 10.5, "tolerant_max_high_close")
        self.assertEqual(high_touch["breakout_idx"], 1)
        self.assertEqual(close_confirm["breakout_idx"], 2)
        self.assertEqual(tolerant["breakout_idx"], 1)

    def test_failure_taxonomy_detects_timezone_misalignment(self) -> None:
        session = _session_df(
            "2021-06-14T14:30:00Z",
            66,
            [101.0] * 66,
            [100.5] * 66,
        )
        metadata = _session_metadata(session)
        failure_reason = _failure_taxonomy(session, metadata, current_breakout_idx=0)
        self.assertEqual(failure_reason, "timezone_or_timestamp_misalignment")

    def test_recoverability_class_is_mutually_exclusive(self) -> None:
        self.assertEqual(
            _recoverability_class(False, True, True, True),
            "recoverable_by_alignment_only",
        )
        self.assertEqual(
            _recoverability_class(False, False, True, True),
            "recoverable_by_window_rule_only",
        )
        self.assertEqual(
            _recoverability_class(False, False, False, True),
            "recoverable_by_alignment_and_window_rule",
        )
        self.assertEqual(
            _recoverability_class(False, False, False, False),
            "non_recoverable_from_current_archive",
        )

    def test_window_alignment_comparison_is_reproducible(self) -> None:
        trade_df = pd.DataFrame(
            [
                {
                    "split": "full_period",
                    "session_bar_count": 78,
                    "current_breakout_idx": 0,
                    "close_confirm_breakout_idx": 3,
                    "tolerant_breakout_idx": 0,
                    "current_covered": False,
                },
                {
                    "split": "full_period",
                    "session_bar_count": 78,
                    "current_breakout_idx": 4,
                    "close_confirm_breakout_idx": 4,
                    "tolerant_breakout_idx": 4,
                    "current_covered": True,
                },
            ]
        )
        comparison = _window_alignment_comparison(trade_df)
        strict_close = comparison[
            (comparison["split"] == "full_period")
            & (comparison["alignment_rule"] == "close_confirmed_break")
            & (comparison["window_rule"] == "current_strict")
        ].iloc[0]
        self.assertEqual(int(strict_close["covered_trade_count"]), 2)
        self.assertEqual(int(strict_close["recovered_trade_count_vs_current"]), 1)


if __name__ == "__main__":
    unittest.main()
