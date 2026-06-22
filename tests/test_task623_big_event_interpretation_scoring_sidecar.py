from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task623_big_event_interpretation_scoring_sidecar import (
    BIG_EVENT_LANES,
    SCORING_FIELDS,
    build_task623_big_event_interpretation_scoring_sidecar,
)


class Task623BigEventInterpretationScoringSidecarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task623_big_event_interpretation_scoring_sidecar()

    def test_decision_keeps_scores_evaluation_only(self) -> None:
        decision = self.artifacts["task_623_decision"].iloc[0]

        self.assertEqual(decision["decision"], "IMPLEMENT_BIG_EVENT_SCORING_SIDECAR_NOT_TRADING_SIGNAL")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["semantic_scores_used_in_assignment_flag"]), 0)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_scoring_schema_and_large_event_scores_exist(self) -> None:
        scored = self.artifacts["event_interpretation_scores"]
        large = scored[scored["source_lane"].astype(str).isin(BIG_EVENT_LANES)]
        nonzero = large[large["composite_interpretation_score"].astype(float).abs() > 0]

        self.assertTrue(set(SCORING_FIELDS).issubset(scored.columns))
        self.assertGreater(len(large), 0)
        self.assertGreater(len(nonzero), 0)

    def test_broad_events_cannot_be_support_entry(self) -> None:
        scored = self.artifacts["event_interpretation_scores"]
        broad_support = scored[
            scored["event_scope"].astype(str).isin(["macro_policy_general", "theme_or_sector"])
            & scored["support_entry_certified_flag"].astype(int).eq(1)
        ]

        self.assertTrue(broad_support.empty)
        self.assertEqual(int(scored["source_presence_only_used_flag"].sum()), 0)
        self.assertEqual(int(scored["gpt_score_used_as_source_flag"].sum()), 0)

    def test_recent_aerospace_gets_risk_but_no_support_entry(self) -> None:
        recent = self.artifacts["recent_aerospace_event_score_attachment"]
        decision = self.artifacts["task_623_decision"].iloc[0]

        self.assertGreater(len(recent), 0)
        self.assertEqual(int(recent["support_entry_candidate_count"].sum()), 0)
        self.assertGreater(int(recent["risk_off_candidate_count"].sum()), 0)
        self.assertEqual(int(decision["recent_aerospace_support_entry_candidate_count"]), 0)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task623_big_event_interpretation_scoring_sidecar(out_dir=out_dir)

            self.assertTrue((out_dir / "task_623_big_event_interpretation_scoring_sidecar.md").exists())
            self.assertTrue((out_dir / "event_interpretation_scores.csv").exists())
            self.assertTrue((out_dir / "recent_aerospace_event_score_attachment.csv").exists())
            self.assertTrue((out_dir / "task_623_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["event_interpretation_scores"]), 100)


if __name__ == "__main__":
    unittest.main()
