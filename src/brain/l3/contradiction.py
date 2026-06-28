from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from src.brain.contracts import MeaningDirection
from src.brain.l3.contracts import L3EvidenceEdge


@dataclass(frozen=True)
class L3Contradiction:
    contradiction_id: str
    positive_edge_id: str
    negative_edge_id: str
    contradiction_type: str
    severity: str
    resolution_required: bool
    reason_codes: tuple[str, ...]


def detect_contradictions(
    edges: tuple[L3EvidenceEdge, ...],
    *,
    min_edge_weight: float = 0.0,
) -> tuple[L3Contradiction, ...]:
    contradictions: list[L3Contradiction] = []
    for left, right in combinations(edges, 2):
        if left.symbol != right.symbol:
            continue
        if left.economic_dimension != right.economic_dimension:
            continue
        if min(left.edge_weight, right.edge_weight) < min_edge_weight:
            continue
        directions = {left.direction, right.direction}
        if directions != {MeaningDirection.SUPPORTIVE, MeaningDirection.RISK}:
            continue
        positive = left if left.direction == MeaningDirection.SUPPORTIVE else right
        negative = right if positive is left else left
        severity = "HIGH" if min(left.edge_weight, right.edge_weight) >= 0.25 else "MEDIUM"
        contradictions.append(
            L3Contradiction(
                contradiction_id=f"l3_contradiction:{positive.evidence_edge_id}:{negative.evidence_edge_id}",
                positive_edge_id=positive.evidence_edge_id,
                negative_edge_id=negative.evidence_edge_id,
                contradiction_type="OPPOSING_DIRECTION_SAME_DIMENSION",
                severity=severity,
                resolution_required=True,
                reason_codes=("CONTRADICTION_REQUIRES_REVIEW", "DIAGNOSTIC_REVIEW_ONLY"),
            )
        )
    return tuple(contradictions)
