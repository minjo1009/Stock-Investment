from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task620a_actionable_oos_treatment_map import build_task620a_actionable_oos_treatment_map


class Task620AActionableOosTreatmentMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task620a_actionable_oos_treatment_map()

    def test_first_treatment_is_aerospace_entry_block(self) -> None:
        decision = self.artifacts["task_620a_decision"].iloc[0]
        effects = self.artifacts["task_620a_actionable_trigger_effects"]
        recent = effects[
            effects["treatment_name"].eq("block_theme_aerospace_defense")
            & effects["split_name"].eq("recent_oos")
        ].iloc[0]

        self.assertEqual(decision["first_treatment_to_test"], "block_theme_aerospace_defense")
        self.assertEqual(decision["first_treatment_class"], "ENTRY_BLOCK")
        self.assertGreater(float(recent["kept_avg_net_return_pct"]), 5.0)
        self.assertLessEqual(float(recent["kept_entry_reduce_failure_rate"]), 0.50)

    def test_failure_buckets_have_action_classes(self) -> None:
        treatments = self.artifacts["task_620a_failure_bucket_treatment_map"]
        mapping = {row.primary_failure_taxonomy: row.treatment_class for row in treatments.itertuples()}

        self.assertEqual(mapping["theme_specific_collapse_aerospace_defense"], "ENTRY_BLOCK")
        self.assertEqual(mapping["trailing_stop_path_failure"], "EXIT_TREATMENT")
        self.assertEqual(mapping["broad_event_support_without_recent_ir_proxy"], "SOURCE_RETYPING")
        self.assertEqual(mapping["late_midday_continuation_decay"], "DELAY_ENTRY")

    def test_gpt_review_is_not_source_truth(self) -> None:
        gpt = self.artifacts["task_620a_gpt_treatment_review_status"].iloc[0]
        decision = self.artifacts["task_620a_decision"].iloc[0]

        self.assertEqual(int(gpt["gpt_output_used_as_source_flag"]), 0)
        self.assertEqual(int(decision["gpt_or_plugin_used_as_source_flag"]), 0)
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task620a_actionable_oos_treatment_map(out_dir=out_dir)

            self.assertTrue((out_dir / "task_620a_actionable_oos_treatment_map.md").exists())
            self.assertTrue((out_dir / "task_620a_actionable_trigger_effects.csv").exists())
            self.assertTrue((out_dir / "task_620a_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreaterEqual(len(artifacts["task_620a_failure_bucket_treatment_map"]), 6)


if __name__ == "__main__":
    unittest.main()
