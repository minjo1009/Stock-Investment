from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4144"
SLUG = "task_4144_l1_l2_compatibility_bridge"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
L1_PACKET_PATH = ROOT / "data" / "artifacts" / "task_4133_l1_development_plan" / "l1_normalized_source_packets_sample.csv"
L0_AUDIT_PATH = ROOT / "data" / "artifacts" / "l0_backfill_orchestration" / "raw_cache_source_time_audit.csv"

TARGET_FAMILIES = [
    "public_context_news_feeds",
    "public_market_macro_news_feeds",
    "public_newswire_feeds",
]

HANDOFF_COLUMNS = [
    "task_id",
    "compatibility_row_id",
    "source_family",
    "compatibility_status",
    "l2_allowed_scope",
    "l2_handoff_allowed",
    "l2_review_allowed",
    "l2_read_allowed",
    "source_packet_id",
    "candidate_id",
    "raw_path",
    "raw_sha256",
    "provider",
    "source_ts",
    "available_to_brain_ts",
    "decision_asof_ts",
    "timestamp_basis_for_l2",
    "publication_time_precision_for_l2",
    "capture_time_used_as",
    "source_time_certified",
    "l1_gate_classification",
    "mapping_status",
    "mapping_scope_hint",
    "blocker_reason",
    "review_reason",
    "missing_source_is_negative",
    "assignment_uses_future_outcome",
    "outcome_used_for_assignment",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: Any, length: int = 18) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def mapping_scope_hint(row: dict[str, str]) -> str:
    status = row.get("mapping_status", "")
    family = row.get("endpoint_or_source_family", row.get("source_family", ""))
    if row.get("symbol", "").strip():
        return "TICKER"
    if "MACRO_CONTEXT" in status or row.get("macro_context_candidate") == "1" or family == "public_market_macro_news_feeds":
        return "MACRO"
    if "CANDIDATE_HINT" in status or row.get("candidate_hint_only") == "1":
        return "UNKNOWN"
    return "UNKNOWN"


def l1_to_handoff(row: dict[str, str]) -> dict[str, Any]:
    family = row.get("endpoint_or_source_family", "")
    gate = row.get("l1_gate_classification", "")
    mapping = row.get("mapping_status", "")
    scope_hint = mapping_scope_hint(row)
    status = "BLOCKED_SOURCE_TIME_FOR_L2"
    blocker = ""
    review = ""
    handoff_allowed = "0"
    review_allowed = "0"
    read_allowed = "0"
    allowed_scope = "blocked"
    if row.get("source_time_certified") != "1":
        status = "BLOCKED_SOURCE_TIME_FOR_L2"
        blocker = "source_time_not_certified"
    elif not row.get("raw_path") or not row.get("raw_sha256"):
        status = "BLOCKED_RAW_INTEGRITY_FOR_L2"
        blocker = "raw_path_or_hash_missing"
    elif gate == "CONTEXT_ONLY_CERTIFIED" and scope_hint == "MACRO":
        status = "L2_CONTEXT_ARCHIVE_READY"
        handoff_allowed = "1"
        read_allowed = "1"
        allowed_scope = "context_archive"
    elif gate == "DISCOVERY_ONLY":
        status = "L2_MAPPING_REVIEW_READY" if scope_hint == "UNKNOWN" else "L2_DISCOVERY_REVIEW_READY"
        review_allowed = "1"
        allowed_scope = "review_only"
        review = "discovery_or_mapping_review_required"
    elif gate == "STRICT_SOURCE_TIME_CERTIFIED":
        status = "L2_CONTEXT_ACTIVE_READY"
        handoff_allowed = "1"
        read_allowed = "1"
        allowed_scope = "context_active"
    else:
        status = "BLOCKED_SOURCE_TIME_FOR_L2"
        blocker = f"unsupported_l1_gate:{gate}"
    if row.get("missing_source_is_negative") != "0" or row.get("assignment_uses_future_outcome") != "0" or row.get("outcome_used_for_assignment") != "0":
        status = "BLOCKED_POLICY_FOR_L2"
        handoff_allowed = review_allowed = read_allowed = "0"
        blocker = "leakage_or_missing_as_negative_flag"
    return {
        "task_id": TASK_ID,
        "compatibility_row_id": "l1l2_" + stable_hash({"source_packet_id": row.get("source_packet_id", ""), "family": family}),
        "source_family": family,
        "compatibility_status": status,
        "l2_allowed_scope": allowed_scope,
        "l2_handoff_allowed": handoff_allowed,
        "l2_review_allowed": review_allowed,
        "l2_read_allowed": read_allowed,
        "source_packet_id": row.get("source_packet_id", ""),
        "candidate_id": row.get("candidate_id", ""),
        "raw_path": row.get("raw_path", ""),
        "raw_sha256": row.get("raw_sha256", ""),
        "provider": row.get("provider", ""),
        "source_ts": row.get("source_ts", ""),
        "available_to_brain_ts": row.get("available_to_brain_ts", ""),
        "decision_asof_ts": row.get("decision_asof_ts", ""),
        "timestamp_basis_for_l2": "source_time_certified_l1_packet" if row.get("source_time_certified") == "1" else "insufficient",
        "publication_time_precision_for_l2": "IMPUTED_NOMINAL" if "wikimedia_current_events" in row.get("raw_path", "") else "SOURCE_TS",
        "capture_time_used_as": "not_used_as_publication_time",
        "source_time_certified": row.get("source_time_certified", ""),
        "l1_gate_classification": gate,
        "mapping_status": mapping,
        "mapping_scope_hint": scope_hint,
        "blocker_reason": blocker,
        "review_reason": review,
        "missing_source_is_negative": row.get("missing_source_is_negative", ""),
        "assignment_uses_future_outcome": row.get("assignment_uses_future_outcome", ""),
        "outcome_used_for_assignment": row.get("outcome_used_for_assignment", ""),
    }


def l0_audit_to_blocked_candidate(row: dict[str, str]) -> dict[str, Any]:
    family = row.get("source_family", "")
    raw_ok = row.get("raw_path_exists") == "1" and row.get("raw_sha256_present") == "1" and row.get("raw_sha256_match") not in {"False", "READ_ERROR"}
    if not raw_ok:
        status = "BLOCKED_RAW_INTEGRITY_FOR_L2"
        blocker = "l0_audit_raw_integrity_not_l2_ready"
    elif row.get("source_ts_present") != "1":
        status = "BLOCKED_SOURCE_TIME_FOR_L2"
        blocker = "l0_audit_has_no_source_ts"
    elif row.get("available_to_brain_ts_present") != "1":
        status = "BLOCKED_SOURCE_TIME_FOR_L2"
        blocker = "l0_audit_has_no_available_to_brain_ts"
    else:
        status = "BLOCKED_L1_SCOPE_NOT_MATERIALIZED"
        blocker = "l0_audit_row_not_materialized_as_l1_packet"
    return {
        "task_id": TASK_ID,
        "compatibility_row_id": "l1l2gap_" + stable_hash({"raw_path": row.get("raw_path", ""), "source_id": row.get("source_id", "")}),
        "source_family": family,
        "compatibility_status": status,
        "l2_allowed_scope": "blocked",
        "l2_handoff_allowed": "0",
        "l2_review_allowed": "0",
        "l2_read_allowed": "0",
        "source_packet_id": "",
        "candidate_id": row.get("source_id", ""),
        "raw_path": row.get("raw_path", ""),
        "raw_sha256": "present_in_l0_audit" if row.get("raw_sha256_present") == "1" else "",
        "provider": row.get("source_id", "").split("::")[0],
        "source_ts": "",
        "available_to_brain_ts": "",
        "decision_asof_ts": "",
        "timestamp_basis_for_l2": "capture_only_not_publication_time" if row.get("capture_or_updated_ts_present") == "1" else "missing",
        "publication_time_precision_for_l2": "UNKNOWN",
        "capture_time_used_as": "availability_hint_only_not_publication_time" if row.get("capture_or_updated_ts_present") == "1" else "not_available",
        "source_time_certified": "0",
        "l1_gate_classification": "NOT_MATERIALIZED_AS_L1_PACKET",
        "mapping_status": "NOT_EVALUATED",
        "mapping_scope_hint": "UNKNOWN",
        "blocker_reason": blocker,
        "review_reason": "",
        "missing_source_is_negative": row.get("missing_source_is_negative", ""),
        "assignment_uses_future_outcome": row.get("assignment_uses_future_outcome", ""),
        "outcome_used_for_assignment": row.get("outcome_used_for_assignment", ""),
    }


def summary_rows(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    counts = Counter(str(row.get(field, "")) for row in rows)
    return [{"task_id": TASK_ID, field: key, "count": value} for key, value in sorted(counts.items())]


def write_manifest() -> None:
    rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4144 task definition and closeout state", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4144 document registry entries", "modified"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "active_doc", "TASK-4144 active report pointer", "modified"),
        ("docs/active/CURRENT_TASKS.md", "active_doc", "TASK-4144 completion pointer", "modified"),
        ("docs/active/PROJECT_STATUS.md", "active_doc", "TASK-4144 status note", "modified"),
        ("scripts/run_l1_l2_compatibility_4144.py", "script", "Build L1/L2 compatibility bridge", "created"),
        ("scripts/validate_l1_l2_compatibility_4144.py", "validator", "Validate L1/L2 compatibility bridge", "created"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4144 report", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4144 artifact manifest", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4144 validation results", "created"),
        (f"docs/reports/{SLUG}/gpt_prompt.md", "gpt_evidence", "GPT Pro prompt summary", "created"),
        (f"docs/reports/{SLUG}/gpt_response.md", "gpt_evidence", "GPT Pro response capture", "created"),
        (f"docs/reports/{SLUG}/l1_l2_compatibility_summary.json", "summary", "Machine-readable TASK-4144 summary", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_compatibility_handoff.csv", "artifact", "Compatibility handoff rows", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_compatibility_matrix.csv", "artifact", "Compatibility matrix summary", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_scope_gap_report.csv", "artifact", "Scope gap report", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_timestamp_basis_audit.csv", "artifact", "Timestamp basis audit", "created"),
        (f"data/artifacts/{SLUG}/l2_from_compatibility_handoff.csv", "artifact", "L2 rows allowed from handoff", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_block_reason_summary.csv", "artifact", "Block reason summary", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_review_reason_summary.csv", "artifact", "Review reason summary", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_mapping_status_summary.csv", "artifact", "Mapping status summary", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_timestamp_basis_summary.csv", "artifact", "Timestamp basis summary", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_compatibility_validation_report.json", "artifact", "Validation report JSON", "created"),
        (f"data/artifacts/{SLUG}/l1_l2_compatibility_validation_report.md", "artifact", "Validation report Markdown", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "artifact", "Machine-readable validator report", "created"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [{"path": path, "type": typ, "purpose": purpose, "created_or_modified": state, "task_id": TASK_ID} for path, typ, purpose, state in rows],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )


def build_report_text(summary: dict[str, Any]) -> str:
    report = "# TASK-4144 L1/L2 Compatibility Bridge\n\n"
    report += "## 결론\n\n"
    report += (
        "현재 문제는 L2 로직 자체의 실패라기보다, L1이 L2가 바로 읽을 수 있는 "
        "packet/handoff를 충분히 만들어주지 못한 호환성 gap이다. 그래서 L2가 L0 raw를 "
        "직접 읽지 않도록, L1 packet에서 온 행과 L0 audit에만 남아 있는 후보를 분리한 "
        "bridge artifact를 만들었다.\n\n"
    )
    report += "| 항목 | 값 |\n|---|---:|\n"
    for key in [
        "l1_target_packet_rows",
        "l0_audit_target_rows",
        "compatibility_matrix_rows",
        "l2_handoff_allowed_rows",
        "l2_review_allowed_rows",
        "blocked_l0_audit_candidate_rows",
        "capture_only_publication_promotions",
    ]:
        report += f"| {key} | {summary[key]} |\n"
    report += "\n## 처리 원칙\n\n"
    report += "- L2는 L0 raw/headlines를 직접 읽지 않는다.\n"
    report += "- capture time은 availability hint로만 남기고 publication/source time으로 승격하지 않는다.\n"
    report += "- source time이 없는 L0 audit row는 L2-ready가 아니라 blocked/gap 후보로 둔다.\n"
    report += "- L1 packet으로 이미 검문된 row만 L2 handoff/review 대상으로 넘긴다.\n"
    report += "- score, signal, return, ranking, order, broker, paper/live 권한은 열지 않는다.\n"
    return report


def build_and_write() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    l1_rows = [row for row in read_csv(L1_PACKET_PATH) if row.get("endpoint_or_source_family") in TARGET_FAMILIES]
    l0_rows = [row for row in read_csv(L0_AUDIT_PATH) if row.get("source_family") in TARGET_FAMILIES]
    handoff_rows = [l1_to_handoff(row) for row in l1_rows]
    blocked_candidates = [l0_audit_to_blocked_candidate(row) for row in l0_rows]
    matrix_rows = handoff_rows + blocked_candidates
    l2_rows = [row for row in handoff_rows if row["l2_handoff_allowed"] == "1" or row["l2_review_allowed"] == "1"]
    scope_gap_rows = [
        {
            "task_id": TASK_ID,
            "source_family": family,
            "l1_packet_rows": sum(1 for row in l1_rows if row.get("endpoint_or_source_family") == family),
            "l0_audit_rows": sum(1 for row in l0_rows if row.get("source_family") == family),
            "not_materialized_or_blocked_rows": sum(1 for row in blocked_candidates if row.get("source_family") == family),
            "gap_status": "L1_COMPATIBILITY_SCOPE_GAP_PRESENT",
        }
        for family in TARGET_FAMILIES
    ]
    timestamp_rows = [
        {
            "task_id": TASK_ID,
            "compatibility_row_id": row["compatibility_row_id"],
            "source_family": row["source_family"],
            "timestamp_basis_for_l2": row["timestamp_basis_for_l2"],
            "capture_time_used_as": row["capture_time_used_as"],
            "source_time_certified": row["source_time_certified"],
            "compatibility_status": row["compatibility_status"],
        }
        for row in matrix_rows
    ]
    write_csv(ARTIFACT_DIR / "l1_l2_compatibility_handoff.csv", handoff_rows, HANDOFF_COLUMNS)
    write_csv(ARTIFACT_DIR / "l1_l2_compatibility_matrix.csv", matrix_rows, HANDOFF_COLUMNS)
    write_csv(ARTIFACT_DIR / "l1_l2_scope_gap_report.csv", scope_gap_rows, ["task_id", "source_family", "l1_packet_rows", "l0_audit_rows", "not_materialized_or_blocked_rows", "gap_status"])
    write_csv(ARTIFACT_DIR / "l1_l2_timestamp_basis_audit.csv", timestamp_rows, ["task_id", "compatibility_row_id", "source_family", "timestamp_basis_for_l2", "capture_time_used_as", "source_time_certified", "compatibility_status"])
    write_csv(ARTIFACT_DIR / "l2_from_compatibility_handoff.csv", l2_rows, HANDOFF_COLUMNS)
    write_csv(ARTIFACT_DIR / "l1_l2_block_reason_summary.csv", summary_rows(matrix_rows, "blocker_reason"), ["task_id", "blocker_reason", "count"])
    write_csv(ARTIFACT_DIR / "l1_l2_review_reason_summary.csv", summary_rows(matrix_rows, "review_reason"), ["task_id", "review_reason", "count"])
    write_csv(ARTIFACT_DIR / "l1_l2_mapping_status_summary.csv", summary_rows(matrix_rows, "mapping_status"), ["task_id", "mapping_status", "count"])
    write_csv(ARTIFACT_DIR / "l1_l2_timestamp_basis_summary.csv", summary_rows(matrix_rows, "timestamp_basis_for_l2"), ["task_id", "timestamp_basis_for_l2", "count"])
    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "gpt_capture_status": "captured_via_visible_dom_summary",
        "l1_target_packet_rows": len(l1_rows),
        "l0_audit_target_rows": len(l0_rows),
        "compatibility_matrix_rows": len(matrix_rows),
        "l1_handoff_rows": len(handoff_rows),
        "l2_handoff_allowed_rows": sum(1 for row in handoff_rows if row["l2_handoff_allowed"] == "1"),
        "l2_review_allowed_rows": sum(1 for row in handoff_rows if row["l2_review_allowed"] == "1"),
        "blocked_l0_audit_candidate_rows": len(blocked_candidates),
        "capture_only_publication_promotions": sum(1 for row in matrix_rows if row["capture_time_used_as"] == "publication_time"),
        "feature_materialization_allowed_rows": 0,
        "trading_authority_opened_rows": 0,
        "paper_live_broker_order_opened_rows": 0,
    }
    (REPORT_DIR / "l1_l2_compatibility_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    report = "# TASK-4144 L1/L2 Compatibility Bridge\n\n"
    report += "## 결론\n\n"
    report += "문제는 L2 자체보다 L1이 L2용 packet/handoff를 충분히 물질화하지 않은 compatibility gap이다. L2가 L0 raw를 직접 읽지 않도록, L1 packet과 L0 audit gap을 분리한 bridge artifact를 만들었다.\n\n"
    report += "| 항목 | 값 |\n|---|---:|\n"
    for key in ["l1_target_packet_rows", "l0_audit_target_rows", "compatibility_matrix_rows", "l2_handoff_allowed_rows", "l2_review_allowed_rows", "blocked_l0_audit_candidate_rows", "capture_only_publication_promotions"]:
        report += f"| {key} | {summary[key]} |\n"
    report += "\n## 처리 원칙\n\n"
    report += "- L2는 L0 raw/headlines를 직접 읽지 않는다.\n"
    report += "- capture time은 availability hint로만 남기고 publication/source time으로 승격하지 않는다.\n"
    report += "- source time이 없는 L0 audit row는 L2-ready가 아니라 blocked/gap 후보로 둔다.\n"
    report += "- L1 packet으로 이미 검문된 row만 L2 handoff/review 대상으로 넘긴다.\n"
    report += "- score, signal, return, ranking, order, broker, paper/live 권한은 열지 않았다.\n"
    report = build_report_text(summary)
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")
    write_manifest()
    return summary


def main() -> int:
    print(json.dumps(build_and_write(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
