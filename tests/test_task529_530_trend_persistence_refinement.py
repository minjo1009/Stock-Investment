from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task529_530_trend_persistence_refinement import (
    add_entry_bar_features,
    build_task529_trend_persistence_entry_safe_refinement,
    build_task530_paper_shadow_candidate_rerun,
)
from tests.task523_528_fixture import write_gap_fixture


class Task529530TrendPersistenceRefinementTest(unittest.TestCase):
    def test_entry_safe_features_and_paper_shadow_decision_emit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_gap_fixture(root, rows=160)
            artifacts = build_task529_trend_persistence_entry_safe_refinement(task503_panel_path=panel, out_dir=root / "529")
            decision = artifacts["task_529_decision"].iloc[0]
            self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)
            self.assertIn("entry_safe_refinement_pass_flag", decision.index)

            rerun = build_task530_paper_shadow_candidate_rerun(
                task529_decision_path=root / "529" / "task_529_decision.csv",
                task529_selected_path=root / "529" / "trend_persistence_refined_selected_rule.csv",
                out_dir=root / "530",
            )
            self.assertIn("promotion_decision", rerun["task_530_decision"].columns)

    def test_entry_bar_features_are_calculated_without_outcome_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_gap_fixture(root, rows=5)
            import pandas as pd

            frame = pd.read_csv(panel)
            enriched = add_entry_bar_features(frame)
            self.assertIn("entry_close_vs_vwap", enriched.columns)
            self.assertIn("entry_close_pos_in_bar", enriched.columns)


if __name__ == "__main__":
    unittest.main()
