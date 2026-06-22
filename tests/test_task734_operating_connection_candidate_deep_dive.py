from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task734_operating_connection_candidate_deep_dive import build_task734
from src.backtest.operating_candidate_deep_dive import review_operating_candidate


def row_with_text(text: str) -> pd.Series:
    return pd.Series(
        {
            "event_id": "E1",
            "lifecycle_id": "L1",
            "symbol": "TEST",
            "theme_id": "theme",
            "entry_ts": "2024-01-02T14:30:00Z",
            "split_name": "unit",
            "permission_state": "connection_candidate",
            "rule_id": "OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL",
            "content_interpretation_evidence_span": text,
        }
    )


class Task734OperatingConnectionCandidateDeepDiveTest(unittest.TestCase):
    def test_compensation_plan_is_not_operating(self) -> None:
        review = review_operating_candidate(row_with_text("RSU grants stock option grants performance stock unit compensatory plan"))

        self.assertEqual(review["refined_context_family"], "compensation_context")
        self.assertEqual(review["refined_permission_state"], "not_applicable")
        self.assertEqual(review["refined_rule_id"], "COMPENSATION_PLAN_NON_OPERATING")
        self.assertEqual(review["operating_connection_candidate_after_review_flag"], 0)
        self.assertEqual(review["false_positive_flag"], 1)

    def test_mna_survives_as_candidate_not_supported(self) -> None:
        review = review_operating_candidate(row_with_text("Purchase Agreement and agreement to acquire GEOST in a transaction"))

        self.assertEqual(review["refined_context_family"], "strategic_mna_context")
        self.assertEqual(review["refined_permission_state"], "connection_candidate")
        self.assertEqual(review["refined_rule_id"], "MNA_REQUIRES_OPERATING_TRANSMISSION")
        self.assertEqual(review["operating_connection_candidate_after_review_flag"], 1)
        self.assertEqual(review["operating_connection_supported_after_review_flag"], 0)
        self.assertEqual(review["false_positive_flag"], 0)

    def test_task734_build_outputs_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task734(out_dir=out_dir)

            for filename in [
                "task734_candidate_deep_dive.csv",
                "task734_candidate_summary.csv",
                "task734_guardrail.csv",
                "task734_gpt_review_summary.csv",
                "task_734_decision.csv",
                "task_734_pass_fail_matrix.csv",
                "task_734_operating_connection_candidate_deep_dive.md",
                "task734_candidate_deep_dive.jsonl",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            review = artifacts["review"]
            decision = artifacts["decision"].iloc[0]
            pass_fail = artifacts["pass_fail"]

            self.assertEqual(len(review), 9)
            self.assertEqual(int(review["false_positive_flag"].sum()), 8)
            self.assertEqual(int(review["operating_connection_candidate_after_review_flag"].sum()), 1)
            self.assertEqual(int(review["operating_connection_supported_after_review_flag"].sum()), 0)
            self.assertEqual(decision["backtest_permission"], "FAIL")
            self.assertEqual(int(pass_fail.loc[pass_fail["gate_name"] == "guardrail_all_pass", "pass_flag"].iloc[0]), 1)


if __name__ == "__main__":
    unittest.main()
