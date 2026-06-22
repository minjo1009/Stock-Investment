from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task614_p0_intelligence_source_attachment import (
    build_task614_p0_intelligence_source_attachment,
)


class Task614P0IntelligenceSourceAttachmentTest(unittest.TestCase):
    def test_source_store_is_independent_from_entry_linkage(self) -> None:
        with tempfile.TemporaryDirectory() as report_tmp, tempfile.TemporaryDirectory() as artifact_tmp:
            artifacts = build_task614_p0_intelligence_source_attachment(
                out_dir=Path(report_tmp),
                artifact_dir=Path(artifact_tmp),
                fetch_sources=False,
            )
            event_store = artifacts["p0_intelligence_events"]
            linkage = artifacts["entry_p0_intelligence_linkage"]

            self.assertGreater(len(event_store), 1000)
            self.assertNotIn("lifecycle_id", event_store.columns)
            self.assertIn("lifecycle_id", linkage.columns)
            self.assertTrue((Path(artifact_tmp) / "p0_intelligence_event_store.csv").exists())
            self.assertTrue((Path(artifact_tmp) / "source_collection_status.csv").exists())
            self.assertTrue((Path(artifact_tmp) / "artifact_manifest.csv").exists())

    def test_p0_lanes_attach_but_do_not_promote_strategy(self) -> None:
        artifacts = build_task614_p0_intelligence_source_attachment(fetch_sources=False)
        decision = artifacts["task_614_decision"].iloc[0]
        coverage = artifacts["source_lane_attachment_status"]

        self.assertEqual(decision["decision"], "PASS_P0_SOURCE_ATTACHMENT_FAIL_EVENT_PROMOTION")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)
        self.assertGreaterEqual(int(coverage[coverage["priority"].eq("P0")]["coverage_status"].eq("ATTACHED").sum()), 3)

    def test_best_p0_event_stays_below_diagnostic_gate(self) -> None:
        artifacts = build_task614_p0_intelligence_source_attachment(fetch_sources=False)
        decision = artifacts["task_614_decision"].iloc[0]

        self.assertEqual(decision["best_p0_event_scenario"], "passive_13g_pre30d")
        self.assertLess(float(decision["best_p0_failure_rate_lift_pct_point"]), 15.0)
        self.assertEqual(int(decision["p0_event_diagnostic_pass_flag"]), 0)
        self.assertEqual(int(decision["gpt_or_plugin_used_as_source_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
