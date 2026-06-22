from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task627_source_text_theme_linkage_validation import (
    build_task627_source_text_theme_linkage_validation,
)


class Task627SourceTextThemeLinkageValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task627_source_text_theme_linkage_validation()

    def test_source_text_diagnostic_passes_but_trading_remains_blocked(self) -> None:
        decision = self.artifacts["task_627_decision"].iloc[0]

        self.assertEqual(decision["decision"], "PASS_SOURCE_TEXT_AEROSPACE_RISK_DIAGNOSTIC_NOT_ACCEPTED")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["source_text_diagnostic_pass_flag"]), 1)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_source_text_hold_improves_recent_and_validation(self) -> None:
        policy = self.artifacts["task_627_policy_variant_evaluation"]
        original_recent = policy[policy["policy_variant"].eq("original_turboquant") & policy["split_name"].eq("recent_oos")].iloc[0]
        text_recent = policy[policy["policy_variant"].eq("hold_source_text_aerospace_risk") & policy["split_name"].eq("recent_oos")].iloc[0]
        original_validation = policy[policy["policy_variant"].eq("original_turboquant") & policy["split_name"].eq("validation")].iloc[0]
        text_validation = policy[policy["policy_variant"].eq("hold_source_text_aerospace_risk") & policy["split_name"].eq("validation")].iloc[0]

        self.assertGreater(float(text_recent["avg_net_return_pct"]), float(original_recent["avg_net_return_pct"]))
        self.assertGreaterEqual(float(text_validation["avg_net_return_pct"]), float(original_validation["avg_net_return_pct"]))
        self.assertLess(int(text_recent["trade_count"]), int(original_recent["trade_count"]))

    def test_source_text_flags_are_not_presence_or_gpt_driven(self) -> None:
        scores = self.artifacts["task_627_source_text_linkage_scores"]
        pass_fail = self.artifacts["task_627_pass_fail_matrix"]

        self.assertGreater(int(scores["source_text_aerospace_risk_flag"].sum()), 0)
        self.assertEqual(int(scores["source_presence_only_used_flag"].sum()), 0)
        self.assertEqual(int(scores["gpt_score_used_as_source_flag"].sum()), 0)
        self.assertEqual(int(pass_fail[pass_fail["gate"].eq("source_text_linkage_exists")]["pass_flag"].iloc[0]), 1)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task627_source_text_theme_linkage_validation(out_dir=out_dir)

            self.assertTrue((out_dir / "task_627_source_text_theme_linkage_validation.md").exists())
            self.assertTrue((out_dir / "task_627_decision.csv").exists())
            self.assertTrue((out_dir / "task_627_policy_variant_evaluation.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_627_trade_text_linkage_attachment"]), 100)


if __name__ == "__main__":
    unittest.main()
