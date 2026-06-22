from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task624_big_event_score_action_validation import (
    build_task624_big_event_score_action_validation,
)


class Task624BigEventScoreActionValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task624_big_event_score_action_validation()

    def test_decision_rejects_global_risk_and_keeps_strategy_not_accepted(self) -> None:
        decision = self.artifacts["task_624_decision"].iloc[0]

        self.assertEqual(decision["decision"], "PASS_AEROSPACE_SCORE_ACTION_DIAGNOSTIC_REJECT_GLOBAL_RISK_NOT_ACCEPTED")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["semantic_scores_used_in_assignment_flag"]), 0)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_aerospace_risk_off_improves_recent_but_global_risk_is_rejected(self) -> None:
        policy = self.artifacts["task_624_policy_variant_evaluation"]
        original_recent = policy[policy["policy_variant"].eq("original_turboquant") & policy["split_name"].eq("recent_oos")].iloc[0]
        aero_recent = policy[policy["policy_variant"].eq("hold_aerospace_risk_off") & policy["split_name"].eq("recent_oos")].iloc[0]
        global_recent = policy[policy["policy_variant"].eq("reject_global_risk_off") & policy["split_name"].eq("recent_oos")].iloc[0]

        self.assertGreater(float(aero_recent["avg_net_return_pct"]), float(original_recent["avg_net_return_pct"]))
        self.assertLess(float(global_recent["avg_net_return_pct"]), float(original_recent["avg_net_return_pct"]))

    def test_company_direct_support_is_still_missing(self) -> None:
        attachment = self.artifacts["task_624_trade_event_score_attachment"]
        pass_fail = self.artifacts["task_624_pass_fail_matrix"]
        gate = pass_fail[pass_fail["gate"].eq("company_direct_support_still_missing")].iloc[0]

        self.assertEqual(int(attachment["support_entry_candidate_count"].sum()), 0)
        self.assertEqual(int(gate["pass_flag"]), 1)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task624_big_event_score_action_validation(out_dir=out_dir)

            self.assertTrue((out_dir / "task_624_big_event_score_action_validation.md").exists())
            self.assertTrue((out_dir / "task_624_trade_event_score_attachment.csv").exists())
            self.assertTrue((out_dir / "task_624_policy_variant_evaluation.csv").exists())
            self.assertTrue((out_dir / "task_624_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_624_trade_event_score_attachment"]), 100)


if __name__ == "__main__":
    unittest.main()
