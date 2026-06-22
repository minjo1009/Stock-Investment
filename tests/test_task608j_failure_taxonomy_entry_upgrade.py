from __future__ import annotations

import unittest
from pathlib import Path

from src.backtest.build_task608j_failure_taxonomy_entry_upgrade import (
    REPORT_DIR,
    build_task608j_failure_taxonomy_entry_upgrade,
)


class Task608JFailureTaxonomyEntryUpgradeTest(unittest.TestCase):
    def test_taxonomy_and_entry_upgrade_artifacts_remain_diagnostic(self) -> None:
        artifacts = build_task608j_failure_taxonomy_entry_upgrade()
        feature_panel = artifacts["entry_upgrade_feature_panel"]
        taxonomy = artifacts["failure_taxonomy_panel"]
        taxonomy_quality = artifacts["failure_taxonomy_quality"]
        delayed = artifacts["delayed_entry_simulation"]
        staged = artifacts["staged_entry_simulation"]
        confirmation = artifacts["continuation_confirmation_simulation"]
        decisions = artifacts["task_608j_decision"]

        self.assertEqual(len(taxonomy), int(feature_panel["entry_reduce_failure_flag"].sum()))
        self.assertEqual(len(taxonomy), 35)
        self.assertIn("opening_trap", set(taxonomy["failure_type"]))
        self.assertIn("unclassified_mixed_failure", set(taxonomy["failure_type"]))
        self.assertLess(float(taxonomy_quality["taxonomy_coverage_rate"].iloc[0]), 0.70)
        self.assertEqual(int(decisions["pass_flag"].iloc[0]), 0)
        self.assertEqual(decisions["strategy_acceptance_status"].iloc[0], "NOT_ACCEPTED")
        self.assertEqual(decisions["deployment_status"].iloc[0], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")

        required_features = {
            "premarket_high",
            "premarket_vwap",
            "overnight_range_pct",
            "breakout_age_bars",
            "theme_leader_pre_entry_ret",
            "symbol_vs_qqq_pre_entry_ret",
            "gap_abs_percentile_60d",
            "prior_day_volume_ratio_20",
        }
        self.assertTrue(required_features.issubset(set(feature_panel.columns)))
        self.assertGreaterEqual(len(delayed), 4)
        self.assertGreaterEqual(len(staged), 3)
        self.assertEqual(set(confirmation["scenario"]), {
            "confirmation_entry_15m",
            "confirmation_entry_30m",
            "confirmation_entry_60m",
        })

    def test_gpt_review_notes_are_persisted_as_review_only(self) -> None:
        build_task608j_failure_taxonomy_entry_upgrade()
        notes = Path(REPORT_DIR / "gpt_review_notes.md").read_text(encoding="utf-8")

        self.assertIn("external model interpretation only", notes)
        self.assertIn("Reducer retry should remain closed", notes)
        self.assertIn("Task608K", notes)


if __name__ == "__main__":
    unittest.main()
