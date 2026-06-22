from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task727_economic_interaction_brain_contract import build_task727
from src.backtest.economic_interaction_brain import (
    EconomicMeaningObject,
    EvidenceObject,
    backtest_gate,
    contract_frame,
    edge_rulebook_frame,
    schema_frame,
)


class Task727EconomicInteractionBrainContractTest(unittest.TestCase):
    def test_contract_module_defines_required_layers_and_fields(self) -> None:
        contract = contract_frame()
        schema = schema_frame()
        edge_rulebook = edge_rulebook_frame()

        self.assertIn("evidence_object", set(contract["contract_layer"]))
        self.assertIn("primitive_fact_object", set(contract["contract_layer"]))
        self.assertIn("economic_meaning_object", set(contract["contract_layer"]))
        self.assertIn("interaction_edge_object", set(contract["contract_layer"]))
        self.assertIn("slot_decision_explanation", set(contract["contract_layer"]))

        required_fields = set(schema["field_name"])
        for field in [
            "contract_value_amount",
            "revenue_run_rate_denominator",
            "prior_guidance_denominator",
            "backlog_denominator",
            "guidance_direction_state",
            "financing_use_of_proceeds_state",
            "price_acceptance_state",
            "same_timestamp_cohort_id",
        ]:
            self.assertIn(field, required_fields)

        self.assertGreaterEqual(len(edge_rulebook), 10)
        self.assertIn("financing_growth_funds_order", set(edge_rulebook["edge_id"]))
        self.assertIn("guidance_reaffirm_after_news", set(edge_rulebook["edge_id"]))
        self.assertTrue((edge_rulebook["assignment_allowed_flag"] == 0).all())

    def test_contract_objects_block_strong_claims_without_source_or_denominator(self) -> None:
        weak_evidence = EvidenceObject(
            source_event_id="x",
            source_family="generic_8k",
            source_url=None,
            filing_type="8-K",
            asof_timestamp="2026-01-01T09:30:00Z",
            raw_text_path=None,
            evidence_span="contract mentioned",
            reject_reason=None,
        )
        meaning = EconomicMeaningObject(missing_denominators=("revenue_run_rate_denominator",))

        self.assertFalse(weak_evidence.certified())
        self.assertFalse(meaning.strong_claim_allowed())

    def test_backtest_gate_requires_clean_data_denominators_and_edges(self) -> None:
        failed = backtest_gate(
            {
                "clean_economic_events": 1,
                "denominator_fields_present": 0,
                "contamination_count": 1,
                "interaction_objects_present": 0,
            }
        )
        passed = backtest_gate(
            {
                "clean_economic_events": 10,
                "denominator_fields_present": 10,
                "contamination_count": 0,
                "interaction_objects_present": 10,
            }
        )

        self.assertEqual(failed["pass_flag"], 0)
        self.assertEqual(passed["pass_flag"], 1)

    def test_task727_outputs_contract_and_blocks_backtest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task727(out_dir=out_dir)

            expected_files = [
                "task727_brain_gap_audit.csv",
                "task727_economic_interaction_contract.csv",
                "task727_required_schema_fields.csv",
                "task727_interaction_edge_rulebook.csv",
                "task727_code_restructure_map.csv",
                "task727_institutional_review_packet.csv",
                "task_727_decision.csv",
                "task_727_pass_fail_matrix.csv",
                "task_727_economic_interaction_brain_contract.md",
                "artifact_manifest.csv",
            ]
            for filename in expected_files:
                self.assertTrue((out_dir / filename).exists(), filename)

            decision = artifacts["decision"].iloc[0]
            self.assertEqual(decision["backtest_permission"], "FAIL")
            self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
            self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

            gap_audit = artifacts["gap_audit"]
            self.assertIn("Task714 economic transmission", set(gap_audit["task_layer"]))
            self.assertEqual(int(gap_audit["contract_pass_flag"].max()), 0)
            self.assertIn("BLOCKER", set(gap_audit["gap_severity"]))

            review = artifacts["review_packet"]
            self.assertEqual(len(review), 5)
            self.assertTrue((review["gpt_response_captured_flag"] == 1).all())


if __name__ == "__main__":
    unittest.main()
