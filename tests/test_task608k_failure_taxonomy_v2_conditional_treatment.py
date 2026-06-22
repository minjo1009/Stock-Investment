from __future__ import annotations

import unittest

from src.backtest.build_task608k_failure_taxonomy_v2_conditional_treatment import (
    build_task608k_failure_taxonomy_v2_conditional_treatment,
)


class Task608KFailureTaxonomyV2ConditionalTreatmentTest(unittest.TestCase):
    def test_taxonomy_v2_splits_all_failures_without_accepting_strategy(self) -> None:
        artifacts = build_task608k_failure_taxonomy_v2_conditional_treatment()
        taxonomy = artifacts["failure_taxonomy_v2_panel"]
        quality = artifacts["failure_taxonomy_v2_quality"]
        decision = artifacts["task_608k_decision"]

        self.assertEqual(len(taxonomy), 35)
        self.assertEqual(float(decision["taxonomy_coverage_rate"].iloc[0]), 1.0)
        self.assertGreaterEqual(float(decision["live_actionable_coverage_rate"].iloc[0]), 0.80)
        self.assertIn("opening_trap_vwap_loss", set(taxonomy["failure_type_v2"]))
        self.assertIn("late_followthrough_failure", set(taxonomy["failure_type_v2"]))
        self.assertEqual(int(decision["pass_flag"].iloc[0]), 1)
        self.assertEqual(int(decision["rule_lock_ready_flag"].iloc[0]), 0)
        self.assertEqual(decision["strategy_acceptance_status"].iloc[0], "NOT_ACCEPTED")
        self.assertEqual(decision["deployment_status"].iloc[0], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(decision["reducer_retry_status"].iloc[0], "CLOSED")
        self.assertIn("live_actionable_coverage_rate", quality.columns)

    def test_risk_rules_and_treatments_are_diagnostic_only(self) -> None:
        artifacts = build_task608k_failure_taxonomy_v2_conditional_treatment()
        risk_rules = artifacts["live_risk_rule_candidate_summary"]
        treatment = artifacts["conditional_treatment_by_failure_type"]

        self.assertGreater(len(risk_rules), 0)
        self.assertGreater(len(treatment), 0)
        self.assertEqual(int(risk_rules["deployment_claim_flag"].max()), 0)
        self.assertEqual(int(treatment["deployment_claim_flag"].max()), 0)
        self.assertEqual(int(risk_rules["label_used_in_assignment_flag"].max()), 0)
        self.assertEqual(int(treatment["label_used_in_assignment_flag"].min()), 1)


if __name__ == "__main__":
    unittest.main()
