from __future__ import annotations

from typing import Any, Mapping

from src.brain.contracts import MeaningDirection
from src.brain.l3.confidence import build_static_l3_confidence
from src.brain.l3.contracts import L3EconomicMeaningV2
from src.brain.l3.task742_rules import Task742RuleInterpretation, interpret_task742_economic_context
from src.l2.runtime_context import HISTORICAL_RESEARCH


_DIRECTION_MAP = {
    "positive": MeaningDirection.SUPPORTIVE,
    "negative": MeaningDirection.RISK,
    "mixed": MeaningDirection.MIXED,
    "neutral": MeaningDirection.NEUTRAL,
    "unknown": MeaningDirection.UNKNOWN,
}

_DIMENSION_BY_CIRCUIT = {
    "form4_insider_behavior": "SENTIMENT",
    "ownership_float_structure": "VALUATION",
    "activist_control": "EXECUTION",
    "credit_financing": "FINANCING",
    "financial_results_guidance": "REVENUE",
    "generic_8k_classifier": "EXECUTION",
}


def adapt_task742_rule_inputs_to_l3_meaning(
    row: Mapping[str, Any],
    *,
    primitive: Mapping[str, Any] | None = None,
    denominators: Mapping[str, Any] | None = None,
    comparators: Mapping[str, Any] | None = None,
    availability: Mapping[str, Any] | None = None,
    timing: Mapping[str, Any] | None = None,
) -> L3EconomicMeaningV2:
    interpretation = interpret_task742_economic_context(row, primitive, denominators, comparators, availability, timing)
    return adapt_task742_interpretation_to_l3_meaning(row, interpretation)


def adapt_task742_interpretation_to_l3_meaning(
    row: Mapping[str, Any],
    interpretation: Task742RuleInterpretation,
) -> L3EconomicMeaningV2:
    source_event_id = _text(row.get("source_event_id")) or _text(row.get("packet_id")) or "unknown_source_event"
    lifecycle_id = _text(row.get("lifecycle_id"))
    circuit = _text(row.get("source_circuit"))
    flags = tuple(
        dict.fromkeys(
            (
                *interpretation.ambiguity_flags,
                *interpretation.soft_uncertainty_flags,
                *interpretation.hard_blocker_flags,
                *interpretation.needed_confirmation,
            )
        )
    )
    return L3EconomicMeaningV2(
        meaning_id=f"l3v2:task742:{source_event_id}",
        asof_ts=_text(row.get("tradable_after_dt")) or _text(row.get("event_date")) or "HISTORICAL_RESEARCH",
        symbol=_text(row.get("symbol")).upper() or "UNKNOWN",
        l2_primitive_ids=(),
        source_receipt_ids=(source_event_id,),
        source_family="task742_historical_rule",
        provider="task742_github_recovered",
        authority_class="uncertified_source",
        runtime_context=HISTORICAL_RESEARCH,
        source_time_certified=False,
        freshness_status="UNKNOWN",
        event_type=interpretation.interpretation_state,
        economic_dimension=_DIMENSION_BY_CIRCUIT.get(circuit, "UNKNOWN"),
        direction=_DIRECTION_MAP.get(interpretation.economic_direction_hint, MeaningDirection.UNKNOWN),
        confidence=build_static_l3_confidence(interpretation.confidence_band),
        uncertainty_flags=flags,
        reason_codes=(
            "TASK742_RULE_MIGRATED_FROM_GITHUB_SOURCE",
            interpretation.rule_id,
            f"RELATION_TIER_{interpretation.relation_ready_tier.upper()}",
            "HISTORICAL_RESEARCH_ONLY",
            "STATIC_CONFIDENCE_NOT_PROBABILITY",
            "DIAGNOSTIC_REVIEW_ONLY",
            f"LIFECYCLE_ID_{lifecycle_id}" if lifecycle_id else "LIFECYCLE_ID_MISSING",
        ),
    )


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()
