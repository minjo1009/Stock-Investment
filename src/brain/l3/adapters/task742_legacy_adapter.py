from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.brain.contracts import EconomicMeaning
from src.brain.meaning_adapter import adapt_task742_row_to_economic_meaning
from src.brain.l3.confidence import build_static_l3_confidence
from src.brain.l3.contracts import L3EconomicMeaningV2
from src.l2.runtime_context import HISTORICAL_RESEARCH


def adapt_economic_meaning_to_l3_v2(meaning: EconomicMeaning) -> L3EconomicMeaningV2:
    return L3EconomicMeaningV2(
        meaning_id=f"l3v2:{meaning.meaning_id}",
        asof_ts=meaning.asof_ts,
        symbol=meaning.symbol,
        l2_primitive_ids=(),
        source_receipt_ids=meaning.source_packet_ids,
        source_family="historical_artifact",
        provider="task742_legacy",
        authority_class="news_discovery_proxy",
        runtime_context=HISTORICAL_RESEARCH,
        source_time_certified=False,
        freshness_status="UNKNOWN",
        event_type=meaning.event_type,
        economic_dimension=meaning.economic_dimension,
        direction=meaning.direction,
        confidence=build_static_l3_confidence(meaning.confidence_band),
        uncertainty_flags=meaning.uncertainty_flags,
        reason_codes=tuple(
            dict.fromkeys(
                (
                    *meaning.reason_codes,
                    "LEGACY_TASK742_REVIEW_ONLY",
                    "STATIC_CONFIDENCE_NOT_PROBABILITY",
                )
            )
        ),
    )


def adapt_task742_row_to_l3_v2(row: Mapping[str, Any]) -> L3EconomicMeaningV2:
    return adapt_economic_meaning_to_l3_v2(adapt_task742_row_to_economic_meaning(row))
