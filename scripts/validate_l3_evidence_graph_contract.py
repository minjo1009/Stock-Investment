from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.contracts import MeaningDirection
from src.brain.l3.confidence import build_static_l3_confidence
from src.brain.l3.contracts import L3EconomicMeaningV2, L3RelationGraphState
from src.brain.l3.evidence_edge import build_evidence_edge
from src.brain.l3.graph_aggregator import aggregate_evidence_graph
from src.l2.runtime_context import HISTORICAL_RESEARCH


def _meaning(meaning_id: str, direction: MeaningDirection, flags: tuple[str, ...] = ()) -> L3EconomicMeaningV2:
    return L3EconomicMeaningV2(
        meaning_id=meaning_id,
        asof_ts="2026-06-01T10:00:00Z",
        symbol="AAPL",
        l2_primitive_ids=(f"l2-{meaning_id}",),
        source_receipt_ids=(f"receipt-{meaning_id}",),
        source_family="sec_event",
        provider="sec",
        authority_class="official_primary",
        runtime_context=HISTORICAL_RESEARCH,
        source_time_certified=True,
        freshness_status="FRESH",
        event_type="guidance_raise_with_margin_language",
        economic_dimension="REVENUE",
        direction=direction,
        confidence=build_static_l3_confidence("medium"),
        uncertainty_flags=flags,
        reason_codes=("VALIDATOR",),
    )


def validate() -> list[str]:
    errors: list[str] = []
    support = build_evidence_edge(_meaning("support", MeaningDirection.SUPPORTIVE))
    gap = build_evidence_edge(_meaning("gap", MeaningDirection.UNKNOWN, ("not_ready_confirmation",)))
    graph = aggregate_evidence_graph(
        (support, gap),
        relation_graph_id="validator-graph-1",
        symbol="AAPL",
        decision_asof_ts="2026-06-01T10:00:00Z",
        expected_edges=2,
    )
    if graph.graph_state == L3RelationGraphState.BLOCKED_CRITICAL:
        errors.append("noncritical not_ready gap blocked the graph")
    critical = build_evidence_edge(_meaning("critical", MeaningDirection.SUPPORTIVE, ("missing_raw_source",)))
    blocked = aggregate_evidence_graph(
        (critical,),
        relation_graph_id="validator-graph-2",
        symbol="AAPL",
        decision_asof_ts="2026-06-01T10:00:00Z",
        expected_edges=1,
    )
    if blocked.graph_state != L3RelationGraphState.BLOCKED_CRITICAL:
        errors.append("critical missing raw source did not block the graph")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L3_GRAPH_ERROR] {error}")
        sys.exit(1)
    print("[L3_GRAPH_OK]")


if __name__ == "__main__":
    main()
