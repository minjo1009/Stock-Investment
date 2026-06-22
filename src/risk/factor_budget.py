from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FactorBudgetConfig:
    semis_sector_name: str = "semis"
    semis_count_cap: int | None = None
    semis_daily_size_cap: float | None = None


@dataclass(frozen=True)
class FactorBudgetState:
    semis_count_used: int = 0
    semis_size_used: float = 0.0


@dataclass(frozen=True)
class FactorBudgetRequest:
    candidate_id: str
    sector_group: str
    proposed_size: float


@dataclass(frozen=True)
class FactorBudgetDecision:
    candidate_id: str
    allowed: bool
    blocked_by_count_cap: bool
    blocked_by_size_cap: bool
    budget_type: str
    next_state: FactorBudgetState


def initial_factor_budget_state() -> FactorBudgetState:
    return FactorBudgetState()


def evaluate_factor_budget(
    request: FactorBudgetRequest,
    current_state: FactorBudgetState,
    config: FactorBudgetConfig = FactorBudgetConfig(),
) -> FactorBudgetDecision:
    if request.sector_group != config.semis_sector_name:
        return FactorBudgetDecision(
            candidate_id=request.candidate_id,
            allowed=True,
            blocked_by_count_cap=False,
            blocked_by_size_cap=False,
            budget_type="non_semis_passthrough",
            next_state=current_state,
        )

    blocked_by_count_cap = False
    if config.semis_count_cap is not None:
        blocked_by_count_cap = current_state.semis_count_used >= max(int(config.semis_count_cap), 0)

    blocked_by_size_cap = False
    if config.semis_daily_size_cap is not None:
        blocked_by_size_cap = (current_state.semis_size_used + max(float(request.proposed_size), 0.0)) > max(float(config.semis_daily_size_cap), 0.0)

    allowed = not blocked_by_count_cap and not blocked_by_size_cap
    if allowed:
        next_state = FactorBudgetState(
            semis_count_used=current_state.semis_count_used + 1,
            semis_size_used=current_state.semis_size_used + max(float(request.proposed_size), 0.0),
        )
    else:
        next_state = current_state

    if config.semis_daily_size_cap is not None:
        budget_type = "semis_daily_size_cap"
    elif config.semis_count_cap is not None:
        budget_type = "semis_count_cap"
    else:
        budget_type = "no_semis_cap"

    return FactorBudgetDecision(
        candidate_id=request.candidate_id,
        allowed=allowed,
        blocked_by_count_cap=blocked_by_count_cap,
        blocked_by_size_cap=blocked_by_size_cap,
        budget_type=budget_type,
        next_state=next_state,
    )
