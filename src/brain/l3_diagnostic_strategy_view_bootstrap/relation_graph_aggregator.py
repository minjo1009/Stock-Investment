from __future__ import annotations

from collections import defaultdict
from typing import Any

from .contracts import DirectionReview, GraphState, L3EvidenceEdge


def aggregate_relation_graph(edges: list[L3EvidenceEdge], coverage_gaps: list[dict[str, object]]) -> dict[str, Any]:
    grouped: dict[str, list[L3EvidenceEdge]] = defaultdict(list)
    for edge in edges:
        grouped[edge.graph_key].append(edge)

    graphs: list[dict[str, Any]] = []
    for graph_key, items in sorted(grouped.items()):
        support = sum(1 for edge in items if edge.direction_review == DirectionReview.SUPPORT_REVIEW)
        risk = sum(1 for edge in items if edge.direction_review == DirectionReview.RISK_REVIEW)
        context = sum(1 for edge in items if edge.direction_review == DirectionReview.CONTEXT_ONLY)
        blockers = sum(edge.critical_blocker_flag for edge in items)
        gaps = sum(edge.noncritical_gap_flag for edge in items)
        state = _graph_state(support, risk, context, blockers)
        graphs.append(
            {
                "graph_key": graph_key,
                "evidence_edge_count": len(items),
                "support_edge_count": support,
                "risk_edge_count": risk,
                "context_edge_count": context,
                "critical_blocker_count": blockers,
                "noncritical_gap_count": gaps,
                "contradiction_count": 1 if support and risk else 0,
                "graph_state": state.value,
                "diagnostic_only": 1,
                "trading_eligible": 0,
                "signal_export_allowed": 0,
                "order_intent_allowed": 0,
                "broker_mutation_allowed": 0,
                "paper_promotion_allowed": 0,
                "live_order_allowed": 0,
            }
        )

    return {
        "task_id": "TASK-4150",
        "graph_count": len(graphs),
        "coverage_gap_count": len(coverage_gaps),
        "graphs": graphs,
        "coverage_gaps": coverage_gaps,
        "authority": {
            "strategy": "NOT_ACCEPTED",
            "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "broker_mutation_allowed": False,
            "live_order_allowed": False,
            "paper_promotion_allowed": False,
            "signal_export_allowed": False,
            "trading_eligible": False,
        },
    }


def _graph_state(support: int, risk: int, context: int, blockers: int) -> GraphState:
    if blockers:
        return GraphState.BLOCKED_CRITICAL
    if support and risk:
        return GraphState.MIXED_REVIEW
    if support:
        return GraphState.SUPPORT_DOMINANT_REVIEW
    if risk:
        return GraphState.RISK_DOMINANT_REVIEW
    if context:
        return GraphState.CONTEXT_ONLY
    return GraphState.INSUFFICIENT_EVIDENCE

