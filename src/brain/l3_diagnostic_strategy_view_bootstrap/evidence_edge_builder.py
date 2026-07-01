from __future__ import annotations

from .contracts import DirectionReview, L3EvidenceEdge, L3Meaning, closed_authority_flags


def build_evidence_edge(meaning: L3Meaning) -> L3EvidenceEdge:
    graph_key = "|".join(
        [
            meaning.target_node_type,
            meaning.target_node_key,
            meaning.economic_dimension,
            "swing_1m",
        ]
    )
    critical_flag = int(bool(meaning.critical_blockers))
    noncritical_flag = int(bool(meaning.noncritical_gaps))
    return L3EvidenceEdge(
        evidence_edge_id=f"l3edge:{meaning.l3_meaning_id}",
        l3_meaning_id=meaning.l3_meaning_id,
        graph_key=graph_key,
        target_node_type=meaning.target_node_type,
        target_node_key=meaning.target_node_key,
        economic_dimension=meaning.economic_dimension,
        direction_review=meaning.direction_review,
        review_strength_band=_review_strength(meaning.direction_review, critical_flag),
        source_reliability_component=_source_reliability(meaning.source_family),
        freshness_component=0.0 if "STALE_SOURCE" in meaning.noncritical_gaps else 1.0,
        evidence_completeness_component=0.0 if critical_flag else 1.0,
        contradiction_flag=0,
        critical_blocker_flag=critical_flag,
        noncritical_gap_flag=noncritical_flag,
        reason_codes=meaning.reason_codes,
        authority_flags=closed_authority_flags(),
    )


def _source_reliability(source_family: str) -> float:
    if source_family in {"public_newswire_feeds", "public_context_news_feeds"}:
        return 0.75
    if source_family == "public_market_macro_news_feeds":
        return 0.65
    return 0.50


def _review_strength(direction: DirectionReview, critical_flag: int) -> str:
    if critical_flag:
        return "blocked"
    if direction in {DirectionReview.SUPPORT_REVIEW, DirectionReview.RISK_REVIEW}:
        return "medium"
    return "low"

