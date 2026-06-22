from __future__ import annotations

import unittest

from src.backtest.analysis_structural_breakout_pro_quant_roadmap_343 import (
    _go_live_gates,
    _kill_criteria,
    _overlay_translation_options,
    _phase_roadmap,
    _priority_focus,
)


class TestAnalysisStructuralBreakoutProQuantRoadmap343(unittest.TestCase):
    def test_priority_focus_maps_current_state_to_portfolio_translation(self) -> None:
        snapshot = {
            "task340": {"decision": "REJECT_SUBSET"},
            "task341": {"decision": "REGIME_CONDITIONAL_EDGE"},
            "task342": {"decision": "NO_IMPROVEMENT"},
        }
        self.assertEqual(_priority_focus(snapshot), "portfolio_translation_before_new_signal_search")

    def test_phase_roadmap_is_ordered_and_complete(self) -> None:
        snapshot = {
            "task340": {"decision": "REJECT_SUBSET"},
            "task341": {"decision": "REGIME_CONDITIONAL_EDGE"},
            "task342": {"decision": "NO_IMPROVEMENT"},
        }
        df = _phase_roadmap(snapshot)
        self.assertEqual(df["phase_id"].tolist(), ["A", "B", "C", "D", "E"])
        self.assertEqual(df["priority"].tolist(), [1, 2, 3, 4, 5])

    def test_overlay_translation_prefers_priority_overlay(self) -> None:
        df = _overlay_translation_options()
        best = df.sort_values("priority_rank").iloc[0]
        self.assertEqual(best["overlay_type"], "trade_priority_ranking")

    def test_kill_and_go_live_tables_have_expected_minimum_rows(self) -> None:
        self.assertGreaterEqual(len(_kill_criteria()), 5)
        self.assertGreaterEqual(len(_go_live_gates()), 5)


if __name__ == "__main__":
    unittest.main()
