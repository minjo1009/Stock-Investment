"""Runtime authority evidence contracts.

This module is a pre-execution guardrail. It does not submit orders, mutate
broker state, run replay, or promote strategy/deployment status.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from brain.contracts import RuntimeDecision, RuntimeGate


REQUIRED_KILL_SWITCH_LEVELS = (
    "GLOBAL_BLOCK",
    "STRATEGY_BLOCK",
    "SYMBOL_BLOCK",
    "BROKER_BLOCK",
    "SCHEDULER_BLOCK",
)

REQUIRED_PAPER_ELIGIBILITY_EVIDENCE = (
    "SOURCE_FRESHNESS_OK",
    "SNAPSHOT_VERSIONED",
    "LINEAGE_HASH_MATCHED",
    "BROKER_TRUTH_REVIEWED",
    "KILL_SWITCH_CLEAR",
    "PAPER_PERMISSION_EXPLICIT",
)


class RuntimeAuthorityGate(StrEnum):
    BLOCKED = "BLOCKED"
    SHADOW_ONLY = "SHADOW_ONLY"
    PAPER_ELIGIBLE = "PAPER_ELIGIBLE"


def _require_non_empty(value: str, field_name: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _require_tuple(values: tuple[str, ...], field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if any(not str(item or "").strip() for item in values):
        raise ValueError(f"{field_name} cannot contain empty values")


def _parse_utc(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include timezone")
    return parsed


def _canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class RuntimeSnapshotRefs:
    market_data_version: str
    economic_data_version: str
    universe_version: str
    policy_version: str
    source_receipt_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_non_empty(self.market_data_version, "market_data_version")
        _require_non_empty(self.economic_data_version, "economic_data_version")
        _require_non_empty(self.universe_version, "universe_version")
        _require_non_empty(self.policy_version, "policy_version")
        _require_tuple(self.source_receipt_ids, "source_receipt_ids")

    def normalized_payload(self) -> dict[str, object]:
        return {
            "market_data_version": self.market_data_version,
            "economic_data_version": self.economic_data_version,
            "universe_version": self.universe_version,
            "policy_version": self.policy_version,
            "source_receipt_ids": tuple(sorted(set(self.source_receipt_ids))),
        }


@dataclass(frozen=True)
class RuntimeLineageHashes:
    economic_meaning_hash: str
    thesis_bundle_hash: str
    policy_action_hash: str
    runtime_decision_hash: str

    def __post_init__(self) -> None:
        _require_non_empty(self.economic_meaning_hash, "economic_meaning_hash")
        _require_non_empty(self.thesis_bundle_hash, "thesis_bundle_hash")
        _require_non_empty(self.policy_action_hash, "policy_action_hash")
        _require_non_empty(self.runtime_decision_hash, "runtime_decision_hash")

    def normalized_payload(self) -> dict[str, object]:
        return {
            "economic_meaning_hash": self.economic_meaning_hash,
            "thesis_bundle_hash": self.thesis_bundle_hash,
            "policy_action_hash": self.policy_action_hash,
            "runtime_decision_hash": self.runtime_decision_hash,
        }


@dataclass(frozen=True)
class RuntimeAuthorityEvidence:
    authority_id: str
    runtime_decision_id: str
    lineage: RuntimeLineageHashes
    snapshots: RuntimeSnapshotRefs
    valid_from: str
    valid_until: str
    kill_switch_levels_checked: tuple[str, ...]
    paper_eligibility_evidence: tuple[str, ...] = ()
    broker_truth_refs: tuple[str, ...] = ()
    source_quality_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(self.authority_id, "authority_id")
        _require_non_empty(self.runtime_decision_id, "runtime_decision_id")
        _parse_utc(self.valid_from, "valid_from")
        _parse_utc(self.valid_until, "valid_until")
        if _parse_utc(self.valid_from, "valid_from") >= _parse_utc(self.valid_until, "valid_until"):
            raise ValueError("valid_from must be before valid_until")
        missing = set(REQUIRED_KILL_SWITCH_LEVELS).difference(self.kill_switch_levels_checked)
        if missing:
            raise ValueError(f"missing kill-switch levels: {', '.join(sorted(missing))}")
        _require_tuple(self.kill_switch_levels_checked, "kill_switch_levels_checked")

    def normalized_payload(self) -> dict[str, object]:
        return {
            "authority_id": self.authority_id,
            "runtime_decision_id": self.runtime_decision_id,
            "lineage": self.lineage.normalized_payload(),
            "snapshots": self.snapshots.normalized_payload(),
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "kill_switch_levels_checked": tuple(sorted(set(self.kill_switch_levels_checked))),
            "paper_eligibility_evidence": tuple(sorted(set(self.paper_eligibility_evidence))),
            "broker_truth_refs": tuple(sorted(set(self.broker_truth_refs))),
            "source_quality_refs": tuple(sorted(set(self.source_quality_refs))),
        }

    def authority_hash(self) -> str:
        return hashlib.sha256(_canonical_json(self.normalized_payload()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RuntimeAuthorityResult:
    authority_id: str
    gate: RuntimeAuthorityGate
    authority_hash: str
    reason_codes: tuple[str, ...]
    paper_order_intent_allowed: bool

    def __post_init__(self) -> None:
        _require_non_empty(self.authority_id, "authority_id")
        _require_non_empty(self.authority_hash, "authority_hash")
        _require_tuple(self.reason_codes, "reason_codes")
        if self.paper_order_intent_allowed and self.gate != RuntimeAuthorityGate.PAPER_ELIGIBLE:
            raise ValueError("paper order intent requires PAPER_ELIGIBLE authority")


@dataclass(frozen=True)
class RuntimeAuthorityCandidate:
    runtime: RuntimeDecision
    evidence: RuntimeAuthorityEvidence

    def __post_init__(self) -> None:
        if self.runtime.runtime_decision_id != self.evidence.runtime_decision_id:
            raise ValueError("candidate runtime decision id mismatch")


@dataclass(frozen=True)
class LatestRuntimeAuthorityDecision:
    selected_runtime_decision_id: str
    result: RuntimeAuthorityResult
    candidate_count: int
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_tuple(self.reason_codes, "reason_codes")


@dataclass(frozen=True)
class BrokerSubmitIdempotencyPlan:
    local_intent_id: str
    idempotency_key: str
    scheduler_lease_token: str
    broker_supports_client_order_id: bool
    broker_client_order_id: str = ""
    reconciliation_before_retry_required: bool = True

    def __post_init__(self) -> None:
        _require_non_empty(self.local_intent_id, "local_intent_id")
        _require_non_empty(self.idempotency_key, "idempotency_key")
        _require_non_empty(self.scheduler_lease_token, "scheduler_lease_token")
        if self.broker_supports_client_order_id:
            if self.broker_client_order_id != self.idempotency_key:
                raise ValueError("broker_client_order_id must equal idempotency_key when broker idempotency is supported")
        elif not self.reconciliation_before_retry_required:
            raise ValueError("broker without client order id requires reconciliation before retry")


def validate_runtime_authority(
    runtime: RuntimeDecision,
    evidence: RuntimeAuthorityEvidence,
    *,
    now: str,
) -> RuntimeAuthorityResult:
    """Validate L6 authority evidence before any order-intent path can proceed."""

    if runtime.runtime_decision_id != evidence.runtime_decision_id:
        raise ValueError("runtime decision id mismatch")
    now_dt = _parse_utc(now, "now")
    reason_codes: list[str] = ["AUTHORITY_EVIDENCE_CHECKED"]
    if now_dt < _parse_utc(evidence.valid_from, "valid_from"):
        return RuntimeAuthorityResult(
            authority_id=evidence.authority_id,
            gate=RuntimeAuthorityGate.BLOCKED,
            authority_hash=evidence.authority_hash(),
            reason_codes=tuple(reason_codes + ["RUNTIME_DECISION_NOT_YET_VALID"]),
            paper_order_intent_allowed=False,
        )
    if now_dt >= _parse_utc(evidence.valid_until, "valid_until"):
        return RuntimeAuthorityResult(
            authority_id=evidence.authority_id,
            gate=RuntimeAuthorityGate.BLOCKED,
            authority_hash=evidence.authority_hash(),
            reason_codes=tuple(reason_codes + ["RUNTIME_DECISION_EXPIRED"]),
            paper_order_intent_allowed=False,
        )

    if runtime.gate == RuntimeGate.PAPER_ELIGIBLE:
        missing = set(REQUIRED_PAPER_ELIGIBILITY_EVIDENCE).difference(evidence.paper_eligibility_evidence)
        if missing or not evidence.broker_truth_refs or not evidence.source_quality_refs:
            return RuntimeAuthorityResult(
                authority_id=evidence.authority_id,
                gate=RuntimeAuthorityGate.BLOCKED,
                authority_hash=evidence.authority_hash(),
                reason_codes=tuple(reason_codes + ["PAPER_ELIGIBILITY_EVIDENCE_INCOMPLETE"]),
                paper_order_intent_allowed=False,
            )
        if not runtime.paper_order_intent_allowed:
            return RuntimeAuthorityResult(
                authority_id=evidence.authority_id,
                gate=RuntimeAuthorityGate.BLOCKED,
                authority_hash=evidence.authority_hash(),
                reason_codes=tuple(reason_codes + ["PAPER_PERMISSION_NOT_EXPLICIT"]),
                paper_order_intent_allowed=False,
            )
        return RuntimeAuthorityResult(
            authority_id=evidence.authority_id,
            gate=RuntimeAuthorityGate.PAPER_ELIGIBLE,
            authority_hash=evidence.authority_hash(),
            reason_codes=tuple(reason_codes + ["PAPER_ELIGIBILITY_EVIDENCE_COMPLETE"]),
            paper_order_intent_allowed=True,
        )

    if runtime.gate == RuntimeGate.SHADOW_ONLY:
        return RuntimeAuthorityResult(
            authority_id=evidence.authority_id,
            gate=RuntimeAuthorityGate.SHADOW_ONLY,
            authority_hash=evidence.authority_hash(),
            reason_codes=tuple(reason_codes + ["SHADOW_ONLY_NO_ORDER_PERMISSION"]),
            paper_order_intent_allowed=False,
        )

    return RuntimeAuthorityResult(
        authority_id=evidence.authority_id,
        gate=RuntimeAuthorityGate.BLOCKED,
        authority_hash=evidence.authority_hash(),
        reason_codes=tuple(reason_codes + ["RUNTIME_GATE_BLOCKED"]),
        paper_order_intent_allowed=False,
    )


def authorize_latest_runtime_decision(
    candidates: tuple[RuntimeAuthorityCandidate, ...],
    *,
    now: str,
) -> LatestRuntimeAuthorityDecision:
    """Validate exactly one latest L6 runtime decision as the authority source."""

    if not candidates:
        blocked = RuntimeAuthorityResult(
            authority_id="single-l6-authority:none",
            gate=RuntimeAuthorityGate.BLOCKED,
            authority_hash="no-runtime-authority-evidence",
            reason_codes=("NO_RUNTIME_DECISION_CANDIDATE",),
            paper_order_intent_allowed=False,
        )
        return LatestRuntimeAuthorityDecision(
            selected_runtime_decision_id="",
            result=blocked,
            candidate_count=0,
            reason_codes=("NO_RUNTIME_DECISION_CANDIDATE",),
        )

    sorted_candidates = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                _parse_utc(candidate.evidence.valid_from, "valid_from"),
                candidate.runtime.runtime_decision_id,
            ),
            reverse=True,
        )
    )
    latest = sorted_candidates[0]
    tied_latest = [
        candidate
        for candidate in sorted_candidates
        if _parse_utc(candidate.evidence.valid_from, "valid_from")
        == _parse_utc(latest.evidence.valid_from, "valid_from")
    ]
    if len(tied_latest) > 1:
        raise ValueError("single runtime authority requires one latest RuntimeDecision")
    result = validate_runtime_authority(latest.runtime, latest.evidence, now=now)
    reason_codes = tuple(result.reason_codes + ("SINGLE_LATEST_L6_AUTHORITY",))
    return LatestRuntimeAuthorityDecision(
        selected_runtime_decision_id=latest.runtime.runtime_decision_id,
        result=RuntimeAuthorityResult(
            authority_id=result.authority_id,
            gate=result.gate,
            authority_hash=result.authority_hash,
            reason_codes=reason_codes,
            paper_order_intent_allowed=result.paper_order_intent_allowed,
        ),
        candidate_count=len(candidates),
        reason_codes=reason_codes,
    )
