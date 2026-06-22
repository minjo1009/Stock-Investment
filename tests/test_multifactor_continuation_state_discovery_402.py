from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_multifactor_continuation_state_discovery_402 import (
    build_multifactor_continuation_state_discovery_402,
)


class TestMultiFactorContinuationStateDiscovery402(unittest.TestCase):
    def test_archetype_assignment_uses_entry_state_not_labels(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "panel.csv"
            pd.DataFrame(
                [
                    _row("L1", "validation", "add_scale_success", 0.03),
                    _row("L2", "validation", "entry_reduce_failure", -0.02),
                    _row("L3", "recent_oos", "add_scale_success", 0.04),
                    _row("L4", "recent_oos", "add_only_weak", -0.01),
                ]
            ).to_csv(panel, index=False, encoding="utf-8-sig")

            artifacts = build_multifactor_continuation_state_discovery_402(
                lifecycle_panel_path=panel,
                out_dir=root / "out",
            )

            assignment = artifacts.archetype_assignment_panel
            self.assertTrue((assignment["label_used_for_assignment_flag"] == 0).all())
            self.assertTrue((assignment["symbol_session_inference_used_flag"] == 0).all())
            self.assertIn("continuation_archetype_id", assignment.columns)
            self.assertIn("failure_group", assignment.columns)
            self.assertNotIn("failure_group", [
                "market_state",
                "theme_state",
                "entry_state",
                "risk_state",
                "tradability_state",
            ])

            leakage = artifacts.archetype_leakage_audit
            self.assertEqual(int(leakage["leakage_pass_flag"].min()), 1)
            decision = artifacts.task_402_decision.iloc[0]
            self.assertEqual(str(decision["task_402_verdict"]), "COMPLETE_PASS")
            self.assertEqual(int(decision["label_used_for_assignment_flag"]), 0)
            self.assertTrue((root / "out" / "task_402_multifactor_continuation_state_discovery.md").exists())

    def test_identical_state_with_different_outcomes_keeps_same_archetype(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "panel.csv"
            rows = [
                _row("L1", "validation", "add_scale_success", 0.03),
                _row("L2", "validation", "entry_reduce_failure", -0.02),
            ]
            pd.DataFrame(rows).to_csv(panel, index=False, encoding="utf-8-sig")

            artifacts = build_multifactor_continuation_state_discovery_402(
                lifecycle_panel_path=panel,
                out_dir=root / "out",
            )

            archetypes = artifacts.archetype_assignment_panel["continuation_archetype_id"].unique()
            self.assertEqual(len(archetypes), 1)


def _row(lifecycle_id: str, split: str, failure_group: str, net: float) -> dict:
    return {
        "policy_name": "cost_constrained_forward_live_strict",
        "policy_accepted_lifecycle_flag": 1,
        "lifecycle_id": lifecycle_id,
        "symbol": "NVDA",
        "theme": "ai_semiconductors",
        "role": "leader",
        "entry_ts": "2026-01-01T15:00:00Z",
        "anchored_split": split,
        "forward_live_breadth_positive_rate": 0.72,
        "forward_live_avg_symbol_return": 0.012,
        "forward_live_avg_intraday_range": 0.018,
        "forward_live_liquidity_ratio": 1.25,
        "forward_live_market_regime": "risk_on_broad",
        "forward_live_breadth_regime": "broad_participation",
        "forward_live_volatility_regime": "low_vol",
        "forward_live_liquidity_regime": "liquidity_expansion",
        "forward_live_theme_return": 0.022,
        "forward_live_theme_rank": 1,
        "forward_live_theme_leadership_regime": "theme_leader",
        "estimated_total_cost": 0.003,
        "entry_hour": 15,
        "entry_time_bucket": "15:00",
        "failure_group": failure_group,
        "net_return_from_entry": net,
        "return_from_entry": net + 0.003,
        "add_flag": int(failure_group == "add_scale_success"),
        "scale_flag": int(failure_group == "add_scale_success"),
        "reduce_flag": int(failure_group != "add_scale_success"),
        "add_scale_flag": int(failure_group == "add_scale_success"),
        "post_cost_positive_return_flag": int(net > 0),
    }


if __name__ == "__main__":
    unittest.main()
