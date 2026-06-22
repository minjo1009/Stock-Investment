from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task635_content_interpretation_readiness_audit import (
    REQUIRED_CONTENT_FIELDS,
    build_task635_content_interpretation_readiness_audit,
)


class Task635ContentInterpretationReadinessAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task635_content_interpretation_readiness_audit()

    def test_source_text_exists_but_content_prediction_is_not_ready(self) -> None:
        readiness = self.artifacts["task_635_content_readiness_audit"].iloc[0]
        decision = self.artifacts["task_635_decision"].iloc[0]

        self.assertGreater(int(readiness["source_text_certified_count"]), 0)
        self.assertEqual(int(readiness["missing_content_field_count"]), len(REQUIRED_CONTENT_FIELDS))
        self.assertEqual(int(readiness["content_prediction_ready_flag"]), 0)
        self.assertEqual(decision["decision"], "FAIL_CONTENT_INTERPRETATION_NOT_READY")

    def test_presence_fields_are_blocked_from_assignment(self) -> None:
        policy = self.artifacts["task_635_presence_field_block_policy"]
        pass_fail = self.artifacts["task_635_pass_fail_matrix"]

        self.assertGreater(len(policy), 5)
        self.assertEqual(int(policy["assignment_use_allowed_flag"].sum()), 0)
        self.assertEqual(
            int(pass_fail[pass_fail["gate"].eq("presence_fields_blocked_from_assignment")]["pass_flag"].iloc[0]),
            1,
        )
        self.assertEqual(
            int(pass_fail[pass_fail["gate"].eq("assignment_allowed")]["pass_flag"].iloc[0]),
            0,
        )

    def test_required_schema_is_explicit(self) -> None:
        schema = self.artifacts["task_635_required_content_prediction_schema"]

        self.assertEqual(set(schema["field"]), set(REQUIRED_CONTENT_FIELDS))
        self.assertEqual(int(schema["required_for_assignment_flag"].sum()), len(REQUIRED_CONTENT_FIELDS))

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            build_task635_content_interpretation_readiness_audit(out_dir=out_dir)

            self.assertTrue((out_dir / "task_635_content_interpretation_readiness_audit.md").exists())
            self.assertTrue((out_dir / "task_635_content_readiness_audit.csv").exists())
            self.assertTrue((out_dir / "task_635_presence_field_block_policy.csv").exists())
            self.assertTrue((out_dir / "task_635_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
