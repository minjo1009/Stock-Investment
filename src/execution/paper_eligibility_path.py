"""Evidence-backed PAPER_ELIGIBLE runtime-to-intent path.

This module stops at local paper-order intent creation. It does not submit to a
broker, mutate broker state, create live orders, or grant deployment readiness.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    from src.brain.runtime_authority import (
        BrokerSubmitIdempotencyPlan,
        RuntimeAuthorityCandidate,
        RuntimeAuthorityGate,
        authorize_latest_runtime_decision,
    )
    from src.execution.broker_submit_state import PaperOrderIntentSpec, create_authorized_paper_order_intent
    from src.state.store import record_runtime_authority_evidence
except ModuleNotFoundError:  # pragma: no cover - legacy PYTHONPATH=src execution.
    from brain.runtime_authority import (
        BrokerSubmitIdempotencyPlan,
        RuntimeAuthorityCandidate,
        RuntimeAuthorityGate,
        authorize_latest_runtime_decision,
    )
    from execution.broker_submit_state import PaperOrderIntentSpec, create_authorized_paper_order_intent
    from state.store import record_runtime_authority_evidence


@dataclass(frozen=True)
class PaperEligibilityIntentResult:
    selected_runtime_decision_id: str
    authority_hash: str
    evidence_inserted: bool
    intent: dict


def create_paper_intent_from_latest_authority(
    db_path: str,
    *,
    candidates: tuple[RuntimeAuthorityCandidate, ...],
    idempotency: BrokerSubmitIdempotencyPlan,
    symbol: str,
    side: str,
    quantity: float,
    limit_price: float,
    now: str,
    created_at: str,
) -> PaperEligibilityIntentResult:
    latest = authorize_latest_runtime_decision(candidates, now=now)
    if latest.result.gate != RuntimeAuthorityGate.PAPER_ELIGIBLE or not latest.result.paper_order_intent_allowed:
        raise RuntimeError("LATEST_RUNTIME_DECISION_NOT_PAPER_ELIGIBLE")
    selected = next(
        candidate for candidate in candidates if candidate.runtime.runtime_decision_id == latest.selected_runtime_decision_id
    )
    authority_hash = selected.evidence.authority_hash()
    evidence_inserted = record_runtime_authority_evidence(
        db_path,
        authority_hash=authority_hash,
        authority_id=selected.evidence.authority_id,
        runtime_decision_id=selected.evidence.runtime_decision_id,
        payload=selected.evidence.normalized_payload(),
        created_at=created_at,
    )
    spec = PaperOrderIntentSpec(
        runtime_decision_id=selected.runtime.runtime_decision_id,
        authority=latest.result,
        idempotency=idempotency,
        lineage_hash=selected.runtime.lineage_hash,
        symbol=symbol,
        side=side,
        quantity=quantity,
        limit_price=limit_price,
    )
    intent = create_authorized_paper_order_intent(db_path, spec=spec, created_at=created_at)
    return PaperEligibilityIntentResult(
        selected_runtime_decision_id=latest.selected_runtime_decision_id,
        authority_hash=authority_hash,
        evidence_inserted=evidence_inserted,
        intent=intent,
    )
