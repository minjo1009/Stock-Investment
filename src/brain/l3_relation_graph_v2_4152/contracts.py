from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


TASK_ID = "TASK-4152"
HORIZON_LABEL = "swing_1m"


class GraphFamily(StrEnum):
    ENTITY_EVENT = "ENTITY_EVENT"
    ENTITY_DIMENSION = "ENTITY_DIMENSION"
    MACRO_FACTOR = "MACRO_FACTOR"
    MACRO_SECTOR = "MACRO_SECTOR"
    SECTOR_THEME = "SECTOR_THEME"
    SOURCE_EVENT_CLUSTER = "SOURCE_EVENT_CLUSTER"
    CONTRADICTION = "CONTRADICTION"
    COVERAGE_GAP = "COVERAGE_GAP"


class DirectionReview(StrEnum):
    RISK_REVIEW = "RISK_REVIEW"
    SUPPORT_REVIEW = "SUPPORT_REVIEW"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    MIXED_REVIEW = "MIXED_REVIEW"
    UNKNOWN_BLOCKER = "UNKNOWN_BLOCKER"


FORBIDDEN_OUTPUT_VALUES = {
    "BUY",
    "SELL",
    "RANK",
    "SCORE",
    "SIZING",
    "ORDER",
    "ORDER_INTENT",
    "PAPER_ELIGIBLE",
    "LIVE_ELIGIBLE",
    "BROKER_MUTATION",
    "STRATEGY_ACCEPTED",
    "DEPLOYMENT_READY",
}


@dataclass(frozen=True)
class RelationEdge:
    edge_id: str
    graph_key: str
    graph_family: GraphFamily
    source_node_id: str
    target_node_id: str
    edge_type: str
    source_artifact: str
    source_row_id: str
    l1_packet_id: str
    l2_row_id: str
    source_family: str
    source_provider: str
    mapping_status: str
    admission_status: str
    economic_dimension: str
    direction_review: DirectionReview
    evidence_time: str
    time_bucket: str
    dedupe_key: str
    blocked_reason: str
    raw_l0_read: bool = False
    diagnostic_only: int = 1
    trading_eligible: int = 0
    signal_export_allowed: int = 0
    order_intent_allowed: int = 0
    broker_mutation_allowed: int = 0
    paper_promotion_allowed: int = 0
    live_order_allowed: int = 0
    strategy_acceptance_allowed: int = 0
    deployment_readiness_allowed: int = 0
    real_capital_allowed: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["graph_family"] = self.graph_family.value
        data["direction_review"] = self.direction_review.value
        data["raw_l0_read"] = int(self.raw_l0_read)
        return data


@dataclass(frozen=True)
class EventCluster:
    event_cluster_key: str
    cluster_basis: str
    event_domain: str
    economic_dimension: str
    primary_target_type: str
    primary_target_key: str
    source_family_count: int
    evidence_count: int
    first_evidence_time: str
    last_evidence_time: str
    cluster_state: str
    lineage_complete: int
    blocked_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CoverageGap:
    gap_id: str
    graph_key: str
    source_family: str
    provider: str
    time_bucket: str
    reason_code: str
    blocked_reason: str
    l1_packet_id: str
    l2_row_id: str
    source_row_id: str
    negative_evidence_allowed: int = 0
    diagnostic_only: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

