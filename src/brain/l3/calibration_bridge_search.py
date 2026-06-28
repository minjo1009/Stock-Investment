from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path

from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow, bridge_row_to_dict
from src.brain.l3.calibration_bridge_builder import OUTCOME_VALUE_COLUMNS


@dataclass(frozen=True)
class L3ExplicitBridgeSearchAuditRow:
    source_event_path: str
    outcome_path: str
    source_event_lifecycle_row_count: int
    outcome_lifecycle_row_count: int
    exact_lifecycle_intersection_count: int
    bridge_row_count: int
    inferred_matching_required_flag: int
    allowed_for_calibration_flag: int
    rejection_reason: str


def build_source_event_outcome_bridge_rows(
    source_event_records: Iterable[Mapping[str, object]],
    outcome_records: Iterable[Mapping[str, object]],
    *,
    outcome_source_table: str,
    bridge_source_artifact: str,
) -> tuple[L3OutcomeBridgeRow, ...]:
    """Build source-event to outcome bridges using exact lifecycle ids only."""

    source_rows_by_lifecycle: dict[str, list[Mapping[str, object]]] = {}
    for record in source_event_records:
        source_event_id = _text(record.get("source_event_id"))
        lifecycle_id = _text(record.get("lifecycle_id"))
        if source_event_id and lifecycle_id:
            source_rows_by_lifecycle.setdefault(lifecycle_id, []).append(record)

    outcome_lifecycles = {
        lifecycle_id
        for record in outcome_records
        if (lifecycle_id := _text(record.get("lifecycle_id"))) and _has_outcome_value(record)
    }

    rows: list[L3OutcomeBridgeRow] = []
    for lifecycle_id in sorted(source_rows_by_lifecycle.keys() & outcome_lifecycles):
        for idx, source_record in enumerate(source_rows_by_lifecycle[lifecycle_id], start=1):
            source_event_id = _text(source_record.get("source_event_id"))
            rows.append(
                L3OutcomeBridgeRow(
                    bridge_id=(
                        f"l3_bridge:{_stable_id(bridge_source_artifact)}:"
                        f"{source_event_id}:{lifecycle_id}:{idx}"
                    ),
                    meaning_id="",
                    l2_primitive_id="",
                    source_receipt_id=source_event_id,
                    outcome_source_table=outcome_source_table,
                    outcome_bridge_key=lifecycle_id,
                    lifecycle_id=lifecycle_id,
                    continuation_id="",
                    bridge_method=L3OutcomeBridgeMethod.DIRECT_SOURCE_RECEIPT_ID,
                    bridge_source_artifact=bridge_source_artifact,
                    inferred_matching_used_flag=0,
                )
            )
    return tuple(rows)


def audit_source_event_outcome_bridge_pair(
    source_event_records: Iterable[Mapping[str, object]],
    outcome_records: Iterable[Mapping[str, object]],
    *,
    source_event_path: str,
    outcome_path: str,
) -> L3ExplicitBridgeSearchAuditRow:
    source_records = tuple(source_event_records)
    outcome_records_tuple = tuple(outcome_records)
    source_lifecycles = {
        lifecycle_id
        for record in source_records
        if _text(record.get("source_event_id")) and (lifecycle_id := _text(record.get("lifecycle_id")))
    }
    outcome_lifecycles = {
        lifecycle_id
        for record in outcome_records_tuple
        if (lifecycle_id := _text(record.get("lifecycle_id"))) and _has_outcome_value(record)
    }
    intersection = source_lifecycles & outcome_lifecycles
    bridge_rows = build_source_event_outcome_bridge_rows(
        source_records,
        outcome_records_tuple,
        outcome_source_table=outcome_path,
        bridge_source_artifact=f"{source_event_path}|{outcome_path}",
    )
    allowed = bool(bridge_rows)
    return L3ExplicitBridgeSearchAuditRow(
        source_event_path=source_event_path,
        outcome_path=outcome_path,
        source_event_lifecycle_row_count=len(source_lifecycles),
        outcome_lifecycle_row_count=len(outcome_lifecycles),
        exact_lifecycle_intersection_count=len(intersection),
        bridge_row_count=len(bridge_rows),
        inferred_matching_required_flag=int(not allowed),
        allowed_for_calibration_flag=int(allowed),
        rejection_reason="exact_lifecycle_bridge_available" if allowed else "no_exact_lifecycle_intersection",
    )


def explicit_bridge_search_rows_to_dicts(
    rows: Iterable[L3ExplicitBridgeSearchAuditRow],
) -> list[dict[str, object]]:
    return [asdict(row) for row in rows]


def explicit_bridge_rows_to_dicts(rows: Iterable[L3OutcomeBridgeRow]) -> list[dict[str, object]]:
    return [bridge_row_to_dict(row) for row in rows]


def find_candidate_csvs(root: str | Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    source_event_files: list[Path] = []
    outcome_files: list[Path] = []
    for path in Path(root).rglob("*.csv"):
        header = _csv_header(path)
        header_set = set(header)
        if {"source_event_id", "lifecycle_id"} <= header_set:
            source_event_files.append(path)
        if "lifecycle_id" in header_set and any(column in header_set for column in OUTCOME_VALUE_COLUMNS):
            outcome_files.append(path)
    return tuple(sorted(source_event_files)), tuple(sorted(outcome_files))


def _has_outcome_value(record: Mapping[str, object]) -> bool:
    return any(_text(record.get(column)) for column in OUTCOME_VALUE_COLUMNS)


def _csv_header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        first = handle.readline().strip()
    if not first:
        return ()
    return tuple(part.strip() for part in first.split(","))


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
