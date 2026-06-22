from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task733_circuit_quality_operating_connection import build_task733
from src.backtest.source_circuit_quality import build_context_quality


def context_row(**overrides: object) -> dict[str, object]:
    row = {
        "event_id": "E1",
        "lifecycle_id": "L1",
        "symbol": "TEST",
        "theme_id": "theme",
        "entry_ts": "2024-01-02T14:30:00Z",
        "split_name": "unit",
        "source_form_family": "financing_8k",
        "context_type": "CreditFinancingContext",
        "primitive_fields_json": "{}",
        "interpretation_states": "financing_terms_incomplete",
        "source_is_discarded_flag": 0,
        "backtest_eligible_flag": 0,
    }
    row.update(overrides)
    return row


class Task733CircuitQualityOperatingConnectionTest(unittest.TestCase):
    def test_financing_growth_becomes_candidate_when_operating_path_missing(self) -> None:
        contexts = pd.DataFrame(
            [
                context_row(
                    primitive_fields_json='{"principal_amount":185000000,"growth_use_of_proceeds_flag":1}',
                    interpretation_states="growth_funding_possible|credit_context_alive_terms_incomplete_not_negative",
                )
            ]
        )
        quality, edges = build_context_quality(contexts)

        self.assertEqual(quality.iloc[0]["permission_state"], "connection_candidate")
        self.assertEqual(quality.iloc[0]["connection_rule_id"], "FINANCING_GROWTH_FUNDING_NEEDS_VISIBLE_OPERATING_PATH")
        self.assertEqual(int(quality.iloc[0]["can_create_operating_connection_flag"]), 1)
        self.assertEqual(int(quality.iloc[0]["can_create_operating_fact_flag"]), 0)
        self.assertEqual(edges.iloc[0]["target_context_type"], "OperatingCatalystContext")

    def test_generic_8k_material_agreement_alone_is_not_supported(self) -> None:
        contexts = pd.DataFrame(
            [
                context_row(
                    source_form_family="generic_8k",
                    context_type="Generic8KClassificationContext",
                    primitive_fields_json='{"item_numbers":["1.01"],"agreement_family_state":"unclassified_generic_8k_context","operating_transmission_state":"no_operating_transmission","permission_state":"review_required","connection_rule_id":"UNCLASSIFIED_8K_REVIEW_REQUIRED","required_next_evidence":"item classifier and source text review","operating_candidate_flag":0,"operating_supported_flag":0}',
                    interpretation_states="generic_8k_requires_secondary_classifier|generic_8k_unclassified_generic_8k_context|generic_8k_no_operating_transmission|generic_8k_permission_review_required",
                )
            ]
        )
        quality, edges = build_context_quality(contexts)

        self.assertEqual(quality.iloc[0]["permission_state"], "review_required")
        self.assertEqual(quality.iloc[0]["connection_rule_id"], "UNCLASSIFIED_8K_REVIEW_REQUIRED")
        self.assertEqual(int(quality.iloc[0]["can_create_operating_connection_flag"]), 0)
        self.assertEqual(int(quality.iloc[0]["used_for_trading_flag"]), 0)
        self.assertEqual(int(quality.iloc[0]["backtest_eligible_flag"]), 0)

    def test_form4_remains_modifier_only(self) -> None:
        contexts = pd.DataFrame(
            [
                context_row(
                    source_form_family="form4_insider",
                    context_type="InsiderBehaviorContext",
                    primitive_fields_json='{"open_market_buy_flag":1,"director_or_officer_language_present":1}',
                    interpretation_states="non_operating_context_only|insider_open_market_buy_observed|executive_or_director_signal_present",
                )
            ]
        )
        quality, edges = build_context_quality(contexts)

        self.assertEqual(quality.iloc[0]["permission_state"], "modifier_only")
        self.assertEqual(int(quality.iloc[0]["can_create_operating_connection_flag"]), 0)
        self.assertNotEqual(edges.iloc[0]["target_context_type"], "OperatingCatalystContext")

    def test_task733_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task733(out_dir=out_dir)

            for filename in [
                "task733_context_quality.csv",
                "task733_connection_permission.csv",
                "task733_operating_connection_edges.csv",
                "task733_non_operating_modifier_edges.csv",
                "task733_guardrail_violations.csv",
                "task733_quality_distribution_report.csv",
                "task733_gpt_review_summary.csv",
                "task_733_decision.csv",
                "task_733_pass_fail_matrix.csv",
                "task_733_circuit_quality_operating_connection.md",
                "task733_context_quality.jsonl",
                "task733_operating_connection_edges.jsonl",
                "task733_non_operating_modifier_edges.jsonl",
                "task733_guardrail_violations.jsonl",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            quality = artifacts["quality"]
            operating_edges = artifacts["operating_edges"]
            modifier_edges = artifacts["modifier_edges"]
            violations = artifacts["violations"]
            decision = artifacts["decision"].iloc[0]

            self.assertEqual(len(quality), 5302)
            self.assertGreaterEqual(quality["permission_state"].nunique(), 3)
            self.assertGreaterEqual(len(operating_edges), 0)
            self.assertGreater(len(modifier_edges), 0)
            self.assertEqual(int(quality["can_create_operating_fact_flag"].sum()), 0)
            self.assertEqual(int(quality["backtest_eligible_flag"].sum()), 0)
            self.assertEqual(int(violations["violation_count"].sum()), 0)
            self.assertEqual(decision["backtest_permission"], "FAIL")


if __name__ == "__main__":
    unittest.main()
