from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task612_historical_intelligence_event_backtest import (
    build_task612_historical_intelligence_event_backtest,
)


class Task612HistoricalIntelligenceEventBacktestTest(unittest.TestCase):
    def test_official_events_ingest_but_event_overlay_fails(self) -> None:
        artifacts = build_task612_historical_intelligence_event_backtest(fetch_sources=False)
        decision = artifacts["task_612_decision"].iloc[0]

        self.assertEqual(decision["decision"], "FAIL_OFFICIAL_EVENT_OVERLAY_KEEP_TASK610_REVIEW_TRIGGER")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["deployment_readiness"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["official_source_lanes_active"]), 2)
        self.assertEqual(int(decision["source_lanes_pending"]), 4)
        self.assertEqual(int(decision["event_diagnostic_pass_flag"]), 0)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_best_event_candidate_is_weaker_than_task610_reference(self) -> None:
        artifacts = build_task612_historical_intelligence_event_backtest(fetch_sources=False)
        decision = artifacts["task_612_decision"].iloc[0]
        pass_fail = artifacts["task_612_pass_fail_matrix"]

        self.assertEqual(decision["best_event_scenario"], "earnings_proxy_sec_pre14d")
        self.assertLess(float(decision["best_failure_rate_lift_pct_point"]), 15.0)
        task610_gate = pass_fail[pass_fail["gate"].eq("task610_reference_review_trigger")].iloc[0]
        self.assertEqual(int(task610_gate["pass_flag"]), 1)
        self.assertEqual(decision["best_overall_scenario"], "task610_exact_review_trigger")

    def test_source_gaps_are_reported_not_approximated(self) -> None:
        artifacts = build_task612_historical_intelligence_event_backtest(fetch_sources=False)
        coverage = artifacts["source_lane_coverage"]
        gpt = artifacts["gpt_historical_event_review_pack"]
        linkage = artifacts["entry_event_linkage"]

        pending = coverage[coverage["coverage_status"].eq("SOURCE_LANE_PENDING")]
        self.assertEqual(len(pending), 4)
        self.assertEqual(int(gpt["gpt_output_used_as_source_flag"].max()), 0)
        self.assertEqual(int(linkage["gpt_or_plugin_used_as_source_flag"].max()), 0)
        self.assertEqual(int(linkage["label_used_in_assignment_flag"].max()), 0)

    def test_report_artifacts_are_written_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            build_task612_historical_intelligence_event_backtest(out_dir=out_dir, fetch_sources=False)

            self.assertTrue((out_dir / "task_612_historical_intelligence_event_backtest.md").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertTrue((out_dir / "historical_intelligence_events.csv").exists())
            self.assertTrue((out_dir / "entry_event_linkage.csv").exists())
            self.assertTrue((out_dir / "task_612_decision.csv").exists())


if __name__ == "__main__":
    unittest.main()
