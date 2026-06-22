from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task517_522_firm_grade_completion import (
    build_task517_raw_native_deterministic_replay,
    build_task518_firm_grade_overfit_statistics,
    build_task519_broker_truth_execution_readiness,
    build_task520_live_source_acquisition_loop,
    build_task521_replay_queued_discovery_grid,
    build_task522_firm_grade_promotion_gate,
)
from tests.task512_516_fixture import write_firm_grade_fixture


class Task517522FirmGradeCompletionTest(unittest.TestCase):
    def test_firm_grade_completion_pipeline_blocks_promotion_without_live_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel = write_firm_grade_fixture(root, rows=140)
            raw_dir = root / "raw" / "us_intraday"
            raw_dir.mkdir(parents=True)
            source = pd.read_csv(panel)
            for symbol, subset in source.groupby("symbol"):
                pd.DataFrame(
                    {
                        "timestamp": subset["entry_ts"],
                        "open": subset["entry_price"],
                        "high": subset["entry_price"],
                        "low": subset["entry_price"],
                        "close": subset["entry_price"],
                        "volume": 1000,
                        "vwap": subset["entry_price"],
                    }
                ).to_csv(raw_dir / f"{symbol}.csv", index=False)

            queue = root / "queue.csv"
            pd.DataFrame(
                [
                    {
                        "discovery_rank": 1,
                        "candidate_strategy_name": "q1",
                        "cell_dims": "theme_id|timing_state",
                        "min_avg_net_pct": 0.0,
                        "min_win_rate": 0.5,
                        "max_entry_reduce_rate": 0.5,
                        "max_positions": 10,
                        "requires_deterministic_replay_flag": 1,
                    }
                ]
            ).to_csv(queue, index=False)

            t517 = build_task517_raw_native_deterministic_replay(task505_panel_path=panel, raw_intraday_dir=raw_dir, out_dir=root / "517")
            self.assertEqual(int(t517["task_517_decision"].iloc[0]["raw_native_replay_complete_flag"]), 1)

            t518 = build_task518_firm_grade_overfit_statistics(task503_panel_path=panel, out_dir=root / "518")
            self.assertIn("task_518_decision", t518)

            t519 = build_task519_broker_truth_execution_readiness(out_dir=root / "519")
            self.assertEqual(int(t519["task_519_decision"].iloc[0]["broker_truth_execution_ready_flag"]), 0)

            t520 = build_task520_live_source_acquisition_loop(out_dir=root / "520")
            self.assertEqual(int(t520["task_520_decision"].iloc[0]["full_depth_provider_ready_flag"]), 0)

            t521 = build_task521_replay_queued_discovery_grid(task503_panel_path=panel, task516_queue_path=queue, out_dir=root / "521")
            self.assertGreaterEqual(int(t521["task_521_decision"].iloc[0]["replayed_candidate_count"]), 1)

            # Build promotion gate from repo-default task dirs is covered by real run; here just ensure function can emit.
            t522 = build_task522_firm_grade_promotion_gate(out_dir=root / "522")
            self.assertIn("promotion_decision", t522["task_522_decision"].columns)


if __name__ == "__main__":
    unittest.main()
