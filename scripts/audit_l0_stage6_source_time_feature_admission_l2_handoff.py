from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4127"
STAGE5_TASK_ID = "TASK-4125"
STAGE6_REAUDIT_TASK_ID = "TASK-4126"
STAGE5_SLUG = "task_4125_l0_stage_5_full_2016_to_present_backfill_continuation"
STAGE6_REAUDIT_SLUG = "task_4126_l0_stage_6_full_backfill_l1_quality_coverage_reaudit"
SLUG = "task_4127_l0_stage_6_source_time_feature_admission_l2_context_handoff"
DEFAULT_REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
STAGE5_RAW_DIR = ROOT / f"data/raw/{STAGE5_SLUG}"
STAGE5_REPORT_DIR = ROOT / f"docs/reports/{STAGE5_SLUG}"
STAGE6_REAUDIT_REPORT_DIR = ROOT / f"docs/reports/{STAGE6_REAUDIT_SLUG}"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


def bool_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def headline_payloads() -> list[tuple[Path, dict[str, Any]]]:
    return [(path, read_json(path)) for path in sorted(STAGE5_RAW_DIR.rglob("headlines.json"))]


def source_key_for(path: Path, payload: dict[str, Any], row: dict[str, Any] | None = None) -> str:
    if row:
        value = row.get("source_key") or row.get("provider")
        if value:
            return str(value)
    value = payload.get("source_key") or payload.get("provider")
    if value:
        return str(value)
    parts = path.as_posix().split("/")
    for part in parts:
        if part.startswith("source="):
            return part.split("=", 1)[1]
    return "unknown_source"


def row_has_mapping_or_not_required(row: dict[str, Any]) -> bool:
    required_raw = row.get("ticker_mapping_required_flag", "")
    required = bool_int(required_raw) if str(required_raw) != "" else 1
    macro_context = bool_int(row.get("macro_context_candidate_flag", 0))
    mapping_status = str(row.get("entity_mapping_status") or "")
    has_mapping = bool(row.get("symbols") or row.get("tickers") or row.get("entities") or row.get("entity_map"))
    return required == 0 or macro_context == 1 or mapping_status == "NOT_REQUIRED_MARKET_MACRO_CONTEXT" or has_mapping


def row_has_source_time(row: dict[str, Any]) -> bool:
    return bool(row.get("published_at") or row.get("publication_time") or row.get("event_time") or row.get("source_ts"))


def classify_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    families: dict[str, dict[str, Any]] = {}
    blocked_reasons: dict[str, dict[str, Any]] = {}
    totals = {
        "headline_rows": 0,
        "l2_context_admitted_rows": 0,
        "blocked_rows": 0,
        "source_time_certified_rows": 0,
        "source_time_uncertified_rows": 0,
    }
    for path, payload in headline_payloads():
        rows = payload.get("headlines") if isinstance(payload.get("headlines"), list) else []
        for row in rows:
            source_key = source_key_for(path, payload, row)
            family = families.setdefault(
                source_key,
                {
                    "task_id": TASK_ID,
                    "stage5_task_id": STAGE5_TASK_ID,
                    "source_key": source_key,
                    "provider": row.get("provider") or payload.get("provider") or "",
                    "headline_rows": 0,
                    "source_time_certified_rows": 0,
                    "mapping_ready_rows": 0,
                    "l2_context_admitted_rows": 0,
                    "blocked_rows": 0,
                    "strict_gate_pass_rows": 0,
                    "proxy_feature_allowed_rows": 0,
                    "trade_feature_allowed_rows": 0,
                    "sample_raw_path": rel(path),
                    "admission_status": "",
                },
            )
            has_time = row_has_source_time(row)
            certified = bool_int(row.get("source_time_certified_flag", 0)) == 1
            mapping_ready = row_has_mapping_or_not_required(row)
            l2_context_allowed = certified and has_time and mapping_ready
            family["headline_rows"] += 1
            family["source_time_certified_rows"] += int(certified)
            family["mapping_ready_rows"] += int(mapping_ready)
            family["l2_context_admitted_rows"] += int(l2_context_allowed)
            family["blocked_rows"] += int(not l2_context_allowed)
            family["proxy_feature_allowed_rows"] += int(l2_context_allowed)
            totals["headline_rows"] += 1
            totals["source_time_certified_rows"] += int(certified)
            totals["source_time_uncertified_rows"] += int(not certified)
            totals["l2_context_admitted_rows"] += int(l2_context_allowed)
            totals["blocked_rows"] += int(not l2_context_allowed)
            if not l2_context_allowed:
                reason = []
                if not has_time:
                    reason.append("source_time_missing")
                if has_time and not certified:
                    reason.append("source_time_uncertified")
                if not mapping_ready:
                    reason.append("mapping_not_ready")
                reason_key = "|".join(reason) or "feature_admission_blocked"
                blocked = blocked_reasons.setdefault(
                    f"{source_key}:{reason_key}",
                    {
                        "task_id": TASK_ID,
                        "stage5_task_id": STAGE5_TASK_ID,
                        "source_key": source_key,
                        "blocker": reason_key,
                        "blocked_rows": 0,
                        "missing_source_is_negative": 0,
                        "sample_raw_path": rel(path),
                    },
                )
                blocked["blocked_rows"] += 1
    family_rows = []
    for row in sorted(families.values(), key=lambda item: item["source_key"]):
        admitted = int(row["l2_context_admitted_rows"])
        blocked = int(row["blocked_rows"])
        row["admission_status"] = "L2_CONTEXT_ADMITTED" if admitted and not blocked else "BLOCKED" if blocked and not admitted else "PARTIAL"
        family_rows.append(row)
    return family_rows, sorted(blocked_reasons.values(), key=lambda item: (item["source_key"], item["blocker"])), totals


def write_report_files(report_dir: Path, summary: dict[str, Any]) -> None:
    manifest_rows = [
        {"path": "ops/task_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4127 task scope and closeout tracking", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "ops/doc_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4127 docs and artifacts registered", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "configs/db_source_acquisition_scheduler.json", "type": "CONFIG", "purpose": "Stage 6 L2 context handoff decision recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/ACTIVE_SSOT_INDEX.md", "type": "SSOT", "purpose": "TASK-4127 report registered as active evidence", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/CURRENT_TASKS.md", "type": "SSOT", "purpose": "TASK-4127 closeout recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/PROJECT_STATUS.md", "type": "SSOT", "purpose": "L2 context handoff status recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/architecture/l0_source_acquisition_project_management_plan.md", "type": "GOVERNANCE", "purpose": "Stage 6 context-only handoff decision added", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "scripts/audit_l0_stage6_source_time_feature_admission_l2_handoff.py", "type": "SCRIPT", "purpose": "Source-time feature admission and L2 context handoff runner", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "scripts/validate_l0_stage6_source_time_feature_admission_l2_handoff.py", "type": "VALIDATOR", "purpose": "TASK-4127 validator", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/report.md", "type": "TASK_REPORT", "purpose": "TASK-4127 report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/artifact_manifest.csv", "type": "ARTIFACT_MANIFEST", "purpose": "TASK-4127 artifact manifest", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/validation_results.md", "type": "VALIDATION_REPORT", "purpose": "TASK-4127 validation report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/stage6_source_time_feature_admission_l2_handoff_summary.json", "type": "REFERENCE", "purpose": "TASK-4127 summary", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4127_source_family_admission.csv", "type": "REFERENCE", "purpose": "Source-family admission aggregate", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4127_blocked_source_rows.csv", "type": "REFERENCE", "purpose": "Blocked source row aggregate", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4127_feature_admission_gate.csv", "type": "REFERENCE", "purpose": "Feature admission gate decision", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4127_l2_context_handoff_manifest.csv", "type": "REFERENCE", "purpose": "L2 context-only handoff manifest", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4127_l2_handoff_decision.csv", "type": "REFERENCE", "purpose": "L2 handoff decision", "created_or_modified": "created", "task_id": TASK_ID},
    ]
    write_csv(report_dir / "artifact_manifest.csv", manifest_rows)
    report = "\n".join(
        [
            "# TASK-4127 L0 Stage 6 Source-Time Feature Admission and L2 Context Handoff",
            "",
            "## Goal",
            "",
            "Classify TASK-4125 full-backfill rows into L2 context-only admitted rows and blocked rows after the TASK-4126 full coverage reaudit.",
            "",
            "## Result",
            "",
            f"- Decision: `{summary['l2_handoff_decision']}`.",
            f"- L2 context admitted rows: `{summary['l2_context_admitted_rows']}`.",
            f"- Blocked rows: `{summary['blocked_rows']}`.",
            f"- Source-time certified rows: `{summary['source_time_certified_rows']}`.",
            f"- Source-time uncertified rows: `{summary['source_time_uncertified_rows']}`.",
            f"- Strict trading gate rows: `{summary['strict_gate_pass_rows']}`.",
            f"- Trade feature rows: `{summary['trade_feature_allowed_rows']}`.",
            "",
            "## Decision",
            "",
            "Certified macro/context rows are admitted only as L2 context primitives. Wikimedia Current Events historical rows remain blocked because the collector contract marks them as diagnostic context only with source-time certification closed.",
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
            "# TASK-4127 Validation Results",
            "",
            "## Summary",
            "",
            "Result: pending validator run.",
            "",
            "## Required Commands",
            "",
            "- `python scripts/ops/validate_task_registry.py`",
            "- `python scripts/ops/validate_doc_registry.py --soft`",
            "- `python -m compileall scripts/audit_l0_stage6_source_time_feature_admission_l2_handoff.py scripts/validate_l0_stage6_source_time_feature_admission_l2_handoff.py scripts/validate_l0_source_acquisition_project_management.py`",
            "- `python scripts/audit_l0_stage6_source_time_feature_admission_l2_handoff.py`",
            "- `python scripts/validate_l0_stage6_source_time_feature_admission_l2_handoff.py`",
            "- `python scripts/validate_l0_source_acquisition_project_management.py`",
            "- `python scripts/ops/validate_task_scope.py --task TASK-4127`",
            "- `python scripts/ops/validate_required_artifacts.py --task TASK-4127`",
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
    stage6_summary = read_json(STAGE6_REAUDIT_REPORT_DIR / "stage6_full_backfill_l1_quality_coverage_summary.json")
    family_rows, blocked_rows, totals = classify_rows()
    feature_gate_rows = [
        {
            "task_id": TASK_ID,
            "stage5_task_id": STAGE5_TASK_ID,
            "strict_gate_pass_rows": 0,
            "proxy_feature_allowed_rows": totals["l2_context_admitted_rows"],
            "trade_feature_allowed_rows": 0,
            "feature_builder_enabled": 0,
            "l2_context_handoff_allowed": int(totals["l2_context_admitted_rows"] > 0),
            "l2_trading_handoff_allowed": 0,
            "reason": "Only source-time-certified macro/context rows are allowed for L2 context primitives; strict/trading gates remain closed.",
        }
    ]
    handoff_rows = [
        {
            "task_id": TASK_ID,
            "stage5_task_id": STAGE5_TASK_ID,
            "stage6_reaudit_task_id": STAGE6_REAUDIT_TASK_ID,
            "l2_handoff_decision": "PARTIAL_CONTEXT_ONLY_HANDOFF_READY",
            "l2_context_admitted_rows": totals["l2_context_admitted_rows"],
            "l2_blocked_rows": totals["blocked_rows"],
            "blockers": "wikimedia_current_events_source_time_uncertified" if totals["blocked_rows"] else "",
            "strict_gate_pass_rows": 0,
            "trade_feature_allowed_rows": 0,
            "missing_source_is_negative": 0,
            "assignment_uses_future_outcome": 0,
            "outcome_used_for_assignment": 0,
            "decision_note": "Partial L2 context-only handoff is ready for certified macro/context rows; blocked rows remain neutral blockers.",
        }
    ]
    handoff_manifest_rows = [
        {
            "task_id": TASK_ID,
            "stage5_task_id": STAGE5_TASK_ID,
            "source_key": row["source_key"],
            "l2_context_admitted_rows": row["l2_context_admitted_rows"],
            "proxy_feature_allowed_rows": row["proxy_feature_allowed_rows"],
            "strict_gate_pass_rows": row["strict_gate_pass_rows"],
            "trade_feature_allowed_rows": row["trade_feature_allowed_rows"],
            "admission_status": row["admission_status"],
            "sample_raw_path": row["sample_raw_path"],
        }
        for row in family_rows
        if int(row["l2_context_admitted_rows"]) > 0
    ]
    write_csv(report_dir / "task_4127_source_family_admission.csv", family_rows)
    write_csv(report_dir / "task_4127_blocked_source_rows.csv", blocked_rows)
    write_csv(report_dir / "task_4127_feature_admission_gate.csv", feature_gate_rows)
    write_csv(report_dir / "task_4127_l2_context_handoff_manifest.csv", handoff_manifest_rows)
    write_csv(report_dir / "task_4127_l2_handoff_decision.csv", handoff_rows)
    summary = {
        "task_id": TASK_ID,
        "stage5_task_id": STAGE5_TASK_ID,
        "stage6_reaudit_task_id": STAGE6_REAUDIT_TASK_ID,
        "stage6_status": "SOURCE_TIME_FEATURE_ADMISSION_COMPLETE_PARTIAL_L2_CONTEXT_HANDOFF_READY",
        "stage5_total_event_rows": int(stage5_summary.get("total_event_rows", 0) or 0),
        "stage6_reaudit_source_time_blocker_rows": int(stage6_summary.get("source_time_blocker_rows", 0) or 0),
        "headline_rows": totals["headline_rows"],
        "source_family_count": len(family_rows),
        "l2_context_admitted_rows": totals["l2_context_admitted_rows"],
        "blocked_rows": totals["blocked_rows"],
        "source_time_certified_rows": totals["source_time_certified_rows"],
        "source_time_uncertified_rows": totals["source_time_uncertified_rows"],
        "strict_gate_pass_rows": 0,
        "proxy_feature_allowed_rows": totals["l2_context_admitted_rows"],
        "trade_feature_allowed_rows": 0,
        "l2_handoff_decision": handoff_rows[0]["l2_handoff_decision"],
        "l2_handoff_blockers": handoff_rows[0]["blockers"],
        "missing_source_is_negative": 0,
        "assignment_uses_future_outcome": 0,
        "outcome_used_for_assignment": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_json(report_dir / "stage6_source_time_feature_admission_l2_handoff_summary.json", summary)
    write_report_files(report_dir, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify Stage 6 source-time feature admission and L2 context-only handoff.")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()
    summary = run(args.report_dir)
    print(
        "[L0_STAGE6_SOURCE_TIME_FEATURE_ADMISSION] "
        f"status={summary['stage6_status']} decision={summary['l2_handoff_decision']} "
        f"admitted={summary['l2_context_admitted_rows']} blocked={summary['blocked_rows']} "
        "strict_gate_rows=0 trade_feature_rows=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
