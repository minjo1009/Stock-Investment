"""Typed contracts for the Trader Brain handoff into runtime and UI layers.

These objects are boundary contracts only. They do not rank trades, size
positions, submit orders, run replay, or change acceptance status.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class BrainLayer(StrEnum):
    L3_ECONOMIC_MEANING = "L3_ECONOMIC_MEANING"
    L4_THESIS_BUNDLE = "L4_THESIS_BUNDLE"
    L5_POLICY_ACTION = "L5_POLICY_ACTION"
    L6_RUNTIME_GATE = "L6_RUNTIME_GATE"
    L7_FRONTEND_READ_MODEL = "L7_FRONTEND_READ_MODEL"


class MeaningDirection(StrEnum):
    SUPPORTIVE = "SUPPORTIVE"
    RISK = "RISK"
    MIXED = "MIXED"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


class RelationEdgeType(StrEnum):
    SUPPORTS_THESIS = "SUPPORTS_THESIS"
    RISKS_THESIS = "RISKS_THESIS"
    MIXED_CONTEXT = "MIXED_CONTEXT"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    BLOCKED_NOT_READY = "BLOCKED_NOT_READY"


class ThesisInvalidationState(StrEnum):
    NONE = "NONE"
    WATCH = "WATCH"
    HARD_INVALIDATED = "HARD_INVALIDATED"
    UNKNOWN = "UNKNOWN"


class PolicyActionType(StrEnum):
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    EXIT = "EXIT"
    RERISK = "RERISK"
    WATCH = "WATCH"
    SKIP = "SKIP"


class SizingDirective(StrEnum):
    NONE = "NONE"
    UNCHANGED = "UNCHANGED"
    CAP_ONLY = "CAP_ONLY"
    REDUCE_ONLY = "REDUCE_ONLY"


class RuntimeGate(StrEnum):
    SHADOW_ONLY = "SHADOW_ONLY"
    PAPER_ELIGIBLE = "PAPER_ELIGIBLE"
    BLOCKED = "BLOCKED"
    BROKER_REVIEW_REQUIRED = "BROKER_REVIEW_REQUIRED"


class SourceGap(StrEnum):
    MISSING_RAW_SOURCE = "MISSING_RAW_SOURCE"
    MISSING_ASOF_TIMESTAMP = "MISSING_ASOF_TIMESTAMP"
    MISSING_BROKER_TRUTH = "MISSING_BROKER_TRUTH"
    PARTIAL_RUNTIME_EVIDENCE = "PARTIAL_RUNTIME_EVIDENCE"
    NONE = "NONE"


def _require_non_empty(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required")


def _require_tuple(values: tuple[str, ...], field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} must contain at least one value")
    if any(not item for item in values):
        raise ValueError(f"{field_name} cannot contain empty values")


def _parse_iso_ts(value: str, field_name: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO timestamp") from exc


def _forbidden_status_text(value: str) -> bool:
    normalized = value.upper().replace("-", "_").replace(" ", "_")
    forbidden_tokens = (
        "ACCEPTED",
        "DEPLOYMENT_READY",
        "LIVE_ORDER_ALLOWED",
        "REAL_CAPITAL_ALLOWED",
    )
    return any(token in normalized for token in forbidden_tokens)


@dataclass(frozen=True)
class EconomicMeaning:
    """L3 interpretation object.

    It may carry direction, confidence, uncertainty, and source references.
    It may not carry assignment labels, order intent, or broker actions.
    """

    meaning_id: str
    asof_ts: str
    symbol: str
    direction: MeaningDirection
    confidence: float
    uncertainty_flags: tuple[str, ...]
    source_packet_ids: tuple[str, ...]
    relation_readiness: str
    outcome_used_for_assignment: bool = False

    def __post_init__(self) -> None:
        _require_non_empty(self.meaning_id, "meaning_id")
        _require_non_empty(self.asof_ts, "asof_ts")
        _require_non_empty(self.symbol, "symbol")
        _require_non_empty(self.relation_readiness, "relation_readiness")
        _require_tuple(self.source_packet_ids, "source_packet_ids")
        if not (0 <= self.confidence <= 1):
            raise ValueError("confidence must be in [0, 1]")
        if self.outcome_used_for_assignment:
            raise ValueError("outcome fields are forbidden in L3 assignment")


@dataclass(frozen=True)
class MeaningRelationEdge:
    """L3 relation edge object built from review-only economic meanings."""

    relation_edge_id: str
    symbol: str
    decision_asof_ts: str
    meaning_ids: tuple[str, ...]
    edge_type: RelationEdgeType
    confidence_floor: float
    source_packet_ids: tuple[str, ...]
    blocker_flags: tuple[str, ...]
    source_gaps: tuple[SourceGap, ...]
    outcome_used_for_assignment: bool = False

    def __post_init__(self) -> None:
        _require_non_empty(self.relation_edge_id, "relation_edge_id")
        _require_non_empty(self.symbol, "symbol")
        _require_non_empty(self.decision_asof_ts, "decision_asof_ts")
        _require_tuple(self.meaning_ids, "meaning_ids")
        _require_tuple(self.source_packet_ids, "source_packet_ids")
        if not (0 <= self.confidence_floor <= 1):
            raise ValueError("confidence_floor must be in [0, 1]")
        if SourceGap.NONE in self.source_gaps and len(self.source_gaps) > 1:
            raise ValueError("SourceGap.NONE cannot be combined with other source gaps")
        if self.outcome_used_for_assignment:
            raise ValueError("outcome fields are forbidden in L3 relation assignment")


@dataclass(frozen=True)
class ThesisBundle:
    """L4 candidate thesis object."""

    thesis_id: str
    trade_spec_id: str
    symbol: str
    decision_asof_ts: str
    meaning_ids: tuple[str, ...]
    catalyst_summary: str
    invalidation_state: ThesisInvalidationState
    blocker_flags: tuple[str, ...]
    source_gaps: tuple[SourceGap, ...]
    outcome_used_for_assignment: bool = False

    def __post_init__(self) -> None:
        _require_non_empty(self.thesis_id, "thesis_id")
        _require_non_empty(self.trade_spec_id, "trade_spec_id")
        _require_non_empty(self.symbol, "symbol")
        _require_non_empty(self.decision_asof_ts, "decision_asof_ts")
        _require_non_empty(self.catalyst_summary, "catalyst_summary")
        _require_tuple(self.meaning_ids, "meaning_ids")
        if SourceGap.NONE in self.source_gaps and len(self.source_gaps) > 1:
            raise ValueError("SourceGap.NONE cannot be combined with other source gaps")
        if self.outcome_used_for_assignment:
            raise ValueError("outcome fields are forbidden in L4 assignment")


@dataclass(frozen=True)
class PolicyAction:
    """L5 policy action proposal.

    L5 can propose an action under a policy, but cannot create orders directly.
    """

    action_id: str
    policy_id: str
    thesis_id: str
    action: PolicyActionType
    sizing_directive: SizingDirective
    reason_codes: tuple[str, ...]
    evidence_paths: tuple[str, ...]
    creates_order_intent: bool = False

    def __post_init__(self) -> None:
        _require_non_empty(self.action_id, "action_id")
        _require_non_empty(self.policy_id, "policy_id")
        _require_non_empty(self.thesis_id, "thesis_id")
        _require_tuple(self.reason_codes, "reason_codes")
        _require_tuple(self.evidence_paths, "evidence_paths")
        if self.creates_order_intent:
            raise ValueError("L5 PolicyAction cannot create order intent directly")
        if self.action in (PolicyActionType.HOLD, PolicyActionType.WATCH, PolicyActionType.SKIP):
            if self.sizing_directive not in (SizingDirective.NONE, SizingDirective.UNCHANGED):
                raise ValueError("non-sizing actions cannot carry sizing directives")
        if self.action == PolicyActionType.REDUCE and self.sizing_directive != SizingDirective.REDUCE_ONLY:
            raise ValueError("REDUCE action requires REDUCE_ONLY sizing directive")


@dataclass(frozen=True)
class RuntimeDecision:
    """L6 runtime gate decision."""

    runtime_decision_id: str
    policy_action_id: str
    gate: RuntimeGate
    blocker_flags: tuple[str, ...]
    validation_refs: tuple[str, ...]
    paper_order_intent_allowed: bool = False
    live_order_allowed: bool = False
    valid_from: str = ""
    valid_until: str = ""
    snapshot_refs: tuple[str, ...] = ()
    lineage_hash: str = ""

    def __post_init__(self) -> None:
        _require_non_empty(self.runtime_decision_id, "runtime_decision_id")
        _require_non_empty(self.policy_action_id, "policy_action_id")
        _require_tuple(self.validation_refs, "validation_refs")
        if self.live_order_allowed:
            raise ValueError("live order permission is forbidden while real capital is FORBIDDEN")
        if self.paper_order_intent_allowed and self.gate != RuntimeGate.PAPER_ELIGIBLE:
            raise ValueError("paper order intent requires PAPER_ELIGIBLE gate")
        if self.gate == RuntimeGate.PAPER_ELIGIBLE and self.blocker_flags:
            raise ValueError("PAPER_ELIGIBLE runtime decisions cannot carry blocker_flags")
        if self.gate in (RuntimeGate.BLOCKED, RuntimeGate.BROKER_REVIEW_REQUIRED) and not self.blocker_flags:
            raise ValueError("blocked or broker-review runtime decisions require blocker_flags")
        has_authority_fields = bool(self.valid_from or self.valid_until or self.snapshot_refs or self.lineage_hash)
        if self.gate == RuntimeGate.PAPER_ELIGIBLE or self.paper_order_intent_allowed or has_authority_fields:
            _require_non_empty(self.valid_from, "valid_from")
            _require_non_empty(self.valid_until, "valid_until")
            _require_tuple(self.snapshot_refs, "snapshot_refs")
            _require_non_empty(self.lineage_hash, "lineage_hash")
            if _parse_iso_ts(self.valid_from, "valid_from") >= _parse_iso_ts(self.valid_until, "valid_until"):
                raise ValueError("valid_from must be before valid_until")


@dataclass(frozen=True)
class FrontendReadModel:
    """L7 read-only cockpit object."""

    read_model_id: str
    runtime_decision_id: str
    source_tier: str
    display_status: str
    provenance_paths: tuple[str, ...]
    blocker_flags: tuple[str, ...]
    read_only: bool = True

    def __post_init__(self) -> None:
        _require_non_empty(self.read_model_id, "read_model_id")
        _require_non_empty(self.runtime_decision_id, "runtime_decision_id")
        _require_non_empty(self.source_tier, "source_tier")
        _require_non_empty(self.display_status, "display_status")
        _require_tuple(self.provenance_paths, "provenance_paths")
        if _forbidden_status_text(self.display_status):
            raise ValueError("frontend display status cannot claim acceptance, deployment, live-order, or real-capital readiness")
        if not self.read_only:
            raise ValueError("frontend read models must be read-only")


def assert_no_assignment_leakage(
    meaning: EconomicMeaning,
    thesis: ThesisBundle,
    action: PolicyAction,
    runtime: RuntimeDecision,
    read_model: FrontendReadModel,
) -> None:
    """Validate the first package-level brain-runtime contract invariants."""

    if meaning.meaning_id not in thesis.meaning_ids:
        raise ValueError("thesis must reference the supplied meaning")
    if meaning.symbol != thesis.symbol:
        raise ValueError("meaning and thesis symbols must match")
    if _parse_iso_ts(meaning.asof_ts, "meaning.asof_ts") > _parse_iso_ts(thesis.decision_asof_ts, "thesis.decision_asof_ts"):
        raise ValueError("meaning asof_ts cannot be after thesis decision_asof_ts")
    if action.thesis_id != thesis.thesis_id:
        raise ValueError("policy action must reference the supplied thesis")
    if runtime.policy_action_id != action.action_id:
        raise ValueError("runtime decision must reference the supplied policy action")
    if read_model.runtime_decision_id != runtime.runtime_decision_id:
        raise ValueError("frontend read model must reference the runtime decision")
    if not read_model.read_only:
        raise ValueError("frontend read model must be read-only")
    if runtime.paper_order_intent_allowed and action.action in (PolicyActionType.HOLD, PolicyActionType.WATCH, PolicyActionType.SKIP):
        raise ValueError("non-trading policy actions cannot be paper-order eligible")
    if runtime.live_order_allowed:
        raise ValueError("live order permission is forbidden")
