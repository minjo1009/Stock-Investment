from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task610_plugin_assisted_intelligence_backtest import (
    SELECTED_RULE,
    build_task610_plugin_assisted_intelligence_backtest,
)


class Task610PluginAssistedIntelligenceBacktestTest(unittest.TestCase):
    def test_selected_plugin_review_candidate_passes_but_rule_lock_fails(self) -> None:
        artifacts = build_task610_plugin_assisted_intelligence_backtest()
        decision = artifacts["task_610_decision"].iloc[0]

        self.assertEqual(decision["decision"], "PASS_PLUGIN_REVIEW_CANDIDATE_FAIL_RULE_LOCK")
        self.assertEqual(int(decision["pass_flag"]), 1)
        self.assertEqual(int(decision["rule_lock_pass_flag"]), 0)
        self.assertEqual(decision["selected_rule"], SELECTED_RULE)
        self.assertEqual(int(decision["selected_trigger_count"]), 6)
        self.assertEqual(int(decision["selected_failure_count"]), 5)
        self.assertEqual(int(decision["selected_clean_false_count"]), 1)
        self.assertGreater(float(decision["selected_failure_rate"]), float(decision["baseline_failure_rate"]))

    def test_assignment_does_not_use_labels_or_plugin_direct_trade(self) -> None:
        artifacts = build_task610_plugin_assisted_intelligence_backtest()
        profile = artifacts["selected_plugin_review_rule_profile"].iloc[0]
        candidates = artifacts["plugin_review_candidate_summary"]

        self.assertEqual(int(profile["label_used_in_assignment_flag"]), 0)
        self.assertEqual(int(profile["plugin_direct_trade_flag"]), 0)
        self.assertEqual(int(candidates["label_used_in_assignment_flag"].max()), 0)
        self.assertEqual(int(candidates["plugin_direct_trade_flag"].max()), 0)

    def test_gpt_attempt_is_recorded_but_not_used(self) -> None:
        artifacts = build_task610_plugin_assisted_intelligence_backtest()
        gpt = artifacts["gpt_review_status"].iloc[0]
        decision = artifacts["task_610_decision"].iloc[0]

        self.assertEqual(gpt["attempt_status"], "ATTEMPTED_BUT_NOT_CONFIRMED")
        self.assertEqual(int(gpt["safe_payload_used_flag"]), 1)
        self.assertEqual(int(gpt["gpt_output_used_flag"]), 0)
        self.assertEqual(int(decision["gpt_output_used_flag"]), 0)

    def test_plugin_source_status_keeps_quartr_and_alpaca_caveats(self) -> None:
        artifacts = build_task610_plugin_assisted_intelligence_backtest()
        source_probe = artifacts["plugin_source_probe_status"]
        statuses = set(source_probe["probe_status"].astype(str))

        self.assertIn("SINGLE_SYMBOL_QUOTE_OBSERVED", statuses)
        self.assertIn("TIMEOUT", statuses)
        self.assertIn("BLOCKED_PROVIDER_GUIDE_RESOURCE_UNAVAILABLE", statuses)
        self.assertIn("AVAILABLE_FOR_VALIDATED_ARTIFACTS", statuses)

    def test_report_artifacts_are_written_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            build_task610_plugin_assisted_intelligence_backtest(out_dir=out_dir)

            self.assertTrue((out_dir / "task_610_plugin_assisted_intelligence_backtest.md").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertTrue((out_dir / "plugin_review_candidate_summary.csv").exists())
            self.assertTrue((out_dir / "task_610_decision.csv").exists())


if __name__ == "__main__":
    unittest.main()
