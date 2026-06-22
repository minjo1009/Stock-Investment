from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_refined_archetype_portfolio_rebuild_405 import (
    build_refined_archetype_portfolio_rebuild_405,
)


class TestRefinedArchetypePortfolioRebuild405(unittest.TestCase):
    def test_refined_states_separate_trading_failure_modes_and_build_sets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "panel.csv"
            decision = root / "task404.csv"
            pd.DataFrame(_rows()).to_csv(panel, index=False, encoding="utf-8-sig")
            pd.DataFrame([{"task401_exact_label_coverage_sufficient": "YES"}]).to_csv(decision, index=False, encoding="utf-8-sig")

            artifacts = build_refined_archetype_portfolio_rebuild_405(
                lifecycle_panel_path=panel,
                task401_entry_candidates_path=root / "missing_candidates.csv",
                task401_labels_path=root / "missing_labels.csv",
                task404_decision_path=decision,
                out_dir=root / "out",
            )

            assignment = artifacts.refined_archetype_assignment_panel
            self.assertIn("late_chase", set(assignment["entry_state_v2"]))
            self.assertIn("pullback_reclaim_or_isolated_strength", set(assignment["entry_state_v2"]))
            self.assertIn("volatility_stress", set(assignment["risk_state_v2"]))
            self.assertEqual(int(assignment["label_used_for_assignment_flag"].max()), 0)
            self.assertGreaterEqual(artifacts.refined_archetype_set_definitions["refined_archetype_set_name"].nunique(), 6)
            self.assertIn("entry_reduce_failure", set(artifacts.refined_archetype_set_false_positive_audit["failure_group"]))
            self.assertEqual(int(artifacts.refined_archetype_leakage_audit["leakage_pass_flag"].min()), 1)
            self.assertTrue((root / "out" / "task_405_refined_archetype_portfolio_rebuild.md").exists())


def _rows() -> list[dict]:
    rows = []
    for i in range(80):
        split = "validation" if i % 2 == 0 else "recent_oos"
        hour = [10, 15, 19, 16][i % 4]
        theme_ret = [0.02, 0.015, -0.01, 0.02][i % 4]
        market_ret = [0.01, 0.012, 0.005, -0.005][i % 4]
        rng = [0.015, 0.025, 0.038, 0.05][i % 4]
        failure = "add_scale_success" if i % 5 in {1, 2} else ("entry_reduce_failure" if i % 5 in {0, 3} else "add_only_weak")
        rows.append(
            {
                "policy_name": "cost_constrained_forward_live_strict",
                "policy_accepted_lifecycle_flag": 1,
                "lifecycle_id": f"L{i}",
                "symbol": f"S{i % 12}",
                "theme": f"theme_{i % 8}",
                "role": "leader",
                "entry_ts": f"2026-01-{(i % 9) + 1:02d}T{hour:02d}:00:00Z",
                "anchored_split": split,
                "forward_live_breadth_positive_rate": 0.70 if i % 4 != 3 else 0.42,
                "forward_live_avg_symbol_return": market_ret,
                "forward_live_avg_intraday_range": rng,
                "forward_live_liquidity_ratio": 1.2 if i % 3 else 0.85,
                "forward_live_market_regime": "risk_on_broad",
                "forward_live_breadth_regime": "broad_participation",
                "forward_live_volatility_regime": "high_vol" if rng > 0.032 else "low_vol",
                "forward_live_liquidity_regime": "liquidity_expansion" if i % 3 else "liquidity_neutral",
                "forward_live_theme_return": theme_ret,
                "forward_live_theme_rank": (i % 6) + 1,
                "forward_live_theme_leadership_regime": "theme_leader" if i % 6 < 3 and theme_ret > 0 else "theme_middle",
                "estimated_total_cost": 0.003 + (i % 4) * 0.001,
                "entry_hour": hour,
                "entry_time_bucket": f"{hour:02d}:00",
                "failure_group": failure,
                "net_return_from_entry": 0.02 if failure == "add_scale_success" else -0.01,
                "return_from_entry": 0.025 if failure == "add_scale_success" else -0.006,
                "add_flag": int(failure in {"add_scale_success", "add_only_weak"}),
                "scale_flag": int(failure == "add_scale_success"),
                "reduce_flag": int(failure == "entry_reduce_failure"),
            }
        )
    return rows


if __name__ == "__main__":
    unittest.main()
