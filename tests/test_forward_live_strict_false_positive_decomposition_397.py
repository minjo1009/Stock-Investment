from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_forward_live_strict_false_positive_decomposition_397 import (
    build_forward_live_strict_false_positive_decomposition_397,
)


class TestForwardLiveStrictFalsePositive397(unittest.TestCase):
    def test_decomposes_forward_live_strict_groups(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "cost_panel.csv"
            pd.DataFrame(
                [
                    _row("L1", "validation", 1, 1, 0.03),
                    _row("L2", "validation", 1, 0, -0.01),
                    _row("L3", "validation", 0, 0, -0.02),
                ]
            ).to_csv(panel, index=False, encoding="utf-8-sig")
            artifacts = build_forward_live_strict_false_positive_decomposition_397(task396_panel_path=panel, out_dir=root / "out")
            groups = set(artifacts.false_positive_lifecycle_panel["failure_group"])
            self.assertIn("add_scale_success", groups)
            self.assertIn("add_only_weak", groups)
            self.assertIn("entry_reduce_failure", groups)
            self.assertTrue((root / "out" / "task_397_forward_live_strict_false_positive_decomposition.md").exists())


def _row(lifecycle_id: str, split: str, add: int, scale: int, ret: float) -> dict:
    return {
        "policy_name": "cost_constrained_forward_live_strict",
        "policy_accepted_lifecycle_flag": 1,
        "lifecycle_id": lifecycle_id,
        "symbol": "NVDA",
        "theme": "ai_semiconductors",
        "entry_ts": "2026-01-01T14:30:00Z",
        "anchored_split": split,
        "return_from_entry": ret,
        "net_return_from_entry": ret - 0.003,
        "estimated_total_cost": 0.003,
        "add_flag": add,
        "scale_flag": scale,
        "add_scale_flag": int(add and scale),
        "reduce_flag": int(not scale),
        "forward_live_theme_rank": 1,
        "forward_live_theme_return": 0.01,
        "forward_live_breadth_positive_rate": 0.7,
        "forward_live_liquidity_ratio": 1.2,
        "forward_live_avg_intraday_range": 0.02,
        "forward_live_theme_leadership_regime": "theme_leader",
    }


if __name__ == "__main__":
    unittest.main()
