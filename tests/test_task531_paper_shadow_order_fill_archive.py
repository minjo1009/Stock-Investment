from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task529_530_trend_persistence_refinement import build_task529_trend_persistence_entry_safe_refinement
from src.backtest.build_task531_paper_shadow_order_fill_archive import (
    BLOCKED_ONLINE_LABEL_FIELDS,
    build_task531_paper_shadow_order_fill_archive,
)
from tests.task523_528_fixture import write_gap_fixture


class Task531PaperShadowOrderFillArchiveTest(unittest.TestCase):
    def test_shadow_archive_links_decision_order_fill_lifecycle_without_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_gap_fixture(root, rows=160)
            build_task529_trend_persistence_entry_safe_refinement(task503_panel_path=panel, out_dir=root / "529")
            artifacts = build_task531_paper_shadow_order_fill_archive(
                task503_panel_path=panel,
                task529_selected_path=root / "529" / "trend_persistence_refined_selected_rule.csv",
                out_dir=root / "531",
            )

            decision = artifacts["task_531_decision"].iloc[0]
            self.assertEqual(int(decision["decision_to_client_order_to_order_to_fill_to_lifecycle_flag"]), 1)
            self.assertEqual(int(decision["order_submission_enabled_flag"]), 0)
            self.assertEqual(int(decision["broker_truth_fill_available_flag"]), 0)

            lineage = artifacts["paper_shadow_lifecycle_lineage"]
            self.assertTrue({"decision_id", "client_order_id", "order_id", "fill_id", "lifecycle_id"}.issubset(lineage.columns))
            self.assertEqual(int(lineage["lineage_complete_flag"].min()), 1)

            assignment_cols = set(artifacts["paper_shadow_assignment_panel"].columns)
            self.assertFalse(assignment_cols.intersection(BLOCKED_ONLINE_LABEL_FIELDS))

    def test_missing_receive_timestamp_is_not_live_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_gap_fixture(root, rows=160)
            build_task529_trend_persistence_entry_safe_refinement(task503_panel_path=panel, out_dir=root / "529")
            artifacts = build_task531_paper_shadow_order_fill_archive(
                task503_panel_path=panel,
                task529_selected_path=root / "529" / "trend_persistence_refined_selected_rule.csv",
                out_dir=root / "531",
            )
            recv = artifacts["paper_shadow_receive_ts_audit"].iloc[0]
            self.assertEqual(int(recv["historical_rows_treated_live_ready_flag"]), 0)
            self.assertEqual(int(recv["live_clock_record_count"]), 0)


if __name__ == "__main__":
    unittest.main()
