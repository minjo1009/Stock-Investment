from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import json


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "kis"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestCancelLoop(unittest.TestCase):
    def _load_fixture(self, name: str) -> dict:
        path = FIXTURE_DIR / name
        return json.loads(path.read_text(encoding="utf-8"))

    def test_cancel_logs_include_api_and_confirmed(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        logs: list[str] = []
        polls = iter(
            [
                {"state": "PENDING", "raw_status": "OPEN"},
                {"state": "CANCELLED", "raw_status": "CANCELLED"},
            ]
        )

        result = cancel_until_terminal(
            "ord-log-1",
            poll_status=lambda _oid: next(polls),
            request_cancel=lambda _oid: {"success": True, "broker_status": "CANCELLED"},
            update_local_status=lambda _oid, _status, _raw: None,
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 1.0) or c[0])),
            log_fn=logs.append,
        )
        self.assertEqual(result.final_state, "CANCELLED")
        self.assertTrue(any("[CANCEL_API_REQUEST]" in item for item in logs))
        self.assertTrue(any("[CANCEL_API_RESPONSE]" in item for item in logs))
        self.assertTrue(any("[CANCEL_CONFIRMED]" in item for item in logs))

    def test_fixture_pending_to_cancelled_flow(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        pending = self._load_fixture("order_status_pending.json")["response"]["output1"][0]
        cancelled = self._load_fixture("cancel_success.json")["response"]["output"]
        polls = iter(
            [
                {"state": pending.get("ord_stts"), "raw_status": pending.get("ord_stts"), "filled_qty": 0, "order_qty": 1},
                {"state": cancelled.get("ord_stts"), "raw_status": cancelled.get("ord_stts"), "filled_qty": 0, "order_qty": 1},
            ]
        )
        result = cancel_until_terminal(
            "ord-1",
            poll_status=lambda _oid: next(polls),
            request_cancel=lambda _oid: self._load_fixture("cancel_success.json")["response"],
            update_local_status=lambda _oid, _status, _raw: None,
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 1.0) or c[0])),
            log_fn=lambda _m: None,
        )
        self.assertEqual(result.final_state, "CANCELLED")

    def test_fixture_pending_to_filled_flow(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        polls = iter(
            [
                {"state": "PENDING", "raw_status": "PENDING", "filled_qty": 0, "order_qty": 1},
                {"state": "FILLED", "raw_status": "FILLED", "filled_qty": 1, "order_qty": 1},
            ]
        )
        result = cancel_until_terminal(
            "ord-1",
            poll_status=lambda _oid: next(polls),
            request_cancel=lambda _oid: self._load_fixture("cancel_rejected.json")["response"],
            update_local_status=lambda _oid, _status, _raw: None,
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 1.0) or c[0])),
            log_fn=lambda _m: None,
        )
        self.assertEqual(result.final_state, "FILLED")

    def test_fixture_unknown_response_escalates_unknown(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        err = self._load_fixture("error_transport_or_api.json")["response"]
        polls = iter(
            [
                {"state": "UNKNOWN", "raw_status": str(err.get("msg_cd") or "UNKNOWN"), "filled_qty": 0, "order_qty": 0},
                {"state": "UNKNOWN", "raw_status": str(err.get("msg_cd") or "UNKNOWN"), "filled_qty": 0, "order_qty": 0},
                {"state": "UNKNOWN", "raw_status": str(err.get("msg_cd") or "UNKNOWN"), "filled_qty": 0, "order_qty": 0},
            ]
        )
        result = cancel_until_terminal(
            "ord-1",
            poll_status=lambda _oid: next(polls),
            request_cancel=lambda _oid: {"success": False, "broker_status": "UNKNOWN", "raw_response": err},
            update_local_status=lambda _oid, _status, _raw: None,
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 25.0) or c[0])),
            max_attempts=5,
            max_elapsed_seconds=60,
            log_fn=lambda _m: None,
        )
        self.assertEqual(result.final_state, "UNKNOWN")

    def test_timeout_cancel_confirmed(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        polls = iter(
            [
                {"state": "PENDING", "raw_status": "OPEN"},
                {"state": "PENDING", "raw_status": "OPEN"},
                {"state": "CANCELLED", "raw_status": "CANCELLED"},
            ]
        )
        updates: list[str] = []
        cancel_calls = 0

        def _poll(_order_id: str):
            return next(polls)

        def _cancel(_order_id: str):
            nonlocal cancel_calls
            cancel_calls += 1

        def _update(_order_id: str, status: str, _raw: str | None):
            updates.append(status)

        result = cancel_until_terminal(
            "ord-1",
            poll_status=_poll,
            request_cancel=_cancel,
            update_local_status=_update,
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 1.0) or c[0])),
            log_fn=lambda _m: None,
        )
        self.assertEqual(result.final_state, "CANCELLED")
        self.assertGreaterEqual(cancel_calls, 1)
        self.assertIn("CANCEL_REQUESTED", updates)
        self.assertIn("CANCEL_IN_PROGRESS", updates)
        self.assertIn("CANCELLED", updates)

    def test_cancel_race_filled(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        polls = iter(
            [
                {"state": "PENDING", "raw_status": "OPEN"},
                {"state": "FILLED", "raw_status": "FILLED"},
            ]
        )
        updates: list[str] = []

        result = cancel_until_terminal(
            "ord-2",
            poll_status=lambda _oid: next(polls),
            request_cancel=lambda _oid: None,
            update_local_status=lambda _oid, status, _raw: updates.append(status),
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 1.0) or c[0])),
            log_fn=lambda _m: None,
        )
        self.assertEqual(result.final_state, "FILLED")
        self.assertIn("FILLED", updates)

    def test_partial_fill_then_cancel(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        polls = iter(
            [
                {"state": "SUBMITTED", "filled_qty": 0.2, "order_qty": 1.0, "raw_status": "PARTIALLY_FILLED"},
                {"state": "CANCELLED", "raw_status": "CANCELLED"},
            ]
        )
        updates: list[str] = []

        result = cancel_until_terminal(
            "ord-3",
            poll_status=lambda _oid: next(polls),
            request_cancel=lambda _oid: None,
            update_local_status=lambda _oid, status, _raw: updates.append(status),
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 1.0) or c[0])),
            log_fn=lambda _m: None,
        )
        self.assertEqual(result.final_state, "CANCELLED")
        self.assertIn("CANCEL_IN_PROGRESS", updates)

    def test_cancel_response_failure_retries_then_unknown(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        polls = iter([{"state": "PENDING", "raw_status": "OPEN"}] * 6)
        attempts = 0

        def _request(_oid: str):
            nonlocal attempts
            attempts += 1
            return {"success": False, "broker_status": "REJECTED", "raw_response": {"rt_cd": "1"}}

        result = cancel_until_terminal(
            "ord-3b",
            poll_status=lambda _oid: next(polls),
            request_cancel=_request,
            update_local_status=lambda _oid, _status, _raw: None,
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 20.0) or c[0])),
            max_attempts=10,
            max_elapsed_seconds=60,
            log_fn=lambda _m: None,
        )
        self.assertEqual(result.final_state, "UNKNOWN")
        self.assertGreaterEqual(attempts, 1)

    def test_cancel_retry_then_unknown(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        polls = iter([{"state": "PENDING", "raw_status": "OPEN"}] * 5)
        cancel_attempts = 0
        updates: list[str] = []
        logs: list[str] = []

        def _cancel(_oid: str):
            nonlocal cancel_attempts
            cancel_attempts += 1
            raise RuntimeError("cancel failed")

        result = cancel_until_terminal(
            "ord-4",
            poll_status=lambda _oid: next(polls),
            request_cancel=_cancel,
            update_local_status=lambda _oid, status, _raw: updates.append(status),
            reconcile=lambda _oid: None,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 20.0) or c[0])),
            max_attempts=10,
            max_elapsed_seconds=60,
            log_fn=logs.append,
        )
        self.assertEqual(result.final_state, "UNKNOWN")
        self.assertGreaterEqual(cancel_attempts, 1)
        self.assertIn("UNKNOWN", updates)
        self.assertTrue(any("[CANCEL_FAILED]" in item for item in logs))
        self.assertTrue(any("[UNKNOWN_ESCALATED]" in item for item in logs))

    def test_cancelled_with_filled_qty_applies_late_fill(self) -> None:
        from execution.cancel_loop import cancel_until_terminal

        late_fill_calls = 0
        logs: list[str] = []

        def _late_fill(_oid: str):
            nonlocal late_fill_calls
            late_fill_calls += 1

        result = cancel_until_terminal(
            "ord-late-1",
            poll_status=lambda _oid: {
                "state": "CANCELLED",
                "raw_status": "CANCELLED",
                "filled_qty": 0.25,
                "order_qty": 1.0,
            },
            request_cancel=lambda _oid: {"success": True, "broker_status": "CANCELLED"},
            update_local_status=lambda _oid, _status, _raw: None,
            reconcile=lambda _oid: None,
            on_late_fill=_late_fill,
            sleep_fn=lambda _s: None,
            monotonic_fn=(lambda c=[0.0]: (c.__setitem__(0, c[0] + 1.0) or c[0])),
            log_fn=logs.append,
        )
        self.assertEqual(result.final_state, "CANCELLED")
        self.assertEqual(late_fill_calls, 1)
        self.assertTrue(any("[LATE_FILL_APPLIED]" in item for item in logs))

    def test_late_fill_applied_updates_position_and_reconciliation(self) -> None:
        import app.run_trade_once as run_trade_once
        from state.store import (
            get_fills_for_order,
            get_position,
            initialize_store,
            list_reconciliation_events,
            list_recent_reconciliation_runs,
            record_order,
            record_trade_run_start,
        )

        class FakeKIS:
            def get_fills(self, order_id: str, *, symbol: str | None = None):
                return [
                    {
                        "order_id": order_id,
                        "symbol": symbol or "AAPL",
                        "filled_qty": 1.0,
                        "fill_price": 120.5,
                        "filled_at": "2026-01-01T00:00:00Z",
                        "raw_status": "FILLED",
                        "mapped_status": "FILLED",
                    }
                ]

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            record_order(
                db_path,
                order_id="ord-late-integ-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                submitted_at="2026-01-01T00:00:01Z",
                status="CANCELLED",
                environment="paper",
            )

            applied = run_trade_once._apply_broker_fill_correction(  # type: ignore[attr-defined]
                kis=FakeKIS(),  # type: ignore[arg-type]
                db_path=db_path,
                run_id=run_id,
                order_id="ord-late-integ-1",
                symbol="AAPL",
                side="BUY",
                fallback_price=120.0,
                late_fill=True,
            )
            self.assertAlmostEqual(applied, 1.0, places=6)
            # Idempotent on repeated call.
            applied_again = run_trade_once._apply_broker_fill_correction(  # type: ignore[attr-defined]
                kis=FakeKIS(),  # type: ignore[arg-type]
                db_path=db_path,
                run_id=run_id,
                order_id="ord-late-integ-1",
                symbol="AAPL",
                side="BUY",
                fallback_price=120.0,
                late_fill=True,
            )
            self.assertAlmostEqual(applied_again, 0.0, places=6)

            fills = get_fills_for_order(db_path, "ord-late-integ-1")
            self.assertEqual(len(fills), 1)
            position = get_position(db_path, "AAPL")
            self.assertIsNotNone(position)
            assert position is not None
            self.assertAlmostEqual(float(position["quantity"]), 1.0, places=6)
            self.assertAlmostEqual(float(position["avg_price"]), 120.5, places=6)

            recon_runs = list_recent_reconciliation_runs(db_path, limit=5)
            self.assertGreaterEqual(len(recon_runs), 1)
            recon_id = recon_runs[0]["reconciliation_id"]
            events = list_reconciliation_events(db_path, recon_id)
            self.assertTrue(any(event["event_type"] == "LATE_FILL" for event in events))

    def test_unknown_order_guard_blocks_run(self) -> None:
        import app.run_trade_once as run_trade_once
        from state.store import initialize_store, record_order, record_trade_run_start

        with tempfile.TemporaryDirectory() as td:
            db_path = str(Path(td) / "state.db")
            initialize_store(db_path)
            run_id = record_trade_run_start(
                db_path,
                symbol="AAPL",
                side="BUY",
                requested_quantity=1.0,
                started_at="2026-01-01T00:00:00Z",
                environment="paper",
            )
            record_order(
                db_path,
                order_id="ord-unknown-1",
                run_id=run_id,
                symbol="AAPL",
                side="BUY",
                quantity=1.0,
                submitted_at="2026-01-01T00:00:01Z",
                status="UNKNOWN",
                environment="paper",
            )
            with patch.dict(os.environ, {"TRADING_DB_PATH": db_path}, clear=False):
                with self.assertRaisesRegex(RuntimeError, "UNKNOWN ORDER EXISTS"):
                    run_trade_once.run()


if __name__ == "__main__":
    unittest.main()
