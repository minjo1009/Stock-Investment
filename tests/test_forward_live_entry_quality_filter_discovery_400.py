from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_forward_live_entry_quality_filter_discovery_400 import (
    build_forward_live_entry_quality_filter_discovery_400,
)


class TestForwardLiveEntryQualityFilterDiscovery400(unittest.TestCase):
    def test_entry_only_panel_blocks_outcome_features_and_builds_filters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "false_positive_panel.csv"
            pd.DataFrame(
                [
                    _row("L1", "validation", "add_scale_success", 1),
                    _row("L2", "validation", "entry_reduce_failure", 0),
                    _row("L3", "recent_oos", "add_only_weak", 0),
                    _row("L4", "recent_oos", "post_cost_false_positive", 0),
                ]
            ).to_csv(panel, index=False, encoding="utf-8-sig")

            artifacts = build_forward_live_entry_quality_filter_discovery_400(
                false_positive_panel_path=panel,
                out_dir=root / "out",
            )

            features = artifacts.entry_quality_feature_panel
            self.assertEqual(int(features[features["lifecycle_id"].eq("L1")]["entry_quality_target"].iloc[0]), 1)
            self.assertEqual(int(features[features["lifecycle_id"].eq("L2")]["entry_quality_target"].iloc[0]), 0)
            for blocked in ["return_from_entry", "net_return_from_entry", "exit_reason", "reduce_flag", "add_flag", "scale_flag"]:
                self.assertNotIn(blocked, features.columns)

            leakage = artifacts.entry_quality_leakage_audit
            self.assertEqual(int(leakage["leakage_pass_flag"].min()), 1)
            candidates = artifacts.entry_filter_candidate_audit
            self.assertTrue((candidates["diagnostic_only_flag"] == 1).all())
            self.assertIn("oracle_add_scale_upper_bound", set(candidates["candidate_filter_name"]))
            decision = artifacts.task_400_decision.iloc[0]
            self.assertEqual(str(decision["task_400_verdict"]), "COMPLETE_PASS")
            self.assertEqual(int(decision["oracle_filter_used_for_acceptance_flag"]), 0)
            self.assertTrue((root / "out" / "task_400_forward_live_entry_quality_filter_discovery.md").exists())


def _row(lifecycle_id: str, split: str, group: str, target: int) -> dict:
    return {
        "policy_name": "cost_constrained_forward_live_strict",
        "policy_accepted_lifecycle_flag": 1,
        "lifecycle_id": lifecycle_id,
        "symbol": "NVDA",
        "theme": "ai_semiconductors",
        "role": "leader",
        "entry_ts": "2026-01-01T14:30:00Z",
        "exit_ts": "2026-01-01T18:30:00Z",
        "anchored_split": split,
        "entry_hour": 14,
        "entry_minute": 30,
        "entry_time_bucket": "14:30",
        "failure_group": group,
        "return_from_entry": 0.03 if target else -0.01,
        "net_return_from_entry": 0.02 if target else -0.02,
        "exit_reason": "fixture",
        "add_flag": target,
        "scale_flag": target,
        "reduce_flag": 1 - target,
        "add_scale_flag": target,
        "forward_live_breadth_positive_rate": 0.7,
        "forward_live_avg_symbol_return": 0.01,
        "forward_live_avg_intraday_range": 0.02,
        "forward_live_liquidity_ratio": 1.2,
        "forward_live_breadth_regime": "broad_participation",
        "forward_live_volatility_regime": "mid_vol",
        "forward_live_liquidity_regime": "liquidity_expansion",
        "forward_live_market_regime": "risk_on_broad",
        "forward_live_theme_return": 0.02,
        "forward_live_theme_rank": 1,
        "forward_live_theme_leadership_regime": "theme_leader",
        "base_round_trip_cost": 0.00125,
        "volatility_penalty": 0.002,
        "spread_penalty": 0.0,
        "estimated_total_cost": 0.004,
    }


if __name__ == "__main__":
    unittest.main()
