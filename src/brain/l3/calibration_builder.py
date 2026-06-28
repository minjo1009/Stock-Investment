from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict
import hashlib
from typing import Any

from src.brain.l3.calibration_contracts import (
    L3CalibrationAuditBucket,
    L3CalibrationOutcomeRow,
    L3OutcomeLabel,
    L3OutcomeMetric,
)
from src.brain.l3.calibration_bridge import L3OutcomeBridgeRow
from src.brain.l3.contracts import L3CalibrationStatus, L3EconomicMeaningV2


def _text(value: object) -> str:
    return "" if value is None else str(value)


def _int_flag(value: object) -> int:
    return 1 if str(value).strip().lower() in {"1", "1.0", "true", "yes", "y"} else 0


def _float_or_none(value: object) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def _outcome_label(value: object) -> L3OutcomeLabel:
    text = _text(value).strip().upper()
    if text in {"1", "TRUE", "WIN", "POSITIVE"}:
        return L3OutcomeLabel.POSITIVE
    if text in {"0", "FALSE", "LOSS", "NEGATIVE"}:
        return L3OutcomeLabel.NEGATIVE
    if text == "NEUTRAL":
        return L3OutcomeLabel.NEUTRAL
    if text in {"", "MISSING", "NA", "NAN"}:
        return L3OutcomeLabel.MISSING
    return L3OutcomeLabel(text)


def build_calibration_outcome_row(
    meaning: L3EconomicMeaningV2,
    outcome: Mapping[str, Any],
    *,
    evidence_edge_id: str = "",
) -> L3CalibrationOutcomeRow:
    """Build a calibration row only from explicit bridge keys.

    The function intentionally rejects proximity joins. A non-missing outcome
    must reference the meaning id, one of the L2 primitive ids, or one of the
    source receipt ids.
    """

    bridge_key = _text(outcome.get("outcome_bridge_key")).strip()
    allowed_keys = {meaning.meaning_id, *meaning.l2_primitive_ids, *meaning.source_receipt_ids}
    missing_label = _int_flag(outcome.get("missing_label_flag"))
    if not missing_label and bridge_key not in allowed_keys:
        raise ValueError("outcome_bridge_key must explicitly match meaning, L2 primitive, or source receipt id")
    if _int_flag(outcome.get("inferred_matching_used_flag")):
        raise ValueError("inferred matching is forbidden for L3 calibration")
    return _build_calibration_row(
        meaning,
        outcome,
        evidence_edge_id=evidence_edge_id,
        bridge_key=bridge_key,
    )


def build_calibration_outcome_row_from_bridge(
    meaning: L3EconomicMeaningV2,
    bridge: L3OutcomeBridgeRow,
    outcome: Mapping[str, Any],
    *,
    evidence_edge_id: str = "",
) -> L3CalibrationOutcomeRow:
    if int(bridge.inferred_matching_used_flag) != 0 or _int_flag(outcome.get("inferred_matching_used_flag")):
        raise ValueError("inferred matching is forbidden for L3 calibration")
    if not _bridge_matches_meaning(meaning, bridge):
        raise ValueError("bridge row does not explicitly match the L3 meaning")
    outcome_key = (
        _text(outcome.get("outcome_bridge_key")).strip()
        or _text(outcome.get("lifecycle_id")).strip()
        or _text(outcome.get("continuation_id")).strip()
        or _text(outcome.get("simulated_lifecycle_id")).strip()
    )
    allowed_outcome_keys = {bridge.outcome_bridge_key, bridge.lifecycle_id, bridge.continuation_id}
    allowed_outcome_keys = {item for item in allowed_outcome_keys if item}
    if outcome_key not in allowed_outcome_keys:
        raise ValueError("outcome row does not explicitly match the bridge row")
    normalized = _normalize_outcome_for_bridge(outcome, bridge, outcome_key)
    return _build_calibration_row(
        meaning,
        normalized,
        evidence_edge_id=evidence_edge_id,
        bridge_key=outcome_key,
    )


def _build_calibration_row(
    meaning: L3EconomicMeaningV2,
    outcome: Mapping[str, Any],
    *,
    evidence_edge_id: str,
    bridge_key: str,
) -> L3CalibrationOutcomeRow:
    missing_label = _int_flag(outcome.get("missing_label_flag"))
    l2_id = _text(outcome.get("l2_primitive_id")) or (meaning.l2_primitive_ids[0] if meaning.l2_primitive_ids else "")
    receipt_id = _text(outcome.get("source_receipt_id")) or (
        meaning.source_receipt_ids[0] if meaning.source_receipt_ids else ""
    )
    label = _outcome_label(outcome.get("outcome_label"))
    if missing_label:
        label = L3OutcomeLabel.MISSING
    source_table = _text(outcome.get("outcome_source_table"))
    row_id = _text(outcome.get("calibration_row_id")) or (
        f"l3_cal:{meaning.meaning_id}:{_stable_id(source_table)}:{bridge_key or 'missing'}"
    )
    return L3CalibrationOutcomeRow(
        calibration_row_id=row_id,
        meaning_id=meaning.meaning_id,
        evidence_edge_id=evidence_edge_id or _text(outcome.get("evidence_edge_id")),
        l2_primitive_id=l2_id,
        source_receipt_id=receipt_id,
        symbol=meaning.symbol,
        entity_id=_text(outcome.get("entity_id")),
        asof_ts=meaning.asof_ts,
        event_time=_text(outcome.get("event_time")),
        source_ts=_text(outcome.get("source_ts")),
        available_to_brain_ts=_text(outcome.get("available_to_brain_ts")),
        runtime_context=meaning.runtime_context,
        source_time_certified=meaning.source_time_certified,
        freshness_status=meaning.freshness_status,
        event_type=meaning.event_type,
        economic_dimension=meaning.economic_dimension,
        direction=meaning.direction,
        confidence_raw_band=meaning.confidence.raw_band,
        confidence_static_weight=meaning.confidence.static_weight,
        split_name=_text(outcome.get("split_name")),
        outcome_source_table=source_table,
        outcome_bridge_key=bridge_key,
        lifecycle_id=_text(outcome.get("lifecycle_id")),
        continuation_id=_text(outcome.get("continuation_id")),
        outcome_start_ts=_text(outcome.get("outcome_start_ts")),
        outcome_end_ts=_text(outcome.get("outcome_end_ts")),
        outcome_horizon=_text(outcome.get("outcome_horizon")),
        outcome_metric=L3OutcomeMetric(_text(outcome.get("outcome_metric")) or L3OutcomeMetric.FORWARD_RETURN_PCT),
        outcome_value=_float_or_none(outcome.get("outcome_value")),
        outcome_label=label,
        label_source=_text(outcome.get("label_source")),
        inferred_matching_used_flag=_int_flag(outcome.get("inferred_matching_used_flag")),
        label_used_in_assignment_flag=_int_flag(outcome.get("label_used_in_assignment_flag")),
        outcome_used_in_assignment_flag=_int_flag(outcome.get("outcome_used_in_assignment_flag")),
        missing_label_flag=missing_label,
    )


def _bridge_matches_meaning(meaning: L3EconomicMeaningV2, bridge: L3OutcomeBridgeRow) -> bool:
    if bridge.meaning_id and bridge.meaning_id == meaning.meaning_id:
        return True
    if bridge.l2_primitive_id and bridge.l2_primitive_id in meaning.l2_primitive_ids:
        return True
    if bridge.source_receipt_id and bridge.source_receipt_id in meaning.source_receipt_ids:
        return True
    return False


def _normalize_outcome_for_bridge(
    outcome: Mapping[str, Any],
    bridge: L3OutcomeBridgeRow,
    outcome_key: str,
) -> dict[str, Any]:
    normalized = dict(outcome)
    normalized["outcome_bridge_key"] = outcome_key
    normalized.setdefault("outcome_source_table", bridge.outcome_source_table)
    normalized.setdefault("lifecycle_id", bridge.lifecycle_id)
    normalized.setdefault("continuation_id", bridge.continuation_id)
    normalized.setdefault(
        "split_name",
        _first_text(outcome, "split_name", "canonical_split", "anchored_split", "current_split", "walk_forward_test_quarter")
        or "UNSPECIFIED_SPLIT_REVIEW_ONLY",
    )
    normalized.setdefault("outcome_start_ts", _first_text(outcome, "outcome_start_ts", "entry_ts", "timestamp"))
    normalized.setdefault("outcome_end_ts", _first_text(outcome, "outcome_end_ts", "exit_ts", "simulated_exit_ts"))
    normalized.setdefault("outcome_horizon", _text(outcome.get("outcome_horizon")) or "EXPLICIT_BRIDGE")
    normalized.setdefault("outcome_metric", _infer_outcome_metric(outcome))
    normalized.setdefault("outcome_value", _first_text(outcome, "outcome_value", "forward_return_pct", "net_return_from_entry", "return_from_entry"))
    normalized.setdefault("outcome_label", _first_text(outcome, "outcome_label", "win_flag", "positive_return_flag"))
    if not _text(normalized.get("outcome_label")):
        normalized["missing_label_flag"] = 1
    normalized.setdefault("label_source", _text(outcome.get("label_source")) or "explicit_l3_outcome_bridge")
    return normalized


def _first_text(mapping: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = _text(mapping.get(key)).strip()
        if value:
            return value
    return ""


def _infer_outcome_metric(outcome: Mapping[str, Any]) -> str:
    if _text(outcome.get("forward_return_pct")).strip():
        return L3OutcomeMetric.FORWARD_RETURN_PCT.value
    if _text(outcome.get("net_return_from_entry")).strip() or _text(outcome.get("return_from_entry")).strip():
        return L3OutcomeMetric.FORWARD_RETURN_PCT.value
    return _text(outcome.get("outcome_metric")) or L3OutcomeMetric.FORWARD_RETURN_PCT.value


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def calibration_rows_to_dicts(rows: Sequence[L3CalibrationOutcomeRow]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        values = asdict(row)
        values["direction"] = row.direction.value
        values["outcome_metric"] = row.outcome_metric.value
        values["outcome_label"] = row.outcome_label.value
        out.append(values)
    return out


def audit_calibration_buckets(
    rows: Sequence[L3CalibrationOutcomeRow],
    *,
    min_sample_size: int = 100,
) -> tuple[L3CalibrationAuditBucket, ...]:
    grouped: dict[tuple[str, str, object, str, str], list[L3CalibrationOutcomeRow]] = defaultdict(list)
    for row in rows:
        key = (row.event_type, row.economic_dimension, row.direction, row.confidence_raw_band, row.split_name)
        grouped[key].append(row)
    buckets: list[L3CalibrationAuditBucket] = []
    for (event_type, dimension, direction, band, split_name), items in sorted(grouped.items(), key=lambda item: str(item[0])):
        non_missing = [row for row in items if row.outcome_label != L3OutcomeLabel.MISSING]
        positives = sum(1 for row in non_missing if row.outcome_label == L3OutcomeLabel.POSITIVE)
        negatives = sum(1 for row in non_missing if row.outcome_label == L3OutcomeLabel.NEGATIVE)
        neutrals = sum(1 for row in non_missing if row.outcome_label == L3OutcomeLabel.NEUTRAL)
        missing = len(items) - len(non_missing)
        sample_size = len(non_missing)
        avg_static = sum(row.confidence_static_weight for row in non_missing) / sample_size if sample_size else 0.0
        observed = positives / sample_size if sample_size else None
        brier = None
        error = None
        status = L3CalibrationStatus.INSUFFICIENT_SAMPLE
        calibrated_probability = None
        if sample_size >= min_sample_size and observed is not None:
            brier = sum((row.confidence_static_weight - (1.0 if row.outcome_label == L3OutcomeLabel.POSITIVE else 0.0)) ** 2 for row in non_missing) / sample_size
            error = abs(avg_static - observed)
            status = L3CalibrationStatus.CALIBRATED
            calibrated_probability = observed
        buckets.append(
            L3CalibrationAuditBucket(
                event_type=event_type,
                economic_dimension=dimension,
                direction=direction,
                confidence_raw_band=band,
                split_name=split_name,
                sample_size=sample_size,
                positive_count=positives,
                negative_count=negatives,
                neutral_count=neutrals,
                missing_count=missing,
                observed_positive_rate=observed,
                average_static_weight=avg_static,
                brier_score=brier,
                calibration_error=error,
                calibration_status=status,
                calibrated_probability=calibrated_probability,
            )
        )
    return tuple(buckets)
