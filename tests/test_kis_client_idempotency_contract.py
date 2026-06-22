from __future__ import annotations

import unittest

from src.integration.kis_client import KISClient


class _DummyAuth:
    def get_valid_access_token(self) -> str:
        return "token"


class _FakeKISClient(KISClient):
    def _request(self, method, path, *, params=None, payload=None, extra_headers=None, auth_required=True):
        self.last_payload = payload
        return {"output": {"ODNO": "12345", "KRX_FWDG_ORD_ORGNO": "BR"}}


class KISClientIdempotencyContractTest(unittest.TestCase):
    def _client(self) -> _FakeKISClient:
        return _FakeKISClient(
            app_key="key",
            app_secret="secret",
            account_number="12345678",
            product_code="01",
            environment="paper",
            exchange_code="NASD",
            auth_manager=_DummyAuth(),
        )

    def test_client_order_id_is_rejected_until_broker_payload_support_exists(self) -> None:
        client = self._client()
        with self.assertRaises(RuntimeError):
            client.submit_order_with_response(
                symbol="AMD",
                side="BUY",
                quantity=1,
                limit_price=100.0,
                idempotency_key="intent-1",
                broker_client_order_id="intent-1",
            )

    def test_local_idempotency_metadata_is_preserved_without_sending_payload_field(self) -> None:
        client = self._client()
        order_id, response = client.submit_order_with_response(
            symbol="AMD",
            side="BUY",
            quantity=1,
            limit_price=100.0,
            idempotency_key="intent-1",
            reconciliation_before_retry_required=True,
        )
        self.assertEqual(order_id, "12345")
        self.assertEqual(response["_local_idempotency_key"], "intent-1")
        self.assertFalse(response["_broker_client_order_id_supported"])
        self.assertTrue(response["_reconciliation_before_retry_required"])
        self.assertNotIn("client_order_id", client.last_payload)


if __name__ == "__main__":
    unittest.main()
