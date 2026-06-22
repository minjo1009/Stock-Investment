from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.task_091a_controlled_broker_lifecycle import (
    MODE_CANCEL_TEST,
    MODE_FILL_TEST,
    _is_live_environment,
    _sanitize,
    run_controlled_lifecycle,
)
from state.store import initialize_store


class FakeBroker:
    def __init__(
        self,
        *,
        price: float = 100.0,
        snapshots: list[dict] | None = None,
        fills: list[dict] | None = None,
        cancel_success: bool = True,
    ) -> None:
        self.price = price
        self.snapshots = snapshots or []
        self.fills_payload = fills or []
        self.cancel_success = cancel_success
        self.submit_called = 0
        self.cancel_called = 0
        self._idx = 0

    def get_current_price(self, symbol: str) -> tuple[float, dict]:
        return self.price, {"rt_cd": "0", "output": {"last": str(self.price)}, "symbol": symbol}

    def submit_limit_buy(self, symbol: str, qty: int, limit_price: float) -> tuple[str, dict]:
        self.submit_called += 1
        return "ORD-TEST-1", {"rt_cd": "0", "output": {"ODNO": "ORD-TEST-1", "PDNO": symbol, "ORD_QTY": qty, "OVRS_ORD_UNPR": limit_price}}

    def get_order_snapshot(self, order_id: str, symbol: str) -> dict:
        if not self.snapshots:
            return {"order_id": order_id, "symbol": symbol, "mapped_status": "PENDING", "filled_qty": 0, "order_qty": 1}
        idx = min(self._idx, len(self.snapshots) - 1)
        row = dict(self.snapshots[idx])
        self._idx += 1
        row.setdefault("order_id", order_id)
        row.setdefault("symbol", symbol)
        row.setdefault("filled_qty", 0)
        row.setdefault("order_qty", 1)
        row.setdefault("raw_status", row.get("mapped_status", "UNKNOWN"))
        return row

    def get_fills(self, order_id: str, symbol: str) -> list[dict]:
        return list(self.fills_payload)

    def cancel_order(self, order_id: str, symbol: str, qty: int, price: float, order_type: str) -> dict:
        self.cancel_called += 1
        return {"success": self.cancel_success, "broker_status": "CANCELLED" if self.cancel_success else "UNKNOWN", "raw_response": {"rt_cd": "0" if self.cancel_success else "1"}}

    def fetch_broker_order_statuses(self, symbol: str) -> list[dict]:
        # conservative stable response for reconciliation
        if self.snapshots:
            last = self.snapshots[min(max(self._idx - 1, 0), len(self.snapshots) - 1)]
            mapped = str(last.get("mapped_status", "UNKNOWN"))
            return [{"order_id": "ORD-TEST-1", "symbol": symbol, "mapped_status": mapped, "filled_qty": float(last.get("filled_qty", 0) or 0), "order_qty": float(last.get("order_qty", 1) or 1)}]
        return []


class TestTask091AControlledLifecycle(unittest.TestCase):
    def _env_patch(self):
        return patch.dict(
            "os.environ",
            {
                "KIS_ENVIRONMENT": "paper",
                "KIS_APP_KEY": "x",
                "KIS_APP_SECRET": "y",
                "KIS_ACCOUNT_NUMBER": "z",
                "KIS_PRODUCT_CODE": "01",
                "KIS_ORDER_DVSN": "00",
            },
            clear=False,
        )

    def _run_with_db(self, broker: FakeBroker, **kwargs):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "trading.db"
            initialize_store(str(db))
            with self._env_patch(), patch("app.task_091a_controlled_broker_lifecycle._is_market_open", return_value=True):
                return run_controlled_lifecycle(
                    mode=kwargs.get("mode", MODE_CANCEL_TEST),
                    symbol="AAPL",
                    qty=kwargs.get("qty", 1),
                    max_notional=kwargs.get("max_notional", 300.0),
                    db_path=str(db),
                    adapter=broker,
                    dry_run=kwargs.get("dry_run", False),
                    status_poll_interval_seconds=0,
                    max_status_poll_attempts=kwargs.get("max_status_poll_attempts", 3),
                    cancel_poll_interval_seconds=0,
                    max_cancel_attempts=kwargs.get("max_cancel_attempts", 3),
                    hard_timeout_seconds=kwargs.get("hard_timeout_seconds", 3),
                )

    def test_live_prod_env_is_blocked(self):
        self.assertTrue(_is_live_environment("live"))
        self.assertTrue(_is_live_environment("prod"))

    def test_missing_credentials_blocks_submit(self):
        broker = FakeBroker()
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "trading.db"
            initialize_store(str(db))
            with patch.dict("os.environ", {"KIS_ENVIRONMENT": "paper"}, clear=True), patch(
                "app.task_091a_controlled_broker_lifecycle._is_market_open", return_value=True
            ):
                report, _ = run_controlled_lifecycle(
                    mode=MODE_CANCEL_TEST,
                    symbol="AAPL",
                    qty=1,
                    max_notional=300,
                    db_path=str(db),
                    adapter=broker,
                    dry_run=False,
                    status_poll_interval_seconds=0,
                    max_status_poll_attempts=2,
                    cancel_poll_interval_seconds=0,
                    max_cancel_attempts=2,
                    hard_timeout_seconds=2,
                )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("MISSING_CREDENTIALS", report["failure_reasons"])
        self.assertEqual(broker.submit_called, 0)

    def test_qty_not_one_blocks_submit(self):
        report, _ = self._run_with_db(FakeBroker(), qty=2)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("QTY_NOT_EQUAL_1", report["failure_reasons"])

    def test_market_order_path_impossible(self):
        broker = FakeBroker()
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "trading.db"
            initialize_store(str(db))
            with patch.dict(
                "os.environ",
                {
                    "KIS_ENVIRONMENT": "paper",
                    "KIS_APP_KEY": "x",
                    "KIS_APP_SECRET": "y",
                    "KIS_ACCOUNT_NUMBER": "z",
                    "KIS_PRODUCT_CODE": "01",
                    "KIS_ORDER_DVSN": "01",
                },
                clear=False,
            ), patch("app.task_091a_controlled_broker_lifecycle._is_market_open", return_value=True):
                report, _ = run_controlled_lifecycle(
                    mode=MODE_CANCEL_TEST,
                    symbol="AAPL",
                    qty=1,
                    max_notional=300,
                    db_path=str(db),
                    adapter=broker,
                    dry_run=False,
                    status_poll_interval_seconds=0,
                    max_status_poll_attempts=1,
                    cancel_poll_interval_seconds=0,
                    max_cancel_attempts=1,
                    hard_timeout_seconds=1,
                )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("MARKET_ORDER_PATH_TRIGGERED", report["failure_reasons"])

    def test_notional_cap_breach_blocks_submit(self):
        report, _ = self._run_with_db(FakeBroker(price=1000.0), max_notional=100.0)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("NOTIONAL_CAP_BREACH", report["failure_reasons"])

    def test_dry_run_warning_without_submit(self):
        broker = FakeBroker()
        report, _ = self._run_with_db(broker, dry_run=True)
        self.assertEqual(report["status"], "WARNING")
        self.assertIn("DRY_RUN_NO_BROKER_SUBMIT", report["warnings"])
        self.assertEqual(broker.submit_called, 0)

    def test_fill_test_filled_path_pass(self):
        broker = FakeBroker(
            snapshots=[{"mapped_status": "SUBMITTED"}, {"mapped_status": "FILLED", "filled_qty": 1, "order_qty": 1}],
            fills=[{"order_id": "ORD-TEST-1", "symbol": "AAPL", "filled_qty": 1, "fill_price": 101.0}],
        )
        report, _ = self._run_with_db(broker, mode=MODE_FILL_TEST)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["answer"], "YES")

    def test_cancel_test_cancelled_path_pass(self):
        broker = FakeBroker(
            snapshots=[{"mapped_status": "SUBMITTED"}, {"mapped_status": "PENDING"}, {"mapped_status": "CANCELLED"}],
            fills=[],
            cancel_success=True,
        )
        report, _ = self._run_with_db(broker, mode=MODE_CANCEL_TEST, max_status_poll_attempts=1, max_cancel_attempts=3)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["cancel_requested"])
        self.assertTrue(report["cancel_confirmed"])

    def test_cancel_race_fill_not_fail(self):
        broker = FakeBroker(
            snapshots=[{"mapped_status": "SUBMITTED"}, {"mapped_status": "PENDING"}, {"mapped_status": "FILLED", "filled_qty": 1, "order_qty": 1}],
            fills=[{"order_id": "ORD-TEST-1", "symbol": "AAPL", "filled_qty": 1, "fill_price": 101.0}],
            cancel_success=True,
        )
        report, _ = self._run_with_db(broker, mode=MODE_CANCEL_TEST, max_status_poll_attempts=1, max_cancel_attempts=3)
        self.assertNotEqual(report["status"], "FAIL")

    def test_unresolved_final_state_fail(self):
        broker = FakeBroker(
            snapshots=[{"mapped_status": "SUBMITTED"}, {"mapped_status": "PENDING"}],
            fills=[],
            cancel_success=False,
        )
        report, _ = self._run_with_db(broker, mode=MODE_CANCEL_TEST, max_status_poll_attempts=1, max_cancel_attempts=1, hard_timeout_seconds=1)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(x in report["failure_reasons"] for x in ("UNRESOLVED_FINAL_STATE", "CANCEL_LOOP_UNKNOWN_ESCALATION", "UNKNOWN_EVENT")))

    def test_sanitization_removes_secrets(self):
        raw = {
            "appkey": "secret",
            "authorization": "Bearer abc",
            "output": {"token": "xyz", "price": "100"},
        }
        cleaned = _sanitize(raw)
        self.assertEqual(cleaned["appkey"], "__REDACTED__")
        self.assertEqual(cleaned["authorization"], "__REDACTED__")
        self.assertEqual(cleaned["output"]["token"], "__REDACTED__")
        self.assertEqual(cleaned["output"]["price"], "100")


if __name__ == "__main__":
    unittest.main()

