from __future__ import annotations

import unittest

from src.backtest.build_task608m_early_adverse_rule_lock_validation import (
    build_task608m_early_adverse_rule_lock_validation,
)


class Task608MEarlyAdverseRuleLockValidationTest(unittest.TestCase):
    def test_candidate_fails_strict_rule_lock(self) -> None:
        artifacts = build_task608m_early_adverse_rule_lock_validation()
        decision = artifacts["task_608m_decision"].iloc[0]

        self.assertEqual(decision["decision"], "FAIL_RULE_LOCK_INSUFFICIENT_SUPPORT")
        self.assertEqual(int(decision["pass_flag"]), 0)
        self.assertEqual(int(decision["candidate_trigger_count"]), 3)
        self.assertEqual(int(decision["eligible_fold_count"]), 0)
        self.assertEqual(int(decision["positive_test_count"]), 0)
        self.assertEqual(int(decision["winner_destruction_risk_flag"]), 1)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["deployment_status"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(decision["rule_lock_status"], "FAILED")
        self.assertEqual(decision["reducer_retry_status"], "CLOSED")

    def test_threshold_neighborhood_is_too_small_despite_some_positive_cells(self) -> None:
        artifacts = build_task608m_early_adverse_rule_lock_validation()
        threshold = artifacts["threshold_neighborhood_validation"]
        winner = artifacts["winner_destruction_audit"].iloc[0]

        self.assertGreater(int(threshold["pass_neighborhood_flag"].sum()), 0)
        self.assertLess(int(threshold["pass_neighborhood_flag"].sum()), len(threshold))
        self.assertEqual(int(winner["candidate_clean_false_count"]), 1)
        self.assertGreater(float(winner["clean_false_avg_return_pct"]), 0.0)


if __name__ == "__main__":
    unittest.main()
