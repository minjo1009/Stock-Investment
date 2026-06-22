"""Diagnostic L0-L6 orchestration guardrails.

This module builds deterministic state hashes and idempotency keys for the
review-only realtime operating loop. It does not submit orders, run replay,
mutate broker state, or change acceptance/deployment status.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum


STRATEGY_NOT_ACCEPTED = "NOT_ACCEPTED"
DEPLOYMENT_NOT_READY = "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"
REAL_CAPITAL_FORBIDDEN = "FORBIDDEN"


class DiagnosticHeartbeatCadence(StrEnum):
    EVENT_DRIVEN = "event_driven"
    SAFETY_5_MIN = "5_min_safety"
    BRAIN_10_MIN = "10_min_brain"
    HEAVY_SOURCE_30_MIN = "30_min_heavy_source"
    DAILY_CLOSE = "daily_close"


class DiagnosticOrchestrationStatus(StrEnum):
    DIAGNOSTIC_RUN_REQUIRED = "DIAGNOSTIC_RUN_REQUIRED"
    DUPLICATE_STATE_SKIPPED = "DUPLICATE_STATE_SKIPPED"
    NO_CHANGED_CANDIDATES_SKIPPED = "NO_CHANGED_CANDIDATES_SKIPPED"


def _require_non_empty(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required")


def _require_tuple(values: tuple[str, ...], field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if any(not item for item in values):
        raise ValueError(f"{field_name} cannot contain empty values")


def _normalize_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class L0L6DiagnosticRuntimeState:
    """Immutable runtime state summary for one diagnostic heartbeat."""

    cadence: DiagnosticHeartbeatCadence
    heartbeat_bucket_ts: str
    market_session_id: str
    market_data_asof_ts: str
    account_state_ref: str
    source_receipt_ids: tuple[str, ...]
    primitive_batch_ids: tuple[str, ...]
    meaning_ids: tuple[str, ...]
    thesis_ids: tuple[str, ...]
    policy_action_ids: tuple[str, ...]
    runtime_decision_ids: tuple[str, ...]
    order_state_refs: tuple[str, ...]
    changed_candidate_ids: tuple[str, ...]
    validation_refs: tuple[str, ...]
    strategy_status: str = STRATEGY_NOT_ACCEPTED
    deployment_status: str = DEPLOYMENT_NOT_READY
    real_capital_status: str = REAL_CAPITAL_FORBIDDEN
    paper_order_intent_count: int = 0
    live_order_count: int = 0

    def __post_init__(self) -> None:
        _require_non_empty(self.heartbeat_bucket_ts, "heartbeat_bucket_ts")
        _require_non_empty(self.market_session_id, "market_session_id")
        _require_non_empty(self.market_data_asof_ts, "market_data_asof_ts")
        _require_non_empty(self.account_state_ref, "account_state_ref")
        _require_tuple(self.validation_refs, "validation_refs")

        if self.strategy_status != STRATEGY_NOT_ACCEPTED:
            raise ValueError("strategy_status must remain NOT_ACCEPTED")
        if self.deployment_status != DEPLOYMENT_NOT_READY:
            raise ValueError("deployment_status must remain DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        if self.real_capital_status != REAL_CAPITAL_FORBIDDEN:
            raise ValueError("real_capital_status must remain FORBIDDEN")
        if self.paper_order_intent_count != 0:
            raise ValueError("diagnostic orchestration cannot include paper order intents")
        if self.live_order_count != 0:
            raise ValueError("diagnostic orchestration cannot include live orders")

        if self.cadence == DiagnosticHeartbeatCadence.SAFETY_5_MIN:
            if self.changed_candidate_ids:
                raise ValueError("5-minute safety heartbeat cannot run changed-candidate brain work")
            if self.meaning_ids or self.thesis_ids or self.policy_action_ids:
                raise ValueError("5-minute safety heartbeat cannot recompute L3-L5 brain state")
        if self.cadence == DiagnosticHeartbeatCadence.BRAIN_10_MIN:
            if self.changed_candidate_ids and not self.runtime_decision_ids:
                raise ValueError("10-minute brain heartbeat with changed candidates requires L6 runtime decision refs")
        if self.cadence == DiagnosticHeartbeatCadence.HEAVY_SOURCE_30_MIN:
            if not self.source_receipt_ids:
                raise ValueError("30-minute heavy-source heartbeat requires source receipt refs")

    def normalized_payload(self) -> dict[str, object]:
        """Return the deterministic payload used for state hashing."""

        return {
            "cadence": self.cadence.value,
            "heartbeat_bucket_ts": self.heartbeat_bucket_ts,
            "market_session_id": self.market_session_id,
            "market_data_asof_ts": self.market_data_asof_ts,
            "account_state_ref": self.account_state_ref,
            "source_receipt_ids": _normalize_ids(self.source_receipt_ids),
            "primitive_batch_ids": _normalize_ids(self.primitive_batch_ids),
            "meaning_ids": _normalize_ids(self.meaning_ids),
            "thesis_ids": _normalize_ids(self.thesis_ids),
            "policy_action_ids": _normalize_ids(self.policy_action_ids),
            "runtime_decision_ids": _normalize_ids(self.runtime_decision_ids),
            "order_state_refs": _normalize_ids(self.order_state_refs),
            "changed_candidate_ids": _normalize_ids(self.changed_candidate_ids),
            "validation_refs": _normalize_ids(self.validation_refs),
            "strategy_status": self.strategy_status,
            "deployment_status": self.deployment_status,
            "real_capital_status": self.real_capital_status,
            "paper_order_intent_count": self.paper_order_intent_count,
            "live_order_count": self.live_order_count,
        }

    def state_hash(self) -> str:
        """Return a stable SHA-256 hash for the diagnostic runtime state."""

        return hashlib.sha256(_canonical_json(self.normalized_payload()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DiagnosticOrchestrationDecision:
    """Decision for whether a diagnostic heartbeat should run or be skipped."""

    cadence: DiagnosticHeartbeatCadence
    status: DiagnosticOrchestrationStatus
    state_hash: str
    idempotency_key: str
    allowed_operations: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    reason_codes: tuple[str, ...]
    should_execute: bool

    def __post_init__(self) -> None:
        _require_non_empty(self.state_hash, "state_hash")
        _require_non_empty(self.idempotency_key, "idempotency_key")
        _require_tuple(self.allowed_operations, "allowed_operations")
        _require_tuple(self.forbidden_operations, "forbidden_operations")
        _require_tuple(self.reason_codes, "reason_codes")
        forbidden_text = " ".join(self.forbidden_operations).upper()
        if "LIVE_ORDER" not in forbidden_text or "REAL_CAPITAL" not in forbidden_text:
            raise ValueError("forbidden_operations must explicitly block live orders and real capital")


def build_idempotency_key(state: L0L6DiagnosticRuntimeState, state_hash: str | None = None) -> str:
    digest = state_hash or state.state_hash()
    return f"l0l6-diagnostic:{state.cadence.value}:{state.heartbeat_bucket_ts}:{digest[:16]}"


def _allowed_operations_for(cadence: DiagnosticHeartbeatCadence) -> tuple[str, ...]:
    if cadence == DiagnosticHeartbeatCadence.SAFETY_5_MIN:
        return (
            "check_market_session_freshness",
            "check_account_state_ref",
            "check_order_state_refs",
            "check_existing_l6_runtime_state",
        )
    if cadence == DiagnosticHeartbeatCadence.BRAIN_10_MIN:
        return (
            "refresh_changed_candidate_review_state",
            "validate_l3_l6_review_chain",
            "publish_diagnostic_decision_artifact",
        )
    if cadence == DiagnosticHeartbeatCadence.HEAVY_SOURCE_30_MIN:
        return (
            "refresh_source_receipt_manifest",
            "check_heavy_source_freshness",
            "publish_reporting_snapshot",
        )
    if cadence == DiagnosticHeartbeatCadence.EVENT_DRIVEN:
        return (
            "handle_source_broker_risk_or_freshness_event",
            "validate_event_state_hash",
            "publish_diagnostic_event_artifact",
        )
    return (
        "close_shadow_journal",
        "reconcile_diagnostic_state",
        "publish_next_day_blocker_report",
    )


def _forbidden_operations() -> tuple[str, ...]:
    return (
        "create_paper_order_intent",
        "submit_live_order",
        "mutate_broker_state",
        "run_replay",
        "change_selector_or_sizing",
        "claim_strategy_acceptance",
        "claim_deployment_readiness",
        "permit_real_capital",
    )


def build_diagnostic_orchestration_decision(
    state: L0L6DiagnosticRuntimeState,
    previous_state_hash: str | None = None,
) -> DiagnosticOrchestrationDecision:
    """Build the idempotent decision for one diagnostic heartbeat."""

    state_hash = state.state_hash()
    reason_codes: list[str] = ["DIAGNOSTIC_ONLY", "NO_ORDER_PERMISSION"]
    status = DiagnosticOrchestrationStatus.DIAGNOSTIC_RUN_REQUIRED
    should_execute = True

    if previous_state_hash and previous_state_hash == state_hash:
        status = DiagnosticOrchestrationStatus.DUPLICATE_STATE_SKIPPED
        should_execute = False
        reason_codes.append("STATE_HASH_UNCHANGED")
    elif state.cadence == DiagnosticHeartbeatCadence.BRAIN_10_MIN and not state.changed_candidate_ids:
        status = DiagnosticOrchestrationStatus.NO_CHANGED_CANDIDATES_SKIPPED
        should_execute = False
        reason_codes.append("NO_CHANGED_CANDIDATES")
    else:
        reason_codes.append("STATE_HASH_CHANGED_OR_FIRST_RUN")

    return DiagnosticOrchestrationDecision(
        cadence=state.cadence,
        status=status,
        state_hash=state_hash,
        idempotency_key=build_idempotency_key(state, state_hash),
        allowed_operations=_allowed_operations_for(state.cadence),
        forbidden_operations=_forbidden_operations(),
        reason_codes=tuple(reason_codes),
        should_execute=should_execute,
    )
