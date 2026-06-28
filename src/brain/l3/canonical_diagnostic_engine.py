from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from typing import Any

from src.brain.contracts import MeaningDirection
from src.brain.l3.confidence import build_static_l3_confidence
from src.brain.l3.contracts import L3EconomicMeaningV2, L3EvidenceEdge, L3RelationGraph
from src.brain.l3.evidence_edge import build_evidence_edge
from src.brain.l3.graph_aggregator import aggregate_evidence_graph
from src.l2.runtime_context import HISTORICAL_RESEARCH


CANONICAL_REBUILD_PROVIDER = "canonical_source_event_rebuild"
CANONICAL_REBUILD_SOURCE_FAMILY = "canonical_source_event"
CANONICAL_REBUILD_AUTHORITY_CLASS = "uncertified_source"
CANONICAL_RESEARCH_ARTIFACT_RELIABILITY = 0.25
CANONICAL_RESEARCH_EVENT_PRIOR = 0.50
CSV_TUPLE_SEPARATOR = ";"


def adapt_canonical_source_event_to_l3_meaning(
    row: Mapping[str, Any],
) -> L3EconomicMeaningV2:
    source_event_id = _required_text(row, "source_event_id")
    lifecycle_id = _text(row.get("lifecycle_id"))
    event_type = (_text(row.get("canonical_event_type")) or _text(row.get("event_type")) or "SOURCE_EVENT").lower()
    event_ts = _text(row.get("event_timestamp")) or _text(row.get("created_at")) or "HISTORICAL_RESEARCH"
    symbol = _text(row.get("symbol")).upper() or "UNKNOWN"
    return L3EconomicMeaningV2(
        meaning_id=f"l3v2:canonical_source_event:{source_event_id}",
        asof_ts=event_ts,
        symbol=symbol,
        l2_primitive_ids=(),
        source_receipt_ids=(source_event_id,),
        source_family=CANONICAL_REBUILD_SOURCE_FAMILY,
        provider=CANONICAL_REBUILD_PROVIDER,
        authority_class=CANONICAL_REBUILD_AUTHORITY_CLASS,
        runtime_context=HISTORICAL_RESEARCH,
        source_time_certified=False,
        freshness_status="HISTORICAL",
        event_type=f"canonical_source_event_{event_type}",
        economic_dimension="EXECUTION",
        direction=MeaningDirection.NEUTRAL,
        confidence=build_static_l3_confidence("low", calibration_version="UNAVAILABLE"),
        uncertainty_flags=(
            "historical_source_event_bridge",
            "task742_packet_unrecoverable",
            "not_task742_golden_replay",
        ),
        reason_codes=(
            "CANONICAL_SOURCE_EVENT_REBUILD",
            "TASK742_HISTORICAL_PACKET_UNRECOVERABLE",
            "NOT_TASK742_GOLDEN_REPLAY",
            "EXECUTION_CONTEXT_NOT_ECONOMIC_THESIS_SIGNAL",
            "STATIC_CONFIDENCE_NOT_PROBABILITY",
            "DIAGNOSTIC_REVIEW_ONLY",
            f"LIFECYCLE_ID_{lifecycle_id}" if lifecycle_id else "LIFECYCLE_ID_MISSING",
        ),
    )


def build_canonical_evidence_edge(meaning: L3EconomicMeaningV2) -> L3EvidenceEdge:
    return build_evidence_edge(
        meaning,
        evidence_edge_id=f"l3_edge:canonical_source_event:{meaning.source_receipt_ids[0]}",
        source_reliability=CANONICAL_RESEARCH_ARTIFACT_RELIABILITY,
        event_prior=CANONICAL_RESEARCH_EVENT_PRIOR,
        freshness_decay_score=1.0,
        evidence_completeness_score=1.0,
        contradiction_penalty=0.0,
    )


def build_canonical_relation_graphs(
    rows: Iterable[Mapping[str, Any]],
    edges_by_source_receipt_id: Mapping[str, L3EvidenceEdge],
) -> tuple[L3RelationGraph, ...]:
    grouped: dict[str, list[tuple[Mapping[str, Any], L3EvidenceEdge]]] = defaultdict(list)
    for row in rows:
        source_event_id = _text(row.get("source_event_id"))
        lifecycle_id = _text(row.get("lifecycle_id"))
        edge = edges_by_source_receipt_id.get(source_event_id)
        if source_event_id and lifecycle_id and edge is not None:
            grouped[lifecycle_id].append((row, edge))

    graphs: list[L3RelationGraph] = []
    for lifecycle_id, items in sorted(grouped.items()):
        ordered = sorted(items, key=lambda item: _event_sort_key(item[0]))
        first_row = ordered[0][0]
        last_row = ordered[-1][0]
        symbol = _text(first_row.get("symbol")).upper() or "UNKNOWN"
        decision_asof_ts = _text(last_row.get("event_timestamp")) or _text(last_row.get("created_at")) or "HISTORICAL_RESEARCH"
        graphs.append(
            aggregate_evidence_graph(
                tuple(edge for _, edge in ordered),
                relation_graph_id=f"l3_graph:canonical_source_event:{lifecycle_id}",
                symbol=symbol,
                decision_asof_ts=decision_asof_ts,
                expected_edges=len(ordered),
            )
        )
    return tuple(graphs)


def build_canonical_l3_objects(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[tuple[L3EconomicMeaningV2, ...], tuple[L3EvidenceEdge, ...], tuple[L3RelationGraph, ...]]:
    deduped_rows: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        source_event_id = _text(row.get("source_event_id"))
        if source_event_id and source_event_id not in deduped_rows:
            deduped_rows[source_event_id] = row
    ordered_rows = tuple(deduped_rows[key] for key in sorted(deduped_rows))
    meanings = tuple(adapt_canonical_source_event_to_l3_meaning(row) for row in ordered_rows)
    edges = tuple(build_canonical_evidence_edge(meaning) for meaning in meanings)
    edges_by_receipt = {
        meaning.source_receipt_ids[0]: edge
        for meaning, edge in zip(meanings, edges, strict=True)
    }
    graphs = build_canonical_relation_graphs(ordered_rows, edges_by_receipt)
    return meanings, edges, graphs


def meaning_to_dict(meaning: L3EconomicMeaningV2) -> dict[str, object]:
    return {
        "meaning_id": meaning.meaning_id,
        "asof_ts": meaning.asof_ts,
        "symbol": meaning.symbol,
        "l2_primitive_ids": CSV_TUPLE_SEPARATOR.join(meaning.l2_primitive_ids),
        "source_receipt_ids": CSV_TUPLE_SEPARATOR.join(meaning.source_receipt_ids),
        "source_family": meaning.source_family,
        "provider": meaning.provider,
        "authority_class": meaning.authority_class,
        "runtime_context": meaning.runtime_context,
        "source_time_certified": int(meaning.source_time_certified),
        "freshness_status": meaning.freshness_status,
        "event_type": meaning.event_type,
        "economic_dimension": meaning.economic_dimension,
        "direction": meaning.direction.value,
        "confidence_raw_band": meaning.confidence.raw_band,
        "confidence_static_weight": meaning.confidence.static_weight,
        "confidence_calibrated_probability": meaning.confidence.calibrated_probability,
        "confidence_calibration_status": meaning.confidence.calibration_status.value,
        "confidence_calibration_version": meaning.confidence.calibration_version,
        "uncertainty_flags": CSV_TUPLE_SEPARATOR.join(meaning.uncertainty_flags),
        "reason_codes": CSV_TUPLE_SEPARATOR.join(meaning.reason_codes),
        "diagnostic_only": meaning.diagnostic_only,
        "trade_output_flag": meaning.trade_output_flag,
        "score_output_flag": meaning.score_output_flag,
        "order_intent_flag": meaning.order_intent_flag,
    }


def evidence_edge_to_dict(edge: L3EvidenceEdge) -> dict[str, object]:
    values = asdict(edge)
    values["direction"] = edge.direction.value
    values["edge_state"] = edge.edge_state.value
    values["critical_blocker_flags"] = CSV_TUPLE_SEPARATOR.join(edge.critical_blocker_flags)
    values["noncritical_gap_flags"] = CSV_TUPLE_SEPARATOR.join(edge.noncritical_gap_flags)
    values["reason_codes"] = CSV_TUPLE_SEPARATOR.join(edge.reason_codes)
    return values


def relation_graph_to_dict(graph: L3RelationGraph) -> dict[str, object]:
    values = asdict(graph)
    values["evidence_edge_ids"] = CSV_TUPLE_SEPARATOR.join(graph.evidence_edge_ids)
    values["graph_state"] = graph.graph_state.value
    values["critical_blocker_flags"] = CSV_TUPLE_SEPARATOR.join(graph.critical_blocker_flags)
    values["noncritical_gap_flags"] = CSV_TUPLE_SEPARATOR.join(graph.noncritical_gap_flags)
    return values


def _event_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (_text(row.get("event_timestamp")) or _text(row.get("created_at")), _text(row.get("source_event_id")))


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = _text(row.get(key))
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()
