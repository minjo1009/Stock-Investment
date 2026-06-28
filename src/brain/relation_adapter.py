from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from src.brain.contracts import (
    EconomicMeaning,
    MeaningDirection,
    MeaningRelationEdge,
    MeaningRelationEdgeType,
    SourceGap,
)


"""Legacy review-only relation adapter.

This module preserves the conservative Task3351-3370 style relation behavior:
any legacy not_ready meaning blocks the whole legacy edge. New diagnostic L3 v2
graph scoring lives under src.brain.l3 and does not change this behavior.
"""


def _classify_relation_edge(meanings: tuple[EconomicMeaning, ...]) -> MeaningRelationEdgeType:
    readiness = {meaning.relation_readiness.strip().lower() for meaning in meanings}
    directions = {meaning.direction for meaning in meanings}
    if "not_ready" in readiness:
        return MeaningRelationEdgeType.BLOCKED_NOT_READY
    if directions == {MeaningDirection.SUPPORTIVE} and readiness == {"directional"}:
        return MeaningRelationEdgeType.SUPPORTS_THESIS
    if directions == {MeaningDirection.RISK} and readiness == {"directional"}:
        return MeaningRelationEdgeType.RISKS_THESIS
    if directions <= {MeaningDirection.NEUTRAL, MeaningDirection.UNKNOWN}:
        return MeaningRelationEdgeType.CONTEXT_ONLY
    return MeaningRelationEdgeType.MIXED_CONTEXT


def _source_gaps_from_meanings(meanings: tuple[EconomicMeaning, ...]) -> tuple[SourceGap, ...]:
    gaps: set[SourceGap] = set()
    for meaning in meanings:
        for flag in meaning.uncertainty_flags:
            normalized = flag.strip().lower()
            if "missing" in normalized:
                gaps.add(SourceGap.MISSING_RAW_SOURCE)
            elif "incomplete" in normalized:
                gaps.add(SourceGap.INCOMPLETE_SOURCE)
    return tuple(sorted(gaps, key=lambda item: item.value))


def build_legacy_relation_edge(
    meanings: Iterable[EconomicMeaning],
    *,
    relation_edge_id: str | None = None,
) -> MeaningRelationEdge:
    items = tuple(meanings)
    if not items:
        raise ValueError("at least one meaning is required")
    symbol = items[0].symbol
    lifecycle_id = items[0].lifecycle_id
    if any(item.symbol != symbol or item.lifecycle_id != lifecycle_id for item in items):
        raise ValueError("legacy relation edge requires one symbol and lifecycle_id")
    edge_id = relation_edge_id or f"legacy_relation:{symbol}:{lifecycle_id}"
    directions = tuple(sorted({item.direction for item in items}, key=lambda item: item.value))
    readiness = tuple(sorted({item.relation_readiness.strip().lower() for item in items}))
    return MeaningRelationEdge(
        relation_edge_id=edge_id,
        symbol=symbol,
        lifecycle_id=lifecycle_id,
        meaning_ids=tuple(item.meaning_id for item in items),
        edge_type=_classify_relation_edge(items),
        confidence_floor=min(float(item.confidence) for item in items),
        source_gaps=_source_gaps_from_meanings(items),
        direction_set=directions,
        readiness_set=readiness,
    )


def build_legacy_relation_edges(meanings: Iterable[EconomicMeaning]) -> list[MeaningRelationEdge]:
    grouped: dict[tuple[str, str], list[EconomicMeaning]] = defaultdict(list)
    for meaning in meanings:
        grouped[(meaning.lifecycle_id, meaning.symbol)].append(meaning)
    return [build_legacy_relation_edge(items) for items in grouped.values()]
