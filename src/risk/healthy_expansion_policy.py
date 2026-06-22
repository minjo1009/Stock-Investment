from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


HealthyExpansionPolicyLabel = Literal[
    "NO_CHANGE",
    "RELAX_SIZE_ONLY",
    "RELAX_ADD_ONLY",
    "RELAX_SIZE_AND_ADD",
    "KEEP_SUPPRESSED",
]


@dataclass(frozen=True)
class HealthyExpansionPolicyInputs:
    quality_label: str
    expansion_score: float
    fragility_score: float
    confidence: float
    state_label: str
    continuation_risk_score: float
    staged_gate_stage: str
    staged_add_allowed: bool
    factor_budget_allowed: bool
    factor_budget_multiplier: float
    gross_exposure_multiplier: float
    current_size_multiplier: float | None = None


@dataclass(frozen=True)
class HealthyExpansionPolicyConfig:
    healthy_expansion_min_score: float = 0.65
    max_fragility_for_relax: float = 0.45
    min_confidence_for_relax: float = 0.50
    max_risk_score_for_add_relax: float = 0.55
    healthy_size_floor: float = 0.65
    healthy_add_size_floor: float = 0.50
    neutral_size_floor: float = 0.35


@dataclass(frozen=True)
class HealthyExpansionPolicyDecision:
    policy_label: HealthyExpansionPolicyLabel
    final_size_multiplier: float
    final_add_allowed: bool
    reasons: tuple[str, ...]


def evaluate_healthy_expansion_policy(
    inputs: HealthyExpansionPolicyInputs,
    config: HealthyExpansionPolicyConfig = HealthyExpansionPolicyConfig(),
) -> HealthyExpansionPolicyDecision:
    current_size = max(float(inputs.current_size_multiplier or 0.0), 0.0)
    reasons: list[str] = []

    if inputs.state_label == "DISLOCATION":
        reasons.append("dislocation_never_relaxes")
        return HealthyExpansionPolicyDecision("KEEP_SUPPRESSED", current_size, False, tuple(reasons))
    if not inputs.factor_budget_allowed or float(inputs.factor_budget_multiplier) <= 0.0:
        reasons.append("factor_budget_prevents_relaxation")
        return HealthyExpansionPolicyDecision("KEEP_SUPPRESSED", current_size, False, tuple(reasons))
    if inputs.quality_label == "FRAGILE_CROWDING":
        reasons.append("fragile_crowding_never_relaxes")
        return HealthyExpansionPolicyDecision("KEEP_SUPPRESSED", current_size, False, tuple(reasons))
    if inputs.quality_label == "UNKNOWN":
        reasons.append("unknown_quality_conservative_default")
        return HealthyExpansionPolicyDecision("KEEP_SUPPRESSED", current_size, False, tuple(reasons))

    if inputs.quality_label == "NEUTRAL_PARTICIPATION":
        final_size = max(current_size, min(config.neutral_size_floor, float(inputs.gross_exposure_multiplier)))
        if final_size > current_size:
            reasons.append("neutral_participation_mild_size_floor")
            return HealthyExpansionPolicyDecision("RELAX_SIZE_ONLY", final_size, False, tuple(reasons))
        reasons.append("neutral_participation_no_add_relaxation")
        return HealthyExpansionPolicyDecision("NO_CHANGE", current_size, False, tuple(reasons))

    healthy_conditions = (
        inputs.quality_label == "HEALTHY_EXPANSION"
        and float(inputs.expansion_score) >= config.healthy_expansion_min_score
        and float(inputs.fragility_score) <= config.max_fragility_for_relax
        and float(inputs.confidence) >= config.min_confidence_for_relax
    )
    if not healthy_conditions:
        reasons.append("healthy_threshold_not_met")
        return HealthyExpansionPolicyDecision("KEEP_SUPPRESSED", current_size, False, tuple(reasons))

    allow_add = (
        inputs.state_label in {"NORMAL", "ELEVATED"}
        and float(inputs.continuation_risk_score) <= config.max_risk_score_for_add_relax
    )
    stage_name = str(inputs.staged_gate_stage)
    size_floor = config.healthy_add_size_floor if allow_add else config.healthy_size_floor
    final_size = max(current_size, min(size_floor, float(inputs.gross_exposure_multiplier), float(inputs.factor_budget_multiplier)))

    if allow_add and not inputs.staged_add_allowed and stage_name in {"stage_1_probe", "delayed_probe", "PROBE_ONLY"}:
        reasons.append("healthy_expansion_add_relaxed")
        if final_size > current_size:
            reasons.append("healthy_expansion_size_floor_applied")
            return HealthyExpansionPolicyDecision("RELAX_SIZE_AND_ADD", final_size, True, tuple(reasons))
        return HealthyExpansionPolicyDecision("RELAX_ADD_ONLY", final_size, True, tuple(reasons))

    if final_size > current_size:
        reasons.append("healthy_expansion_size_floor_applied")
        if inputs.staged_add_allowed:
            reasons.append("existing_add_path_preserved")
        return HealthyExpansionPolicyDecision("RELAX_SIZE_ONLY", final_size, bool(inputs.staged_add_allowed), tuple(reasons))

    reasons.append("healthy_expansion_no_incremental_change")
    return HealthyExpansionPolicyDecision("NO_CHANGE", current_size, bool(inputs.staged_add_allowed), tuple(reasons))
