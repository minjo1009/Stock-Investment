from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ParticipationQualityLabel = Literal[
    "HEALTHY_EXPANSION",
    "NEUTRAL_PARTICIPATION",
    "FRAGILE_CROWDING",
    "UNKNOWN",
]


@dataclass(frozen=True)
class ParticipationQualityInputs:
    breadth_change: float | None = None
    breadth_participation_ratio: float | None = None
    liquidity_change: float | None = None
    dip_absorption_score: float | None = None
    reversal_stability_score: float | None = None
    factor_concentration_score: float | None = None
    same_day_signal_crowding: float | None = None
    volatility_expansion_score: float | None = None
    continuation_persistence_score: float | None = None
    session_timing_score: float | None = None


@dataclass(frozen=True)
class ParticipationQualityConfig:
    unknown_confidence_threshold: float = 0.35
    neutral_band: float = 0.08
    volatility_support_weight: float = 0.35
    healthy_label_threshold: float = 0.45
    fragile_label_threshold: float = 0.45


@dataclass(frozen=True)
class ParticipationQualityDecision:
    quality_label: ParticipationQualityLabel
    expansion_score: float
    fragility_score: float
    confidence: float
    reasons: tuple[str, ...]


def _clamp01(value: float | None) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if numeric < 0.0:
        return 0.0
    if numeric > 1.0:
        return 1.0
    return numeric


def _signed_to_unit(value: float | None) -> float | None:
    if value is None:
        return None
    numeric = max(min(float(value), 1.0), -1.0)
    return (numeric + 1.0) / 2.0


def _average(values: tuple[float, ...]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def evaluate_participation_quality(
    inputs: ParticipationQualityInputs,
    config: ParticipationQualityConfig = ParticipationQualityConfig(),
) -> ParticipationQualityDecision:
    present_fields = 0
    total_fields = len(inputs.__dataclass_fields__)
    reasons: list[str] = []

    breadth_change_unit = _signed_to_unit(inputs.breadth_change)
    breadth_ratio = _clamp01(inputs.breadth_participation_ratio)
    liquidity_unit = _signed_to_unit(inputs.liquidity_change)
    dip_absorption = _clamp01(inputs.dip_absorption_score)
    reversal_stability = _clamp01(inputs.reversal_stability_score)
    factor_concentration = _clamp01(inputs.factor_concentration_score)
    same_day_crowding = _clamp01(inputs.same_day_signal_crowding)
    volatility_expansion = _clamp01(inputs.volatility_expansion_score)
    continuation_persistence = _clamp01(inputs.continuation_persistence_score)
    session_timing = _clamp01(inputs.session_timing_score)

    normalized_values = (
        breadth_change_unit,
        breadth_ratio,
        liquidity_unit,
        dip_absorption,
        reversal_stability,
        factor_concentration,
        same_day_crowding,
        volatility_expansion,
        continuation_persistence,
        session_timing,
    )
    present_fields = sum(value is not None for value in normalized_values)
    confidence = present_fields / float(total_fields)

    if breadth_change_unit is None:
        reasons.append("missing_breadth_change")
    if breadth_ratio is None:
        reasons.append("missing_breadth_participation_ratio")
    if liquidity_unit is None:
        reasons.append("missing_liquidity_change")
    if dip_absorption is None:
        reasons.append("missing_dip_absorption_score")
    if reversal_stability is None:
        reasons.append("missing_reversal_stability_score")
    if factor_concentration is None:
        reasons.append("missing_factor_concentration_score")
    if same_day_crowding is None:
        reasons.append("missing_same_day_signal_crowding")
    if volatility_expansion is None:
        reasons.append("missing_volatility_expansion_score")
    if continuation_persistence is None:
        reasons.append("missing_continuation_persistence_score")
    if session_timing is None:
        reasons.append("missing_session_timing_score")

    expansion_components = tuple(
        value
        for value in (
            breadth_change_unit,
            breadth_ratio,
            liquidity_unit,
            dip_absorption,
            reversal_stability,
            continuation_persistence,
            None if factor_concentration is None else 1.0 - factor_concentration,
            session_timing,
        )
        if value is not None
    )
    fragility_components = tuple(
        value
        for value in (
            None if breadth_change_unit is None else 1.0 - breadth_change_unit,
            None if breadth_ratio is None else 1.0 - breadth_ratio,
            None if liquidity_unit is None else 1.0 - liquidity_unit,
            None if dip_absorption is None else 1.0 - dip_absorption,
            None if reversal_stability is None else 1.0 - reversal_stability,
            factor_concentration,
            same_day_crowding,
            None
            if volatility_expansion is None
            else volatility_expansion
            * (
                1.0
                if breadth_ratio is None
                else 1.0 - (config.volatility_support_weight * breadth_ratio)
            ),
            None if session_timing is None else 1.0 - session_timing,
        )
        if value is not None
    )

    expansion_score = _average(expansion_components)
    fragility_score = _average(fragility_components)

    if breadth_ratio is not None and breadth_ratio >= 0.60:
        reasons.append("broad_participation_support")
    if dip_absorption is not None and dip_absorption >= 0.60:
        reasons.append("strong_dip_absorption")
    if continuation_persistence is not None and continuation_persistence >= 0.60:
        reasons.append("continuation_persistence_support")
    if factor_concentration is not None and factor_concentration >= 0.65:
        reasons.append("high_factor_concentration")
    if same_day_crowding is not None and same_day_crowding >= 0.65:
        reasons.append("same_day_signal_crowding")
    if volatility_expansion is not None and volatility_expansion >= 0.70 and (breadth_ratio or 0.0) < 0.50:
        reasons.append("unsupported_volatility_expansion")
    if session_timing is not None and session_timing <= 0.35:
        reasons.append("late_or_uncertain_participation")

    if confidence < config.unknown_confidence_threshold:
        label: ParticipationQualityLabel = "UNKNOWN"
        reasons.append("insufficient_pretrade_inputs")
    else:
        delta = expansion_score - fragility_score
        if (
            delta >= config.neutral_band
            and expansion_score >= config.healthy_label_threshold
        ):
            label = "HEALTHY_EXPANSION"
        elif (
            -delta >= config.neutral_band
            and fragility_score >= config.fragile_label_threshold
        ):
            label = "FRAGILE_CROWDING"
        else:
            label = "NEUTRAL_PARTICIPATION"
        reasons.append(f"expansion_minus_fragility={delta:.3f}")

    return ParticipationQualityDecision(
        quality_label=label,
        expansion_score=round(expansion_score, 6),
        fragility_score=round(fragility_score, 6),
        confidence=round(confidence, 6),
        reasons=tuple(reasons),
    )
