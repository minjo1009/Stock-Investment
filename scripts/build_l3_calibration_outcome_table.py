from __future__ import annotations

import csv
import io
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.contracts import MeaningDirection
from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow
from src.brain.l3.calibration_builder import (
    audit_calibration_buckets,
    build_calibration_outcome_row_from_bridge,
    calibration_rows_to_dicts,
)
from src.brain.l3.calibration_contracts import L3CalibrationAuditBucket, L3CalibrationOutcomeRow
from src.brain.l3.calibration_store import CALIBRATION_OUTCOME_COLUMNS
from src.brain.l3.confidence import build_static_l3_confidence
from src.brain.l3.contracts import L3EconomicMeaningV2
from src.l2.runtime_context import HISTORICAL_RESEARCH


REPORT_DIR = Path("docs/reports/task_l3_calibration_rule_migration")
BRIDGE_PATH = REPORT_DIR / "l3_explicit_source_event_outcome_bridge.csv"
OUTCOME_PATH = REPORT_DIR / "l3_calibration_outcomes.csv"
BUCKET_PATH = REPORT_DIR / "l3_calibration_audit_buckets.csv"


def main() -> None:
    bridge_records = _read_csv(BRIDGE_PATH)
    source_cache: dict[Path, dict[str, dict[str, str]]] = {}
    outcome_cache: dict[Path, dict[str, dict[str, str]]] = {}
    rows: dict[str, L3CalibrationOutcomeRow] = {}
    for record in bridge_records:
        bridge = _bridge_from_record(record)
        source_path = Path(bridge.bridge_source_artifact.split("|", 1)[0])
        if source_path not in source_cache:
            source_cache[source_path] = _index_by(source_path, "source_event_id")
        outcome_path = Path(bridge.outcome_source_table)
        if outcome_path not in outcome_cache:
            outcome_cache[outcome_path] = _index_by(outcome_path, "lifecycle_id")
        source_rows = source_cache[source_path]
        outcome_rows = outcome_cache[outcome_path]
        source_record = source_rows.get(bridge.source_receipt_id)
        outcome_record = outcome_rows.get(bridge.lifecycle_id)
        if source_record is None or outcome_record is None:
            continue
        meaning = _meaning_from_source_event(source_record, bridge)
        row = build_calibration_outcome_row_from_bridge(
            meaning,
            bridge,
            _enriched_outcome_record(outcome_record, source_record, bridge),
        )
        rows[row.calibration_row_id] = row

    outcome_rows_tuple = tuple(rows[key] for key in sorted(rows))
    buckets = audit_calibration_buckets(outcome_rows_tuple, min_sample_size=100)
    _write_csv(OUTCOME_PATH, calibration_rows_to_dicts(outcome_rows_tuple), CALIBRATION_OUTCOME_COLUMNS)
    _write_csv(BUCKET_PATH, _bucket_rows_to_dicts(buckets))
    non_missing = sum(1 for row in outcome_rows_tuple if row.missing_label_flag == 0)
    calibrated_buckets = sum(1 for bucket in buckets if bucket.calibrated_probability is not None)
    print(
        "[L3_CALIBRATION_TABLE] "
        f"rows={len(outcome_rows_tuple)} non_missing={non_missing} "
        f"buckets={len(buckets)} calibrated_buckets={calibrated_buckets}"
    )


def _bridge_from_record(record: dict[str, str]) -> L3OutcomeBridgeRow:
    return L3OutcomeBridgeRow(
        bridge_id=record["bridge_id"],
        meaning_id=record["meaning_id"],
        l2_primitive_id=record["l2_primitive_id"],
        source_receipt_id=record["source_receipt_id"],
        outcome_source_table=record["outcome_source_table"],
        outcome_bridge_key=record["outcome_bridge_key"],
        lifecycle_id=record["lifecycle_id"],
        continuation_id=record["continuation_id"],
        bridge_method=L3OutcomeBridgeMethod(record["bridge_method"]),
        bridge_source_artifact=record["bridge_source_artifact"],
        inferred_matching_used_flag=int(record["inferred_matching_used_flag"]),
    )


def _meaning_from_source_event(record: dict[str, str], bridge: L3OutcomeBridgeRow) -> L3EconomicMeaningV2:
    event_type = _text(record.get("event_type")) or "canonical_source_event"
    event_ts = _text(record.get("event_timestamp")) or _text(record.get("created_at")) or "HISTORICAL_RESEARCH"
    return L3EconomicMeaningV2(
        meaning_id=f"l3v2:source_event:{bridge.source_receipt_id}",
        asof_ts=event_ts,
        symbol=_text(record.get("symbol")).upper() or "UNKNOWN",
        l2_primitive_ids=(),
        source_receipt_ids=(bridge.source_receipt_id,),
        source_family="canonical_source_event",
        provider="local_canonical_artifact",
        authority_class="uncertified_source",
        runtime_context=HISTORICAL_RESEARCH,
        source_time_certified=False,
        freshness_status="HISTORICAL",
        event_type=f"canonical_source_event_{event_type.lower()}",
        economic_dimension="EXECUTION",
        direction=MeaningDirection.UNKNOWN,
        confidence=build_static_l3_confidence("unknown"),
        uncertainty_flags=("historical_source_event_bridge",),
        reason_codes=(
            "EXPLICIT_SOURCE_EVENT_LIFECYCLE_BRIDGE",
            "DIAGNOSTIC_CALIBRATION_SEED_ONLY",
            "NOT_TASK742_GOLDEN_PACKET_CALIBRATION",
        ),
    )


def _enriched_outcome_record(
    outcome: dict[str, str],
    source: dict[str, str],
    bridge: L3OutcomeBridgeRow,
) -> dict[str, str | int]:
    event_ts = _text(source.get("event_timestamp"))
    created_at = _text(source.get("created_at")) or event_ts
    enriched: dict[str, str | int] = dict(outcome)
    enriched.update(
        {
            "outcome_source_table": bridge.outcome_source_table,
            "outcome_bridge_key": bridge.outcome_bridge_key,
            "lifecycle_id": bridge.lifecycle_id,
            "event_time": event_ts,
            "source_ts": event_ts,
            "available_to_brain_ts": created_at,
            "entity_id": _text(source.get("setup_id")),
            "label_source": _text(outcome.get("label_source")) or "explicit_source_event_lifecycle_bridge",
            "inferred_matching_used_flag": 0,
            "label_used_in_assignment_flag": 0,
            "outcome_used_in_assignment_flag": 0,
        }
    )
    has_window = bool(_first_text(enriched, "outcome_start_ts", "entry_ts", "timestamp")) and bool(
        _first_text(enriched, "outcome_end_ts", "exit_ts", "simulated_exit_ts")
    )
    has_value = bool(_first_text(enriched, "outcome_value", "forward_return_pct", "net_return_from_entry", "return_from_entry"))
    if not has_window or not has_value:
        enriched["outcome_label"] = ""
        enriched["missing_label_flag"] = 1
    return enriched


def _index_by(path: Path, key: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            value = _text(record.get(key))
            if value and value not in rows:
                rows[value] = record
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8")


def _bucket_rows_to_dicts(buckets: tuple[L3CalibrationAuditBucket, ...]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for bucket in buckets:
        values = asdict(bucket)
        values["direction"] = bucket.direction.value
        values["calibration_status"] = bucket.calibration_status.value
        rows.append(values)
    return rows


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _first_text(mapping: dict[str, str | int], *keys: str) -> str:
    for key in keys:
        value = _text(mapping.get(key))
        if value:
            return value
    return ""


if __name__ == "__main__":
    main()
