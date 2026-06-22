"""Durable broker submit state-machine helpers.

This module contains local state transitions only. It does not call a broker,
submit an order, run replay, or grant paper/live trading permission.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from src.brain.runtime_authority import BrokerSubmitIdempotencyPlan, RuntimeAuthorityResult
    from src.state.store import (
        create_paper_order_intent,
        get_paper_order_intent,
        resolve_paper_order_intent_after_reconciliation,
        transition_paper_order_intent,
    )
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from brain.runtime_authority import BrokerSubmitIdempotencyPlan, RuntimeAuthorityResult
    from state.store import (
        create_paper_order_intent,
        get_paper_order_intent,
        resolve_paper_order_intent_after_reconciliation,
        transition_paper_order_intent,
    )


@dataclass(frozen=True)
class PaperOrderIntentSpec:
    runtime_decision_id: str
    authority: RuntimeAuthorityResult
    idempotency: BrokerSubmitIdempotencyPlan
    lineage_hash: str
    symbol: str
    side: str
    quantity: float
    limit_price: float

    def __post_init__(self) -> None:
        if not self.authority.paper_order_intent_allowed:
            raise ValueError("authority does not allow paper order intent")
        if not self.runtime_decision_id:
            raise ValueError("runtime_decision_id is required")
        if not self.lineage_hash:
            raise ValueError("lineage_hash is required")
        if not self.symbol:
            raise ValueError("symbol is required")
        if self.side.upper() not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.limit_price <= 0:
            raise ValueError("limit_price must be positive")


def create_authorized_paper_order_intent(
    db_path: str,
    *,
    spec: PaperOrderIntentSpec,
    created_at: str,
) -> dict:
    return create_paper_order_intent(
        db_path,
        intent_id=spec.idempotency.local_intent_id,
        idempotency_key=spec.idempotency.idempotency_key,
        runtime_decision_id=spec.runtime_decision_id,
        authority_id=spec.authority.authority_id,
        lineage_hash=spec.lineage_hash,
        scheduler_lease_token=spec.idempotency.scheduler_lease_token,
        symbol=spec.symbol,
        side=spec.side,
        quantity=spec.quantity,
        limit_price=spec.limit_price,
        broker_supports_client_order_id=spec.idempotency.broker_supports_client_order_id,
        broker_client_order_id=spec.idempotency.broker_client_order_id or None,
        created_at=created_at,
    )


def mark_paper_order_intent_submitting(
    db_path: str,
    *,
    idempotency_key: str,
    updated_at: str,
) -> bool:
    return transition_paper_order_intent(
        db_path,
        idempotency_key=idempotency_key,
        from_state="CREATED",
        to_state="SUBMITTING",
        updated_at=updated_at,
    )


def mark_paper_order_intent_local_recorded(
    db_path: str,
    *,
    idempotency_key: str,
    broker_order_id: str,
    raw_response: dict,
    updated_at: str,
) -> bool:
    return transition_paper_order_intent(
        db_path,
        idempotency_key=idempotency_key,
        from_state="SUBMITTING",
        to_state="SUBMITTED_LOCAL_RECORDED",
        updated_at=updated_at,
        broker_order_id=broker_order_id,
        raw_response=raw_response,
    )


def mark_paper_order_intent_unknown_after_submit(
    db_path: str,
    *,
    idempotency_key: str,
    broker_order_id: str,
    raw_response: dict,
    updated_at: str,
) -> bool:
    return transition_paper_order_intent(
        db_path,
        idempotency_key=idempotency_key,
        from_state="SUBMITTING",
        to_state="UNKNOWN",
        updated_at=updated_at,
        broker_order_id=broker_order_id,
        raw_response=raw_response,
    )


def reconcile_paper_order_intent(
    db_path: str,
    *,
    idempotency_key: str,
    broker_state: str,
    local_state: str,
    updated_at: str,
) -> str:
    return resolve_paper_order_intent_after_reconciliation(
        db_path,
        idempotency_key=idempotency_key,
        broker_state=broker_state,
        local_state=local_state,
        updated_at=updated_at,
    )


def get_submit_state(db_path: str, *, idempotency_key: str) -> dict | None:
    return get_paper_order_intent(db_path, idempotency_key=idempotency_key)
