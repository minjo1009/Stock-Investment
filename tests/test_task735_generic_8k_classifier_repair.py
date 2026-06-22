from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task735_generic_8k_classifier_repair import build_task735
from src.backtest.generic_8k_classifier import classify_generic_8k_text


class Task735Generic8KClassifierRepairTest(unittest.TestCase):
    def test_material_agreement_alone_is_not_operating_supported(self) -> None:
        result = classify_generic_8k_text("Item 1.01 Entry into a Material Definitive Agreement. Purchase Agreement transaction.")

        self.assertNotEqual(result.permission_state, "connection_supported")
        self.assertEqual(result.operating_supported_flag, 0)
        self.assertEqual(result.operating_candidate_flag, 0)

    def test_compensation_award_is_not_operating(self) -> None:
        result = classify_generic_8k_text("Restricted stock unit awards, performance stock unit awards, and stock option grant agreement.")

        self.assertEqual(result.agreement_family_state, "compensation_award_context")
        self.assertEqual(result.permission_state, "not_applicable")
        self.assertEqual(result.operating_candidate_flag, 0)

    def test_director_and_severance_are_not_operating(self) -> None:
        director = classify_generic_8k_text("The Board appointed Jane Doe as a Class III director and audit committee member.")
        severance = classify_generic_8k_text("The company adopted a change in control severance benefits policy.")

        self.assertEqual(director.agreement_family_state, "governance_board_context")
        self.assertEqual(director.permission_state, "modifier_only")
        self.assertEqual(director.operating_candidate_flag, 0)
        self.assertEqual(severance.agreement_family_state, "severance_or_change_in_control_context")
        self.assertEqual(severance.permission_state, "modifier_only")
        self.assertEqual(severance.operating_candidate_flag, 0)

    def test_financing_routes_out_of_operating(self) -> None:
        result = classify_generic_8k_text("Securities Purchase Agreement with warrants and convertible notes. Use of proceeds for growth.")

        self.assertEqual(result.agreement_family_state, "financing_credit_context")
        self.assertEqual(result.permission_state, "review_required")
        self.assertEqual(result.operating_candidate_flag, 0)

    def test_real_customer_contract_can_be_supported_review_only(self) -> None:
        result = classify_generic_8k_text(
            "Customer purchase order and supply agreement for production capacity expansion. "
            "The contract award includes revenue contribution and backlog impact."
        )

        self.assertEqual(result.agreement_family_state, "supply_or_customer_contract_context")
        self.assertEqual(result.operating_transmission_state, "operating_transmission_supported")
        self.assertEqual(result.permission_state, "connection_supported")
        self.assertEqual(result.operating_candidate_flag, 1)
        self.assertEqual(result.operating_supported_flag, 1)

    def test_task735_build_outputs_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task735(out_dir=out_dir)

            for filename in [
                "task735_generic_8k_classification.csv",
                "task735_agreement_family_distribution.csv",
                "task735_task734_prior_candidate_reclassification.csv",
                "task735_guardrail.csv",
                "task735_gpt_review_summary.csv",
                "task_735_decision.csv",
                "task_735_pass_fail_matrix.csv",
                "task_735_generic_8k_classifier_repair.md",
                "task735_generic_8k_classification.jsonl",
                "task735_task734_prior_candidate_reclassification.jsonl",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            classification = artifacts["classification"]
            prior = artifacts["prior_reclass"]
            guardrail = artifacts["guardrail"]
            decision = artifacts["decision"].iloc[0]

            self.assertEqual(len(classification), 95)
            self.assertEqual(len(prior), 9)
            self.assertEqual(int(prior["operating_supported_flag"].fillna(0).sum()), 0)
            self.assertGreaterEqual(int(prior["task735_repair_state"].str.contains("false_positive_repaired", na=False).sum()), 8)
            self.assertEqual(int(guardrail["pass_flag"].min()), 1)
            self.assertEqual(decision["backtest_permission"], "FAIL")


if __name__ == "__main__":
    unittest.main()
