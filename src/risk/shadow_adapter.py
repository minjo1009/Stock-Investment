from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .factor_budget import (
    FactorBudgetConfig,
    FactorBudgetDecision,
    FactorBudgetRequest,
    FactorBudgetState,
    evaluate_factor_budget,
)
from .participation_quality import (
    ParticipationQualityConfig,
    ParticipationQualityDecision,
    ParticipationQualityInputs,
    evaluate_participation_quality,
)
from .staged_gate import StagedGateConfig, StagedGateDecision, StagedGateRequest, evaluate_staged_gate
from .state_detector import (
    CROWDED_DISLOCATION_STATE,
    NORMAL_CONTINUATION_STATE,
    UNCERTAIN_TRANSITION_STATE,
    StateDetectorConfig,
    StateObservation,
    detect_day_state,
)


@dataclass(frozen=True)
class ShadowAdapterConfig:
    factor_budget_config: FactorBudgetConfig = FactorBudgetConfig(semis_count_cap=None, semis_daily_size_cap=0.45)
    participation_quality_config: ParticipationQualityConfig = ParticipationQualityConfig()
    staged_gate_config: StagedGateConfig = StagedGateConfig()
    state_detector_config: StateDetectorConfig = StateDetectorConfig()
    dislocation_probe_gross_limit: float = 0.15
    default_base_size: float = 0.10


@dataclass(frozen=True)
class ShadowStateDecision:
    continuation_risk_score: float
    state_label: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ShadowExposureDecision:
    gross_exposure_multiplier: float
    allow_new_entry: bool
    allow_add: bool
    max_new_notional_multiplier: float
    max_add_notional_multiplier: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ShadowRiskDecision:
    signal_id: str | None
    timestamp: Any
    symbol: str
    strategy_id: str | None
    state_decision: ShadowStateDecision
    participation_quality_decision: ParticipationQualityDecision
    factor_budget_decision: FactorBudgetDecision
    exposure_decision: ShadowExposureDecision
    staged_gate_decision: StagedGateDecision
    factor_exposure_violated: bool
    violated_factors: tuple[str, ...]
    shadow_size_multiplier: float
    block_reasons: tuple[str, ...]
    next_factor_budget_state: FactorBudgetState


def _safe_text(value: Any, default: str) -> str:
    text = str(value) if value is not None else ""
    text = text.strip()
    return text if text else default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(default)
    if pd.isna(numeric):
        return float(default)
    return numeric


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        numeric = int(float(value))
    except (TypeError, ValueError):
        return int(default)
    return numeric


def _base_size(row: pd.Series, config: ShadowAdapterConfig) -> float:
    for key in ("size_multiplier", "base_size_multiplier", "final_size", "base_size"):
        if key in row.index:
            value = _safe_float(row.get(key), config.default_base_size)
            if value > 0:
                return value
    return config.default_base_size


def _build_observations(day_slice: pd.DataFrame, config: ShadowAdapterConfig) -> tuple[StateObservation, ...]:
    observations: list[StateObservation] = []
    if day_slice.empty:
        return ()
    semis_share = float(day_slice["sector_group"].astype(str).eq("semis").mean()) if "sector_group" in day_slice.columns else 0.0
    for _, row in day_slice.iterrows():
        observations.append(
            StateObservation(
                candidate_id=_safe_text(row.get("trade_id", row.get("event_id")), "unknown_candidate"),
                sector_group=_safe_text(row.get("sector_group"), "unknown"),
                session_timing_bucket=_safe_text(row.get("session_timing_bucket"), "unknown"),
                execution_quality_bucket="unknown",
                gap_environment_state=_safe_text(row.get("gap_environment_state"), "unknown"),
                market_breadth_state=_safe_text(row.get("market_breadth_state"), "unknown"),
                sector_leadership_state=_safe_text(row.get("sector_leadership_state"), "unknown"),
                same_day_candidate_count=_safe_float(row.get("same_day_candidate_count"), 0.0),
                same_day_sector_candidate_count=_safe_float(row.get("same_day_sector_candidate_count"), 0.0),
                dispersion_20d=_safe_float(row.get("dispersion_20d"), 0.0),
                mean_pairwise_corr=_safe_float(row.get("mean_pairwise_corr"), 0.0),
                semis_concentration_ratio=_safe_float(row.get("semis_concentration_ratio"), semis_share),
            )
        )
    return tuple(observations)


def _bounded_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    ratio = numerator / denominator
    if ratio < 0.0:
        return 0.0
    if ratio > 1.0:
        return 1.0
    return ratio


def _session_timing_score(bucket: str) -> float | None:
    mapping = {
        "preopen": 0.65,
        "mid_session": 0.85,
        "first_30m": 0.45,
        "last_hour": 0.25,
        "unknown": 0.30,
    }
    return mapping.get(bucket)


def _quality_inputs(row: pd.Series, day_slice: pd.DataFrame) -> ParticipationQualityInputs:
    breadth_text = _safe_text(row.get("market_breadth_state"), "unknown")
    gap_text = _safe_text(row.get("gap_environment_state"), "unknown")
    leadership_text = _safe_text(row.get("sector_leadership_state"), "unknown")
    session_text = _safe_text(row.get("session_timing_bucket"), "unknown")
    sector_text = _safe_text(row.get("sector_group"), "unknown")

    same_day_count = _safe_float(row.get("same_day_candidate_count"), 0.0)
    same_day_sector_count = _safe_float(row.get("same_day_sector_candidate_count"), 0.0)
    breadth_ratio = _bounded_ratio(max(same_day_count - same_day_sector_count, 0.0), max(same_day_count, 1.0))
    semis_ratio = _safe_float(row.get("semis_concentration_ratio"), 0.0)
    sector_ratio = _bounded_ratio(same_day_sector_count, max(same_day_count, 1.0))

    breadth_change = None
    if breadth_text == "broad":
        breadth_change = 0.60
    elif breadth_text == "narrow":
        breadth_change = -0.60

    liquidity_change = None
    if gap_text == "calm":
        liquidity_change = 0.40
    elif gap_text == "unstable":
        liquidity_change = -0.40

    persistence = None
    if leadership_text in {"broad_led", "broad_risk_on"}:
        persistence = 0.75
    elif leadership_text == "tech_led":
        persistence = 0.45
    elif breadth_text == "broad":
        persistence = 0.60
    elif breadth_text == "narrow":
        persistence = 0.35

    dispersion = row.get("dispersion_20d")
    volatility_expansion = None if dispersion is None else min(max(_safe_float(dispersion, 0.0), 0.0), 1.0)
    corr_value = row.get("mean_pairwise_corr")
    corr_numeric = None if corr_value is None else min(max(_safe_float(corr_value, 0.0), 0.0), 1.0)

    reversal_stability = None if corr_numeric is None else 1.0 - (0.65 * corr_numeric)
    dip_absorption = None
    if session_text == "mid_session":
        dip_absorption = 0.70
    elif session_text == "first_30m":
        dip_absorption = 0.40
    elif session_text == "last_hour":
        dip_absorption = 0.25
    elif session_text == "unknown":
        dip_absorption = 0.35

    factor_concentration = max(semis_ratio, sector_ratio or 0.0)
    if sector_text == "semis":
        factor_concentration = min(1.0, factor_concentration + 0.20)
    elif sector_text == "software_internet":
        factor_concentration = min(1.0, factor_concentration + 0.10)

    same_day_signal_crowding = min(max(same_day_count / 12.0, 0.0), 1.0) if same_day_count > 0 else None

    return ParticipationQualityInputs(
        breadth_change=breadth_change,
        breadth_participation_ratio=breadth_ratio,
        liquidity_change=liquidity_change,
        dip_absorption_score=dip_absorption,
        reversal_stability_score=reversal_stability,
        factor_concentration_score=factor_concentration,
        same_day_signal_crowding=same_day_signal_crowding,
        volatility_expansion_score=volatility_expansion,
        continuation_persistence_score=persistence,
        session_timing_score=_session_timing_score(session_text),
    )


def _map_state_label(row_state: str, day_state: str) -> str:
    if row_state == CROWDED_DISLOCATION_STATE and day_state == CROWDED_DISLOCATION_STATE:
        return "DISLOCATION"
    if row_state == CROWDED_DISLOCATION_STATE or day_state == CROWDED_DISLOCATION_STATE:
        return "CROWDED"
    if row_state == UNCERTAIN_TRANSITION_STATE or day_state == UNCERTAIN_TRANSITION_STATE:
        return "ELEVATED"
    return "NORMAL"


def _risk_score_for_label(label: str, row: pd.Series, day_summary: Any) -> float:
    base = {
        "NORMAL": 0.15,
        "ELEVATED": 0.40,
        "CROWDED": 0.62,
        "DISLOCATION": 0.85,
    }[label]
    same_day_count = _safe_float(row.get("same_day_candidate_count"), 0.0)
    same_day_high = _safe_float(getattr(day_summary.thresholds, "same_day_candidate_high", 0.0), 0.0)
    if same_day_high > 0 and same_day_count >= same_day_high:
        base += 0.05
    if _safe_text(row.get("sector_group"), "") == "semis":
        base += 0.03
    return min(max(base, 0.0), 1.0)


def _exposure_decision(
    state_label: str,
    current_gross_exposure: float,
    factor_allowed: bool,
    config: ShadowAdapterConfig,
) -> ShadowExposureDecision:
    reasons: list[str] = []
    if state_label == "NORMAL":
        gross = 1.0
        allow_new = True
        allow_add = True
        max_new = 1.0
        max_add = 1.0
    elif state_label == "ELEVATED":
        gross = 0.75
        allow_new = True
        allow_add = True
        max_new = 0.75
        max_add = 0.50
        reasons.append("elevated_state_size_reduction")
    elif state_label == "CROWDED":
        gross = 0.40
        allow_new = True
        allow_add = False
        max_new = 0.40
        max_add = 0.0
        reasons.append("crowded_state_add_restricted")
    else:
        allow_new = current_gross_exposure < config.dislocation_probe_gross_limit
        gross = 0.20 if allow_new else 0.0
        allow_add = False
        max_new = gross
        max_add = 0.0
        reasons.append("dislocation_state_add_blocked")

    if not factor_allowed:
        allow_new = False
        allow_add = False
        gross = 0.0
        max_new = 0.0
        max_add = 0.0
        reasons.append("factor_budget_blocked_entry")

    if not reasons:
        reasons.append("shadow_full_participation_allowed")

    return ShadowExposureDecision(
        gross_exposure_multiplier=gross,
        allow_new_entry=allow_new,
        allow_add=allow_add,
        max_new_notional_multiplier=max_new,
        max_add_notional_multiplier=max_add,
        reasons=tuple(reasons),
    )


def _violated_factors(row: pd.Series, budget_decision: FactorBudgetDecision) -> tuple[str, ...]:
    if budget_decision.allowed:
        return ()
    sector_group = _safe_text(row.get("sector_group"), "unknown")
    if sector_group == "semis":
        return ("semis",)
    if sector_group == "software_internet":
        return ("ai",)
    return ("high_beta_momentum",)


def _stage_multiplier(stage_name: str) -> float:
    mapping = {
        "full_participation": 1.0,
        "stage_2_add": 1.0,
        "delayed_probe": 0.60,
        "stage_1_probe": 0.35,
    }
    return mapping.get(stage_name, 0.0)


def build_shadow_risk_decision(
    row: pd.Series,
    day_slice: pd.DataFrame,
    *,
    current_gross_exposure: float = 0.0,
    factor_budget_state: FactorBudgetState | None = None,
    config: ShadowAdapterConfig | None = None,
) -> ShadowRiskDecision:
    cfg = config or ShadowAdapterConfig()
    budget_state = factor_budget_state or FactorBudgetState()
    observations = _build_observations(day_slice, cfg)
    day_summary = detect_day_state(observations, cfg.state_detector_config)
    candidate_id = _safe_text(row.get("trade_id", row.get("event_id")), "unknown_candidate")
    detection = next((item for item in day_summary.detections if item.candidate_id == candidate_id), None)
    row_state = detection.row_state if detection is not None else UNCERTAIN_TRANSITION_STATE
    state_label = _map_state_label(row_state, day_summary.day_state)

    reasons = [f"row_state={row_state}", f"day_state={day_summary.day_state}"]
    if "dispersion_20d" not in row.index:
        reasons.append("missing_dispersion_defaulted")
    if "mean_pairwise_corr" not in row.index:
        reasons.append("missing_corr_defaulted")
    if "semis_concentration_ratio" not in row.index:
        reasons.append("missing_semis_concentration_defaulted")
    reasons.append("state_detector_execution_bucket_forced_unknown")

    state_decision = ShadowStateDecision(
        continuation_risk_score=_risk_score_for_label(state_label, row, day_summary),
        state_label=state_label,
        reasons=tuple(reasons),
    )
    participation_quality_decision = evaluate_participation_quality(
        _quality_inputs(row, day_slice),
        cfg.participation_quality_config,
    )

    budget_request = FactorBudgetRequest(
        candidate_id=candidate_id,
        sector_group=_safe_text(row.get("sector_group"), "unknown"),
        proposed_size=_base_size(row, cfg),
    )
    factor_budget_decision = evaluate_factor_budget(budget_request, budget_state, cfg.factor_budget_config)
    exposure_decision = _exposure_decision(
        state_decision.state_label,
        current_gross_exposure=current_gross_exposure,
        factor_allowed=factor_budget_decision.allowed,
        config=cfg,
    )

    staged_gate_decision = evaluate_staged_gate(
        StagedGateRequest(
            candidate_id=candidate_id,
            row_state=row_state,
            execution_quality_bucket=_safe_text(row.get("execution_quality_bucket"), "unknown"),
            session_timing_bucket=_safe_text(row.get("session_timing_bucket"), "unknown"),
        ),
        cfg.staged_gate_config,
    )

    stage_multiplier = _stage_multiplier(staged_gate_decision.participation_stage)
    shadow_size_multiplier = exposure_decision.gross_exposure_multiplier * stage_multiplier
    violated_factors = _violated_factors(row, factor_budget_decision)
    block_reasons: list[str] = []
    if not exposure_decision.allow_new_entry:
        block_reasons.extend(exposure_decision.reasons)
    if not factor_budget_decision.allowed:
        block_reasons.append(f"factor_violation={','.join(violated_factors) or 'unknown'}")
    if staged_gate_decision.participation_stage != "stage_2_add":
        block_reasons.append(f"stage={staged_gate_decision.participation_stage}")

    return ShadowRiskDecision(
        signal_id=None if pd.isna(row.get("event_id")) else str(row.get("event_id")),
        timestamp=row.get("entry_ts"),
        symbol=_safe_text(row.get("symbol"), "unknown"),
        strategy_id=_safe_text(row.get("strategy_id"), "continuation_sleeve"),
        state_decision=state_decision,
        participation_quality_decision=participation_quality_decision,
        factor_budget_decision=factor_budget_decision,
        exposure_decision=exposure_decision,
        staged_gate_decision=staged_gate_decision,
        factor_exposure_violated=not factor_budget_decision.allowed,
        violated_factors=violated_factors,
        shadow_size_multiplier=shadow_size_multiplier,
        block_reasons=tuple(block_reasons),
        next_factor_budget_state=factor_budget_decision.next_state if factor_budget_decision.allowed else budget_state,
    )
