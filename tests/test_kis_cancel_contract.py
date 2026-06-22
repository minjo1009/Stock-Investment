from __future__ import annotations

import sys
import unittest
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "kis"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class _FakeAuthManager:
    def get_valid_access_token(self) -> str:
        return "fake-token"

    def describe_token_state(self) -> dict[str, bool]:
        return {"token_present": True, "expired": False}


class TestKisCancelContract(unittest.TestCase):
    def _load_fixture(self, name: str) -> dict:
        path = FIXTURE_DIR / name
        return json.loads(path.read_text(encoding="utf-8"))

    def _assert_no_sensitive_keys(self, payload: object) -> None:
        sensitive_tokens = ("authorization", "appkey", "appsecret", "token", "cano", "acnt_prdt_cd", "hashkey")
        if isinstance(payload, dict):
            for key, value in payload.items():
                self.assertFalse(
                    any(token in str(key).lower() for token in sensitive_tokens),
                    msg=f"sensitive key leaked: {key}",
                )
                self._assert_no_sensitive_keys(value)
            return
        if isinstance(payload, list):
            for item in payload:
                self._assert_no_sensitive_keys(item)

    def _make_client(self):
        from integration.kis_client import KISClient

        client = KISClient(
            app_key="k",
            app_secret="s",
            account_number="12345678",
            product_code="01",
            environment="paper",
            exchange_code="NASD",
            auth_manager=_FakeAuthManager(),  # type: ignore[arg-type]
        )
        client._order_branch_by_order_id = {"ord-1": "001"}
        client._order_meta_by_order_id = {
            "ord-1": {"symbol": "AAPL", "qty": 1, "price": 123.45, "order_type": "00", "side": "BUY"}
        }
        return client

    def test_cancel_order_success_response_contract(self) -> None:
        client = self._make_client()
        fixture = self._load_fixture("cancel_success.json")
        client._request = lambda *_a, **_k: fixture["response"]  # type: ignore[assignment]

        result = client.cancel_order("ord-1")
        self.assertTrue(result["success"])
        self.assertEqual(result["broker_status"], "CANCELLED")
        self.assertIn("raw_response", result)

    def test_cancel_order_rejected_response_contract(self) -> None:
        client = self._make_client()
        fixture = self._load_fixture("cancel_rejected.json")
        client._request = lambda *_a, **_k: fixture["response"]  # type: ignore[assignment]

        result = client.cancel_order("ord-1")
        self.assertFalse(result["success"])
        self.assertIn("broker_status", result)

    def test_cancel_order_missing_fields_is_defensive(self) -> None:
        client = self._make_client()
        client._request = lambda *_a, **_k: {"output": None}  # type: ignore[assignment]

        result = client.cancel_order("ord-1")
        self.assertFalse(result["success"])
        self.assertEqual(result["broker_status"], "UNKNOWN")

    def test_cancel_order_null_or_type_mismatch_is_defensive(self) -> None:
        client = self._make_client()
        client._request = lambda *_a, **_k: {  # type: ignore[assignment]
            "rt_cd": None,
            "msg_cd": 12345,
            "msg1": None,
            "output": {"ord_stts": None},
        }

        result = client.cancel_order("ord-1")
        self.assertFalse(result["success"])
        self.assertEqual(result["broker_status"], "UNKNOWN")

    def test_cancel_order_network_error_propagates(self) -> None:
        client = self._make_client()

        def _raise(*_a, **_k):
            raise RuntimeError("network timeout")

        client._request = _raise  # type: ignore[assignment]
        with self.assertRaisesRegex(RuntimeError, "network timeout"):
            client.cancel_order("ord-1")

    def test_get_order_status_and_snapshot_contract(self) -> None:
        client = self._make_client()
        fixture = self._load_fixture("fills_partial_or_full.json")
        client._request = lambda *_a, **_k: fixture["response"]  # type: ignore[assignment]
        self.assertEqual(client.get_order_status("ord-1"), "SUBMITTED")
        snapshot = client.get_order_snapshot("ord-1", symbol="AAPL")
        self.assertEqual(snapshot["mapped_status"], "SUBMITTED")

    def test_get_fills_contract_from_snapshot(self) -> None:
        client = self._make_client()
        fixture = self._load_fixture("order_status_filled.json")
        client._request = lambda *_a, **_k: fixture["response"]  # type: ignore[assignment]
        fills = client.get_fills("ord-1", symbol="AAPL")
        self.assertEqual(len(fills), 1)
        self.assertEqual(float(fills[0]["filled_qty"]), 1.0)
        self.assertAlmostEqual(float(fills[0]["fill_price"]), 122.75, places=6)

    def test_order_status_pending_fixture_maps_to_submitted(self) -> None:
        client = self._make_client()
        fixture = self._load_fixture("order_status_pending.json")
        client._request = lambda *_a, **_k: fixture["response"]  # type: ignore[assignment]
        rows = client.fetch_broker_order_statuses(symbol="AAPL")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["mapped_status"], "SUBMITTED")

    def test_fills_empty_fixture_returns_no_fill(self) -> None:
        client = self._make_client()
        fixture = self._load_fixture("fills_empty.json")
        client._request = lambda *_a, **_k: fixture["response"]  # type: ignore[assignment]
        fills = client.get_fills("ord-1", symbol="AAPL")
        self.assertEqual(fills, [])

    def test_fixture_sanitization_contract(self) -> None:
        for file_name in (
            "cancel_success.json",
            "cancel_rejected.json",
            "order_status_pending.json",
            "order_status_filled.json",
            "fills_empty.json",
            "fills_partial_or_full.json",
            "error_transport_or_api.json",
        ):
            fixture = self._load_fixture(file_name)
            self.assertTrue(fixture.get("_fixture_meta", {}).get("sanitized", False))
            self._assert_no_sensitive_keys(fixture)


if __name__ == "__main__":
    unittest.main()
