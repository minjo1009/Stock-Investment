from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task737_semantic_modifier_bundle_attachment import build_task737
from src.backtest.semantic_modifier_bundle_attachment import attach_semantic_modifiers


class Task737SemanticModifierBundleAttachmentTest(unittest.TestCase):
    def test_conflict_and_queue_are_explanatory_not_score(self) -> None:
        bundles = pd.DataFrame(
            [
                {
                    "lifecycle_id": "L1",
                    "symbol": "TEST",
                    "theme_id": "theme",
                    "entry_ts": "2024-01-02T14:30:00Z",
                    "split_name": "unit",
                    "bundle_id": "bundle::L1",
                }
            ]
        )
        translations = pd.DataFrame(
            [
                {
                    "lifecycle_id": "L1",
                    "semantic_polarity": "constructive",
                    "semantic_state": "growth_funding_constructive",
                    "transmission_channel": "growth_funding",
                    "edge_effect": "confidence_modifier",
                    "target_layer": "L2",
                },
                {
                    "lifecycle_id": "L1",
                    "semantic_polarity": "adverse",
                    "semantic_state": "dilution_overhang_adverse",
                    "transmission_channel": "dilution_overhang",
                    "edge_effect": "risk_modifier",
                    "target_layer": "L5",
                },
            ]
        )

        attached = attach_semantic_modifiers(bundles, translations)
        row = attached.iloc[0]

        self.assertEqual(row["constructive_count"], 1)
        self.assertEqual(row["adverse_count"], 1)
        self.assertIn("constructive_adverse_conflict", row["conflict_state"])
        self.assertIn("growth_funding_dilution_conflict", row["conflict_state"])
        self.assertEqual(row["queue_transition_state"], "semantic_conflict_review_needed")
        self.assertEqual(int(row["direct_score_created_flag"]), 0)
        self.assertEqual(int(row["buy_sell_signal_created_flag"]), 0)
        self.assertEqual(int(row["backtest_eligible_flag"]), 0)

    def test_unknown_modifier_is_enrichment_not_negative(self) -> None:
        bundles = pd.DataFrame(
            [
                {
                    "lifecycle_id": "L2",
                    "symbol": "TEST",
                    "theme_id": "theme",
                    "entry_ts": "2024-01-02T14:30:00Z",
                    "split_name": "unit",
                    "bundle_id": "bundle::L2",
                }
            ]
        )
        translations = pd.DataFrame(
            [
                {
                    "lifecycle_id": "L2",
                    "semantic_polarity": "unknown",
                    "semantic_state": "terms_incomplete_unknown",
                    "transmission_channel": "context_only",
                    "edge_effect": "research_escalation",
                    "target_layer": "L1",
                }
            ]
        )

        attached = attach_semantic_modifiers(bundles, translations)
        row = attached.iloc[0]

        self.assertEqual(row["unknown_count"], 1)
        self.assertEqual(row["adverse_count"], 0)
        self.assertEqual(row["queue_transition_state"], "semantic_enrichment_needed")

    def test_task737_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task737(out_dir=out_dir)

            for filename in [
                "task737_bundle_semantic_modifier_attachment.csv",
                "task737_task688_semantic_modifier_attach_attempt.csv",
                "task737_modifier_attachment_edges.csv",
                "task737_queue_transition_summary.csv",
                "task737_conflict_summary.csv",
                "task737_coverage_report.csv",
                "task737_guardrail.csv",
                "task737_gpt_review_summary.csv",
                "task_737_decision.csv",
                "task_737_pass_fail_matrix.csv",
                "task_737_semantic_modifier_bundle_attachment.md",
                "task737_bundle_semantic_modifier_attachment.jsonl",
                "task737_task688_semantic_modifier_attach_attempt.jsonl",
                "task737_modifier_attachment_edges.jsonl",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            attachment = artifacts["attachment"]
            guardrail = artifacts["guardrail"]
            decision = artifacts["decision"].iloc[0]
            coverage = artifacts["coverage"]

            self.assertEqual(len(attachment), 345)
            self.assertEqual(int(attachment["direct_score_created_flag"].sum()), 0)
            self.assertEqual(int(attachment["buy_sell_signal_created_flag"].sum()), 0)
            self.assertEqual(int(attachment["backtest_eligible_flag"].sum()), 0)
            self.assertEqual(int(guardrail["pass_flag"].min()), 1)
            self.assertEqual(decision["backtest_permission"], "FAIL")
            self.assertIn("semantic_modifier_absent_not_negative_report_only", set(coverage["coverage_state"]))
            broader = artifacts["broader_attachment"]
            self.assertEqual(len(broader), 1621)
            self.assertTrue(broader["queue_transition_state"].eq("semantic_modifier_absent_not_negative").all())


if __name__ == "__main__":
    unittest.main()
