from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MeaningDirection(StrEnum):
    SUPPORTIVE = "SUPPORTIVE"
    RISK = "RISK"
    MIXED = "MIXED"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


class MeaningRelationEdgeType(StrEnum):
    SUPPORTS_THESIS = "SUPPORTS_THESIS"
    RISKS_THESIS = "RISKS_THESIS"
    MIXED_CONTEXT = "MIXED_CONTEXT"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    BLOCKED_NOT_READY = "BLOCKED_NOT_READY"


class SourceGap(StrEnum):
    MISSING_RAW_SOURCE = "MISSING_RAW_SOURCE"
    INCOMPLETE_SOURCE = "INCOMPLETE_SOURCE"
    UNKNOWN_SOURCE_GAP = "UNKNOWN_SOURCE_GAP"


@dataclass(frozen=True)
class EconomicMeaning:
    meaning_id: str
    asof_ts: str
    symbol: str
    lifecycle_id: str
    source_packet_ids: tuple[str, ...]
    direction: MeaningDirection
    confidence: float
    confidence_band: str
    relation_readiness: str
    uncertainty_flags: tuple[str, ...]
    reason_codes: tuple[str, ...] = ()
    event_type: str = "unknown"
    economic_dimension: str = "UNKNOWN"
    diagnostic_only: bool = True
    trade_output_flag: int = 0
    score_output_flag: int = 0
    order_intent_flag: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if not self.diagnostic_only:
            raise ValueError("EconomicMeaning is diagnostic-only")
        for flag_name in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
            if int(getattr(self, flag_name)) != 0:
                raise ValueError(f"{flag_name} must remain 0")
        for field_name in ("meaning_id", "asof_ts", "symbol", "lifecycle_id"):
            if not str(getattr(self, field_name, "")).strip():
                raise ValueError(f"{field_name} is required")


@dataclass(frozen=True)
class MeaningRelationEdge:
    relation_edge_id: str
    symbol: str
    lifecycle_id: str
    meaning_ids: tuple[str, ...]
    edge_type: MeaningRelationEdgeType
    confidence_floor: float
    source_gaps: tuple[SourceGap, ...]
    direction_set: tuple[MeaningDirection, ...]
    readiness_set: tuple[str, ...]
    diagnostic_only: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence_floor) <= 1.0:
            raise ValueError("confidence_floor must be in [0, 1]")
        if not self.diagnostic_only:
            raise ValueError("MeaningRelationEdge is diagnostic-only")
        if not self.relation_edge_id:
            raise ValueError("relation_edge_id is required")
