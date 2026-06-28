from __future__ import annotations

from collections.abc import Iterable

from src.brain.contracts import MeaningDirection
from src.brain.l3.contracts import L3EvidenceEdge, L3RelationGraph, L3RelationGraphState
from src.brain.l3.relation_graph import load_relation_graph_thresholds


def aggregate_evidence_graph(
    edges: Iterable[L3EvidenceEdge],
    *,
    relation_graph_id: str,
    symbol: str,
    decision_asof_ts: str,
    expected_edges: int | None = None,
    coverage_threshold: float | None = None,
    dominance_ratio: float | None = None,
) -> L3RelationGraph:
    items = tuple(edges)
    thresholds = load_relation_graph_thresholds()
    coverage_limit = float(coverage_threshold if coverage_threshold is not None else thresholds["coverage_threshold"])
    dominance = float(dominance_ratio if dominance_ratio is not None else thresholds["dominance_ratio"])
    expected = expected_edges if expected_edges is not None else len(items)
    critical_flags = tuple(
        sorted({flag for edge in items for flag in edge.critical_blocker_flags})
    )
    noncritical_flags = tuple(
        sorted({flag for edge in items for flag in edge.noncritical_gap_flags})
    )
    valid_edges = [edge for edge in items if not edge.critical_blocker_flags]
    coverage_score = 0.0 if expected <= 0 else max(0.0, min(1.0, len(valid_edges) / expected))
    support_score = sum(edge.edge_weight for edge in valid_edges if edge.direction == MeaningDirection.SUPPORTIVE)
    risk_score = sum(edge.edge_weight for edge in valid_edges if edge.direction == MeaningDirection.RISK)
    context_score = sum(
        edge.edge_weight
        for edge in valid_edges
        if edge.direction in {MeaningDirection.NEUTRAL, MeaningDirection.UNKNOWN, MeaningDirection.MIXED}
    )
    blocker_score = float(len(critical_flags))
    if critical_flags:
        graph_state = L3RelationGraphState.BLOCKED_CRITICAL
    elif coverage_score < coverage_limit:
        graph_state = L3RelationGraphState.INSUFFICIENT_EVIDENCE
    elif support_score > risk_score * dominance and support_score > 0.0:
        graph_state = L3RelationGraphState.SUPPORT_DOMINANT_REVIEW
    elif risk_score > support_score * dominance and risk_score > 0.0:
        graph_state = L3RelationGraphState.RISK_DOMINANT_REVIEW
    elif context_score > 0.0 and support_score == 0.0 and risk_score == 0.0:
        graph_state = L3RelationGraphState.CONTEXT_ONLY
    else:
        graph_state = L3RelationGraphState.MIXED_REVIEW
    confidence_values = [edge.confidence_static_weight for edge in items]
    confidence_floor = min(confidence_values) if confidence_values else 0.0
    total_weight = sum(edge.edge_weight for edge in items)
    if total_weight > 0.0:
        confidence_weighted_mean = sum(edge.confidence_static_weight * edge.edge_weight for edge in items) / total_weight
    else:
        confidence_weighted_mean = 0.0
    return L3RelationGraph(
        relation_graph_id=relation_graph_id,
        symbol=symbol,
        decision_asof_ts=decision_asof_ts,
        evidence_edge_ids=tuple(edge.evidence_edge_id for edge in items),
        support_score=support_score,
        risk_score=risk_score,
        context_score=context_score,
        blocker_score=blocker_score,
        net_direction_score=support_score - risk_score,
        coverage_score=coverage_score,
        graph_state=graph_state,
        critical_blocker_flags=critical_flags,
        noncritical_gap_flags=noncritical_flags,
        confidence_floor=confidence_floor,
        confidence_weighted_mean=max(0.0, min(1.0, confidence_weighted_mean)),
    )
