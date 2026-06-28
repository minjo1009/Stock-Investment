from __future__ import annotations

import csv
import hashlib
import sys
from dataclasses import fields
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow
from src.brain.l3.calibration_bridge_search import (
    explicit_bridge_rows_to_dicts,
    explicit_bridge_search_rows_to_dicts,
    L3ExplicitBridgeSearchAuditRow,
)
from src.brain.l3.calibration_bridge_builder import OUTCOME_VALUE_COLUMNS


OUT_DIR = Path("docs/reports/task_l3_calibration_rule_migration")
AUDIT_PATH = OUT_DIR / "l3_explicit_bridge_search_audit.csv"
BRIDGE_PATH = OUT_DIR / "l3_explicit_source_event_outcome_bridge.csv"
SOURCE_EVENT_CANDIDATES = (
    Path("docs/reports/task_385_canonical_continuation_engine/task_382_replay/canonical_lifecycle_event_stream.csv"),
    Path("docs/reports/task_385_canonical_continuation_engine/task_383_capture/canonical_capture_event_stream.csv"),
    Path("docs/reports/task_385_canonical_continuation_engine/task_384_accumulation/canonical_accumulation_event_stream.csv"),
)
OUTCOME_CANDIDATES = (
    Path("docs/reports/task_385_canonical_continuation_engine/canonical_continuation_lifecycle_summary.csv"),
    Path("docs/reports/task_386_canonical_continuation_quality/canonical_lifecycle_quality_panel.csv"),
    Path("docs/reports/task_387_canonical_continuation_oos_overlay/canonical_oos_quality_panel.csv"),
)


def main() -> None:
    source_files = [path for path in SOURCE_EVENT_CANDIDATES if path.exists()]
    outcome_files = [path for path in OUTCOME_CANDIDATES if path.exists()]

    audit_rows = []
    bridge_rows = []
    source_cache = {path: _read_source_event_lifecycle_index(path) for path in sorted(set(source_files))}
    outcome_cache = {path: _read_outcome_lifecycles(path) for path in sorted(set(outcome_files))}
    for source_path, source_index in source_cache.items():
        source_lifecycles = set(source_index)
        for outcome_path, outcome_lifecycles in outcome_cache.items():
            intersection = source_lifecycles & outcome_lifecycles
            pair_bridge_rows = _bridge_rows_from_intersection(source_path, source_index, outcome_path, intersection)
            bridge_rows.extend(pair_bridge_rows)
            allowed = bool(pair_bridge_rows)
            audit_rows.append(
                L3ExplicitBridgeSearchAuditRow(
                    source_event_path=source_path.as_posix(),
                    outcome_path=outcome_path.as_posix(),
                    source_event_lifecycle_row_count=len(source_lifecycles),
                    outcome_lifecycle_row_count=len(outcome_lifecycles),
                    exact_lifecycle_intersection_count=len(intersection),
                    bridge_row_count=len(pair_bridge_rows),
                    inferred_matching_required_flag=int(not allowed),
                    allowed_for_calibration_flag=int(allowed),
                    rejection_reason="exact_lifecycle_bridge_available" if allowed else "no_exact_lifecycle_intersection",
                )
            )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(AUDIT_PATH, explicit_bridge_search_rows_to_dicts(audit_rows))
    _write_csv(BRIDGE_PATH, explicit_bridge_rows_to_dicts(_dedupe_bridge_rows(bridge_rows)), _bridge_fieldnames())
    buildable = sum(1 for row in audit_rows if row.allowed_for_calibration_flag)
    print(
        "[L3_EXPLICIT_BRIDGE_SEARCH] "
        f"source_candidates={len(source_cache)} outcome_candidates={len(outcome_cache)} "
        f"buildable_pairs={buildable} bridge_rows={len(_dedupe_bridge_rows(bridge_rows))}"
    )


def _read_source_event_lifecycle_index(path: Path) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            source_event_id = _text(record.get("source_event_id"))
            lifecycle_id = _text(record.get("lifecycle_id"))
            if source_event_id and lifecycle_id:
                index.setdefault(lifecycle_id, set()).add(source_event_id)
    return index


def _read_outcome_lifecycles(path: Path) -> set[str]:
    lifecycles: set[str] = set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            lifecycle_id = _text(record.get("lifecycle_id"))
            if lifecycle_id and any(_text(record.get(column)) for column in OUTCOME_VALUE_COLUMNS):
                lifecycles.add(lifecycle_id)
    return lifecycles


def _bridge_rows_from_intersection(
    source_path: Path,
    source_index: dict[str, set[str]],
    outcome_path: Path,
    intersection: set[str],
) -> list[L3OutcomeBridgeRow]:
    rows: list[L3OutcomeBridgeRow] = []
    for lifecycle_id in sorted(intersection):
        for idx, source_event_id in enumerate(sorted(source_index[lifecycle_id]), start=1):
            rows.append(
                L3OutcomeBridgeRow(
                    bridge_id=(
                        f"l3_bridge:{_stable_id(source_path.as_posix() + '|' + outcome_path.as_posix())}:"
                        f"{source_event_id}:{lifecycle_id}:{idx}"
                    ),
                    meaning_id="",
                    l2_primitive_id="",
                    source_receipt_id=source_event_id,
                    outcome_source_table=outcome_path.as_posix(),
                    outcome_bridge_key=lifecycle_id,
                    lifecycle_id=lifecycle_id,
                    continuation_id="",
                    bridge_method=L3OutcomeBridgeMethod.DIRECT_SOURCE_RECEIPT_ID,
                    bridge_source_artifact=f"{source_path.as_posix()}|{outcome_path.as_posix()}",
                    inferred_matching_used_flag=0,
                )
            )
    return rows


def _dedupe_bridge_rows(rows: list[L3OutcomeBridgeRow]) -> tuple[L3OutcomeBridgeRow, ...]:
    deduped: dict[tuple[str, str, str], L3OutcomeBridgeRow] = {}
    for row in rows:
        deduped[(row.source_receipt_id, row.outcome_source_table, row.outcome_bridge_key)] = row
    return tuple(deduped[key] for key in sorted(deduped))


def _bridge_fieldnames() -> list[str]:
    return [field.name for field in fields(L3OutcomeBridgeRow)]


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


if __name__ == "__main__":
    main()
