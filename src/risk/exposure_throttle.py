from __future__ import annotations

from dataclasses import dataclass

from .factor_budget import (
    FactorBudgetConfig,
    FactorBudgetDecision,
    FactorBudgetRequest,
    FactorBudgetState,
    evaluate_factor_budget,
    initial_factor_budget_state,
)
from .staged_gate import StagedGateConfig, StagedGateDecision, StagedGateRequest, evaluate_staged_gate
from .state_detector import CROWDED_DISLOCATION_STATE, NORMAL_CONTINUATION_STATE, UNCERTAIN_TRANSITION_STATE


@dataclass(frozen=True)
class ExposureCandidate:
    candidate_id: str
    symbol: str
    sector_group: str
    session_timing_bucket: str
    execution_quality_bucket: str
    row_state: str
    day_state: str
    base_score: float
    base_size: float = 1.0
    same_day_candidate_count: float = 0.0
    same_day_sector_candidate_count: float = 0.0
    order_index: int = 0


@dataclass(frozen=True)
class ExposureThrottleConfig:
    max_normal_positions: int = 3
    max_uncertain_positions: int = 2
    max_crowded_positions: int = 1
    uncertain_state_penalty: float = 0.25
    crowded_state_penalty: float = 1.0
    same_sector_penalty: float = 0.30
    same_session_penalty: float = 0.15
    same_symbol_penalty: float = 1.00
    semis_overlap_penalty: float = 0.40


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    adjusted_score: float
    state_penalty: float
    overlap_penalty: float
    total_penalty: float


@dataclass(frozen=True)
class RejectedCandidate:
    candidate_id: str
    symbol: str
    rejection_reason: str
    adjusted_score: float
    total_penalty: float
    blocked_by_count_cap: bool
    blocked_by_size_cap: bool


@dataclass(frozen=True)
class SelectedExposure:
    candidate_id: str
    symbol: str
    sector_group: str
    adjusted_score: float
    base_score: float
    state_penalty: float
    overlap_penalty: float
    participation_stage: str
    stage_weight: float
    base_size: float
    final_size: float
    budget_type: str


@dataclass(frozen=True)
class ExposurePlan:
    day_state: str
    position_cap: int
    selected: tuple[SelectedExposure, ...]
    rejected: tuple[RejectedCandidate, ...]
    factor_budget_state: FactorBudgetState


def position_cap_for_day_state(
    day_state: str,
    config: ExposureThrottleConfig = ExposureThrottleConfig(),
) -> int:
    if day_state == NORMAL_CONTINUATION_STATE:
        return max(config.max_normal_positions, 0)
    if day_state == CROWDED_DISLOCATION_STATE:
        return max(config.max_crowded_positions, 0)
    return max(config.max_uncertain_positions, 0)


def state_penalty_for_candidate(
    candidate: ExposureCandidate,
    config: ExposureThrottleConfig = ExposureThrottleConfig(),
) -> float:
    if candidate.row_state == NORMAL_CONTINUATION_STATE:
        return 0.0
    if candidate.row_state == CROWDED_DISLOCATION_STATE:
        return config.crowded_state_penalty
    if candidate.row_state == UNCERTAIN_TRANSITION_STATE:
        return config.uncertain_state_penalty
    return config.uncertain_state_penalty


def overlap_penalty_for_candidate(
    candidate: ExposureCandidate,
    selected: tuple[ExposureCandidate, ...],
    factor_budget_config: FactorBudgetConfig = FactorBudgetConfig(),
    config: ExposureThrottleConfig = ExposureThrottleConfig(),
) -> float:
    if not selected:
        return 0.0
    same_sector = sum(1 for item in selected if item.sector_group == candidate.sector_group)
    same_session = sum(1 for item in selected if item.session_timing_bucket == candidate.session_timing_bucket)
    same_symbol = sum(1 for item in selected if item.symbol == candidate.symbol)
    semis_selected = sum(1 for item in selected if item.sector_group == factor_budget_config.semis_sector_name)
    penalty = 0.0
    penalty += config.same_sector_penalty * float(same_sector)
    penalty += config.same_session_penalty * float(same_session)
    penalty += config.same_symbol_penalty * float(same_symbol)
    if candidate.sector_group == factor_budget_config.semis_sector_name:
        penalty += config.semis_overlap_penalty * float(semis_selected)
    return penalty


def marginal_score_candidate(
    candidate: ExposureCandidate,
    selected: tuple[ExposureCandidate, ...],
    factor_budget_config: FactorBudgetConfig = FactorBudgetConfig(),
    config: ExposureThrottleConfig = ExposureThrottleConfig(),
) -> CandidateScore:
    state_penalty = state_penalty_for_candidate(candidate, config)
    overlap_penalty = overlap_penalty_for_candidate(candidate, selected, factor_budget_config, config)
    total_penalty = state_penalty + overlap_penalty
    return CandidateScore(
        candidate_id=candidate.candidate_id,
        adjusted_score=float(candidate.base_score) - total_penalty,
        state_penalty=state_penalty,
        overlap_penalty=overlap_penalty,
        total_penalty=total_penalty,
    )


def build_exposure_plan(
    candidates: tuple[ExposureCandidate, ...],
    throttle_config: ExposureThrottleConfig = ExposureThrottleConfig(),
    factor_budget_config: FactorBudgetConfig = FactorBudgetConfig(),
    staged_gate_config: StagedGateConfig = StagedGateConfig(),
) -> ExposurePlan:
    if not candidates:
        return ExposurePlan(
            day_state=UNCERTAIN_TRANSITION_STATE,
            position_cap=position_cap_for_day_state(UNCERTAIN_TRANSITION_STATE, throttle_config),
            selected=(),
            rejected=(),
            factor_budget_state=initial_factor_budget_state(),
        )

    day_state = candidates[0].day_state
    position_cap = position_cap_for_day_state(day_state, throttle_config)
    if position_cap <= 0:
        rejected = tuple(
            RejectedCandidate(
                candidate_id=candidate.candidate_id,
                symbol=candidate.symbol,
                rejection_reason="day_position_cap_reached",
                adjusted_score=float(candidate.base_score),
                total_penalty=0.0,
                blocked_by_count_cap=False,
                blocked_by_size_cap=False,
            )
            for candidate in sorted(candidates, key=lambda item: (-item.base_score, item.order_index, item.candidate_id))
        )
        return ExposurePlan(
            day_state=day_state,
            position_cap=position_cap,
            selected=(),
            rejected=rejected,
            factor_budget_state=initial_factor_budget_state(),
        )

    available = tuple(sorted(candidates, key=lambda item: (-item.base_score, item.order_index, item.candidate_id)))
    selected_candidates: tuple[ExposureCandidate, ...] = ()
    selected_rows: tuple[SelectedExposure, ...] = ()
    rejected_rows: tuple[RejectedCandidate, ...] = ()
    budget_state = initial_factor_budget_state()

    while len(selected_rows) < position_cap and available:
        evaluations: list[
            tuple[
                ExposureCandidate,
                CandidateScore,
                StagedGateDecision,
                FactorBudgetDecision,
            ]
        ] = []
        for candidate in available:
            score = marginal_score_candidate(candidate, selected_candidates, factor_budget_config, throttle_config)
            stage_decision = evaluate_staged_gate(
                StagedGateRequest(
                    candidate_id=candidate.candidate_id,
                    row_state=candidate.row_state,
                    execution_quality_bucket=candidate.execution_quality_bucket,
                    session_timing_bucket=candidate.session_timing_bucket,
                ),
                staged_gate_config,
            )
            proposed_size = max(float(candidate.base_size), 0.0) * max(float(stage_decision.stage_weight), 0.0)
            budget_decision = evaluate_factor_budget(
                FactorBudgetRequest(
                    candidate_id=candidate.candidate_id,
                    sector_group=candidate.sector_group,
                    proposed_size=proposed_size,
                ),
                budget_state,
                factor_budget_config,
            )
            evaluations.append((candidate, score, stage_decision, budget_decision))
        evaluations.sort(
            key=lambda item: (
                not item[3].allowed,
                -item[1].adjusted_score,
                item[0].order_index,
                item[0].candidate_id,
            )
        )
        best_candidate, best_score, best_stage, best_budget = evaluations[0]
        if not best_budget.allowed:
            for candidate, score, _stage_decision, budget_decision in evaluations:
                rejected_rows += (
                    RejectedCandidate(
                        candidate_id=candidate.candidate_id,
                        symbol=candidate.symbol,
                        rejection_reason="factor_budget_blocked",
                        adjusted_score=score.adjusted_score,
                        total_penalty=score.total_penalty,
                        blocked_by_count_cap=budget_decision.blocked_by_count_cap,
                        blocked_by_size_cap=budget_decision.blocked_by_size_cap,
                    ),
                )
            break

        final_size = max(float(best_candidate.base_size), 0.0) * max(float(best_stage.stage_weight), 0.0)
        selected_rows += (
            SelectedExposure(
                candidate_id=best_candidate.candidate_id,
                symbol=best_candidate.symbol,
                sector_group=best_candidate.sector_group,
                adjusted_score=best_score.adjusted_score,
                base_score=float(best_candidate.base_score),
                state_penalty=best_score.state_penalty,
                overlap_penalty=best_score.overlap_penalty,
                participation_stage=best_stage.participation_stage,
                stage_weight=best_stage.stage_weight,
                base_size=float(best_candidate.base_size),
                final_size=final_size,
                budget_type=best_budget.budget_type,
            ),
        )
        selected_candidates += (best_candidate,)
        budget_state = best_budget.next_state
        available = tuple(candidate for candidate in available if candidate.candidate_id != best_candidate.candidate_id)

    selected_ids = {item.candidate_id for item in selected_rows}
    rejected_ids = {item.candidate_id for item in rejected_rows}
    for candidate in available:
        if candidate.candidate_id in selected_ids or candidate.candidate_id in rejected_ids:
            continue
        score = marginal_score_candidate(candidate, selected_candidates, factor_budget_config, throttle_config)
        rejected_rows += (
            RejectedCandidate(
                candidate_id=candidate.candidate_id,
                symbol=candidate.symbol,
                rejection_reason="position_cap_reached",
                adjusted_score=score.adjusted_score,
                total_penalty=score.total_penalty,
                blocked_by_count_cap=False,
                blocked_by_size_cap=False,
            ),
        )

    return ExposurePlan(
        day_state=day_state,
        position_cap=position_cap,
        selected=selected_rows,
        rejected=rejected_rows,
        factor_budget_state=budget_state,
    )
