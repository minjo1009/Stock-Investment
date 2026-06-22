from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task609_realtime_intelligence_trading_layer import (
    build_task609_realtime_intelligence_trading_layer,
)


class Task609RealtimeIntelligenceTradingLayerTest(unittest.TestCase):
    def test_decision_preserves_non_deployment_status(self) -> None:
        artifacts = build_task609_realtime_intelligence_trading_layer()
        decision = artifacts["task_609_decision"].iloc[0]
        gate_policy = artifacts["intelligence_trading_gate_policy"]

        self.assertEqual(decision["decision"], "BUILD_INTELLIGENCE_LAYER_BEFORE_REFINEMENT")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["deployment_status"], "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["llm_direct_trade_allowed_flag"]), 0)
        self.assertEqual(int(gate_policy["llm_direct_trade_allowed_flag"].sum()), 0)

    def test_event_schema_requires_exact_source_and_time_fields(self) -> None:
        artifacts = build_task609_realtime_intelligence_trading_layer()
        schema = artifacts["intelligence_event_schema"]
        fields = set(schema["field_name"].astype(str))

        required = {
            "intelligence_event_id",
            "source_id",
            "published_at_utc",
            "captured_at_utc",
            "raw_path",
            "evidence_hash",
            "label_leakage_guard",
            "no_trade_if_unverified_flag",
        }
        self.assertTrue(required.issubset(fields))
        self.assertEqual(int(schema.loc[schema["field_name"].isin(required), "required_flag"].min()), 1)

    def test_task608_failures_are_linked_to_information_tests(self) -> None:
        artifacts = build_task609_realtime_intelligence_trading_layer()
        linkage = artifacts["task608_failure_intelligence_linkage"]

        self.assertGreaterEqual(int(linkage["count_from_task608k"].sum()), 27)
        self.assertIn("opening_trap_vwap_loss", set(linkage["task608_failure_type"].astype(str)))
        self.assertIn("late_followthrough_failure", set(linkage["task608_failure_type"].astype(str)))
        self.assertNotIn("", set(linkage["intelligence_test"].astype(str)))

    def test_report_artifacts_are_written_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            build_task609_realtime_intelligence_trading_layer(out_dir=out_dir)

            self.assertTrue((out_dir / "task_609_realtime_intelligence_trading_layer.md").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertTrue((out_dir / "intelligence_source_contract.csv").exists())
            self.assertTrue((out_dir / "intelligence_trading_gate_policy.csv").exists())


if __name__ == "__main__":
    unittest.main()
