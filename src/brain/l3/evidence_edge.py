from __future__ import annotations

from src.brain.contracts import MeaningDirection
from src.brain.l3.contracts import L3EconomicMeaningV2, L3EvidenceEdge, L3EvidenceEdgeState
from src.brain.l3.event_priors import event_prior_score
from src.brain.l3.source_gaps import classify_source_gaps
from src.brain.l3.source_reliability import source_reliability_score


def calculate_edge_weight(
    *,
    confidence_static_weight: float,
    source_reliability_score: float,
    event_prior_score: float,
    freshness_decay_score: float,
    evidence_completeness_score: float,
    contradiction_penalty: float,
) -> float:
    raw = (
        confidence_static_weight
        * source_reliability_score
        * event_prior_score
        * freshness_decay_score
        * evidence_completeness_score
        * (1.0 - contradiction_penalty)
    )
    return max(0.0, min(1.0, float(raw)))


def _edge_state(
    meaning: L3EconomicMeaningV2,
    critical_flags: tuple[str, ...],
    noncritical_flags: tuple[str, ...],
) -> L3EvidenceEdgeState:
    if critical_flags:
        return L3EvidenceEdgeState.CRITICAL_BLOCKED
    if "DISCOVERY_ONLY_SOURCE" in noncritical_flags:
        return L3EvidenceEdgeState.DISCOVERY_ONLY
    if "STALE_SOURCE" in noncritical_flags:
        return L3EvidenceEdgeState.STALE
    if meaning.direction == MeaningDirection.SUPPORTIVE:
        return L3EvidenceEdgeState.SUPPORTIVE
    if meaning.direction == MeaningDirection.RISK:
        return L3EvidenceEdgeState.RISK
    if meaning.direction == MeaningDirection.MIXED:
        return L3EvidenceEdgeState.MIXED
    return L3EvidenceEdgeState.CONTEXT


def build_evidence_edge(
    meaning: L3EconomicMeaningV2,
    *,
    evidence_edge_id: str | None = None,
    source_reliability: float | None = None,
    event_prior: float | None = None,
    freshness_decay_score: float = 1.0,
    evidence_completeness_score: float = 1.0,
    contradiction_penalty: float = 0.0,
) -> L3EvidenceEdge:
    critical, noncritical = classify_source_gaps(
        meaning.uncertainty_flags,
        runtime_context=meaning.runtime_context,
        source_time_certified=meaning.source_time_certified,
        freshness_status=meaning.freshness_status,
        authority_class=meaning.authority_class,
    )
    critical_flags = tuple(item.value for item in critical)
    noncritical_flags = tuple(item.value for item in noncritical)
    reliability = source_reliability
    if reliability is None:
        reliability = source_reliability_score(meaning.authority_class)
    prior = event_prior
    if prior is None:
        prior = event_prior_score(meaning.event_type)
    edge_weight = calculate_edge_weight(
        confidence_static_weight=meaning.confidence.static_weight,
        source_reliability_score=reliability,
        event_prior_score=prior,
        freshness_decay_score=freshness_decay_score,
        evidence_completeness_score=evidence_completeness_score,
        contradiction_penalty=contradiction_penalty,
    )
    reason_codes = tuple(
        dict.fromkeys(
            (
                *meaning.reason_codes,
                "STATIC_CONFIDENCE_NOT_PROBABILITY",
                "DIAGNOSTIC_REVIEW_ONLY",
                *(f"CRITICAL_{flag}" for flag in critical_flags),
                *(f"GAP_{flag}" for flag in noncritical_flags),
            )
        )
    )
    return L3EvidenceEdge(
        evidence_edge_id=evidence_edge_id or f"l3_edge:{meaning.meaning_id}",
        meaning_id=meaning.meaning_id,
        symbol=meaning.symbol,
        event_type=meaning.event_type,
        economic_dimension=meaning.economic_dimension,
        direction=meaning.direction,
        edge_state=_edge_state(meaning, critical_flags, noncritical_flags),
        source_reliability_score=reliability,
        event_prior_score=prior,
        freshness_decay_score=freshness_decay_score,
        evidence_completeness_score=evidence_completeness_score,
        contradiction_penalty=contradiction_penalty,
        confidence_static_weight=meaning.confidence.static_weight,
        calibrated_probability=meaning.confidence.calibrated_probability,
        edge_weight=edge_weight,
        critical_blocker_flags=critical_flags,
        noncritical_gap_flags=noncritical_flags,
        reason_codes=reason_codes,
    )
