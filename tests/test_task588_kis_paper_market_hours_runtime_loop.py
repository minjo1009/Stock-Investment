from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.app.task_588_kis_paper_market_hours_runtime_loop import run_task588


class Task588KisPaperMarketHoursRuntimeLoopTest(unittest.TestCase):
    def test_loop_runs_one_iteration_and_writes_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "missing.env"
            with (
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task583") as t583,
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task584") as t584,
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task585") as t585,
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task587") as t587,
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop._build_catalog_only", return_value=(0, "ok", "")),
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.sidecar_enabled", return_value=True),
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task615_realtime_intelligence_sidecar") as t615,
            ):
                t615.return_value = {
                    "latest_runtime_intelligence_sidecar_status.csv": pd.DataFrame(
                        [
                            {
                                "decision_status": "INTELLIGENCE_SIDECAR_COLLECTION_OK",
                                "event_store_rows": 11999,
                                "attached_source_lanes": 4,
                                "sidecar_trade_signal_used_flag": 0,
                                "exception": "",
                            }
                        ]
                    )
                }
                t583.return_value = {"task_583_decision.csv": pd.DataFrame([{"decision_status": "LIVE_SIGNAL_REFRESH_REPAIRED", "fresh_rows": 1, "paper_order_candidate_rows": 0}])}
                t584.return_value = {"task_584_decision.csv": pd.DataFrame([{"decision_status": "NO_TRADE", "runtime_decision_id": "d1", "symbol": "AAPL", "reason_code": "STRATEGY_FILTER_NOT_MET"}])}
                t585.return_value = {
                    "task_585_decision.csv": pd.DataFrame([{"decision_status": "ORDER_SKIPPED", "order_status": "SKIPPED", "orders_submitted": 0, "broker_truth_fill_count": 0}]),
                    "paper_active_order_status_refresh.csv": pd.DataFrame([{"broker_truth_fill_flag": 1}]),
                    "paper_order_fill_lineage.csv": pd.DataFrame([{"broker_truth_fill_flag": 1}, {"broker_truth_fill_flag": 0}]),
                }
                t587.return_value = {"task_587_decision.csv": pd.DataFrame([{"decision_status": "SLACK_BLOCKED_MISSING_WEBHOOK"}])}
                artifacts = run_task588(db_path=db_path, env_file=env_path, iterations=1, interval_seconds=1)
            decision = artifacts["task_588_decision.csv"].iloc[0].to_dict()
            self.assertEqual(decision["decision_status"], "PAPER_RUNTIME_LOOP_RUNNING_OK")
            self.assertEqual(int(decision["iterations"]), 1)
            self.assertEqual(int(decision["active_broker_truth_fill_count"]), 1)
            self.assertEqual(int(decision["confirmed_broker_truth_fill_total"]), 1)
            self.assertEqual(decision["intelligence_sidecar_status"], "INTELLIGENCE_SIDECAR_COLLECTION_OK")
            self.assertEqual(int(decision["intelligence_event_store_rows"]), 11999)
            self.assertEqual(int(decision["intelligence_sidecar_trade_signal_used_flag"]), 0)
            loop_row = artifacts["paper_runtime_loop_log.csv"].iloc[0].to_dict()
            self.assertEqual(loop_row["diagnostic_cadence"], "5_min_safety")
            self.assertEqual(loop_row["diagnostic_status"], "DIAGNOSTIC_RUN_REQUIRED")
            self.assertEqual(int(loop_row["diagnostic_should_execute"]), 1)

    def test_duplicate_safety_heartbeat_skips_legacy_task_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "missing.env"
            with (
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task583") as t583,
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task584") as t584,
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task585") as t585,
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.run_task587") as t587,
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop._build_catalog_only", return_value=(0, "ok", "")),
                patch("src.app.task_588_kis_paper_market_hours_runtime_loop.sidecar_enabled", return_value=False),
            ):
                t583.return_value = {"task_583_decision.csv": pd.DataFrame([{"decision_status": "LIVE_SIGNAL_REFRESH_REPAIRED", "fresh_rows": 1, "paper_order_candidate_rows": 0}])}
                t584.return_value = {"task_584_decision.csv": pd.DataFrame([{"decision_status": "NO_TRADE", "runtime_decision_id": "d1", "symbol": "AAPL", "reason_code": "STRATEGY_FILTER_NOT_MET"}])}
                t585.return_value = {
                    "task_585_decision.csv": pd.DataFrame([{"decision_status": "ORDER_SKIPPED", "order_status": "SKIPPED", "orders_submitted": 0, "broker_truth_fill_count": 0}]),
                    "paper_active_order_status_refresh.csv": pd.DataFrame(),
                    "paper_order_fill_lineage.csv": pd.DataFrame(),
                }
                t587.return_value = {"task_587_decision.csv": pd.DataFrame([{"decision_status": "SLACK_BLOCKED_MISSING_WEBHOOK"}])}
                artifacts = run_task588(db_path=db_path, env_file=env_path, iterations=2, interval_seconds=1)
            loop_log = artifacts["paper_runtime_loop_log.csv"]
            self.assertEqual(len(loop_log), 2)
            self.assertEqual(loop_log.iloc[1]["diagnostic_status"], "DUPLICATE_STATE_SKIPPED")
            self.assertEqual(int(loop_log.iloc[1]["orders_submitted"]), 0)
            self.assertEqual(t583.call_count, 1)
            self.assertEqual(t584.call_count, 1)
            self.assertEqual(t585.call_count, 1)
            self.assertEqual(t587.call_count, 1)


if __name__ == "__main__":
    unittest.main()
