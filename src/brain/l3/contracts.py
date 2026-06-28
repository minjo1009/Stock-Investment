from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.brain.contracts import MeaningDirection


class L3CalibrationStatus(StrEnum):
    NOT_CALIBRATED = "NOT_CALIBRATED"
    CALIBRATED = "CALIBRATED"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    STALE_CALIBRATION = "STALE_CALIBRATION"


class L3EvidenceEdgeState(StrEnum):
    SUPPORTIVE = "SUPPORTIVE"
    RISK = "RISK"
    MIXED = "MIXED"
    CONTEXT = "CONTEXT"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    STALE = "STALE"
    MISSING = "MISSING"
    CRITICAL_BLOCKED = "CRITICAL_BLOCKED"


class L3RelationGraphState(StrEnum):
    SUPPORT_DOMINANT_REVIEW = "SUPPORT_DOMINANT_REVIEW"
    RISK_DOMINANT_REVIEW = "RISK_DOMINANT_REVIEW"
    MIXED_REVIEW = "MIXED_REVIEW"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    BLOCKED_CRITICAL = "BLOCKED_CRITICAL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


def _require_probability(name: str, value: float | None) -> None:
    if value is None:
        return
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")


def _require_tuple(name: str, value: tuple[str, ...]) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{name} must be a tuple")


@dataclass(frozen=True)
class L3Confidence:
    raw_band: str
    static_weight: float
    calibrated_probability: float | None
    calibration_status: L3CalibrationStatus
    calibration_version: str
    sample_size: int | None
    brier_score: float | None
    calibration_error: float | None

    def __post_init__(self) -> None:
        _require_probability("static_weight", self.static_weight)
        _require_probability("calibrated_probability", self.calibrated_probability)
        _require_probability("brier_score", self.brier_score)
        _require_probability("calibration_error", self.calibration_error)
        if self.calibration_status != L3CalibrationStatus.CALIBRATED and self.calibrated_probability is not None:
            raise ValueError("calibrated_probability must be None unless status is CALIBRATED")
        if self.calibration_status == L3CalibrationStatus.CALIBRATED:
            if self.calibrated_probability is None:
                raise ValueError("CALIBRATED requires calibrated_probability")
            if not self.calibration_version:
                raise ValueError("CALIBRATED requires calibration_version")
            if self.sample_size is None or int(self.sample_size) <= 0:
                raise ValueError("CALIBRATED requires positive sample_size")


@dataclass(frozen=True)
class L3EconomicMeaningV2:
    meaning_id: str
    asof_ts: str
    symbol: str
    l2_primitive_ids: tuple[str, ...]
    source_receipt_ids: tuple[str, ...]
    source_family: str
    provider: str
    authority_class: str
    runtime_context: str
    source_time_certified: bool
    freshness_status: str
    event_type: str
    economic_dimension: str
    direction: MeaningDirection
    confidence: L3Confidence
    uncertainty_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    diagnostic_only: bool = True
    trade_output_flag: int = 0
    score_output_flag: int = 0
    order_intent_flag: int = 0

    def __post_init__(self) -> None:
        for name in (
            "meaning_id",
            "asof_ts",
            "symbol",
            "source_family",
            "provider",
            "authority_class",
            "runtime_context",
            "freshness_status",
            "event_type",
            "economic_dimension",
        ):
            if not str(getattr(self, name, "")).strip():
                raise ValueError(f"{name} is required")
        for name in ("l2_primitive_ids", "source_receipt_ids", "uncertainty_flags", "reason_codes"):
            _require_tuple(name, getattr(self, name))
        if not isinstance(self.source_time_certified, bool):
            raise ValueError("source_time_certified must be explicit bool")
        if not self.diagnostic_only:
            raise ValueError("L3EconomicMeaningV2 must remain diagnostic_only")
        for flag_name in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
            if int(getattr(self, flag_name)) != 0:
                raise ValueError(f"{flag_name} must remain 0")


@dataclass(frozen=True)
class L3EvidenceEdge:
    evidence_edge_id: str
    meaning_id: str
    symbol: str
    event_type: str
    economic_dimension: str
    direction: MeaningDirection
    edge_state: L3EvidenceEdgeState
    source_reliability_score: float
    event_prior_score: float
    freshness_decay_score: float
    evidence_completeness_score: float
    contradiction_penalty: float
    confidence_static_weight: float
    calibrated_probability: float | None
    edge_weight: float
    critical_blocker_flags: tuple[str, ...]
    noncritical_gap_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("evidence_edge_id", "meaning_id", "symbol", "event_type", "economic_dimension"):
            if not str(getattr(self, name, "")).strip():
                raise ValueError(f"{name} is required")
        for name in (
            "source_reliability_score",
            "event_prior_score",
            "freshness_decay_score",
            "evidence_completeness_score",
            "contradiction_penalty",
            "confidence_static_weight",
            "edge_weight",
        ):
            _require_probability(name, float(getattr(self, name)))
        _require_probability("calibrated_probability", self.calibrated_probability)
        for name in ("critical_blocker_flags", "noncritical_gap_flags", "reason_codes"):
            _require_tuple(name, getattr(self, name))


@dataclass(frozen=True)
class L3RelationGraph:
    relation_graph_id: str
    symbol: str
    decision_asof_ts: str
    evidence_edge_ids: tuple[str, ...]
    support_score: float
    risk_score: float
    context_score: float
    blocker_score: float
    net_direction_score: float
    coverage_score: float
    graph_state: L3RelationGraphState
    critical_blocker_flags: tuple[str, ...]
    noncritical_gap_flags: tuple[str, ...]
    confidence_floor: float
    confidence_weighted_mean: float
    diagnostic_only: bool = True

    def __post_init__(self) -> None:
        for name in ("relation_graph_id", "symbol", "decision_asof_ts"):
            if not str(getattr(self, name, "")).strip():
                raise ValueError(f"{name} is required")
        _require_tuple("evidence_edge_ids", self.evidence_edge_ids)
        _require_probability("coverage_score", self.coverage_score)
        _require_probability("confidence_floor", self.confidence_floor)
        _require_probability("confidence_weighted_mean", self.confidence_weighted_mean)
        if min(self.support_score, self.risk_score, self.context_score, self.blocker_score) < 0.0:
            raise ValueError("graph scores must be non-negative")
        if not self.diagnostic_only:
            raise ValueError("L3RelationGraph must remain diagnostic_only")
