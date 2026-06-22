from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task609p_plugin_utilization_map import build_task609p_plugin_utilization_map


class Task609PPluginUtilizationMapTest(unittest.TestCase):
    def test_public_equity_and_data_analytics_are_p0(self) -> None:
        artifacts = build_task609p_plugin_utilization_map()
        priority = artifacts["plugin_priority_map"]
        p0_plugins = set(priority.loc[priority["priority"].eq("P0"), "plugin"].astype(str))

        self.assertIn("Public Equity Investing", p0_plugins)
        self.assertIn("Data Analytics", p0_plugins)
        self.assertNotIn("Investment Banking", p0_plugins)

    def test_decision_preserves_not_accepted_and_forbidden_capital(self) -> None:
        artifacts = build_task609p_plugin_utilization_map()
        decision = artifacts["task_609p_decision"].iloc[0]

        self.assertEqual(decision["decision"], "USE_PUBLIC_EQUITY_AND_DATA_ANALYTICS_AS_P0_IB_AS_P2_CONTEXT")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["deployment_status"], "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")

    def test_guardrails_block_direct_trade_and_acceptance_changes(self) -> None:
        artifacts = build_task609p_plugin_utilization_map()
        guardrails = artifacts["plugin_guardrails"]
        names = set(guardrails["guardrail"].astype(str))

        self.assertIn("no_plugin_changes_acceptance", names)
        self.assertIn("no_llm_direct_trade", names)
        self.assertIn("alpaca_market_data_not_broker_truth", names)
        self.assertIn("quartr_provider_sequence", names)

    def test_source_lane_map_routes_quartr_alpaca_and_widgets(self) -> None:
        artifacts = build_task609p_plugin_utilization_map()
        source_lanes = artifacts["task609_source_lane_plugin_map"]
        tools = set(source_lanes["preferred_app_or_tool"].astype(str))

        self.assertIn("Quartr", tools)
        self.assertIn("Alpaca", tools)
        self.assertIn("datascienceWidgets", tools)

    def test_report_artifacts_are_written_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            build_task609p_plugin_utilization_map(out_dir=out_dir)

            self.assertTrue((out_dir / "task_609p_plugin_utilization_map.md").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertTrue((out_dir / "plugin_priority_map.csv").exists())
            self.assertTrue((out_dir / "plugin_guardrails.csv").exists())


if __name__ == "__main__":
    unittest.main()
