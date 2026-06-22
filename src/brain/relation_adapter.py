"""Adapters from L3 economic meanings into relation edges and L4 thesis bundles.

The adapter is contract plumbing only. It groups already-built
`EconomicMeaning` objects into reviewable relation context and L4
`ThesisBundle` objects without ranking, sizing, replay, or order intent.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from brain.contracts import (
    EconomicMeaning,
    MeaningDirection,
    MeaningRelationEdge,
    RelationEdgeType,
    SourceGap,
    ThesisBundle,
    ThesisInvalidationState,
)


def _parse_iso_ts(value: str, field_name: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO timestamp") from exc


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return tuple(seen)


def _source_gaps_from_meanings(meanings: tuple[EconomicMeaning, ...]) -> tuple[SourceGap, ...]:
    flags = [flag.lower() for meaning in meanings for flag in meaning.uncertainty_flags]
    if any("missing" in flag or "incomplete" in flag for flag in flags):
        return (SourceGap.MISSING_RAW_SOURCE,)
    return (SourceGap.NONE,)


def _edge_type_from_meanings(meanings: tuple[EconomicMeaning, ...]) -> RelationEdgeType:
    readiness = {meaning.relation_readiness.strip().lower() for meaning in meanings}
    directions = {meaning.direction for meaning in meanings}
    if "not_ready" in readiness:
        return RelationEdgeType.BLOCKED_NOT_READY
    if directions == {MeaningDirection.SUPPORTIVE} and readiness == {"directional"}:
        return RelationEdgeType.SUPPORTS_THESIS
    if directions == {MeaningDirection.RISK} and readiness == {"directional"}:
        return RelationEdgeType.RISKS_THESIS
    if directions <= {MeaningDirection.NEUTRAL, MeaningDirection.UNKNOWN}:
        return RelationEdgeType.CONTEXT_ONLY
    return RelationEdgeType.MIXED_CONTEXT


def _blockers_for_edge(edge_type: RelationEdgeType, source_gaps: tuple[SourceGap, ...]) -> tuple[str, ...]:
    blockers: list[str] = []
    if edge_type == RelationEdgeType.BLOCKED_NOT_READY:
        blockers.append("RELATION_NOT_READY")
    if edge_type == RelationEdgeType.CONTEXT_ONLY:
        blockers.append("CONTEXT_ONLY_NOT_DIRECTIONAL")
    if edge_type == RelationEdgeType.MIXED_CONTEXT:
        blockers.append("MIXED_RELATION_CONTEXT")
    if SourceGap.NONE not in source_gaps:
        blockers.append("SOURCE_GAP_FLAGS_PRESENT")
    return tuple(blockers)


def build_meaning_relation_edge(
    meanings: Iterable[EconomicMeaning],
    relation_edge_id: str,
    decision_asof_ts: str | None = None,
) -> MeaningRelationEdge:
    """Build one review-only relation edge from same-symbol L3 meanings."""

    items = tuple(meanings)
    if not items:
        raise ValueError("at least one EconomicMeaning is required")
    if any(meaning.outcome_used_for_assignment for meaning in items):
        raise ValueError("outcome fields are forbidden in relation edges")
    symbols = {meaning.symbol for meaning in items}
    if len(symbols) != 1:
        raise ValueError("relation edge meanings must share one symbol")

    asof_pairs = [(_parse_iso_ts(meaning.asof_ts, "meaning.asof_ts"), meaning.asof_ts) for meaning in items]
    max_asof, max_asof_text = max(asof_pairs, key=lambda item: item[0])
    edge_asof = decision_asof_ts or max_asof_text
    edge_asof_dt = _parse_iso_ts(edge_asof, "decision_asof_ts")
    if max_asof > edge_asof_dt:
        raise ValueError("relation edge decision_asof_ts cannot precede any meaning asof_ts")

    source_gaps = _source_gaps_from_meanings(items)
    edge_type = _edge_type_from_meanings(items)
    return MeaningRelationEdge(
        relation_edge_id=relation_edge_id,
        symbol=items[0].symbol,
        decision_asof_ts=edge_asof,
        meaning_ids=tuple(meaning.meaning_id for meaning in items),
        edge_type=edge_type,
        confidence_floor=min(meaning.confidence for meaning in items),
        source_packet_ids=_dedupe(source_id for meaning in items for source_id in meaning.source_packet_ids),
        blocker_flags=_blockers_for_edge(edge_type, source_gaps),
        source_gaps=source_gaps,
    )


def build_thesis_bundle_from_relation_edge(
    edge: MeaningRelationEdge,
    trade_spec_id: str,
    thesis_id: str | None = None,
    catalyst_summary: str | None = None,
) -> ThesisBundle:
    """Build one L4 thesis bundle from a review-only relation edge."""

    if not trade_spec_id:
        raise ValueError("trade_spec_id is required")
    invalidation_state = ThesisInvalidationState.NONE
    if edge.edge_type == RelationEdgeType.RISKS_THESIS:
        invalidation_state = ThesisInvalidationState.WATCH
    elif edge.edge_type == RelationEdgeType.BLOCKED_NOT_READY:
        invalidation_state = ThesisInvalidationState.UNKNOWN

    thesis = ThesisBundle(
        thesis_id=thesis_id or f"thesis:{edge.relation_edge_id}",
        trade_spec_id=trade_spec_id,
        symbol=edge.symbol,
        decision_asof_ts=edge.decision_asof_ts,
        meaning_ids=edge.meaning_ids,
        catalyst_summary=catalyst_summary
        or f"{edge.edge_type.value} relation edge from {len(edge.meaning_ids)} L3 meaning objects",
        invalidation_state=invalidation_state,
        blocker_flags=edge.blocker_flags,
        source_gaps=edge.source_gaps,
    )
    assert_relation_edge_thesis_chain(edge, thesis)
    return thesis


def assert_relation_edge_thesis_chain(edge: MeaningRelationEdge, thesis: ThesisBundle) -> None:
    """Validate relation-edge to thesis-bundle contract invariants."""

    if edge.symbol != thesis.symbol:
        raise ValueError("relation edge and thesis symbols must match")
    if tuple(edge.meaning_ids) != tuple(thesis.meaning_ids):
        raise ValueError("thesis must preserve relation edge meaning ids")
    if _parse_iso_ts(edge.decision_asof_ts, "edge.decision_asof_ts") > _parse_iso_ts(
        thesis.decision_asof_ts, "thesis.decision_asof_ts"
    ):
        raise ValueError("relation edge asof cannot be after thesis decision_asof_ts")
    if thesis.outcome_used_for_assignment:
        raise ValueError("outcome fields are forbidden in thesis assignment")
