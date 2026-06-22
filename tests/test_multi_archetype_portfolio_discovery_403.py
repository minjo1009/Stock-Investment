from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_multi_archetype_continuation_portfolio_discovery_403 import (
    build_multi_archetype_continuation_portfolio_discovery_403,
)


class TestMultiArchetypePortfolioDiscovery403(unittest.TestCase):
    def test_builds_multiple_archetype_sets_without_assignment_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "panel.csv"
            decision = root / "task402r.csv"
            pd.DataFrame(_rows()).to_csv(panel, index=False, encoding="utf-8-sig")
            pd.DataFrame(
                [
                    {
                        "task401_label_coverage_sufficient": "NO",
                        "task401_exact_label_coverage_rate": 0.0,
                    }
                ]
            ).to_csv(decision, index=False, encoding="utf-8-sig")

            artifacts = build_multi_archetype_continuation_portfolio_discovery_403(
                lifecycle_panel_path=panel,
                task402r_decision_path=decision,
                out_dir=root / "out",
            )

            definitions = artifacts.archetype_set_definitions
            self.assertIn("top_10_archetype_set", set(definitions["archetype_set_name"]))
            self.assertIn("top_20_archetype_set", set(definitions["archetype_set_name"]))
            self.assertGreaterEqual(definitions["continuation_archetype_id"].nunique(), 10)
            self.assertEqual(int(artifacts.archetype_set_leakage_audit["leakage_pass_flag"].min()), 1)
            self.assertEqual(str(artifacts.task_403_decision.iloc[0]["task401_label_coverage_sufficient"]), "NO")
            self.assertEqual(int(artifacts.task_403_decision.iloc[0]["selected_only_one_combo_flag"]), 0)
            self.assertTrue((root / "out" / "task_403_multi_archetype_continuation_portfolio_discovery.md").exists())

    def test_concentration_audit_flags_overconcentrated_sets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "panel.csv"
            decision = root / "task402r.csv"
            rows = _rows(symbol_count=1, theme_count=1)
            pd.DataFrame(rows).to_csv(panel, index=False, encoding="utf-8-sig")
            pd.DataFrame([{"task401_label_coverage_sufficient": "NO", "task401_exact_label_coverage_rate": 0.0}]).to_csv(
                decision,
                index=False,
                encoding="utf-8-sig",
            )

            artifacts = build_multi_archetype_continuation_portfolio_discovery_403(
                lifecycle_panel_path=panel,
                task402r_decision_path=decision,
                out_dir=root / "out",
            )

            self.assertTrue((artifacts.archetype_set_concentration_audit["concentration_risk_flag"] == 1).any())


def _rows(symbol_count: int = 12, theme_count: int = 12) -> list[dict]:
    rows = []
    for i in range(60):
        split = "validation" if i % 2 == 0 else "recent_oos"
        symbol = f"S{i % symbol_count}"
        theme = f"theme_{i % theme_count}"
        avg_ret = 0.01 if i % 7 not in {0, 1} else -0.006
        breadth = 0.70 if i % 5 not in {0, 1} else 0.40
        theme_ret = 0.02 if i % 6 not in {0, 1} else -0.01
        theme_rank = (i % 9) + 1
        hour = [10, 12, 15, 18, 20][i % 5]
        rows.append(
            {
                "policy_name": "cost_constrained_forward_live_strict",
                "policy_accepted_lifecycle_flag": 1,
                "lifecycle_id": f"L{i}",
                "symbol": symbol,
                "theme": theme,
                "role": "leader",
                "entry_ts": f"2026-01-{(i % 9) + 1:02d}T15:00:00Z",
                "anchored_split": split,
                "forward_live_breadth_positive_rate": breadth,
                "forward_live_avg_symbol_return": avg_ret,
                "forward_live_avg_intraday_range": 0.015 + (i % 4) * 0.01,
                "forward_live_liquidity_ratio": 1.2 if i % 2 else 0.95,
                "forward_live_market_regime": "risk_on_broad" if breadth >= 0.65 and avg_ret > 0 else "mixed_market",
                "forward_live_breadth_regime": "broad_participation" if breadth >= 0.65 else "weak_breadth",
                "forward_live_volatility_regime": ["low_vol", "mid_vol", "high_vol", "mid_vol"][i % 4],
                "forward_live_liquidity_regime": "liquidity_expansion" if i % 2 else "liquidity_neutral",
                "forward_live_theme_return": theme_ret,
                "forward_live_theme_rank": theme_rank,
                "forward_live_theme_leadership_regime": "theme_leader" if theme_rank <= 3 and theme_ret > 0 else "theme_middle",
                "estimated_total_cost": 0.003 + (i % 4) * 0.001,
                "entry_hour": hour,
                "entry_time_bucket": "15:00",
                "failure_group": "add_scale_success" if i % 4 in {1, 2} else "entry_reduce_failure",
                "net_return_from_entry": 0.02 if i % 4 in {1, 2} else -0.01,
                "return_from_entry": 0.025 if i % 4 in {1, 2} else -0.006,
                "add_flag": int(i % 4 in {1, 2}),
                "scale_flag": int(i % 4 in {1, 2}),
                "reduce_flag": int(i % 4 not in {1, 2}),
            }
        )
    return rows


if __name__ == "__main__":
    unittest.main()
