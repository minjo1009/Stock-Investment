from __future__ import annotations

from dataclasses import dataclass

from .state_detector import CROWDED_DISLOCATION_STATE, NORMAL_CONTINUATION_STATE


@dataclass(frozen=True)
class StagedGateConfig:
    enabled: bool = True
    strong_execution_bucket: str = "strong"
    mixed_execution_bucket: str = "mixed"
    first_stage_session_buckets: tuple[str, ...] = ("first_30m", "unknown")
    stage_2_weight: float = 1.0
    delayed_probe_weight: float = 0.60
    crowded_probe_weight_strong: float = 0.35
    crowded_probe_weight_other: float = 0.20


@dataclass(frozen=True)
class StagedGateRequest:
    candidate_id: str
    row_state: str
    execution_quality_bucket: str
    session_timing_bucket: str


@dataclass(frozen=True)
class StagedGateDecision:
    candidate_id: str
    participation_stage: str
    stage_weight: float


def evaluate_staged_gate(
    request: StagedGateRequest,
    config: StagedGateConfig = StagedGateConfig(),
) -> StagedGateDecision:
    if not config.enabled:
        return StagedGateDecision(
            candidate_id=request.candidate_id,
            participation_stage="full_participation",
            stage_weight=1.0,
        )
    if request.row_state == NORMAL_CONTINUATION_STATE and request.execution_quality_bucket in (
        config.strong_execution_bucket,
        config.mixed_execution_bucket,
    ):
        return StagedGateDecision(
            candidate_id=request.candidate_id,
            participation_stage="stage_2_add",
            stage_weight=config.stage_2_weight,
        )
    if request.row_state == CROWDED_DISLOCATION_STATE or request.session_timing_bucket in config.first_stage_session_buckets:
        stage_weight = config.crowded_probe_weight_strong if request.execution_quality_bucket == config.strong_execution_bucket else config.crowded_probe_weight_other
        return StagedGateDecision(
            candidate_id=request.candidate_id,
            participation_stage="stage_1_probe",
            stage_weight=stage_weight,
        )
    return StagedGateDecision(
        candidate_id=request.candidate_id,
        participation_stage="delayed_probe",
        stage_weight=config.delayed_probe_weight,
    )
