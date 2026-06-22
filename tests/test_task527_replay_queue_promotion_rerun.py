from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task523_528_gap_closure import build_task527_replay_queue_promotion_rerun


class Task527ReplayQueuePromotionRerunTest(unittest.TestCase):
    def test_promotion_requires_suppression_pass_or_terminal_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            quality = root / "quality.csv"
            pd.DataFrame(
                [{"candidate_strategy_name": "c1", "lifecycle_count": 100, "capital_pnl_pct": 50.0, "entry_reduce_failure_rate": 0.25}]
            ).to_csv(quality, index=False)
            suppression = root / "supp.csv"
            pd.DataFrame([{"suppression_oos_pass_flag": 0}]).to_csv(suppression, index=False)
            artifacts = build_task527_replay_queue_promotion_rerun(queue_quality_path=quality, suppression_decision_path=suppression, out_dir=root / "out")
            decision = artifacts["task_527_decision"].iloc[0]
            self.assertEqual(int(decision["has_clear_terminal_decision_flag"]), 1)
            self.assertEqual(int(decision["promoted_candidate_count"]), 0)


if __name__ == "__main__":
    unittest.main()
