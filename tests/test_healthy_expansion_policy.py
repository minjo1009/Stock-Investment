from __future__ import annotations

import unittest

from src.risk.healthy_expansion_policy import (
    HealthyExpansionPolicyInputs,
    evaluate_healthy_expansion_policy,
)


class TestHealthyExpansionPolicy(unittest.TestCase):
    def test_healthy_expansion_relaxes_size(self) -> None:
        decision = evaluate_healthy_expansion_policy(
            HealthyExpansionPolicyInputs(
                quality_label="HEALTHY_EXPANSION",
                expansion_score=0.75,
                fragility_score=0.30,
                confidence=0.90,
                state_label="NORMAL",
                continuation_risk_score=0.40,
                staged_gate_stage="stage_1_probe",
                staged_add_allowed=False,
                factor_budget_allowed=True,
                factor_budget_multiplier=1.0,
                gross_exposure_multiplier=1.0,
                current_size_multiplier=0.20,
            )
        )
        self.assertIn(decision.policy_label, {"RELAX_SIZE_ONLY", "RELAX_SIZE_AND_ADD"})
        self.assertGreater(decision.final_size_multiplier, 0.20)

    def test_healthy_expansion_can_allow_add(self) -> None:
        decision = evaluate_healthy_expansion_policy(
            HealthyExpansionPolicyInputs(
                quality_label="HEALTHY_EXPANSION",
                expansion_score=0.80,
                fragility_score=0.20,
                confidence=0.90,
                state_label="ELEVATED",
                continuation_risk_score=0.40,
                staged_gate_stage="stage_1_probe",
                staged_add_allowed=False,
                factor_budget_allowed=True,
                factor_budget_multiplier=1.0,
                gross_exposure_multiplier=1.0,
                current_size_multiplier=0.25,
            )
        )
        self.assertTrue(decision.final_add_allowed)

    def test_fragile_crowding_never_relaxes(self) -> None:
        decision = evaluate_healthy_expansion_policy(
            HealthyExpansionPolicyInputs(
                quality_label="FRAGILE_CROWDING",
                expansion_score=0.20,
                fragility_score=0.80,
                confidence=0.90,
                state_label="CROWDED",
                continuation_risk_score=0.60,
                staged_gate_stage="stage_1_probe",
                staged_add_allowed=False,
                factor_budget_allowed=True,
                factor_budget_multiplier=1.0,
                gross_exposure_multiplier=0.40,
                current_size_multiplier=0.10,
            )
        )
        self.assertEqual(decision.policy_label, "KEEP_SUPPRESSED")
        self.assertFalse(decision.final_add_allowed)

    def test_dislocation_never_relaxes(self) -> None:
        decision = evaluate_healthy_expansion_policy(
            HealthyExpansionPolicyInputs(
                quality_label="HEALTHY_EXPANSION",
                expansion_score=0.90,
                fragility_score=0.20,
                confidence=0.90,
                state_label="DISLOCATION",
                continuation_risk_score=0.40,
                staged_gate_stage="stage_2_add",
                staged_add_allowed=True,
                factor_budget_allowed=True,
                factor_budget_multiplier=1.0,
                gross_exposure_multiplier=0.20,
                current_size_multiplier=0.10,
            )
        )
        self.assertEqual(decision.policy_label, "KEEP_SUPPRESSED")

    def test_factor_budget_violation_prevents_relaxation(self) -> None:
        decision = evaluate_healthy_expansion_policy(
            HealthyExpansionPolicyInputs(
                quality_label="HEALTHY_EXPANSION",
                expansion_score=0.90,
                fragility_score=0.20,
                confidence=0.90,
                state_label="NORMAL",
                continuation_risk_score=0.40,
                staged_gate_stage="stage_2_add",
                staged_add_allowed=True,
                factor_budget_allowed=False,
                factor_budget_multiplier=0.0,
                gross_exposure_multiplier=1.0,
                current_size_multiplier=0.10,
            )
        )
        self.assertEqual(decision.policy_label, "KEEP_SUPPRESSED")

    def test_low_confidence_prevents_aggressive_relaxation(self) -> None:
        decision = evaluate_healthy_expansion_policy(
            HealthyExpansionPolicyInputs(
                quality_label="HEALTHY_EXPANSION",
                expansion_score=0.90,
                fragility_score=0.20,
                confidence=0.20,
                state_label="NORMAL",
                continuation_risk_score=0.40,
                staged_gate_stage="stage_1_probe",
                staged_add_allowed=False,
                factor_budget_allowed=True,
                factor_budget_multiplier=1.0,
                gross_exposure_multiplier=1.0,
                current_size_multiplier=0.10,
            )
        )
        self.assertEqual(decision.policy_label, "KEEP_SUPPRESSED")

    def test_unknown_remains_conservative(self) -> None:
        decision = evaluate_healthy_expansion_policy(
            HealthyExpansionPolicyInputs(
                quality_label="UNKNOWN",
                expansion_score=0.50,
                fragility_score=0.50,
                confidence=0.20,
                state_label="NORMAL",
                continuation_risk_score=0.40,
                staged_gate_stage="delayed_probe",
                staged_add_allowed=False,
                factor_budget_allowed=True,
                factor_budget_multiplier=1.0,
                gross_exposure_multiplier=1.0,
                current_size_multiplier=0.10,
            )
        )
        self.assertEqual(decision.policy_label, "KEEP_SUPPRESSED")

    def test_neutral_does_not_become_aggressive(self) -> None:
        decision = evaluate_healthy_expansion_policy(
            HealthyExpansionPolicyInputs(
                quality_label="NEUTRAL_PARTICIPATION",
                expansion_score=0.55,
                fragility_score=0.45,
                confidence=0.80,
                state_label="ELEVATED",
                continuation_risk_score=0.45,
                staged_gate_stage="stage_1_probe",
                staged_add_allowed=False,
                factor_budget_allowed=True,
                factor_budget_multiplier=1.0,
                gross_exposure_multiplier=0.75,
                current_size_multiplier=0.15,
            )
        )
        self.assertFalse(decision.final_add_allowed)
        self.assertNotEqual(decision.policy_label, "RELAX_SIZE_AND_ADD")


if __name__ == "__main__":
    unittest.main()
