from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task620b_proactive_prescription_logic import (
    FORBIDDEN_RULE_COLUMNS,
    build_task620b_proactive_prescription_logic,
)


class Task620BProactivePrescriptionLogicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task620b_proactive_prescription_logic()

    def test_rulebook_uses_pre_entry_columns_only(self) -> None:
        rulebook = self.artifacts["task_620b_proactive_rulebook"]
        used = set()
        for value in rulebook["condition_columns"].astype(str):
            used.update(value.split("|"))

        self.assertFalse(used.intersection(FORBIDDEN_RULE_COLUMNS))
        self.assertEqual(int(rulebook["label_used_in_assignment_flag"].max()), 0)

    def test_primary_rule_is_proactive_not_accepted(self) -> None:
        decision = self.artifacts["task_620b_decision"].iloc[0]
        policy = self.artifacts["task_620b_policy_variant_evaluation"]
        recent = policy[
            policy["policy_name"].eq("PROACTIVE_V1_AEROSPACE_RISK_OFF")
            & policy["split_name"].eq("recent_oos")
        ].iloc[0]

        self.assertEqual(decision["primary_proactive_rule"], "AEROSPACE_SPACE_RISK_OFF_GATE")
        self.assertEqual(decision["primary_pre_entry_action"], "BLOCK_UNTIL_SOURCE_RETYPED")
        self.assertEqual(int(decision["treatment_rule_accepted_flag"]), 0)
        self.assertGreater(float(recent["kept_avg_net_return_pct"]), 5.0)
        self.assertLessEqual(float(recent["kept_entry_reduce_failure_rate"]), 0.50)

    def test_global_ir_requirement_is_rejected(self) -> None:
        pass_fail = self.artifacts["task_620b_pass_fail_matrix"]
        gate = pass_fail[pass_fail["gate"].eq("global_ir_requirement_rejected")].iloc[0]

        self.assertEqual(int(gate["pass_flag"]), 1)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task620b_proactive_prescription_logic(out_dir=out_dir)

            self.assertTrue((out_dir / "task_620b_proactive_prescription_logic.md").exists())
            self.assertTrue((out_dir / "task_620b_proactive_rulebook.csv").exists())
            self.assertTrue((out_dir / "task_620b_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreaterEqual(len(artifacts["task_620b_proactive_rulebook"]), 5)


if __name__ == "__main__":
    unittest.main()
