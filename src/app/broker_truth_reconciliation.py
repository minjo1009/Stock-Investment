"""Broker-truth reconciliation source adapter.

This module consumes broker order-status snapshots and records local
reconciliation evidence. It does not submit or cancel orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

try:
    from src.app.reconciliation import reconcile_local_and_broker
    from src.integration.kis_client import KISClient
    from src.state.store import (
        initialize_store,
        list_local_filled_order_ids,
        list_open_orders,
        list_paper_order_intents,
        record_reconciliation_event,
        record_reconciliation_run,
        resolve_paper_order_intent_after_reconciliation,
    )
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from app.reconciliation import reconcile_local_and_broker
    from integration.kis_client import KISClient
    from state.store import (
        initialize_store,
        list_local_filled_order_ids,
        list_open_orders,
        list_paper_order_intents,
        record_reconciliation_event,
        record_reconciliation_run,
        resolve_paper_order_intent_after_reconciliation,
    )


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def build_broker_truth_ref(*, broker_orders: list[dict[str, Any]], fetched_at: str, source: str) -> str:
    minimal_rows = [
        {
            "source": str(row.get("source") or ""),
            "order_id": str(row.get("order_id") or ""),
            "symbol": str(row.get("symbol") or ""),
            "mapped_status": str(row.get("mapped_status") or ""),
            "raw_status": str(row.get("raw_status") or ""),
            "order_qty": float(row.get("order_qty") or 0.0),
            "filled_qty": float(row.get("filled_qty") or 0.0),
        }
        for row in broker_orders
    ]
    payload = {"source": source, "fetched_at": fetched_at, "orders": minimal_rows}
    return "broker-truth:" + hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class BrokerTruthReconciliationResult:
    reconciliation_id: str
    broker_truth_ref: str
    status: str
    max_severity: str
    block_new_orders: bool
    event_count: int
    resolved_intents: tuple[dict[str, str], ...]

    def to_dict(self) -> dict:
        return {
            "reconciliation_id": self.reconciliation_id,
            "broker_truth_ref": self.broker_truth_ref,
            "status": self.status,
            "max_severity": self.max_severity,
            "block_new_orders": self.block_new_orders,
            "event_count": self.event_count,
            "resolved_intents": list(self.resolved_intents),
        }


def run_broker_truth_reconciliation(
    *,
    db_path: str,
    broker_orders: list[dict[str, Any]] | None = None,
    kis_client: KISClient | None = None,
    symbol: str | None = None,
    run_id: str = "broker-truth-reconciliation",
    now: str | None = None,
    resolve_intents: bool = True,
) -> BrokerTruthReconciliationResult:
    initialize_store(db_path)
    now = now or _utc_now()
    if broker_orders is None:
        if kis_client is None:
            kis_client = KISClient.from_env()
        if str(kis_client.environment or "").strip().lower() != "paper":
            raise RuntimeError("BROKER_TRUTH_RECONCILIATION_REQUIRES_PAPER_ENVIRONMENT")
        broker_orders = kis_client.fetch_broker_order_statuses(symbol=symbol)

    broker_truth_ref = build_broker_truth_ref(
        broker_orders=broker_orders,
        fetched_at=now,
        source="KIS_PAPER_ORDER_STATUS",
    )
    local_open_orders = list_open_orders(db_path)
    local_filled_order_ids = list_local_filled_order_ids(db_path, symbol=symbol)
    outcome = reconcile_local_and_broker(
        local_open_orders=local_open_orders,
        local_filled_order_ids=local_filled_order_ids,
        broker_orders=broker_orders,
    )
    raw_snapshot = {
        "broker_truth_ref": broker_truth_ref,
        "broker_order_count": len(broker_orders),
        "local_open_order_count": len(local_open_orders),
        "local_filled_order_count": len(local_filled_order_ids),
        "source": "KIS_PAPER_ORDER_STATUS",
    }
    reconciliation_id = record_reconciliation_run(
        db_path,
        run_id=run_id,
        started_at=now,
        finished_at=now,
        status=outcome.status,
        max_severity=outcome.severity,
        block_new_orders=outcome.block_new_orders,
        summary_text=outcome.summary_text,
        raw_snapshot_json=_canonical_json(raw_snapshot),
    )
    for event in outcome.events:
        record_reconciliation_event(
            db_path,
            reconciliation_id=reconciliation_id,
            symbol=event.get("symbol"),
            local_order_id=event.get("local_order_id"),
            broker_order_id=event.get("broker_order_id"),
            event_type=str(event.get("event_type") or "UNKNOWN"),
            severity=str(event.get("severity") or "WARN"),
            local_status=event.get("local_status"),
            broker_status=event.get("broker_status"),
            details=event.get("details") if isinstance(event.get("details"), dict) else None,
            created_at=now,
        )

    resolved: list[dict[str, str]] = []
    if resolve_intents:
        broker_by_id = {str(row.get("order_id") or ""): row for row in broker_orders if row.get("order_id")}
        intents = list_paper_order_intents(db_path, states=("UNKNOWN", "SUBMITTED_LOCAL_RECORDED"), limit=100)
        for intent in intents:
            broker_order_id = str(intent.get("broker_order_id") or "")
            broker_row = broker_by_id.get(broker_order_id)
            broker_state = str(broker_row.get("mapped_status") or "ORDER_NOT_FOUND") if broker_row else "ORDER_NOT_FOUND"
            local_state = "UNKNOWN" if str(intent.get("state") or "").upper() == "UNKNOWN" else "SUBMITTED"
            resolution = resolve_paper_order_intent_after_reconciliation(
                db_path,
                idempotency_key=str(intent["idempotency_key"]),
                broker_state=broker_state,
                local_state=local_state,
                updated_at=now,
            )
            resolved.append(
                {
                    "idempotency_key": str(intent["idempotency_key"]),
                    "broker_order_id": broker_order_id,
                    "broker_state": broker_state,
                    "resolution": resolution,
                }
            )

    return BrokerTruthReconciliationResult(
        reconciliation_id=reconciliation_id,
        broker_truth_ref=broker_truth_ref,
        status=outcome.status,
        max_severity=outcome.severity,
        block_new_orders=outcome.block_new_orders,
        event_count=len(outcome.events),
        resolved_intents=tuple(resolved),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run broker-truth reconciliation against KIS paper order status.")
    parser.add_argument("--db-path", default="trading.db")
    parser.add_argument("--symbol", default=None)
    args = parser.parse_args()
    result = run_broker_truth_reconciliation(db_path=args.db_path, symbol=args.symbol)
    print(json.dumps(result.to_dict(), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
