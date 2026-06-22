from __future__ import annotations

import unittest

import pandas as pd

from src.backtest.analysis_structural_breakout_coverage_corrected_revalidation_346 import (
    _corrected_coverage_row,
    _delta_value,
    _final_decision,
    _signal_classification,
)


class TestAnalysisStructuralBreakoutCoverageCorrectedRevalidation346(unittest.TestCase):
    def test_corrected_coverage_uses_close_confirm_and_relaxed_prebreak(self) -> None:
        trade_row = pd.Series({"symbol": "ABC", "entry_date": "2024-01-02", "breakout_level": 10.0})
        intraday_df = pd.DataFrame(
            {
                "symbol": ["ABC"] * 6,
                "bar_date": ["2024-01-02"] * 6,
                "bar_start_ts": pd.date_range("2024-01-02T14:30:00Z", periods=6, freq="5min", tz="UTC"),
                "high": [10.2, 10.1, 10.0, 10.0, 10.0, 10.0],
                "close": [9.8, 9.9, 10.0, 10.1, 10.2, 10.1],
            }
        )
        coverage = _corrected_coverage_row(trade_row, intraday_df)
        self.assertEqual(coverage["breakout_bar_index"], 2)
        self.assertEqual(coverage["entry_only_status"], "covered")

    def test_signal_classification_maps_partial_and_strong(self) -> None:
        partial_df = pd.DataFrame([{"decision": "PARTIAL_INTRADAY_EDGE"}])
        strong_df = pd.DataFrame([{"decision": "STRONG_INTRADAY_EDGE"}])
        weak_df = pd.DataFrame([{"decision": "NO_INTRADAY_EDGE", "positive_oos_lift_exists": True}])
        self.assertEqual(_signal_classification(partial_df), "PARTIAL")
        self.assertEqual(_signal_classification(strong_df), "STRONG")
        self.assertEqual(_signal_classification(weak_df), "WEAK")

    def test_delta_value_handles_strings_and_numbers(self) -> None:
        self.assertEqual(_delta_value("A", "B"), "")
        self.assertEqual(_delta_value(True, False), -1)
        self.assertAlmostEqual(_delta_value(1.5, 2.0), 0.5)

    def test_final_decision_detects_partial_artifact_case(self) -> None:
        edge_reclass_df = pd.DataFrame(
            [
                {"layer": "signal", "classification": "PARTIAL"},
                {"layer": "subset", "classification": "CONDITIONAL"},
                {"layer": "portfolio", "classification": "NONE"},
            ]
        )
        corrected_metrics = {
            "task_338": {"covered_trade_count": 98.0, "decision": "PARTIAL_INTRADAY_EDGE"},
            "task_342": {"decision": "NO_IMPROVEMENT"},
        }
        original_metrics = {
            "task_338": {"covered_trade_count": 50.0},
        }
        final_df = _final_decision(edge_reclass_df, corrected_metrics, original_metrics)
        self.assertEqual(str(final_df.iloc[0]["decision"]), "PARTIAL_ARTIFACT_WITH_REAL_WEAKNESS")


if __name__ == "__main__":
    unittest.main()
