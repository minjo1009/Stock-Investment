from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task738_semantic_enrichment_requirements import build_task738
from src.backtest.semantic_enrichment_requirements import build_enrichment_requirements, requirement_for_translation


class Task738SemanticEnrichmentRequirementsTest(unittest.TestCase):
    def test_form4_plan_sale_requires_size_role_and_history(self) -> None:
        row = pd.Series(
            {
                "event_id": "E1",
                "lifecycle_id": "L1",
                "symbol": "TEST",
                "theme_id": "theme",
                "entry_ts": "2024-01-02T14:30:00Z",
                "split_name": "unit",
                "source_form_family": "form4_insider",
                "context_type": "InsiderBehaviorContext",
                "semantic_state": "automatic_plan_sale_neutral_to_unknown",
                "semantic_polarity": "unknown",
                "transmission_channel": "governance_quality",
                "edge_effect": "research_escalation",
            }
        )

        requirement = requirement_for_translation(row, "bundle::L1")

        self.assertEqual(requirement.requirement_family, "form4_plan_pattern_enrichment")
        self.assertEqual(requirement.resolver_target_state, "insider_pattern_needed")
        self.assertIn("plan_adoption_date", requirement.missing_primitive_fields)
        self.assertIn("percent_of_holdings", requirement.missing_primitive_fields)
        self.assertEqual(requirement.review_lane, "normal_review_lane")
        self.assertEqual(requirement.backtest_eligible_flag, 0)

    def test_financing_terms_are_high_review_not_trade_ready(self) -> None:
        row = pd.Series(
            {
                "event_id": "E2",
                "lifecycle_id": "L2",
                "symbol": "TEST",
                "theme_id": "theme",
                "entry_ts": "2024-01-02T14:30:00Z",
                "split_name": "unit",
                "source_form_family": "generic_8k",
                "context_type": "Generic8KClassificationContext",
                "semantic_state": "generic_financing_review_required",
                "semantic_polarity": "conditional",
                "transmission_channel": "growth_funding|dilution_overhang",
                "edge_effect": "research_escalation",
            }
        )

        requirement = requirement_for_translation(row, "bundle::L2")

        self.assertEqual(requirement.requirement_family, "financing_terms_enrichment")
        self.assertEqual(requirement.review_lane, "high_review_lane")
        self.assertIn("use_of_proceeds", requirement.missing_primitive_fields)
        self.assertIn("operating_catalyst_alignment", requirement.required_interaction_fields)
        self.assertEqual(requirement.can_create_operating_catalyst, 0)
        self.assertEqual(requirement.actionability_created_flag, 0)

    def test_attachment_filter_creates_requirement_for_enrichment_queue_only(self) -> None:
        attachments = pd.DataFrame(
            [
                {
                    "lifecycle_id": "L1",
                    "bundle_id": "bundle::L1",
                    "queue_transition_state": "semantic_enrichment_needed",
                    "source_modifier_count": 1,
                },
                {
                    "lifecycle_id": "L2",
                    "bundle_id": "bundle::L2",
                    "queue_transition_state": "context_only_no_change",
                    "source_modifier_count": 1,
                },
            ]
        )
        translations = pd.DataFrame(
            [
                {
                    "event_id": "E1",
                    "lifecycle_id": "L1",
                    "symbol": "A",
                    "theme_id": "theme",
                    "entry_ts": "2024-01-02T14:30:00Z",
                    "split_name": "unit",
                    "source_form_family": "ownership",
                    "context_type": "OwnershipStructureContext",
                    "semantic_state": "ownership_change_unknown",
                    "semantic_polarity": "unknown",
                    "transmission_channel": "ownership_concentration",
                    "edge_effect": "research_escalation",
                },
                {
                    "event_id": "E2",
                    "lifecycle_id": "L2",
                    "symbol": "B",
                    "theme_id": "theme",
                    "entry_ts": "2024-01-02T14:30:00Z",
                    "split_name": "unit",
                    "source_form_family": "form4_insider",
                    "context_type": "InsiderBehaviorContext",
                    "semantic_state": "option_exercise_or_award_neutral",
                    "semantic_polarity": "neutral",
                    "transmission_channel": "governance_quality",
                    "edge_effect": "context_only",
                },
            ]
        )

        requirements = build_enrichment_requirements(attachments, translations)

        self.assertEqual(len(requirements), 1)
        self.assertEqual(requirements.iloc[0]["lifecycle_id"], "L1")
        self.assertEqual(requirements.iloc[0]["requirement_family"], "ownership_change_enrichment")

    def test_task738_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task738(out_dir=out_dir)

            for filename in [
                "task738_enrichment_requirements.csv",
                "task738_enrichment_requirements.jsonl",
                "task738_requirement_family_distribution.csv",
                "task738_resolver_targets.csv",
                "task738_resolver_targets.jsonl",
                "task738_review_lane_assignment.csv",
                "task738_missing_primitive_matrix.csv",
                "task738_denominator_requirement_matrix.csv",
                "task738_interaction_requirement_edges.csv",
                "task738_interaction_requirement_edges.jsonl",
                "task738_coverage_report.csv",
                "task738_guardrail.csv",
                "task738_gpt_review_summary.csv",
                "task_738_decision.csv",
                "task_738_pass_fail_matrix.csv",
                "task_738_semantic_enrichment_requirements.md",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            requirements = artifacts["requirements"]
            guardrail = artifacts["guardrail"]
            decision = artifacts["decision"].iloc[0]

            self.assertEqual(requirements["lifecycle_id"].nunique(), 235)
            self.assertEqual(len(requirements), 4101)
            self.assertEqual(int(requirements["backtest_eligible_flag"].sum()), 0)
            self.assertEqual(int(requirements["actionability_created_flag"].sum()), 0)
            self.assertEqual(int(requirements["can_create_operating_catalyst"].sum()), 0)
            self.assertEqual(int(guardrail["pass_flag"].min()), 1)
            self.assertEqual(decision["backtest_permission"], "FAIL")


if __name__ == "__main__":
    unittest.main()
