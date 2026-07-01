from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4168"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_4168_l3_gap_reason_narrowing_recall_traceability"

TRIAGE_CSV = "task_4168_l3_gap_triage.csv"
TRIAGE_JSON = "task_4168_l3_gap_triage.json"
RECONCILIATION_JSON = "task_4168_l3_l4_gap_reconciliation.json"
RECONCILIATION_DETAIL_CSV = "task_4168_l3_l4_gap_reconciliation_detail.csv"
PRIORITY_LEDGER_JSON = "task_4168_p1_p2_priority_ledger.json"
BLOCKER_TAXONOMY_CSV = "task_4168_l4_blocker_taxonomy.csv"
EVENT_IDENTITY_JSON = "task_4168_event_identity_audit.json"
L0_STATUS_JSON = "task_4168_l0_status_snapshot.json"

ALLOWED_TRACE_STATUS = {
    "TRACE_OK",
    "TRACE_PARTIAL",
    "TRACE_REFERENCE_MISSING",
    "TRACE_UNAVAILABLE",
    "TRACEABLE",
    "PARTIAL",
    "PARTIAL_TRACE",
    "PARTIAL_TRACEABLE",
    "UNAVAILABLE",
    "UNKNOWN",
    "UNKNOWN_BLOCKER",
}

EXPECTED_GAP_REASONS = {
    "L2_BLOCKED_CANDIDATES_PRESENT",
    "NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE",
    "NEWSWIRE_RECALL_REVIEW_ENTITY_FEATURE_PENDING",
}

EXPECTED_RECONCILIATION_STATUSES = {
    "EXPECTED",
    "EXPECTED_DIFFERENCE",
    "EXPECTED_MISMATCH",
    "RECONCILED_EXPECTED",
}

FIXED_RECONCILIATION_STATUSES = {
    "FIXED",
    "RECONCILED_FIXED",
    "RESOLVED",
    "RESOLVED_FIXED",
}

FALSE_VALUES = {False, 0, "0", "false", "False", "FALSE", "no", "No", "NO"}
TRUE_VALUES = {True, 1, "1", "true", "True", "TRUE", "yes", "Yes", "YES"}


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path, failures: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"malformed JSON: {rel(path)}: {exc.msg} at line {exc.lineno} column {exc.colno}")
    except OSError as exc:
        failures.append(f"cannot read JSON: {rel(path)}: {exc}")
    return None


def load_csv(path: Path, failures: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                failures.append(f"malformed CSV: {rel(path)} has no header")
                return [], []
            if len(set(reader.fieldnames)) != len(reader.fieldnames):
                failures.append(f"malformed CSV: {rel(path)} has duplicate header columns")
                return reader.fieldnames, []
            return reader.fieldnames, list(reader)
    except csv.Error as exc:
        failures.append(f"malformed CSV: {rel(path)}: {exc}")
    except UnicodeDecodeError as exc:
        failures.append(f"malformed CSV encoding: {rel(path)}: {exc}")
    except OSError as exc:
        failures.append(f"cannot read CSV: {rel(path)}: {exc}")
    return [], []


def walk_dicts(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(walk_dicts(child))
    elif isinstance(value, list):
        for item in value:
            found.extend(walk_dicts(item))
    return found


def dict_rows_with_keys(value: Any, keys: set[str]) -> list[dict[str, Any]]:
    return [item for item in walk_dicts(value) if keys.issubset(set(item))]


def check_safety_mapping(label: str, mapping: dict[str, Any], failures: list[str]) -> bool:
    saw_field = False
    if "negative_evidence_allowed" in mapping:
        saw_field = True
        if mapping.get("negative_evidence_allowed") not in FALSE_VALUES:
            failures.append(
                f"{label} negative_evidence_allowed must be false/0, got {mapping.get('negative_evidence_allowed')!r}"
            )
    if "diagnostic_only" in mapping:
        saw_field = True
        if mapping.get("diagnostic_only") not in TRUE_VALUES:
            failures.append(f"{label} diagnostic_only must be true/1, got {mapping.get('diagnostic_only')!r}")
    return saw_field


def check_safety_in_json(label: str, data: Any, failures: list[str]) -> None:
    mappings = walk_dicts(data)
    saw_negative = any("negative_evidence_allowed" in item for item in mappings)
    saw_diagnostic = any("diagnostic_only" in item for item in mappings)
    for idx, item in enumerate(mappings):
        if "negative_evidence_allowed" in item or "diagnostic_only" in item:
            check_safety_mapping(f"{label} object[{idx}]", item, failures)
    if saw_negative or saw_diagnostic:
        return

    # Summary-only JSON artifacts may carry safety as zero-count authority fields
    # instead of row-level diagnostic flags.
    safety_items = [item for item in mappings if isinstance(item.get("safety"), dict)]
    safety_dicts = [item["safety"] for item in safety_items]
    if isinstance(data, dict) and isinstance(data.get("safety"), dict):
        safety_dicts.append(data["safety"])
    for safety in safety_dicts:
        deployment = str(safety.get("deployment", "")).upper()
        if deployment and "DIAGNOSTIC_ONLY" not in deployment:
            failures.append(f"{label} safety deployment is not diagnostic-only: {safety.get('deployment')!r}")
        for key in (
            "broker_mutation_count",
            "live_order_count",
            "order_count",
            "paper_promotion_count",
            "trading_authority_opened_rows",
            "paper_live_broker_order_opened_rows",
        ):
            if key in safety:
                try:
                    value = int(safety[key])
                except (TypeError, ValueError):
                    failures.append(f"{label} safety {key} is not numeric: {safety[key]!r}")
                    continue
                if value != 0:
                    failures.append(f"{label} safety {key} must be 0, got {value}")


def check_csv_core_columns(fieldnames: list[str], failures: list[str]) -> None:
    columns = set(fieldnames)
    required = {
        "gap_reason",
        "gap_subreason",
        "source",
        "l0_reference",
        "l1_reference",
        "l2_reference",
        "l3_gap_id",
        "trace_status",
        "negative_evidence_allowed",
        "diagnostic_only",
    }
    missing = sorted(required - columns)
    if missing:
        failures.append(f"{TRIAGE_CSV} missing core columns: {', '.join(missing)}")
    if not ({"event_date", "month"} & columns):
        failures.append(f"{TRIAGE_CSV} missing core date column: event_date or month")
    if not ({"entity", "ticker"} & columns):
        failures.append(f"{TRIAGE_CSV} missing core entity column: entity or ticker")


def check_trace_statuses(label: str, values: list[Any], failures: list[str]) -> None:
    unknown = sorted({str(value).strip() for value in values if str(value).strip() not in ALLOWED_TRACE_STATUS})
    if unknown:
        failures.append(f"{label} unknown trace_status values: {', '.join(unknown)}")


def check_triage_csv(path: Path, passes: list[str], failures: list[str]) -> None:
    fieldnames, rows = load_csv(path, failures)
    if not fieldnames:
        return
    check_csv_core_columns(fieldnames, failures)
    if not rows:
        failures.append(f"{TRIAGE_CSV} has no data rows")
        return

    check_trace_statuses(TRIAGE_CSV, [row.get("trace_status", "") for row in rows], failures)
    for line_number, row in enumerate(rows, start=2):
        check_safety_mapping(f"{TRIAGE_CSV} line {line_number}", row, failures)
        if not row.get("l3_gap_id", "").strip():
            failures.append(f"{TRIAGE_CSV} line {line_number} missing l3_gap_id")
        if not row.get("gap_reason", "").strip():
            failures.append(f"{TRIAGE_CSV} line {line_number} missing gap_reason")
        if not row.get("gap_subreason", "").strip():
            failures.append(f"{TRIAGE_CSV} line {line_number} missing gap_subreason")

    present_reasons = {row.get("gap_reason", "").strip() for row in rows}
    missing_reasons = sorted(EXPECTED_GAP_REASONS - present_reasons)
    if missing_reasons:
        failures.append(f"{TRIAGE_CSV} missing expected gap reasons: {', '.join(missing_reasons)}")
    passes.append(f"{TRIAGE_CSV} rows={len(rows)}")


def check_triage_json(path: Path, passes: list[str], failures: list[str]) -> None:
    data = load_json(path, failures)
    if data is None:
        return
    check_safety_in_json(TRIAGE_JSON, data, failures)

    row_like = dict_rows_with_keys(data, {"l3_gap_id", "gap_reason", "trace_status"})
    if row_like:
        check_trace_statuses(TRIAGE_JSON, [row.get("trace_status", "") for row in row_like], failures)
        passes.append(f"{TRIAGE_JSON} row_objects={len(row_like)}")
    elif isinstance(data, dict):
        # Summary-shaped JSON is acceptable if it carries explicit counts and safety fields.
        if not any(key in data for key in ("gap_reason_counts", "gap_subreason_counts", "triage_rows", "total_gap_rows")):
            failures.append(f"{TRIAGE_JSON} lacks row objects or summary count fields")
        else:
            passes.append(f"{TRIAGE_JSON} summary_shape")
    else:
        failures.append(f"{TRIAGE_JSON} must be an object or contain row objects")


def find_number(mapping: dict[str, Any], names: tuple[str, ...]) -> int | None:
    for name in names:
        if name in mapping:
            try:
                return int(mapping[name])
            except (TypeError, ValueError):
                return None
    return None


def check_reconciliation(path: Path, passes: list[str], failures: list[str]) -> None:
    data = load_json(path, failures)
    if data is None:
        return
    if not isinstance(data, dict):
        failures.append(f"{RECONCILIATION_JSON} must be a JSON object")
        return
    check_safety_in_json(RECONCILIATION_JSON, data, failures)

    status = str(
        data.get("reconciliation_status")
        or data.get("status")
        or data.get("outcome")
        or data.get("result")
        or ""
    ).strip()
    status_upper = status.upper()
    status_ok = (
        status_upper in EXPECTED_RECONCILIATION_STATUSES
        or status_upper in FIXED_RECONCILIATION_STATUSES
        or "EXPECTED" in status_upper
        or "FIXED" in status_upper
    )

    l3_count = find_number(data, ("l3_coverage_gap_count", "l3_coverage_gaps", "l3_gap_count", "l3_coverage_gap_rows"))
    l4_count = find_number(
        data,
        (
            "l4_l3_coverage_gap_count",
            "l4_blocker_count",
            "l4_l3_coverage_gap_blocker_count",
            "l4_l3_coverage_gap_blockers",
        ),
    )
    delta = find_number(data, ("delta", "count_delta", "l4_minus_l3", "gap_count_delta", "difference_l4_minus_l3"))
    if delta is None and l3_count is not None and l4_count is not None:
        delta = l4_count - l3_count

    count_ok = delta in {0, 3}
    if not (status_ok or count_ok):
        failures.append(
            f"{RECONCILIATION_JSON} reconciliation is neither expected nor fixed "
            f"(status={status!r}, delta={delta!r})"
        )
    if delta == 3:
        passes.append(f"{RECONCILIATION_JSON} expected_delta=3")
    elif delta == 0:
        passes.append(f"{RECONCILIATION_JSON} fixed_delta=0")
    elif status_ok:
        passes.append(f"{RECONCILIATION_JSON} status={status_upper}")


def check_optional_ledger(path: Path, passes: list[str], failures: list[str]) -> None:
    if not path.exists():
        passes.append(f"{PRIORITY_LEDGER_JSON} absent_optional")
        return
    data = load_json(path, failures)
    if data is None:
        return
    check_safety_in_json(PRIORITY_LEDGER_JSON, data, failures)
    passes.append(f"{PRIORITY_LEDGER_JSON} present")


def check_csv_required_columns(
    path: Path,
    label: str,
    required_columns: set[str],
    passes: list[str],
    failures: list[str],
) -> None:
    fieldnames, rows = load_csv(path, failures)
    if not fieldnames:
        return
    missing = sorted(required_columns - set(fieldnames))
    if missing:
        failures.append(f"{label} missing columns: {', '.join(missing)}")
    if not rows:
        failures.append(f"{label} has no data rows")
        return
    for line_number, row in enumerate(rows, start=2):
        check_safety_mapping(f"{label} line {line_number}", row, failures)
    passes.append(f"{label} rows={len(rows)}")


def check_event_identity(path: Path, passes: list[str], failures: list[str]) -> None:
    data = load_json(path, failures)
    if data is None:
        return
    if not isinstance(data, dict):
        failures.append(f"{EVENT_IDENTITY_JSON} must be a JSON object")
        return
    check_safety_in_json(EVENT_IDENTITY_JSON, data, failures)
    if data.get("status") not in {"AUDIT_PASS", "DUPLICATE_GAP_ID_BLOCKER"}:
        failures.append(f"{EVENT_IDENTITY_JSON} unknown status: {data.get('status')!r}")
    if int(data.get("duplicate_l3_gap_ids", -1)) != 0:
        failures.append(f"{EVENT_IDENTITY_JSON} duplicate_l3_gap_ids must be 0")
    passes.append(f"{EVENT_IDENTITY_JSON} status={data.get('status')}")


def check_l0_status_snapshot(path: Path, passes: list[str], failures: list[str]) -> None:
    data = load_json(path, failures)
    if data is None:
        return
    if not isinstance(data, dict):
        failures.append(f"{L0_STATUS_JSON} must be a JSON object")
        return
    check_safety_in_json(L0_STATUS_JSON, data, failures)
    newswire = data.get("public_newswire_backfill", {})
    if isinstance(newswire, dict) and int(newswire.get("failed_units") or 0) != 0:
        failures.append(f"{L0_STATUS_JSON} public_newswire_backfill failed_units must be 0")
    context = data.get("public_context_news_backfill", {})
    if isinstance(context, dict) and context.get("pending_units_by_source") and not context.get("explicit_blocker"):
        failures.append(f"{L0_STATUS_JSON} pending public context units must have explicit_blocker")
    passes.append(f"{L0_STATUS_JSON} present")


def emit(passes: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS"
    payload = {
        "task_id": TASK_ID,
        "result": result,
        "passes": passes,
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TASK-4168 L3 gap triage artifacts.")
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    args = parser.parse_args()

    artifact_dir = args.artifact_dir.resolve()
    passes: list[str] = []
    failures: list[str] = []

    required = [
        artifact_dir / TRIAGE_CSV,
        artifact_dir / TRIAGE_JSON,
        artifact_dir / RECONCILIATION_JSON,
        artifact_dir / RECONCILIATION_DETAIL_CSV,
        artifact_dir / BLOCKER_TAXONOMY_CSV,
        artifact_dir / EVENT_IDENTITY_JSON,
        artifact_dir / L0_STATUS_JSON,
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing required file: {rel(path)}" for path in missing)
        return emit(passes, failures)

    check_triage_csv(artifact_dir / TRIAGE_CSV, passes, failures)
    check_triage_json(artifact_dir / TRIAGE_JSON, passes, failures)
    check_reconciliation(artifact_dir / RECONCILIATION_JSON, passes, failures)
    check_csv_required_columns(
        artifact_dir / RECONCILIATION_DETAIL_CSV,
        RECONCILIATION_DETAIL_CSV,
        {"blocker_grain", "match_status", "related_artifact_id", "negative_evidence_allowed", "diagnostic_only"},
        passes,
        failures,
    )
    check_csv_required_columns(
        artifact_dir / BLOCKER_TAXONOMY_CSV,
        BLOCKER_TAXONOMY_CSV,
        {"blocker_type", "blocker_scope", "count", "negative_evidence_allowed", "diagnostic_only"},
        passes,
        failures,
    )
    check_event_identity(artifact_dir / EVENT_IDENTITY_JSON, passes, failures)
    check_l0_status_snapshot(artifact_dir / L0_STATUS_JSON, passes, failures)
    check_optional_ledger(artifact_dir / PRIORITY_LEDGER_JSON, passes, failures)

    if not failures:
        passes.append("safety_fields_diagnostic_only_confirmed")
    return emit(passes, failures)


if __name__ == "__main__":
    sys.exit(main())
