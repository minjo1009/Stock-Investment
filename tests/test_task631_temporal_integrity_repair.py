from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task631_temporal_integrity_repair import (
    STRONG_ACTIONS,
    build_task631_temporal_integrity_repair,
)


class Task631TemporalIntegrityRepairTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task631_temporal_integrity_repair()

    def test_date_only_strong_actions_are_blocked(self) -> None:
        temporal = self.artifacts["task_631_temporal_action_attachment"]
        decision = self.artifacts["task_631_decision"].iloc[0]

        bad = temporal[
            temporal["temporal_action_bucket"].isin(STRONG_ACTIONS)
            & temporal["date_only_event_flag"].astype(int).eq(1)
        ]
        self.assertGreater(int(decision["date_only_original_action_count"]), 0)
        self.assertEqual(len(bad), 0)
        self.assertEqual(int(decision["strong_date_only_after_gate_count"]), 0)

    def test_time_gaps_are_reported_not_traded(self) -> None:
        temporal = self.artifacts["task_631_temporal_action_attachment"]
        pass_fail = self.artifacts["task_631_pass_fail_matrix"]
        gate = pass_fail[pass_fail["gate"].eq("source_time_gap_reported")].iloc[0]

        self.assertGreater(int(temporal["source_time_gap_flag"].sum()), 0)
        self.assertEqual(int(gate["pass_flag"]), 1)

    def test_strategy_remains_not_accepted(self) -> None:
        decision = self.artifacts["task_631_decision"].iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(decision["source_presence_only_used_flag"]), 0)
        self.assertEqual(int(decision["gpt_score_used_as_source_flag"]), 0)
        self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)

    def test_policy_outputs_exist(self) -> None:
        policy = self.artifacts["task_631_policy_variant_evaluation"]
        variants = set(policy["policy_variant"].unique())

        self.assertIn("temporal_strict_exact_delay_15m", variants)
        self.assertIn("temporal_strict_exact_delay_30m", variants)
        self.assertIn("temporal_strict_exact_delay_60m", variants)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task631_temporal_integrity_repair(out_dir=out_dir)

            self.assertTrue((out_dir / "task_631_temporal_integrity_repair.md").exists())
            self.assertTrue((out_dir / "task_631_temporal_action_attachment.csv").exists())
            self.assertTrue((out_dir / "task_631_source_time_audit.csv").exists())
            self.assertTrue((out_dir / "task_631_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_631_temporal_action_attachment"]), 100)


if __name__ == "__main__":
    unittest.main()
