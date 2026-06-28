from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from src.brain.contracts import EconomicMeaning, MeaningDirection


"""Legacy Task742 review-only adapter.

This module preserves the Task742 row -> EconomicMeaning path for compatibility.
The numeric confidence value is a static review weight, not an empirical
probability and not a calibrated forecast.
"""


_CONFIDENCE_MAP = {
    "high": 0.85,
    "medium": 0.60,
    "low": 0.35,
    "insufficient": 0.0,
    "unknown": 0.0,
    "": 0.0,
}

_DIRECTION_MAP = {
    "positive": MeaningDirection.SUPPORTIVE,
    "supportive": MeaningDirection.SUPPORTIVE,
    "support": MeaningDirection.SUPPORTIVE,
    "negative": MeaningDirection.RISK,
    "risk": MeaningDirection.RISK,
    "risky": MeaningDirection.RISK,
    "mixed": MeaningDirection.MIXED,
    "neutral": MeaningDirection.NEUTRAL,
    "unknown": MeaningDirection.UNKNOWN,
    "": MeaningDirection.UNKNOWN,
}


def map_confidence_band_to_static_weight(band: str) -> float:
    return _CONFIDENCE_MAP.get(str(band or "").strip().lower(), 0.0)


def map_direction_hint(value: object) -> MeaningDirection:
    return _DIRECTION_MAP.get(str(value or "").strip().lower(), MeaningDirection.UNKNOWN)


def _row_value(row: Mapping[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if name in row and row[name] is not None:
            return row[name]
    return default


def _tuple_field(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (tuple, list)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    if not text:
        return ()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return tuple(str(item).strip() for item in parsed if str(item).strip())
    return tuple(part.strip() for part in text.replace(";", ",").split(",") if part.strip())


def adapt_task742_row_to_economic_meaning(row: Mapping[str, Any]) -> EconomicMeaning:
    confidence_band = str(_row_value(row, "confidence_band", "confidence", default="unknown")).strip().lower()
    source_packet_ids = _tuple_field(
        _row_value(row, "source_packet_ids", "source_packet_id", "packet_id", "task742_packet_id", default="")
    )
    meaning_id = str(
        _row_value(row, "meaning_id", "task742_packet_id", "packet_id", default="")
        or f"meaning:{_row_value(row, 'symbol', default='UNKNOWN')}:{_row_value(row, 'lifecycle_id', default='unknown')}"
    )
    lifecycle_id = str(_row_value(row, "lifecycle_id", "relation_target", default="legacy_task742")).strip()
    return EconomicMeaning(
        meaning_id=meaning_id,
        asof_ts=str(_row_value(row, "asof_ts", "decision_asof_ts", "created_at", default="HISTORICAL_RESEARCH")),
        symbol=str(_row_value(row, "symbol", default="UNKNOWN")).strip().upper(),
        lifecycle_id=lifecycle_id or "legacy_task742",
        source_packet_ids=source_packet_ids,
        direction=map_direction_hint(_row_value(row, "economic_direction_hint", "direction", default="unknown")),
        confidence=map_confidence_band_to_static_weight(confidence_band),
        confidence_band=confidence_band or "unknown",
        relation_readiness=str(_row_value(row, "relation_readiness", "readiness", default="not_ready")).strip().lower(),
        uncertainty_flags=_tuple_field(_row_value(row, "uncertainty_flags", "ambiguity_flags", default="")),
        reason_codes=_tuple_field(_row_value(row, "reason_codes", default="LEGACY_TASK742_REVIEW_ONLY")),
        event_type=str(_row_value(row, "event_type", "source_circuit", default="unknown")).strip() or "unknown",
        economic_dimension=str(_row_value(row, "economic_dimension", default="UNKNOWN")).strip().upper() or "UNKNOWN",
    )


def adapt_task742_rows_to_economic_meanings(rows: Iterable[Mapping[str, Any]]) -> list[EconomicMeaning]:
    return [adapt_task742_row_to_economic_meaning(row) for row in rows]
