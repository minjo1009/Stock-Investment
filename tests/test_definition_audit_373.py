from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest.analysis_structural_breakout_definition_audit_373 import main as report_main
from backtest.build_definition_audit_373 import build_definition_audit_373, write_definition_audit_373


class DefinitionAudit373Tests(unittest.TestCase):
    def test_definition_frames_are_non_empty_and_have_sources(self) -> None:
        artifacts = build_definition_audit_373()

        for frame in (
            artifacts.good_breakout_definition,
            artifacts.good_entry_definition,
            artifacts.good_flow_definition,
        ):
            self.assertFalse(frame.empty)
            self.assertTrue(frame["source_path"].astype(str).ne("").all())
            self.assertTrue(frame["source_function"].astype(str).ne("").all())

    def test_builder_is_deterministic(self) -> None:
        first = build_definition_audit_373()
        second = build_definition_audit_373()

        pd.testing.assert_frame_equal(first.good_breakout_definition, second.good_breakout_definition)
        pd.testing.assert_frame_equal(first.good_entry_definition, second.good_entry_definition)
        pd.testing.assert_frame_equal(first.good_flow_definition, second.good_flow_definition)
        pd.testing.assert_frame_equal(first.definition_forward_vs_expost_matrix, second.definition_forward_vs_expost_matrix)
        pd.testing.assert_frame_equal(first.definition_conservatism_audit, second.definition_conservatism_audit)

    def test_healthy_threshold_mismatch_is_captured(self) -> None:
        artifacts = build_definition_audit_373()
        entry = artifacts.good_entry_definition

        label_row = entry[entry["rule_id"].astype(str) == "entry.participation_quality_label"].iloc[0]
        action_row = entry[entry["rule_id"].astype(str) == "entry.healthy_action_threshold"].iloc[0]

        self.assertIn("0.45", str(label_row["thresholds"]))
        self.assertIn("0.65", str(action_row["thresholds"]))
        self.assertEqual(str(action_row["logic_issue_flag"]), "threshold_mismatch")

    def test_execution_quality_and_persistence_are_not_forward_clean(self) -> None:
        artifacts = build_definition_audit_373()
        matrix = artifacts.definition_forward_vs_expost_matrix

        breakout_row = matrix[matrix["rule_id"].astype(str) == "breakout.execution_quality_score"].iloc[0]
        persistence_row = matrix[matrix["rule_id"].astype(str) == "flow.persistence_15m"].iloc[0]

        self.assertIn(str(breakout_row["temporal_classification"]), {"mixed", "expost"})
        self.assertEqual(str(persistence_row["temporal_classification"]), "expost")

    def test_report_artifacts_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            artifacts = build_definition_audit_373()
            write_definition_audit_373(artifacts, out_dir)

            argv = sys.argv
            try:
                sys.argv = ["definition_audit_373", "--out-dir", str(out_dir)]
                report_main()
            finally:
                sys.argv = argv

            for name in (
                "good_breakout_definition.csv",
                "good_entry_definition.csv",
                "good_flow_definition.csv",
                "definition_forward_vs_expost_matrix.csv",
                "definition_conservatism_audit.csv",
                "task_373_definition_audit.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
