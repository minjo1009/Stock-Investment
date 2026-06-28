from __future__ import annotations

from src.brain.contracts import MeaningDirection
from src.brain.l3.confidence import build_static_l3_confidence
from src.brain.l3.contracts import L3EconomicMeaningV2
from src.brain.l3.source_reliability import classify_source_authority
from src.l2.contracts import L2PrimitiveFact


def adapt_l2_primitive_to_l3_meaning(
    primitive: L2PrimitiveFact,
    *,
    direction: MeaningDirection = MeaningDirection.UNKNOWN,
    confidence_band: str = "unknown",
    economic_dimension: str | None = None,
    reason_codes: tuple[str, ...] = (),
) -> L3EconomicMeaningV2:
    authority_class = classify_source_authority(primitive.source_family, primitive.provider)
    dimension = economic_dimension or primitive.primitive_type.upper()
    return L3EconomicMeaningV2(
        meaning_id=f"l3v2:{primitive.primitive_id}",
        asof_ts=primitive.asof_ts,
        symbol=str(primitive.symbol or primitive.entity_id or "UNKNOWN").upper(),
        l2_primitive_ids=(primitive.primitive_id,),
        source_receipt_ids=(primitive.source_receipt_id,),
        source_family=primitive.source_family,
        provider=primitive.provider,
        authority_class=authority_class,
        runtime_context=primitive.runtime_context,
        source_time_certified=primitive.source_time_certified,
        freshness_status=primitive.freshness_status,
        event_type=primitive.primitive_subtype,
        economic_dimension=dimension,
        direction=direction,
        confidence=build_static_l3_confidence(confidence_band),
        uncertainty_flags=(),
        reason_codes=tuple(
            dict.fromkeys(
                (
                    *reason_codes,
                    "L2_PRIMITIVE_CANONICAL_INPUT",
                    "DIAGNOSTIC_REVIEW_ONLY",
                    "STATIC_CONFIDENCE_NOT_PROBABILITY",
                )
            )
        ),
    )
