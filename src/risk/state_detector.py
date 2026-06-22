from __future__ import annotations

from dataclasses import dataclass
import math


NORMAL_CONTINUATION_STATE = "normal_continuation_state"
UNCERTAIN_TRANSITION_STATE = "uncertain_transition_state"
CROWDED_DISLOCATION_STATE = "crowded_dislocation_state"


@dataclass(frozen=True)
class StateObservation:
    candidate_id: str
    sector_group: str
    session_timing_bucket: str
    execution_quality_bucket: str
    gap_environment_state: str
    market_breadth_state: str
    sector_leadership_state: str
    same_day_candidate_count: float
    same_day_sector_candidate_count: float
    dispersion_20d: float
    mean_pairwise_corr: float
    semis_concentration_ratio: float


@dataclass(frozen=True)
class StateDetectorConfig:
    semis_sector_name: str = "semis"
    calm_gap_state: str = "calm"
    unstable_gap_state: str = "unstable"
    broad_breadth_state: str = "broad"
    narrow_breadth_state: str = "narrow"
    tech_led_leadership_state: str = "tech_led"
    strong_execution_bucket: str = "strong"
    mixed_execution_bucket: str = "mixed"
    crowded_session_buckets: tuple[str, ...] = ("first_30m", "unknown")
    normal_session_buckets: tuple[str, ...] = ("mid_session", "last_hour")
    same_day_candidate_mid_quantile: float = 0.50
    same_day_candidate_high_quantile: float = 0.75
    same_day_sector_mid_quantile: float = 0.50
    same_day_sector_high_quantile: float = 0.75
    dispersion_high_quantile: float = 0.75
    correlation_high_quantile: float = 0.75
    semis_concentration_high_quantile: float = 0.75
    crowded_trigger_threshold: int = 2
    normal_trigger_threshold: int = 4
    day_crowded_share_threshold: float = 0.45
    day_semis_share_threshold: float = 0.50
    day_normal_share_threshold: float = 0.45
    day_crowded_share_max_for_normal: float = 0.15


@dataclass(frozen=True)
class StateThresholds:
    same_day_candidate_mid: float
    same_day_candidate_high: float
    same_day_sector_mid: float
    same_day_sector_high: float
    dispersion_high: float
    correlation_high: float
    semis_concentration_high: float


@dataclass(frozen=True)
class StateDetection:
    candidate_id: str
    row_state: str


@dataclass(frozen=True)
class DayStateSummary:
    day_state: str
    crowded_share: float
    normal_share: float
    semis_share: float
    average_same_day_candidate_count: float
    thresholds: StateThresholds
    detections: tuple[StateDetection, ...]


def _clean_number(value: float) -> float:
    numeric = float(value)
    if math.isnan(numeric) or math.isinf(numeric):
        return 0.0
    return numeric


def _sorted_valid(values: tuple[float, ...]) -> tuple[float, ...]:
    cleaned = tuple(_clean_number(value) for value in values if not math.isnan(float(value)))
    if not cleaned:
        return (0.0,)
    return tuple(sorted(cleaned))


def _quantile(values: tuple[float, ...], quantile: float) -> float:
    ordered = _sorted_valid(values)
    if len(ordered) == 1:
        return ordered[0]
    q = min(max(float(quantile), 0.0), 1.0)
    position = (len(ordered) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * weight)


def compute_state_thresholds(
    observations: tuple[StateObservation, ...],
    config: StateDetectorConfig = StateDetectorConfig(),
) -> StateThresholds:
    same_day_counts = tuple(observation.same_day_candidate_count for observation in observations)
    same_day_sector_counts = tuple(observation.same_day_sector_candidate_count for observation in observations)
    dispersion_values = tuple(observation.dispersion_20d for observation in observations)
    correlation_values = tuple(observation.mean_pairwise_corr for observation in observations)
    semis_concentration_values = tuple(observation.semis_concentration_ratio for observation in observations)
    return StateThresholds(
        same_day_candidate_mid=_quantile(same_day_counts, config.same_day_candidate_mid_quantile),
        same_day_candidate_high=_quantile(same_day_counts, config.same_day_candidate_high_quantile),
        same_day_sector_mid=_quantile(same_day_sector_counts, config.same_day_sector_mid_quantile),
        same_day_sector_high=_quantile(same_day_sector_counts, config.same_day_sector_high_quantile),
        dispersion_high=_quantile(dispersion_values, config.dispersion_high_quantile),
        correlation_high=_quantile(correlation_values, config.correlation_high_quantile),
        semis_concentration_high=_quantile(semis_concentration_values, config.semis_concentration_high_quantile),
    )


def classify_row_state(
    observation: StateObservation,
    thresholds: StateThresholds,
    config: StateDetectorConfig = StateDetectorConfig(),
) -> str:
    crowded_triggers = 0
    crowded_triggers += int(
        observation.sector_group == config.semis_sector_name
        and observation.same_day_sector_candidate_count >= thresholds.same_day_sector_high
    )
    crowded_triggers += int(
        observation.same_day_candidate_count >= thresholds.same_day_candidate_high
        and observation.session_timing_bucket in config.crowded_session_buckets
    )
    crowded_triggers += int(
        observation.gap_environment_state == config.unstable_gap_state
        and observation.market_breadth_state == config.narrow_breadth_state
    )
    crowded_triggers += int(
        observation.dispersion_20d >= thresholds.dispersion_high
        and observation.mean_pairwise_corr >= thresholds.correlation_high
    )
    crowded_triggers += int(
        observation.execution_quality_bucket == config.strong_execution_bucket
        and observation.session_timing_bucket in config.crowded_session_buckets
        and observation.same_day_candidate_count >= thresholds.same_day_candidate_mid
    )
    crowded_triggers += int(
        observation.sector_group == config.semis_sector_name
        and observation.semis_concentration_ratio >= thresholds.semis_concentration_high
    )
    crowded_triggers += int(
        observation.sector_leadership_state == config.tech_led_leadership_state
        and observation.market_breadth_state == config.narrow_breadth_state
    )
    if crowded_triggers >= config.crowded_trigger_threshold:
        return CROWDED_DISLOCATION_STATE

    normal_triggers = 0
    normal_triggers += int(observation.gap_environment_state == config.calm_gap_state)
    normal_triggers += int(observation.market_breadth_state == config.broad_breadth_state)
    normal_triggers += int(observation.session_timing_bucket in config.normal_session_buckets)
    normal_triggers += int(observation.execution_quality_bucket in (config.strong_execution_bucket, config.mixed_execution_bucket))
    normal_triggers += int(observation.same_day_candidate_count <= thresholds.same_day_candidate_mid)
    normal_triggers += int(observation.same_day_sector_candidate_count <= thresholds.same_day_sector_mid)
    normal_triggers += int(observation.sector_group != config.semis_sector_name)
    if normal_triggers >= config.normal_trigger_threshold:
        return NORMAL_CONTINUATION_STATE
    return UNCERTAIN_TRANSITION_STATE


def detect_states(
    observations: tuple[StateObservation, ...],
    thresholds: StateThresholds,
    config: StateDetectorConfig = StateDetectorConfig(),
) -> tuple[StateDetection, ...]:
    return tuple(
        StateDetection(
            candidate_id=observation.candidate_id,
            row_state=classify_row_state(observation, thresholds, config),
        )
        for observation in observations
    )


def summarize_day_state(
    observations: tuple[StateObservation, ...],
    detections: tuple[StateDetection, ...],
    thresholds: StateThresholds,
    config: StateDetectorConfig = StateDetectorConfig(),
) -> DayStateSummary:
    if not observations:
        return DayStateSummary(
            day_state=UNCERTAIN_TRANSITION_STATE,
            crowded_share=0.0,
            normal_share=0.0,
            semis_share=0.0,
            average_same_day_candidate_count=0.0,
            thresholds=thresholds,
            detections=(),
        )
    row_states = tuple(detection.row_state for detection in detections)
    crowded_share = row_states.count(CROWDED_DISLOCATION_STATE) / float(len(row_states))
    normal_share = row_states.count(NORMAL_CONTINUATION_STATE) / float(len(row_states))
    semis_share = sum(1 for observation in observations if observation.sector_group == config.semis_sector_name) / float(len(observations))
    average_same_day_candidate_count = sum(observation.same_day_candidate_count for observation in observations) / float(len(observations))
    if crowded_share >= config.day_crowded_share_threshold or (
        semis_share >= config.day_semis_share_threshold and average_same_day_candidate_count >= thresholds.same_day_candidate_mid
    ):
        day_state = CROWDED_DISLOCATION_STATE
    elif crowded_share <= config.day_crowded_share_max_for_normal and normal_share >= config.day_normal_share_threshold:
        day_state = NORMAL_CONTINUATION_STATE
    else:
        day_state = UNCERTAIN_TRANSITION_STATE
    return DayStateSummary(
        day_state=day_state,
        crowded_share=crowded_share,
        normal_share=normal_share,
        semis_share=semis_share,
        average_same_day_candidate_count=average_same_day_candidate_count,
        thresholds=thresholds,
        detections=detections,
    )


def detect_day_state(
    observations: tuple[StateObservation, ...],
    config: StateDetectorConfig = StateDetectorConfig(),
) -> DayStateSummary:
    thresholds = compute_state_thresholds(observations, config)
    detections = detect_states(observations, thresholds, config)
    return summarize_day_state(observations, detections, thresholds, config)
