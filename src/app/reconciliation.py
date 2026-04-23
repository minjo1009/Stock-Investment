"""Minimal broker-vs-local reconciliation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


InternalOrderStatus = str
ReconciliationSeverity = str

INTERNAL_STATUS_VALUES = ("SUBMITTED", "FILLED", "REJECTED", "FAILED", "CANCELLED", "UNKNOWN")

_BROKER_STATUS_MAP: dict[str, InternalOrderStatus] = {
    "OPEN": "SUBMITTED",
    "SUBMITTED": "SUBMITTED",
    "PENDING": "SUBMITTED",
    "WORKING": "SUBMITTED",
    "PARTIAL": "SUBMITTED",
    "PARTIALLY_FILLED": "SUBMITTED",
    "FILLED": "FILLED",
    "DONE": "FILLED",
    "REJECTED": "REJECTED",
    "REJECT": "REJECTED",
    "DENIED": "REJECTED",
    "FAILED": "FAILED",
    "FAIL": "FAILED",
    "ERROR": "FAILED",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
    "CANCEL": "CANCELLED",
}


def map_broker_status(raw_status: str | None) -> InternalOrderStatus:
    """Map broker status into minimal internal status with explicit table + UNKNOWN fallback."""
    status = (raw_status or "").strip().upper()
    return _BROKER_STATUS_MAP.get(status, "UNKNOWN")


@dataclass(frozen=True)
class ReconciliationOutcome:
    status: str  # CLEAN / MISMATCH / ERROR
    severity: ReconciliationSeverity  # INFO / WARN / CRITICAL
    block_new_orders: bool
    summary_text: str
    events: tuple[dict[str, Any], ...]


def reconcile_local_and_broker(
    *,
    local_open_orders: list[dict[str, Any]],
    local_filled_order_ids: set[str],
    broker_orders: list[dict[str, Any]],
) -> ReconciliationOutcome:
    """Compare local and broker order/fill truth with conservative mismatch rules."""
    events: list[dict[str, Any]] = []

    local_open_by_id = {
        str(row.get("order_id")): row
        for row in local_open_orders
        if row.get("order_id") not in (None, "")
    }
    broker_by_id = {
        str(row.get("order_id")): row
        for row in broker_orders
        if row.get("order_id") not in (None, "")
    }
    broker_open_by_id = {
        order_id: row
        for order_id, row in broker_by_id.items()
        if row.get("mapped_status") in {"SUBMITTED", "PENDING"}
    }

    for local_order_id, local_row in local_open_by_id.items():
        if local_order_id not in broker_by_id:
            events.append(
                {
                    "event_type": "MISSING_BROKER",
                    "severity": "CRITICAL",
                    "symbol": local_row.get("symbol"),
                    "local_order_id": local_order_id,
                    "broker_order_id": None,
                    "local_status": local_row.get("status"),
                    "broker_status": None,
                    "details": {"reason": "local open order missing in broker open orders"},
                }
            )

    for broker_order_id, broker_row in broker_open_by_id.items():
        if broker_order_id not in local_open_by_id:
            events.append(
                {
                    "event_type": "MISSING_LOCAL",
                    "severity": "CRITICAL",
                    "symbol": broker_row.get("symbol"),
                    "local_order_id": None,
                    "broker_order_id": broker_order_id,
                    "local_status": None,
                    "broker_status": broker_row.get("mapped_status"),
                    "details": {"reason": "broker open order missing in local open orders"},
                }
            )

    for order_id, local_row in local_open_by_id.items():
        broker_row = broker_by_id.get(order_id)
        if broker_row is None:
            continue
        local_status = str(local_row.get("status") or "").upper()
        broker_status = str(broker_row.get("mapped_status") or "")
        if broker_status == "UNKNOWN":
            events.append(
                {
                    "event_type": "STATUS_MISMATCH",
                    "severity": "WARN",
                    "symbol": local_row.get("symbol") or broker_row.get("symbol"),
                    "local_order_id": order_id,
                    "broker_order_id": order_id,
                    "local_status": local_status,
                    "broker_status": broker_status,
                    "details": {"reason": "broker status unknown, block excluded"},
                }
            )
            continue

        critical_status_mismatch = (
            local_status == "SUBMITTED" and broker_status in {"CANCELLED", "REJECTED", "FILLED"}
        )
        if critical_status_mismatch:
            events.append(
                {
                    "event_type": "STATUS_MISMATCH",
                    "severity": "CRITICAL",
                    "symbol": local_row.get("symbol") or broker_row.get("symbol"),
                    "local_order_id": order_id,
                    "broker_order_id": order_id,
                    "local_status": local_status,
                    "broker_status": broker_status,
                    "details": {"reason": "same order has different status local vs broker"},
                }
            )

    for broker_order_id, broker_row in broker_by_id.items():
        filled_qty = float(broker_row.get("filled_qty") or 0.0)
        if filled_qty <= 0:
            continue
        if broker_order_id in local_filled_order_ids:
            continue
        events.append(
            {
                "event_type": "FILL_MISMATCH",
                "severity": "CRITICAL",
                "symbol": broker_row.get("symbol"),
                "local_order_id": broker_order_id if broker_order_id in local_open_by_id else None,
                "broker_order_id": broker_order_id,
                "local_status": local_open_by_id.get(broker_order_id, {}).get("status"),
                "broker_status": broker_row.get("mapped_status"),
                "details": {
                    "reason": "broker shows fill evidence but local fill record is missing",
                    "broker_filled_qty": filled_qty,
                },
            }
        )

    if not events:
        return ReconciliationOutcome(
            status="CLEAN",
            severity="INFO",
            block_new_orders=False,
            summary_text="local and broker states are consistent",
            events=(),
        )

    has_critical = any(str(event.get("severity") or "") == "CRITICAL" for event in events)
    max_severity: ReconciliationSeverity = "CRITICAL" if has_critical else "WARN"
    return ReconciliationOutcome(
        status="MISMATCH",
        severity=max_severity,
        block_new_orders=has_critical,
        summary_text=f"{len(events)} mismatch event(s) detected (severity={max_severity})",
        events=tuple(events),
    )
