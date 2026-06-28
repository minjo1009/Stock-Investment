from __future__ import annotations

import csv
import json
import os
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping


OUT_PATH = Path("docs/reports/task_l3_calibration_rule_migration/l3_task742_schema_search_audit.csv")
CANONICAL_BRIDGE_PATH = Path(
    "docs/reports/task_l3_calibration_rule_migration/l3_explicit_source_event_outcome_bridge.csv"
)

SEARCH_ROOTS = (Path("."),)

PRUNE_REL_PREFIXES = (
    ".dvc",
    ".git",
    ".obsidian",
    "data/raw",
    "frontend",
    "frontend_data",
    "graphify-out",
)

SKIP_DIR_NAMES = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
SCAN_SUFFIXES = {".csv", ".tsv", ".jsonl", ".json"}
DB_SUFFIXES = {".db", ".sqlite", ".sqlite3"}

TASK742_OUTPUT_COLUMNS = {
    "interpretation_state",
    "economic_direction_hint",
    "confidence_band",
    "relation_ready_tier",
}
TASK742_CORE_COLUMNS = TASK742_OUTPUT_COLUMNS | {
    "source_circuit",
    "needed_confirmation",
    "ambiguity_flags",
    "hard_blocker_flags",
    "soft_uncertainty_flags",
}
PACKET_KEY_COLUMNS = {
    "task742_packet_id",
    "packet_id",
    "meaning_id",
    "source_event_id",
    "source_receipt_id",
}
LINEAGE_COLUMNS = {
    "task740_primitive_id",
    "task741_packet_id",
    "raw_text_path",
    "resolver_state",
    "meaning_state",
    "backtest_eligible_flag",
}
OUTCOME_COLUMNS = {
    "outcome_bridge_key",
    "lifecycle_id",
    "continuation_id",
    "win_flag",
    "positive_return_flag",
    "return_from_entry",
    "net_return_from_entry",
    "forward_return_pct",
}


@dataclass(frozen=True)
class Task742SchemaSearchAuditRow:
    candidate_path: str
    artifact_type: str
    row_count: int
    task742_core_columns: str
    packet_key_columns: str
    lineage_columns: str
    outcome_columns: str
    task742_output_column_count: int
    candidate_source_event_id_count: int
    canonical_bridge_source_receipt_id_count: int
    source_event_overlap_with_canonical_bridge_count: int
    task742_packet_schema_flag: int
    task742_rule_input_schema_flag: int
    task740_741_lineage_schema_flag: int
    allowed_as_task742_packet_artifact_flag: int
    allowed_for_task742_calibration_flag: int
    inferred_matching_required_flag: int
    rejection_reason: str


def main() -> None:
    rows = build_audit_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(OUT_PATH, [asdict(row) for row in rows])
    allowed = sum(row.allowed_for_task742_calibration_flag for row in rows)
    packet_candidates = sum(row.allowed_as_task742_packet_artifact_flag for row in rows)
    print(
        "[L3_TASK742_SCHEMA_SEARCH] "
        f"rows={len(rows)} packet_candidates={packet_candidates} calibration_allowed={allowed} out={OUT_PATH}"
    )


def build_audit_rows() -> tuple[Task742SchemaSearchAuditRow, ...]:
    canonical_bridge_ids = _read_bridge_source_receipt_ids(CANONICAL_BRIDGE_PATH)
    rows: list[Task742SchemaSearchAuditRow] = []
    for candidate in _iter_schema_candidates(canonical_bridge_ids):
        rows.append(candidate)
    if rows:
        return tuple(sorted(rows, key=lambda row: row.candidate_path))
    return (
        Task742SchemaSearchAuditRow(
            candidate_path="NO_TASK742_SCHEMA_MATCH_FOUND",
            artifact_type="sentinel",
            row_count=0,
            task742_core_columns="",
            packet_key_columns="",
            lineage_columns="",
            outcome_columns="",
            task742_output_column_count=0,
            candidate_source_event_id_count=0,
            canonical_bridge_source_receipt_id_count=len(canonical_bridge_ids),
            source_event_overlap_with_canonical_bridge_count=0,
            task742_packet_schema_flag=0,
            task742_rule_input_schema_flag=0,
            task740_741_lineage_schema_flag=0,
            allowed_as_task742_packet_artifact_flag=0,
            allowed_for_task742_calibration_flag=0,
            inferred_matching_required_flag=1,
            rejection_reason="no_local_csv_json_or_db_schema_matches_task742_contract",
        ),
    )


def _iter_schema_candidates(
    canonical_bridge_ids: set[str],
) -> Iterable[Task742SchemaSearchAuditRow]:
    root = Path(".").resolve()
    for path in _iter_data_files(root):
        columns = _columns_for_file(path)
        if not columns:
            continue
        row = _audit_candidate(
            path.relative_to(root).as_posix(),
            path.suffix.lower().lstrip("."),
            columns,
            canonical_bridge_ids,
            records_loader=lambda path=path: _records_for_file(path),
            row_counter=lambda path=path: _count_file_rows(path),
        )
        if row is not None:
            yield row
    for db_path, table_name, columns in _iter_db_tables(root):
        relative = db_path.relative_to(root).as_posix()
        row = _audit_candidate(
            f"{relative}::{table_name}",
            "sqlite_table",
            columns,
            canonical_bridge_ids,
            records_loader=lambda db_path=db_path, table_name=table_name: _records_for_sqlite_table(
                db_path, table_name
            ),
            row_counter=lambda db_path=db_path, table_name=table_name: _count_sqlite_rows(
                db_path, table_name
            ),
        )
        if row is not None:
            yield row


def _audit_candidate(
    candidate_path: str,
    artifact_type: str,
    columns: Iterable[str],
    canonical_bridge_ids: set[str],
    *,
    records_loader,
    row_counter,
) -> Task742SchemaSearchAuditRow | None:
    normalized = _normalize_columns(columns)
    core = sorted(normalized & TASK742_CORE_COLUMNS)
    packet_keys = sorted(normalized & PACKET_KEY_COLUMNS)
    lineage = sorted(normalized & LINEAGE_COLUMNS)
    outcome = sorted(normalized & OUTCOME_COLUMNS)
    output_count = len(normalized & TASK742_OUTPUT_COLUMNS)

    has_source_circuit = "source_circuit" in normalized
    has_packet_key = bool(packet_keys)
    has_lifecycle = "lifecycle_id" in normalized
    packet_schema = has_source_circuit and has_packet_key and output_count >= 2
    rule_input_schema = has_source_circuit and has_packet_key and (has_lifecycle or bool(lineage))
    task740_741_schema = (
        "source_event_id" in normalized
        and has_lifecycle
        and bool(set(lineage) | (normalized & {"resolver_state", "meaning_state"}))
    )

    if not (packet_schema or rule_input_schema or task740_741_schema or core):
        return None

    source_event_ids = _source_event_ids(records_loader(), packet_keys)
    overlap = source_event_ids & canonical_bridge_ids
    allowed_packet = int(packet_schema)
    allowed_calibration = int(packet_schema and bool(overlap))
    inferred_required = int(not allowed_calibration)

    return Task742SchemaSearchAuditRow(
        candidate_path=candidate_path,
        artifact_type=artifact_type,
        row_count=row_counter(),
        task742_core_columns="|".join(core),
        packet_key_columns="|".join(packet_keys),
        lineage_columns="|".join(lineage),
        outcome_columns="|".join(outcome),
        task742_output_column_count=output_count,
        candidate_source_event_id_count=len(source_event_ids),
        canonical_bridge_source_receipt_id_count=len(canonical_bridge_ids),
        source_event_overlap_with_canonical_bridge_count=len(overlap),
        task742_packet_schema_flag=int(packet_schema),
        task742_rule_input_schema_flag=int(rule_input_schema),
        task740_741_lineage_schema_flag=int(task740_741_schema),
        allowed_as_task742_packet_artifact_flag=allowed_packet,
        allowed_for_task742_calibration_flag=allowed_calibration,
        inferred_matching_required_flag=inferred_required,
        rejection_reason=_rejection_reason(packet_schema, bool(overlap), core, packet_keys),
    )


def _iter_data_files(root: Path) -> Iterable[Path]:
    for search_root in SEARCH_ROOTS:
        absolute_root = search_root if search_root.is_absolute() else root / search_root
        if not absolute_root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(absolute_root):
            current = Path(dirpath)
            rel = current.relative_to(root).as_posix() if current.is_relative_to(root) else current.as_posix()
            if any(rel == prefix or rel.startswith(f"{prefix}/") for prefix in PRUNE_REL_PREFIXES):
                dirnames[:] = []
                continue
            dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
            for name in filenames:
                path = current / name
                if path.suffix.lower() in SCAN_SUFFIXES:
                    yield path


def _iter_db_tables(root: Path) -> Iterable[tuple[Path, str, tuple[str, ...]]]:
    db_paths: list[Path] = []
    db_paths.extend(path for path in root.iterdir() if path.is_file() and path.suffix.lower() in DB_SUFFIXES)
    data_root = root / "data"
    if data_root.exists():
        db_paths.extend(path for path in data_root.rglob("*") if path.is_file() and path.suffix.lower() in DB_SUFFIXES)
    for db_path in sorted(set(db_paths)):
        try:
            with sqlite3.connect(db_path) as conn:
                tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                for table in tables:
                    columns = tuple(row[1] for row in conn.execute(f'PRAGMA table_info("{table}")'))
                    yield db_path, table, columns
        except sqlite3.Error:
            continue


def _columns_for_file(path: Path) -> tuple[str, ...]:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with path.open(newline="", encoding=encoding) as handle:
                    return tuple(next(csv.reader(handle, delimiter=delimiter), ()))
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
    if suffix == ".jsonl":
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with path.open(encoding=encoding) as handle:
                    for line in handle:
                        line = line.strip()
                        if line:
                            obj = json.loads(line)
                            return tuple(obj.keys()) if isinstance(obj, dict) else ()
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
    if suffix == ".json" and path.stat().st_size <= 20_000_000:
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with path.open(encoding=encoding) as handle:
                    obj = json.load(handle)
                if isinstance(obj, dict):
                    return tuple(obj.keys())
                if isinstance(obj, list) and obj and isinstance(obj[0], dict):
                    return tuple(obj[0].keys())
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
    return ()


def _records_for_file(path: Path) -> tuple[Mapping[str, object], ...]:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with path.open(newline="", encoding=encoding) as handle:
                    return tuple(csv.DictReader(handle, delimiter=delimiter))
            except (OSError, UnicodeDecodeError, csv.Error):
                continue
    if suffix == ".jsonl":
        records: list[Mapping[str, object]] = []
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with path.open(encoding=encoding) as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            records.append(obj)
                return tuple(records)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                records.clear()
                continue
    if suffix == ".json" and path.stat().st_size <= 20_000_000:
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with path.open(encoding=encoding) as handle:
                    obj = json.load(handle)
                if isinstance(obj, dict):
                    return (obj,)
                if isinstance(obj, list):
                    return tuple(item for item in obj if isinstance(item, dict))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
    return ()


def _records_for_sqlite_table(db_path: Path, table_name: str) -> tuple[Mapping[str, object], ...]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return tuple(dict(row) for row in conn.execute(f'SELECT * FROM "{table_name}"'))


def _count_file_rows(path: Path) -> int:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with path.open(encoding=encoding, newline="") as handle:
                    return max(sum(1 for _ in handle) - 1, 0)
            except (OSError, UnicodeDecodeError):
                continue
    if suffix == ".jsonl":
        for encoding in ("utf-8-sig", "utf-8", "cp949"):
            try:
                with path.open(encoding=encoding) as handle:
                    return sum(1 for line in handle if line.strip())
            except (OSError, UnicodeDecodeError):
                continue
    return len(_records_for_file(path))


def _count_sqlite_rows(db_path: Path, table_name: str) -> int:
    try:
        with sqlite3.connect(db_path) as conn:
            return int(conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])
    except sqlite3.Error:
        return -1


def _source_event_ids(records: Iterable[Mapping[str, object]], packet_keys: Iterable[str]) -> set[str]:
    ids: set[str] = set()
    for record in records:
        normalized = {str(key).strip().lower(): value for key, value in record.items()}
        for column in ("source_event_id", "source_receipt_id", "task742_packet_id", "packet_id", "meaning_id"):
            if column not in packet_keys:
                continue
            value = _text(normalized.get(column))
            if value:
                ids.add(value)
    return ids


def _read_bridge_source_receipt_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            value
            for row in csv.DictReader(handle)
            if (value := _text(row.get("source_receipt_id")))
        }


def _normalize_columns(columns: Iterable[str]) -> set[str]:
    return {str(column).strip().lower() for column in columns if str(column).strip()}


def _rejection_reason(
    packet_schema: bool,
    has_overlap: bool,
    core_columns: list[str],
    packet_key_columns: list[str],
) -> str:
    if packet_schema and has_overlap:
        return "eligible_task742_packet_exact_source_event_bridge"
    if packet_schema:
        return "task742_packet_schema_found_but_no_exact_source_event_overlap"
    if not core_columns:
        return "no_task742_core_columns"
    if "source_circuit" not in core_columns:
        return "missing_source_circuit"
    if not packet_key_columns:
        return "missing_packet_or_source_event_key"
    return "partial_task742_schema_not_packet_output"


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else list(Task742SchemaSearchAuditRow.__dataclass_fields__)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


if __name__ == "__main__":
    main()
