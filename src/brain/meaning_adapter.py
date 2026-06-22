"""Adapters from research meaning packets into brain runtime contracts.

The adapter is intentionally narrow: it translates already-built Task742
review-only packets into L3 `EconomicMeaning` objects. It does not build
packets, run replay, rank trades, size positions, or create orders.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from brain.contracts import EconomicMeaning, MeaningDirection


_DIRECTION_MAP = {
    "positive": MeaningDirection.SUPPORTIVE,
    "supportive": MeaningDirection.SUPPORTIVE,
    "negative": MeaningDirection.RISK,
    "risk": MeaningDirection.RISK,
    "mixed": MeaningDirection.MIXED,
    "neutral": MeaningDirection.NEUTRAL,
    "unknown": MeaningDirection.UNKNOWN,
    "": MeaningDirection.UNKNOWN,
}

_CONFIDENCE_MAP = {
    "high": 0.85,
    "medium": 0.6,
    "low": 0.35,
    "insufficient": 0.0,
    "unknown": 0.0,
    "": 0.0,
}

_FORBIDDEN_TRUE_FLAGS = (
    "direction_hint_trade_instruction_flag",
    "trade_output_flag",
    "score_output_flag",
    "backtest_eligible_flag",
    "outcome_used_for_assignment_flag",
)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _int_flag(value: Any) -> int:
    text = _text(value)
    if text == "":
        return 0
    try:
        return int(float(text))
    except ValueError as exc:
        raise ValueError(f"flag value must be numeric: {text}") from exc


def _split_pipe(value: Any) -> tuple[str, ...]:
    return tuple(part.strip() for part in _text(value).split("|") if part.strip())


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return tuple(seen)


def _require_task742_review_only(row: Mapping[str, Any]) -> None:
    failed = [field for field in _FORBIDDEN_TRUE_FLAGS if _int_flag(row.get(field)) != 0]
    if failed:
        raise ValueError("Task742 row is not review-only: " + "|".join(failed))
    if _int_flag(row.get("asof_change_inference_forbidden_flag")) != 1:
        raise ValueError("Task742 row must forbid as-of change inference")


def task742_row_to_economic_meaning(row: Mapping[str, Any]) -> EconomicMeaning:
    """Translate one Task742 pragmatic meaning row into an L3 contract object."""

    _require_task742_review_only(row)
    source_event_id = _text(row.get("source_event_id"))
    lifecycle_id = _text(row.get("lifecycle_id"))
    symbol = _text(row.get("symbol"))
    asof_ts = _text(row.get("tradable_after_dt"))
    if not asof_ts:
        raise ValueError("Task742 row requires tradable_after_dt for L3 asof_ts")

    direction = _DIRECTION_MAP.get(_text(row.get("economic_direction_hint")).lower(), MeaningDirection.UNKNOWN)
    confidence = _CONFIDENCE_MAP.get(_text(row.get("confidence_band")).lower(), 0.0)
    flags = _dedupe(
        (
            *_split_pipe(row.get("ambiguity_flags")),
            *_split_pipe(row.get("soft_uncertainty_flags")),
            *_split_pipe(row.get("hard_blocker_flags")),
            *_split_pipe(row.get("needed_confirmation")),
        )
    )
    relation_readiness = _text(row.get("relation_ready_tier")) or "not_ready"

    return EconomicMeaning(
        meaning_id=f"task742:{lifecycle_id}:{source_event_id}",
        asof_ts=asof_ts,
        symbol=symbol,
        direction=direction,
        confidence=confidence,
        uncertainty_flags=flags,
        source_packet_ids=(source_event_id,),
        relation_readiness=relation_readiness,
        outcome_used_for_assignment=bool(_int_flag(row.get("outcome_used_for_assignment_flag"))),
    )


def task742_rows_to_economic_meanings(rows: Iterable[Mapping[str, Any]]) -> tuple[EconomicMeaning, ...]:
    """Translate Task742 pragmatic meaning rows into immutable L3 objects."""

    return tuple(task742_row_to_economic_meaning(row) for row in rows)
