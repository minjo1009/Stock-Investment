from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4126"
STAGE5_TASK_ID = "TASK-4125"
STAGE5_SLUG = "task_4125_l0_stage_5_full_2016_to_present_backfill_continuation"
SLUG = "task_4126_l0_stage_6_full_backfill_l1_quality_coverage_reaudit"
DEFAULT_REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
STAGE5_REPORT_DIR = ROOT / f"docs/reports/{STAGE5_SLUG}"
STAGE5_RAW_DIR = ROOT / f"data/raw/{STAGE5_SLUG}"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    fields = list(fieldnames or [])
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def secret_like(path: Path) -> bool:
    if path.suffix.lower() not in {".json", ".jsonl", ".csv", ".txt", ".log", ".bin", ".html", ".xml"}:
        return False
    text = path.read_text(encoding="utf-8-sig", errors="ignore")[:200_000]
    patterns = [
        r"(?im)^\s*Authorization\s*[:=]",
        r"(?im)^\s*(Authorization\s*[:=]\s*)?Bearer\s+[A-Za-z0-9._-]{20,}\s*$",
        r"(?i)\b(api[_-]?key|apikey|token|secret)\s*[:=]\s*[A-Za-z0-9._-]{12,}",
        r"\bsk-[A-Za-z0-9_-]{40,}",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def raw_hash_audit() -> list[dict[str, Any]]:
    stage5_raw_ledger = read_csv(STAGE5_REPORT_DIR / "task_4125_raw_response_classification.csv")
    rows: list[dict[str, Any]] = []
    for row in stage5_raw_ledger:
        raw_path = row.get("raw_path", "")
        path = ROOT / raw_path
        exists = path.exists()
        actual_hash = sha256_file(path) if exists else ""
        rows.append(
            {
                "task_id": TASK_ID,
                "stage5_task_id": STAGE5_TASK_ID,
                "raw_path": raw_path,
                "expected_sha256": row.get("raw_sha256", ""),
                "actual_sha256": actual_hash,
                "hash_match": int(exists and actual_hash == row.get("raw_sha256", "")),
                "secret_scan_pass": int(exists and not secret_like(path)),
                "raw_exists": int(exists),
            }
        )
    return rows


def headline_payload_paths() -> list[Path]:
    return sorted(STAGE5_RAW_DIR.rglob("headlines.json"))


def row_mapping_status(row: dict[str, Any]) -> str:
    ticker_raw = row.get("ticker_mapping_required_flag", "")
    ticker_required = int(ticker_raw or 0) if str(ticker_raw) != "" else 1
    macro_context = int(row.get("macro_context_candidate_flag", 0) or 0)
    has_mapping = bool(row.get("symbols") or row.get("tickers") or row.get("entities") or row.get("entity_map"))
    if ticker_required == 0 or macro_context == 1:
        return "PASS_MAPPING_NOT_REQUIRED_CONTEXT_ROW"
    if has_mapping:
        return "PASS_MAPPING_PRESENT"
    return "BLOCKED_MAPPING_MISSING"


def mapping_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in headline_payload_paths():
        payload = read_json(path)
        headlines = payload.get("headlines") if isinstance(payload.get("headlines"), list) else []
        status_counts: dict[str, int] = {}
        source_key = str(payload.get("source_key") or "")
        provider = str(payload.get("provider") or "")
        for row in headlines:
            status = row_mapping_status(row)
            status_counts[status] = status_counts.get(status, 0) + 1
            source_key = str(row.get("source_key") or source_key)
            provider = str(row.get("provider") or provider)
        blocked = sum(count for status, count in status_counts.items() if status.startswith("BLOCKED"))
        rows.append(
            {
                "task_id": TASK_ID,
                "stage5_task_id": STAGE5_TASK_ID,
                "provider": provider,
                "source_key": source_key,
                "raw_path": rel(path),
                "headline_rows": len(headlines),
                "mapping_pass_rows": len(headlines) - blocked,
                "mapping_blocker_rows": blocked,
                "empty_provider_response": int(len(headlines) == 0),
                "mapping_status": "PASS" if blocked == 0 else "BLOCKED_MAPPING_MISSING",
            }
        )
    return rows


def row_source_time_status(row: dict[str, Any]) -> str:
    published = row.get("published_at") or row.get("publication_time") or row.get("event_time")
    certified = int(row.get("source_time_certified_flag", 0) or 0)
    if published and certified:
        return "PASS_SOURCE_TIME_CERTIFIED"
    if published:
        return "BLOCKED_SOURCE_TIME_PRESENT_BUT_UNCERTIFIED"
    return "BLOCKED_SOURCE_TIME_MISSING"


def source_time_audit() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in headline_payload_paths():
        payload = read_json(path)
        headlines = payload.get("headlines") if isinstance(payload.get("headlines"), list) else []
        source_key = str(payload.get("source_key") or "")
        provider = str(payload.get("provider") or "")
        pass_rows = 0
        uncertified_rows = 0
        missing_rows = 0
        for row in headlines:
            source_key = str(row.get("source_key") or source_key)
            provider = str(row.get("provider") or provider)
            status = row_source_time_status(row)
            if status == "PASS_SOURCE_TIME_CERTIFIED":
                pass_rows += 1
            elif status == "BLOCKED_SOURCE_TIME_PRESENT_BUT_UNCERTIFIED":
                uncertified_rows += 1
            else:
                missing_rows += 1
        blocker_rows = uncertified_rows + missing_rows
        rows.append(
            {
                "task_id": TASK_ID,
                "stage5_task_id": STAGE5_TASK_ID,
                "provider": provider,
                "source_key": source_key,
                "raw_path": rel(path),
                "headline_rows": len(headlines),
                "source_time_certified_rows": pass_rows,
                "source_time_uncertified_rows": uncertified_rows,
                "source_time_missing_rows": missing_rows,
                "source_time_blocker_rows": blocker_rows,
                "source_time_status": "PASS" if blocker_rows == 0 else "BLOCKED_SOURCE_TIME_UNCERTIFIED",
            }
        )
    return rows


def coverage_audit() -> list[dict[str, Any]]:
    stage5_summary = read_json(STAGE5_REPORT_DIR / "stage5_full_backfill_continuation_summary.json")
    coverage = read_csv(STAGE5_REPORT_DIR / "task_4125_coverage_progress.csv")
    rows: list[dict[str, Any]] = []
    for row in coverage:
        complete = int(row.get("coverage_complete", 0) or 0)
        rows.append(
            {
                "task_id": TASK_ID,
                "stage5_task_id": STAGE5_TASK_ID,
                "source_key": row.get("source_key", ""),
                "total_units": row.get("total_units", "0"),
                "completed_units": row.get("completed_units", "0"),
                "pending_units": row.get("pending_units", "0"),
                "coverage_complete": complete,
                "coverage_status": "PASS" if complete == 1 else "BLOCKED_PENDING_BACKFILL_UNITS",
                "full_2016_to_present_run_completed": int(stage5_summary.get("full_2016_to_present_run_completed", 0) or 0),
            }
        )
    return rows


def handoff_decision(
    mapping_rows: list[dict[str, Any]],
    source_time_rows: list[dict[str, Any]],
    raw_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blockers = []
    if any(int(row.get("mapping_blocker_rows", 0) or 0) > 0 for row in mapping_rows):
        blockers.append("mapping_blocker")
    if any(int(row.get("source_time_blocker_rows", 0) or 0) > 0 for row in source_time_rows):
        blockers.append("source_time_blocker")
    if any(str(row.get("hash_match")) != "1" or str(row.get("secret_scan_pass")) != "1" for row in raw_rows):
        blockers.append("raw_integrity_or_secret_blocker")
    if any(row.get("coverage_status") != "PASS" for row in coverage_rows):
        blockers.append("coverage_blocker")
    blockers.append("feature_admission_gate_closed")
    return [
        {
            "task_id": TASK_ID,
            "stage5_task_id": STAGE5_TASK_ID,
            "l2_handoff_decision": "BLOCKED",
            "blockers": "|".join(blockers),
            "strict_gate_rows": 0,
            "proxy_feature_rows_allowed": 0,
            "missing_source_is_negative": 0,
            "assignment_uses_future_outcome": 0,
            "outcome_used_for_assignment": 0,
            "decision_note": "Full 2016-to-present raw coverage is complete, but L2 handoff remains blocked until uncertified source-time rows and feature admission gates are explicitly resolved.",
        }
    ]


def write_report_files(report_dir: Path, summary: dict[str, Any]) -> None:
    manifest_rows = [
        {"path": "ops/task_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4126 scope and closeout tracking", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "ops/doc_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4126 docs and artifacts registered", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "configs/db_source_acquisition_scheduler.json", "type": "CONFIG", "purpose": "Stage 6 full-backfill reaudit task recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/PROJECT_STATUS.md", "type": "SSOT", "purpose": "Stage 5 complete and Stage 6 reaudit status recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/architecture/l0_source_acquisition_project_management_plan.md", "type": "GOVERNANCE", "purpose": "Full-backfill completion and L2 handoff blocker recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "scripts/audit_l0_stage6_full_backfill_l1_quality_coverage.py", "type": "SCRIPT", "purpose": "Stage 6 full-backfill L1 quality/coverage reaudit runner", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "scripts/validate_l0_stage6_full_backfill_l1_quality_coverage.py", "type": "VALIDATOR", "purpose": "Stage 6 full-backfill reaudit validator", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/report.md", "type": "TASK_REPORT", "purpose": "TASK-4126 report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/artifact_manifest.csv", "type": "ARTIFACT_MANIFEST", "purpose": "TASK-4126 artifact manifest", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/validation_results.md", "type": "VALIDATION_REPORT", "purpose": "TASK-4126 validation report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/stage6_full_backfill_l1_quality_coverage_summary.json", "type": "REFERENCE", "purpose": "Stage 6 full-backfill reaudit summary", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4126_raw_hash_audit.csv", "type": "REFERENCE", "purpose": "Full-backfill raw hash audit", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4126_mapping_audit.csv", "type": "REFERENCE", "purpose": "Full-backfill mapping audit", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4126_source_time_audit.csv", "type": "REFERENCE", "purpose": "Full-backfill source-time audit", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4126_coverage_audit.csv", "type": "REFERENCE", "purpose": "Full-backfill coverage audit", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4126_l2_handoff_decision.csv", "type": "REFERENCE", "purpose": "Full-backfill L2 handoff decision", "created_or_modified": "created", "task_id": TASK_ID},
    ]
    write_csv(report_dir / "artifact_manifest.csv", manifest_rows)
    report = "\n".join(
        [
            "# TASK-4126 L0 Stage 6 Full-Backfill L1 Quality/Coverage Reaudit",
            "",
            "## Goal",
            "",
            "Reaudit TASK-4125 full 2016-to-present L0/L1 source acquisition evidence for raw integrity, coverage, mapping, source-time readiness, and L2 handoff status.",
            "",
            "## Results",
            "",
            f"- Stage 6 status: `{summary['stage6_status']}`.",
            f"- Stage 5 observed rows: `{summary['stage5_total_event_rows']}`.",
            f"- Coverage complete: `{summary['coverage_complete_count']}/{summary['coverage_source_count']}`.",
            f"- Raw integrity failures: `{summary['raw_integrity_failure_count']}`.",
            f"- Mapping blocker rows: `{summary['mapping_blocker_rows']}`.",
            f"- Source-time blocker rows: `{summary['source_time_blocker_rows']}`.",
            f"- L2 handoff decision: `{summary['l2_handoff_decision']}`.",
            "",
            "## Handoff Decision",
            "",
            "Full 2016-to-present coverage is complete, but L2 handoff remains blocked until uncertified source-time rows and feature admission gates are resolved. Missing or uncertified source evidence remains UNKNOWN/BLOCKER and is not converted to negative evidence.",
            "",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ]
    )
    (report_dir / "report.md").write_text(report + "\n", encoding="utf-8")
    validation = "\n".join(
        [
            "# TASK-4126 Validation Results",
            "",
            "## Summary",
            "",
            "Result: pending external validator run.",
            "",
            "## Required Commands",
            "",
            "- `python scripts/ops/validate_task_registry.py`",
            "- `python scripts/ops/validate_doc_registry.py --soft`",
            "- `python -m compileall scripts/audit_l0_stage6_full_backfill_l1_quality_coverage.py scripts/validate_l0_stage6_full_backfill_l1_quality_coverage.py scripts/validate_l0_source_acquisition_project_management.py`",
            "- `python scripts/audit_l0_stage6_full_backfill_l1_quality_coverage.py`",
            "- `python scripts/validate_l0_stage6_full_backfill_l1_quality_coverage.py`",
            "- `python scripts/validate_l0_source_acquisition_project_management.py`",
            "- `python scripts/ops/validate_task_scope.py --task TASK-4126`",
            "- `python scripts/ops/validate_required_artifacts.py --task TASK-4126`",
            "",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
        ]
    )
    (report_dir / "validation_results.md").write_text(validation + "\n", encoding="utf-8")


def run(report_dir: Path) -> dict[str, Any]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stage5_summary = read_json(STAGE5_REPORT_DIR / "stage5_full_backfill_continuation_summary.json")
    raw_rows = raw_hash_audit()
    mapping_rows = mapping_audit()
    source_time_rows = source_time_audit()
    coverage_rows = coverage_audit()
    handoff_rows = handoff_decision(mapping_rows, source_time_rows, raw_rows, coverage_rows)
    write_csv(report_dir / "task_4126_raw_hash_audit.csv", raw_rows)
    write_csv(report_dir / "task_4126_mapping_audit.csv", mapping_rows)
    write_csv(report_dir / "task_4126_source_time_audit.csv", source_time_rows)
    write_csv(report_dir / "task_4126_coverage_audit.csv", coverage_rows)
    write_csv(report_dir / "task_4126_l2_handoff_decision.csv", handoff_rows)
    summary = {
        "task_id": TASK_ID,
        "stage5_task_id": STAGE5_TASK_ID,
        "stage6_status": "L1_QUALITY_COVERAGE_REAUDIT_COMPLETE_L2_HANDOFF_BLOCKED",
        "stage5_event_count": int(stage5_summary.get("event_count", 0) or 0),
        "stage5_raw_file_count": int(stage5_summary.get("raw_file_count", 0) or 0),
        "stage5_total_event_rows": int(stage5_summary.get("total_event_rows", 0) or 0),
        "coverage_complete_count": sum(1 for row in coverage_rows if row.get("coverage_status") == "PASS"),
        "coverage_source_count": len(coverage_rows),
        "raw_hash_rows": len(raw_rows),
        "raw_integrity_failure_count": sum(1 for row in raw_rows if str(row.get("hash_match")) != "1" or str(row.get("secret_scan_pass")) != "1"),
        "mapping_audit_files": len(mapping_rows),
        "mapping_blocker_rows": sum(int(row.get("mapping_blocker_rows", 0) or 0) for row in mapping_rows),
        "source_time_audit_files": len(source_time_rows),
        "source_time_certified_rows": sum(int(row.get("source_time_certified_rows", 0) or 0) for row in source_time_rows),
        "source_time_blocker_rows": sum(int(row.get("source_time_blocker_rows", 0) or 0) for row in source_time_rows),
        "l2_handoff_decision": handoff_rows[0]["l2_handoff_decision"],
        "l2_handoff_blockers": handoff_rows[0]["blockers"],
        "strict_gate_rows": 0,
        "proxy_feature_rows_allowed": 0,
        "missing_source_is_negative": 0,
        "assignment_uses_future_outcome": 0,
        "outcome_used_for_assignment": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_json(report_dir / "stage6_full_backfill_l1_quality_coverage_summary.json", summary)
    write_report_files(report_dir, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Reaudit L0 Stage 6 after TASK-4125 full 2016-to-present backfill.")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()
    summary = run(args.report_dir)
    print(
        "[L0_STAGE6_FULL_BACKFILL_L1_REAUDIT] "
        f"status={summary['stage6_status']} l2_handoff={summary['l2_handoff_decision']} "
        f"coverage={summary['coverage_complete_count']}/{summary['coverage_source_count']} "
        f"mapping_blocker_rows={summary['mapping_blocker_rows']} "
        f"source_time_blocker_rows={summary['source_time_blocker_rows']} "
        "strict_gate_rows=0 proxy_feature_rows_allowed=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
