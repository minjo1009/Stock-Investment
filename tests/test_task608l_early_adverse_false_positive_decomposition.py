from __future__ import annotations

import unittest

from src.backtest.build_task608l_early_adverse_false_positive_decomposition import (
    build_task608l_early_adverse_false_positive_decomposition,
)


class Task608LEarlyAdverseFalsePositiveDecompositionTest(unittest.TestCase):
    def test_early_adverse_bucket_is_decomposed_without_rule_lock(self) -> None:
        artifacts = build_task608l_early_adverse_false_positive_decomposition()
        trigger_panel = artifacts["early_adverse_trigger_profile"]
        interaction = artifacts["early_adverse_interaction_matrix"]
        fold_forward = artifacts["early_adverse_fold_forward_validation"]
        decision = artifacts["task_608l_decision"]

        self.assertEqual(len(trigger_panel), 13)
        self.assertEqual(int(trigger_panel["entry_reduce_failure_flag"].sum()), 6)
        self.assertEqual(int(trigger_panel["clean_false_flag"].sum()), 7)
        self.assertGreater(len(interaction), 0)
        self.assertGreater(len(fold_forward), 0)
        self.assertEqual(int(decision["pass_flag"].iloc[0]), 1)
        self.assertEqual(decision["strategy_acceptance_status"].iloc[0], "NOT_ACCEPTED")
        self.assertEqual(decision["deployment_status"].iloc[0], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(decision["rule_lock_status"].iloc[0], "NOT_READY")
        self.assertEqual(decision["reducer_retry_status"].iloc[0], "CLOSED")

    def test_best_interaction_improves_failure_concentration_and_reduces_clean_false(self) -> None:
        artifacts = build_task608l_early_adverse_false_positive_decomposition()
        decision = artifacts["task_608l_decision"].iloc[0]

        self.assertGreater(float(decision["best_interaction_failure_rate"]), float(decision["baseline_failure_rate"]))
        self.assertLess(int(decision["best_interaction_clean_false_count"]), int(decision["baseline_clean_false_count"]))
        self.assertGreaterEqual(int(decision["best_interaction_positive_fold_count"]), 1)


if __name__ == "__main__":
    unittest.main()
