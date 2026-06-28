from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.brain.contracts import MeaningDirection
from src.brain.l3.contracts import L3CalibrationStatus


class L3OutcomeLabel(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    MISSING = "MISSING"


class L3OutcomeMetric(StrEnum):
    FORWARD_RETURN_PCT = "FORWARD_RETURN_PCT"
    FORWARD_EXCESS_RETURN_PCT = "FORWARD_EXCESS_RETURN_PCT"
    CONFIRMATION_PRESENT = "CONFIRMATION_PRESENT"
    MANUAL_REVIEW_LABEL = "MANUAL_REVIEW_LABEL"


@dataclass(frozen=True)
class L3CalibrationOutcomeRow:
    calibration_row_id: str
    meaning_id: str
    evidence_edge_id: str
    l2_primitive_id: str
    source_receipt_id: str
    symbol: str
    entity_id: str
    asof_ts: str
    event_time: str
    source_ts: str
    available_to_brain_ts: str
    runtime_context: str
    source_time_certified: bool
    freshness_status: str
    event_type: str
    economic_dimension: str
    direction: MeaningDirection
    confidence_raw_band: str
    confidence_static_weight: float
    split_name: str
    outcome_source_table: str
    outcome_bridge_key: str
    lifecycle_id: str
    continuation_id: str
    outcome_start_ts: str
    outcome_end_ts: str
    outcome_horizon: str
    outcome_metric: L3OutcomeMetric
    outcome_value: float | None
    outcome_label: L3OutcomeLabel
    label_source: str
    inferred_matching_used_flag: int
    label_used_in_assignment_flag: int
    outcome_used_in_assignment_flag: int
    missing_label_flag: int
    diagnostic_only: bool = True
    trade_output_flag: int = 0
    score_output_flag: int = 0
    order_intent_flag: int = 0

    def __post_init__(self) -> None:
        for name in (
            "calibration_row_id",
            "meaning_id",
            "symbol",
            "asof_ts",
            "runtime_context",
            "event_type",
            "economic_dimension",
            "confidence_raw_band",
            "split_name",
            "outcome_source_table",
            "outcome_metric",
            "label_source",
        ):
            if not str(getattr(self, name, "")).strip():
                raise ValueError(f"{name} is required")
        if not 0.0 <= float(self.confidence_static_weight) <= 1.0:
            raise ValueError("confidence_static_weight must be in [0, 1]")
        if int(self.inferred_matching_used_flag) != 0:
            raise ValueError("calibration rows must not use inferred matching")
        if int(self.label_used_in_assignment_flag) != 0:
            raise ValueError("labels/outcomes must not enter assignment logic")
        if int(self.outcome_used_in_assignment_flag) != 0:
            raise ValueError("outcomes must not enter assignment logic")
        if not self.diagnostic_only:
            raise ValueError("calibration rows are diagnostic-only")
        for flag_name in ("trade_output_flag", "score_output_flag", "order_intent_flag"):
            if int(getattr(self, flag_name)) != 0:
                raise ValueError(f"{flag_name} must remain 0")
        if int(self.missing_label_flag) == 1:
            if self.outcome_label != L3OutcomeLabel.MISSING:
                raise ValueError("missing labels must use outcome_label=MISSING")
            return
        if not str(self.outcome_bridge_key).strip():
            raise ValueError("non-missing calibration rows require explicit outcome_bridge_key")
        if not str(self.outcome_start_ts).strip() or not str(self.outcome_end_ts).strip():
            raise ValueError("non-missing calibration rows require outcome window")
        if self.outcome_value is None:
            raise ValueError("non-missing calibration rows require outcome_value")
        if self.outcome_label == L3OutcomeLabel.MISSING:
            raise ValueError("non-missing calibration rows cannot use MISSING label")


@dataclass(frozen=True)
class L3CalibrationAuditBucket:
    event_type: str
    economic_dimension: str
    direction: MeaningDirection
    confidence_raw_band: str
    split_name: str
    sample_size: int
    positive_count: int
    negative_count: int
    neutral_count: int
    missing_count: int
    observed_positive_rate: float | None
    average_static_weight: float
    brier_score: float | None
    calibration_error: float | None
    calibration_status: L3CalibrationStatus
    calibrated_probability: float | None
    diagnostic_only: bool = True

    def __post_init__(self) -> None:
        if self.sample_size < 0:
            raise ValueError("sample_size must be non-negative")
        if not 0.0 <= self.average_static_weight <= 1.0:
            raise ValueError("average_static_weight must be in [0, 1]")
        for name in ("observed_positive_rate", "brier_score", "calibration_error", "calibrated_probability"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.calibration_status != L3CalibrationStatus.CALIBRATED and self.calibrated_probability is not None:
            raise ValueError("calibrated_probability requires CALIBRATED status")
        if not self.diagnostic_only:
            raise ValueError("calibration audit buckets are diagnostic-only")
