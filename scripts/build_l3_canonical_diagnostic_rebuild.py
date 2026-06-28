from __future__ import annotations

import csv
import io
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow
from src.brain.l3.calibration_builder import (
    audit_calibration_buckets,
    build_calibration_outcome_row_from_bridge,
    calibration_rows_to_dicts,
)
from src.brain.l3.calibration_contracts import L3CalibrationAuditBucket, L3CalibrationOutcomeRow
from src.brain.l3.calibration_store import CALIBRATION_OUTCOME_COLUMNS
from src.brain.l3.canonical_diagnostic_engine import (
    build_canonical_l3_objects,
    evidence_edge_to_dict,
    meaning_to_dict,
    relation_graph_to_dict,
)


REPORT_DIR = Path("docs/reports/task_l3_canonical_economic_meaning_rebuild")
ARTIFACT_DIR = Path("data/artifacts/task_l3_canonical_economic_meaning_rebuild")
CALIBRATION_REPORT_DIR = Path("docs/reports/task_l3_calibration_rule_migration")

SOURCE_EVENT_PATHS = (
    Path("docs/reports/task_385_canonical_continuation_engine/task_382_replay/canonical_lifecycle_event_stream.csv"),
    Path("docs/reports/task_385_canonical_continuation_engine/task_383_capture/canonical_capture_event_stream.csv"),
    Path("docs/reports/task_385_canonical_continuation_engine/task_384_accumulation/canonical_accumulation_event_stream.csv"),
)
BRIDGE_PATH = CALIBRATION_REPORT_DIR / "l3_explicit_source_event_outcome_bridge.csv"

MEANINGS_PATH = ARTIFACT_DIR / "l3_canonical_economic_meanings.csv"
EDGES_PATH = ARTIFACT_DIR / "l3_canonical_evidence_edges.csv"
GRAPHS_PATH = ARTIFACT_DIR / "l3_canonical_relation_graphs.csv"
CALIBRATION_OUTCOMES_PATH = ARTIFACT_DIR / "l3_canonical_calibration_outcomes.csv"
CALIBRATION_AUDIT_PATH = ARTIFACT_DIR / "l3_canonical_calibration_audit.csv"


def main() -> None:
    source_records = _dedupe_records_by_key(_read_existing_source_events(), "source_event_id")
    meanings, edges, graphs = build_canonical_l3_objects(source_records)
    meaning_by_receipt = {meaning.source_receipt_ids[0]: meaning for meaning in meanings}
    edge_by_meaning = {edge.meaning_id: edge for edge in edges}
    calibration_rows = _build_calibration_rows(meaning_by_receipt, edge_by_meaning)
    calibration_buckets = audit_calibration_buckets(calibration_rows, min_sample_size=100)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(MEANINGS_PATH, [meaning_to_dict(meaning) for meaning in meanings])
    _write_csv(EDGES_PATH, [evidence_edge_to_dict(edge) for edge in edges])
    _write_csv(GRAPHS_PATH, [relation_graph_to_dict(graph) for graph in graphs])
    _write_csv(CALIBRATION_OUTCOMES_PATH, calibration_rows_to_dicts(calibration_rows), CALIBRATION_OUTCOME_COLUMNS)
    _write_csv(CALIBRATION_AUDIT_PATH, _bucket_rows_to_dicts(calibration_buckets))

    non_missing = sum(1 for row in calibration_rows if row.missing_label_flag == 0)
    calibrated_buckets = sum(1 for bucket in calibration_buckets if bucket.calibrated_probability is not None)
    print(
        "[L3_CANONICAL_REBUILD] "
        f"meanings={len(meanings)} edges={len(edges)} graphs={len(graphs)} "
        f"calibration_rows={len(calibration_rows)} non_missing={non_missing} "
        f"calibration_buckets={len(calibration_buckets)} calibrated_buckets={calibrated_buckets}"
    )


def _read_existing_source_events() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in SOURCE_EVENT_PATHS:
        if path.exists():
            rows.extend(_read_csv(path))
    return rows


def _build_calibration_rows(
    meaning_by_receipt: dict[str, object],
    edge_by_meaning: dict[str, object],
) -> tuple[L3CalibrationOutcomeRow, ...]:
    if not BRIDGE_PATH.exists():
        return ()
    bridge_records = _read_csv(BRIDGE_PATH)
    outcome_cache: dict[Path, dict[str, dict[str, str]]] = {}
    rows: dict[str, L3CalibrationOutcomeRow] = {}
    for bridge_record in bridge_records:
        bridge = _bridge_from_record(bridge_record)
        meaning = meaning_by_receipt.get(bridge.source_receipt_id)
        if meaning is None:
            continue
        outcome_path = Path(bridge.outcome_source_table)
        if outcome_path not in outcome_cache:
            outcome_cache[outcome_path] = _index_by(outcome_path, "lifecycle_id") if outcome_path.exists() else {}
        outcome = outcome_cache[outcome_path].get(bridge.lifecycle_id)
        if outcome is None:
            continue
        edge = edge_by_meaning.get(meaning.meaning_id)
        row = build_calibration_outcome_row_from_bridge(
            meaning,
            bridge,
            _enriched_outcome_record(outcome, bridge),
            evidence_edge_id="" if edge is None else edge.evidence_edge_id,
        )
        rows[row.calibration_row_id] = row
    return tuple(rows[key] for key in sorted(rows))


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


def _enriched_outcome_record(
    outcome: dict[str, str],
    bridge: L3OutcomeBridgeRow,
) -> dict[str, str | int]:
    enriched: dict[str, str | int] = dict(outcome)
    enriched.update(
        {
            "outcome_source_table": bridge.outcome_source_table,
            "outcome_bridge_key": bridge.outcome_bridge_key,
            "lifecycle_id": bridge.lifecycle_id,
            "label_source": _text(outcome.get("label_source")) or "canonical_source_event_exact_bridge",
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


def _dedupe_records_by_key(records: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    deduped: dict[str, dict[str, str]] = {}
    for record in records:
        value = _text(record.get(key))
        if value and value not in deduped:
            deduped[value] = record
    return [deduped[value] for value in sorted(deduped)]


def _index_by(path: Path, key: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            value = _text(record.get(key))
            if value and value not in rows:
                rows[value] = record
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
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


def _first_text(mapping: dict[str, str | int], *keys: str) -> str:
    for key in keys:
        value = _text(mapping.get(key))
        if value:
            return value
    return ""


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


if __name__ == "__main__":
    main()
