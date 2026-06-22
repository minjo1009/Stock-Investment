from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sqlite3
from unittest.mock import patch

from src.app.task_089_market_data_signal_refresh import _init_tables
from src.app.task_585_kis_paper_order_execution import run_task585
from src.app.task_584_runtime_strategy_decision_gate import run_task584
from src.state.store import get_paper_order_intent, initialize_store, record_order, record_trade_run_start


class Task585KisPaperOrderExecutionTest(unittest.TestCase):
    def test_no_runtime_candidate_submits_no_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "missing.env"
            env_path.write_text("TRADING_MAX_PAPER_ORDERS_PER_DAY=0\n", encoding="utf-8")
            artifacts = run_task585(db_path=db_path, env_file=env_path)
            decision = artifacts["task_585_decision.csv"].iloc[0].to_dict()
            execution = artifacts["paper_order_execution_log.csv"].iloc[0].to_dict()
            self.assertEqual(execution["order_status"], "SKIPPED")
            self.assertEqual(execution["reason_code"], "NO_RUNTIME_DECISION")
            self.assertEqual(int(decision["orders_submitted"]), 0)

    def test_existing_pending_order_blocks_duplicate_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "missing.env"
            env_path.write_text("TRADING_MAX_PAPER_ORDERS_PER_DAY=0\n", encoding="utf-8")
            _init_tables(str(db_path))
            initialize_store(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("snap-1", "2026-05-20T01:00:00Z", "AMD", "2026-05-20T01:00:00Z", 100, 99, 98, 97, 99, 1, 1, 1, 1, 0, "ENTER", "BUY", "BREAKOUT", 1, 1, 1),
                )
                con.commit()
            finally:
                con.close()
            run_task584(db_path=db_path)
            run_id = record_trade_run_start(
                str(db_path),
                symbol="AMD",
                side="BUY",
                requested_quantity=1,
                started_at="2026-05-20T01:00:00Z",
                environment="paper",
            )
            record_order(
                str(db_path),
                order_id="pending-1",
                run_id=run_id,
                symbol="AMD",
                side="BUY",
                quantity=1,
                submitted_at="2026-05-20T01:00:01Z",
                status="PENDING",
                environment="paper",
                raw_status="PENDING",
            )
            artifacts = run_task585(db_path=db_path, env_file=env_path)
            execution = artifacts["paper_order_execution_log.csv"].iloc[0].to_dict()
            self.assertEqual(execution["order_status"], "SKIPPED")
            self.assertIn(execution["reason_code"], {"MAX_OPEN_ORDER_LIMIT", "ACTIVE_ORDER_EXISTS_FOR_SYMBOL"})

    def test_daily_order_cap_blocks_new_submission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "paper.env"
            env_path.write_text("KIS_ENVIRONMENT=paper\nTRADING_MAX_PAPER_ORDERS_PER_DAY=1\n", encoding="utf-8")
            _init_tables(str(db_path))
            initialize_store(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("snap-1", "2026-05-20T01:00:00Z", "AMD", "2026-05-20T01:00:00Z", 100, 99, 98, 97, 99, 1, 1, 1, 1, 0, "ENTER", "BUY", "BREAKOUT", 1, 1, 1),
                )
                con.commit()
            finally:
                con.close()
            run_task584(db_path=db_path)
            run_id = record_trade_run_start(
                str(db_path),
                symbol="MSFT",
                side="BUY",
                requested_quantity=1,
                started_at="2026-05-20T01:00:00Z",
                environment="paper",
            )
            record_order(
                str(db_path),
                order_id="filled-1",
                run_id=run_id,
                symbol="MSFT",
                side="BUY",
                quantity=1,
                submitted_at="2026-05-20T01:00:01Z",
                status="FILLED",
                environment="paper",
                raw_status="FILLED",
            )
            artifacts = run_task585(db_path=db_path, env_file=env_path)
            execution = artifacts["paper_order_execution_log.csv"].iloc[0].to_dict()
            self.assertEqual(execution["order_status"], "SKIPPED")
            self.assertEqual(execution["reason_code"], "MAX_DAILY_PAPER_ORDER_LIMIT")

    def test_pre_order_position_baseline_required_before_submit(self) -> None:
        class FakeKIS:
            submitted = False

            def get_order_snapshot(self, order_id: str, *, symbol: str) -> dict:
                return {"mapped_status": "UNKNOWN", "raw_status": "ORDER_NOT_FOUND"}

            def get_position_quantity(self, symbol: str) -> int:
                raise RuntimeError("rate limited")

            def submit_order_with_response(self, **kwargs):
                self.submitted = True
                return "order-1", {"ok": True}

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "paper.env"
            env_path.write_text("KIS_ENVIRONMENT=paper\nTRADING_ALLOW_LEGACY_PAPER_EXECUTION=1\n", encoding="utf-8")
            _init_tables(str(db_path))
            initialize_store(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("snap-1", "2026-05-20T01:00:00Z", "AMD", "2026-05-20T01:00:00Z", 100, 99, 98, 97, 99, 1, 1, 1, 1, 0, "ENTER", "BUY", "BREAKOUT", 1, 1, 1),
                )
                con.commit()
            finally:
                con.close()
            run_task584(db_path=db_path)
            fake = FakeKIS()
            with patch("src.app.task_585_kis_paper_order_execution.KISClient.from_env", return_value=fake):
                artifacts = run_task585(db_path=db_path, env_file=env_path)
            execution = artifacts["paper_order_execution_log.csv"].iloc[0].to_dict()
            self.assertFalse(fake.submitted)
            self.assertEqual(execution["order_status"], "FAILED")
            self.assertEqual(execution["reason_code"], "KIS_ORDER_FAILED")
            self.assertIn("PRE_ORDER_POSITION_BASELINE_BLOCKED", str(execution["raw_response"]))

    def test_legacy_paper_candidate_is_guarded_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "paper.env"
            env_path.write_text("KIS_ENVIRONMENT=paper\n", encoding="utf-8")
            _init_tables(str(db_path))
            initialize_store(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("snap-1", "2026-05-20T01:00:00Z", "AMD", "2026-05-20T01:00:00Z", 100, 99, 98, 97, 99, 1, 1, 1, 1, 0, "ENTER", "BUY", "BREAKOUT", 1, 1, 1),
                )
                con.commit()
            finally:
                con.close()
            run_task584(db_path=db_path)
            with patch("src.app.task_585_kis_paper_order_execution.KISClient.from_env") as kis_mock:
                artifacts = run_task585(db_path=db_path, env_file=env_path)
            execution = artifacts["paper_order_execution_log.csv"].iloc[0].to_dict()
            self.assertEqual(execution["order_status"], "SKIPPED")
            self.assertEqual(execution["reason_code"], "LEGACY_PAPER_EXECUTION_GUARD_BLOCKED")
            kis_mock.assert_not_called()

    def test_submit_success_local_record_failure_leaves_unknown_intent(self) -> None:
        class FakeKIS:
            def get_order_snapshot(self, order_id: str, *, symbol: str) -> dict:
                return {"mapped_status": "SUBMITTED", "raw_status": "SUBMITTED"}

            def get_position_quantity(self, symbol: str) -> int:
                return 0

            def submit_order_with_response(self, **kwargs):
                self.kwargs = kwargs
                return "order-after-submit", {"ok": True}

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "trading.db"
            env_path = Path(tmp) / "paper.env"
            env_path.write_text("KIS_ENVIRONMENT=paper\nTRADING_ALLOW_LEGACY_PAPER_EXECUTION=1\n", encoding="utf-8")
            _init_tables(str(db_path))
            initialize_store(str(db_path))
            con = sqlite3.connect(db_path)
            try:
                con.execute(
                    """
                    INSERT INTO indicator_snapshots(
                        snapshot_id, created_at, symbol, bar_end_ts, close, ma20, ma50, ma200,
                        breakout_high_20, breakout_condition, ma_condition, entry_allowed,
                        data_fresh, insufficient_history, action, side, reason, score,
                        candidate_rank, selected_for_portfolio
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    ("snap-1", "2026-05-20T01:00:00Z", "AMD", "2026-05-20T01:00:00Z", 100, 99, 98, 97, 99, 1, 1, 1, 1, 0, "ENTER", "BUY", "BREAKOUT", 1, 1, 1),
                )
                con.commit()
            finally:
                con.close()
            run_task584(db_path=db_path)
            fake = FakeKIS()
            with (
                patch("src.app.task_585_kis_paper_order_execution.KISClient.from_env", return_value=fake),
                patch("src.app.task_585_kis_paper_order_execution.record_order", side_effect=RuntimeError("local write failed")),
            ):
                artifacts = run_task585(db_path=db_path, env_file=env_path)
            execution = artifacts["paper_order_execution_log.csv"].iloc[0].to_dict()
            self.assertEqual(execution["order_status"], "UNKNOWN")
            self.assertEqual(execution["reason_code"], "LOCAL_RECORD_FAILED_AFTER_BROKER_SUBMIT")
            self.assertEqual(fake.kwargs["idempotency_key"], str(execution["decision_id"]))
            self.assertTrue(fake.kwargs["reconciliation_before_retry_required"])
            intent = get_paper_order_intent(str(db_path), idempotency_key=str(execution["decision_id"]))
            self.assertEqual(intent["state"], "UNKNOWN")
            self.assertEqual(intent["broker_order_id"], "order-after-submit")


if __name__ == "__main__":
    unittest.main()
