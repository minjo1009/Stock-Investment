from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd


TASKS = {
    "713": Path("docs/reports/task_713_evidence_provenance_brain"),
    "714": Path("docs/reports/task_714_economic_transmission_brain"),
    "715": Path("docs/reports/task_715_market_pricing_acceptance_brain"),
    "716": Path("docs/reports/task_716_portfolio_competition_brain"),
    "717": Path("docs/reports/task_717_decision_invalidation_risk_brain"),
}


def assert_core_contract(test: unittest.TestCase, panel: pd.DataFrame) -> None:
    test.assertEqual(len(panel), 5265)
    test.assertEqual(int(panel["source_event_available_flag"].sum()), 2445)
    test.assertEqual(int(panel["translator_output_is_action_flag"].sum()), 0)
    test.assertEqual(int(panel["outcome_used_for_assignment_flag"].sum()), 0)
    test.assertEqual(int(panel["future_price_used_for_assignment_flag"].sum()), 0)
    test.assertEqual(int(panel["missing_source_used_as_negative_flag"].sum()), 0)
    test.assertEqual(int(panel["macro_used_for_assignment_flag"].sum()), 0)
    test.assertEqual(set(panel["real_capital_status"]), {"FORBIDDEN"})


class Task713EvidenceProvenanceBrainTest(unittest.TestCase):
    def test_artifacts_and_contract(self) -> None:
        required = [
            "task713_evidence_provenance_panel.csv",
            "task713_evidence_strength_matrix.csv",
            "task713_source_gap_audit.csv",
            "task713_governance_audit.csv",
            "task_713_decision.csv",
            "task_713_pass_fail_matrix.csv",
            "task_713_evidence_provenance_brain.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASKS["713"] / name).exists(), name)
        panel = pd.read_csv(TASKS["713"] / "task713_evidence_provenance_panel.csv")
        assert_core_contract(self, panel)
        self.assertGreaterEqual(panel["evidence_brain_state"].nunique(), 5)
        self.assertIn("source_gap_unknown_not_negative", set(panel["evidence_brain_state"]))


class Task714EconomicTransmissionBrainTest(unittest.TestCase):
    def test_artifacts_and_contract(self) -> None:
        required = [
            "task714_economic_transmission_panel.csv",
            "task714_mechanism_interaction_matrix.csv",
            "task714_financing_quality_decomposition.csv",
            "task714_governance_audit.csv",
            "task_714_decision.csv",
            "task_714_pass_fail_matrix.csv",
            "task_714_economic_transmission_brain.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASKS["714"] / name).exists(), name)
        panel = pd.read_csv(TASKS["714"] / "task714_economic_transmission_panel.csv")
        assert_core_contract(self, panel)
        self.assertGreaterEqual(panel["economic_transmission_state"].nunique(), 6)
        self.assertIn("capital_need_overhang_vs_growth_question", set(panel["economic_transmission_state"]))


class Task715MarketPricingAcceptanceBrainTest(unittest.TestCase):
    def test_artifacts_and_contract(self) -> None:
        required = [
            "task715_market_pricing_acceptance_panel.csv",
            "task715_priced_vs_unpriced_matrix.csv",
            "task715_price_acceptance_failure_audit.csv",
            "task715_governance_audit.csv",
            "task_715_decision.csv",
            "task_715_pass_fail_matrix.csv",
            "task_715_market_pricing_acceptance_brain.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASKS["715"] / name).exists(), name)
        panel = pd.read_csv(TASKS["715"] / "task715_market_pricing_acceptance_panel.csv")
        assert_core_contract(self, panel)
        self.assertGreaterEqual(panel["market_pricing_brain_state"].nunique(), 5)
        self.assertIn("source_gap_no_market_pricing_claim", set(panel["market_pricing_brain_state"]))


class Task716PortfolioCompetitionBrainTest(unittest.TestCase):
    def test_artifacts_contract_and_guardrail(self) -> None:
        required = [
            "task716_slot_competition_panel.csv",
            "task716_same_timestamp_slot_matrix.csv",
            "task716_exposure_cluster_audit.csv",
            "task716_winner_damage_audit.csv",
            "task716_governance_audit.csv",
            "task_716_decision.csv",
            "task_716_pass_fail_matrix.csv",
            "task_716_portfolio_competition_brain.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASKS["716"] / name).exists(), name)
        panel = pd.read_csv(TASKS["716"] / "task716_slot_competition_panel.csv")
        assert_core_contract(self, panel)
        self.assertGreaterEqual(panel["portfolio_brain_state"].nunique(), 5)
        self.assertTrue(panel["same_timestamp_context_rank"].notna().all())
        damage = pd.read_csv(TASKS["716"] / "task716_winner_damage_audit.csv")
        self.assertEqual(int(damage["top50_winner_count_eval_only"].sum()), 50)
        self.assertEqual(int(damage["bottom50_loser_count_eval_only"].sum()), 50)
        self.assertEqual(int(damage["outcome_used_for_assignment_flag"].sum()), 0)


class Task717DecisionInvalidationRiskBrainTest(unittest.TestCase):
    def test_artifacts_contract_and_guardrail(self) -> None:
        required = [
            "task717_decision_invalidation_panel.csv",
            "task717_invalidation_map.csv",
            "task717_risk_budget_explanation.csv",
            "task717_final_brain_guardrail.csv",
            "task717_governance_audit.csv",
            "task_717_decision.csv",
            "task_717_pass_fail_matrix.csv",
            "task_717_decision_invalidation_risk_brain.md",
            "artifact_manifest.csv",
        ]
        for name in required:
            self.assertTrue((TASKS["717"] / name).exists(), name)
        panel = pd.read_csv(TASKS["717"] / "task717_decision_invalidation_panel.csv")
        assert_core_contract(self, panel)
        self.assertGreaterEqual(panel["final_brain_state"].nunique(), 6)
        self.assertTrue(panel["invalidation_condition"].astype(str).str.len().gt(0).all())
        guardrail = pd.read_csv(TASKS["717"] / "task717_final_brain_guardrail.csv")
        self.assertEqual(int(guardrail["top50_winner_count"].sum()), 50)
        self.assertEqual(int(guardrail["bottom50_loser_count"].sum()), 50)
        self.assertEqual(int(guardrail["outcome_used_for_assignment_flag"].sum()), 0)
        decision = pd.read_csv(TASKS["717"] / "task_717_decision.csv").iloc[0]
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
