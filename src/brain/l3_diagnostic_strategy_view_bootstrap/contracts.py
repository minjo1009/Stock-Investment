from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


TASK_ID = "TASK-4150"


class DirectionReview(StrEnum):
    SUPPORT_REVIEW = "SUPPORT_REVIEW"
    RISK_REVIEW = "RISK_REVIEW"
    MIXED_REVIEW = "MIXED_REVIEW"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    UNKNOWN = "UNKNOWN"


class GraphState(StrEnum):
    SUPPORT_DOMINANT_REVIEW = "SUPPORT_DOMINANT_REVIEW"
    RISK_DOMINANT_REVIEW = "RISK_DOMINANT_REVIEW"
    MIXED_REVIEW = "MIXED_REVIEW"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    BLOCKED_CRITICAL = "BLOCKED_CRITICAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class CalibrationStatus(StrEnum):
    NOT_CALIBRATED = "NOT_CALIBRATED"
    CALIBRATED = "CALIBRATED"


CONFIDENCE_STATIC_WEIGHT = {
    "high": 0.85,
    "medium": 0.60,
    "low": 0.35,
    "unknown": 0.0,
    "insufficient": 0.0,
}

FORBIDDEN_AUTHORITY_FIELDS = {
    "trading_eligible",
    "signal_export_allowed",
    "order_intent_allowed",
    "paper_promotion_allowed",
    "live_order_allowed",
    "broker_mutation_allowed",
    "strategy_acceptance_allowed",
    "deployment_readiness_allowed",
    "real_capital_allowed",
}


@dataclass(frozen=True)
class AuthorityFlags:
    trading_eligible: bool = False
    signal_export_allowed: bool = False
    order_intent_allowed: bool = False
    paper_promotion_allowed: bool = False
    live_order_allowed: bool = False
    broker_mutation_allowed: bool = False
    strategy_acceptance_allowed: bool = False
    deployment_readiness_allowed: bool = False
    real_capital_allowed: bool = False

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)

    def assert_closed(self) -> None:
        opened = [name for name, value in self.to_dict().items() if value]
        if opened:
            raise ValueError(f"L3 authority flags must remain closed: {opened}")


@dataclass(frozen=True)
class L3InputPrimitive:
    input_id: str
    source_kind: str
    l2_row_id: str
    l1_packet_id: str
    source_family: str
    provider: str
    source_key: str
    event_time: str
    available_to_brain_ts: str
    target_node_type: str
    target_node_key: str
    mapping_status: str
    dedupe_status: str
    l1_status: str
    l2_status: str
    raw_sha256: str
    lineage_hash: str
    title: str
    feature_name: str
    feature_value: str
    blocker_reasons: tuple[str, ...]
    noncritical_gaps: tuple[str, ...]


@dataclass(frozen=True)
class L3Meaning:
    l3_meaning_id: str
    input_id: str
    l2_row_id: str
    l1_packet_id: str
    source_family: str
    provider: str
    event_time: str
    available_to_brain_ts: str
    target_node_type: str
    target_node_key: str
    economic_dimension: str
    event_class: str
    direction_review: DirectionReview
    confidence_band: str
    static_confidence_weight: float
    calibration_status: CalibrationStatus
    calibrated_probability: None
    critical_blockers: tuple[str, ...]
    noncritical_gaps: tuple[str, ...]
    reason_codes: tuple[str, ...]
    authority_flags: AuthorityFlags

    def to_dict(self) -> dict[str, Any]:
        self.authority_flags.assert_closed()
        data = asdict(self)
        data["direction_review"] = self.direction_review.value
        data["calibration_status"] = self.calibration_status.value
        data["critical_blockers"] = ";".join(self.critical_blockers)
        data["noncritical_gaps"] = ";".join(self.noncritical_gaps)
        data["reason_codes"] = ";".join(self.reason_codes)
        data.update(self.authority_flags.to_dict())
        data.pop("authority_flags", None)
        return data


@dataclass(frozen=True)
class L3EvidenceEdge:
    evidence_edge_id: str
    l3_meaning_id: str
    graph_key: str
    target_node_type: str
    target_node_key: str
    economic_dimension: str
    direction_review: DirectionReview
    review_strength_band: str
    source_reliability_component: float
    freshness_component: float
    evidence_completeness_component: float
    contradiction_flag: int
    critical_blocker_flag: int
    noncritical_gap_flag: int
    reason_codes: tuple[str, ...]
    authority_flags: AuthorityFlags

    def to_dict(self) -> dict[str, Any]:
        self.authority_flags.assert_closed()
        data = asdict(self)
        data["direction_review"] = self.direction_review.value
        data["reason_codes"] = ";".join(self.reason_codes)
        data.update(self.authority_flags.to_dict())
        data.pop("authority_flags", None)
        return data


def closed_authority_flags() -> AuthorityFlags:
    flags = AuthorityFlags()
    flags.assert_closed()
    return flags

