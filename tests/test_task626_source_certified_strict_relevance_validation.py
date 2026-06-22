from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task626_source_certified_strict_relevance_validation import (
    build_task626_source_certified_strict_relevance_validation,
)


class Task626SourceCertifiedStrictRelevanceValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task626_source_certified_strict_relevance_validation()

    def test_task624_rule_fails_under_strict_source_relevance(self) -> None:
        decision = self.artifacts["task_626_decision"].iloc[0]

        self.assertEqual(decision["decision"], "FAIL_TASK624_AEROSPACE_RULE_UNDER_STRICT_SOURCE_RELEVANCE")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["task624_rule_certified_pass_flag"]), 0)
        self.assertEqual(int(decision["strict_recent_oos_aerospace_risk_off_removed_count"]), 0)

    def test_policy_only_linkage_is_disallowed(self) -> None:
        attachment = self.artifacts["task_626_strict_trade_event_attachment"]
        pass_fail = self.artifacts["task_626_pass_fail_matrix"]

        self.assertEqual(int(attachment["policy_only_link_disallowed_flag"].min()), 1)
        self.assertEqual(int(pass_fail[pass_fail["gate"].eq("policy_only_link_disallowed")]["pass_flag"].iloc[0]), 1)
        self.assertEqual(int(pass_fail[pass_fail["gate"].eq("task624_aerospace_rule_source_certified")]["pass_flag"].iloc[0]), 0)

    def test_strict_policy_does_not_improve_recent_oos(self) -> None:
        policy = self.artifacts["task_626_strict_policy_variant_evaluation"]
        original = policy[policy["policy_variant"].eq("original_turboquant") & policy["split_name"].eq("recent_oos")].iloc[0]
        strict = policy[policy["policy_variant"].eq("hold_strict_aerospace_risk_off") & policy["split_name"].eq("recent_oos")].iloc[0]

        self.assertEqual(int(original["trade_count"]), int(strict["trade_count"]))
        self.assertEqual(float(original["avg_net_return_pct"]), float(strict["avg_net_return_pct"]))

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task626_source_certified_strict_relevance_validation(out_dir=out_dir)

            self.assertTrue((out_dir / "task_626_source_certified_strict_relevance_validation.md").exists())
            self.assertTrue((out_dir / "task_626_decision.csv").exists())
            self.assertTrue((out_dir / "task_626_pass_fail_matrix.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_626_strict_trade_event_attachment"]), 100)


if __name__ == "__main__":
    unittest.main()
