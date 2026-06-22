from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task630_block_hold_coverage_and_exact_delay_replay import (
    build_task630_block_hold_coverage_and_exact_delay_replay,
)


class Task630BlockHoldCoverageAndExactDelayReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task630_block_hold_coverage_and_exact_delay_replay()

    def test_strategy_remains_not_accepted(self) -> None:
        decision = self.artifacts["task_630_decision"].iloc[0]

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertEqual(int(decision["source_presence_only_used_flag"]), 0)
        self.assertEqual(int(decision["gpt_score_used_as_source_flag"]), 0)
        self.assertEqual(int(decision["label_used_in_assignment_flag"]), 0)

    def test_block_hold_coverage_is_audited(self) -> None:
        coverage = self.artifacts["task_630_block_hold_coverage_audit"]
        pass_fail = self.artifacts["task_630_pass_fail_matrix"]
        all_row = coverage[coverage["symbol"].eq("ALL")].iloc[0]
        gate = pass_fail[pass_fail["gate"].eq("block_hold_coverage_audited")].iloc[0]

        self.assertGreaterEqual(int(all_row["direct_company_negative_registry_count"]), 1)
        self.assertEqual(int(gate["pass_flag"]), 1)

    def test_exact_delay_replay_uses_real_intraday_prices(self) -> None:
        replay = self.artifacts["task_630_exact_delayed_entry_replay"]
        delayed = replay[replay["delay_action_flag"].astype(int).eq(1)]

        self.assertGreater(len(delayed), 0)
        self.assertGreater(int(delayed["delayed_price_available_flag"].sum()), 0)
        self.assertIn(15, set(delayed["delay_minutes"].astype(int).unique()))
        self.assertIn(30, set(delayed["delay_minutes"].astype(int).unique()))
        self.assertIn(60, set(delayed["delay_minutes"].astype(int).unique()))

    def test_policy_includes_exact_delay_variants(self) -> None:
        policy = self.artifacts["task_630_policy_variant_evaluation"]
        variants = set(policy["policy_variant"].unique())

        self.assertIn("block_size_exact_delay_15m", variants)
        self.assertIn("block_size_exact_delay_30m", variants)
        self.assertIn("block_size_exact_delay_60m", variants)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task630_block_hold_coverage_and_exact_delay_replay(out_dir=out_dir)

            self.assertTrue((out_dir / "task_630_block_hold_coverage_and_exact_delay_replay.md").exists())
            self.assertTrue((out_dir / "task_630_expanded_event_linkage_registry.csv").exists())
            self.assertTrue((out_dir / "task_630_exact_delayed_entry_replay.csv").exists())
            self.assertTrue((out_dir / "task_630_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["task_630_exact_delayed_entry_replay"]), 100)


if __name__ == "__main__":
    unittest.main()
