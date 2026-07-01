from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4143"
SLUG = "task_4143_l2_completion_gpt_review_and_read_contract"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
SOURCE_ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_4142_l2_swing_event_admission"
SOURCE_REPORT_DIR = ROOT / "docs" / "reports" / "task_4142_l2_swing_event_admission"
L1_PACKET_PATH = ROOT / "data" / "artifacts" / "task_4133_l1_development_plan" / "l1_normalized_source_packets_sample.csv"
L0_AUDIT_PATH = ROOT / "data" / "artifacts" / "l0_backfill_orchestration" / "raw_cache_source_time_audit.csv"
L0_SUMMARY_PATH = ROOT / "data" / "artifacts" / "l0_backfill_orchestration" / "enhanced_latest_summary.json"

TARGET_FAMILIES = [
    "public_context_news_feeds",
    "public_market_macro_news_feeds",
    "public_newswire_feeds",
]

L3_READ_COLUMNS = [
    "task_id",
    "l2_event_id",
    "l2_event_mapping_id",
    "source_family",
    "source_packet_id",
    "raw_path",
    "raw_sha256",
    "provider",
    "publication_date",
    "publication_time_precision",
    "is_publication_time_imputed",
    "available_to_brain_ts",
    "decision_asof_ts",
    "activation_policy",
    "activation_decision_date",
    "mapping_scope",
    "mapping_key",
    "symbol",
    "entity_id",
    "sector_key",
    "macro_key",
    "dedup_key",
    "event_cluster_id",
    "is_canonical_event",
    "cluster_member_count",
    "dedup_status",
    "event_domain",
    "event_type",
    "topic_tags",
    "economic_meaning_status",
    "primary_effect_window",
    "secondary_effect_windows",
    "window_1d_start_date",
    "window_1d_end_date",
    "window_5d_start_date",
    "window_5d_end_date",
    "window_20d_start_date",
    "window_20d_end_date",
    "window_60d_start_date",
    "window_60d_end_date",
    "stale_status",
    "read_status",
    "read_note",
]

FORBIDDEN_L3_COLUMNS = {
    "sentiment_score",
    "bullish",
    "bearish",
    "alpha_score",
    "rank",
    "ranking",
    "realized_return",
    "forward_return",
    "hit_rate",
    "sizing",
    "order_intent",
    "signal",
    "target",
    "score",
    "feature_materialization_allowed",
    "trading_authority_opened",
    "paper_live_broker_order_opened",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def counter_rows(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    counts = Counter(str(row.get(field, "")) for row in rows)
    return [{"task_id": TASK_ID, field: key, "count": value} for key, value in sorted(counts.items())]


def load_l0_lane_rows() -> dict[str, dict[str, Any]]:
    if not L0_SUMMARY_PATH.exists():
        return {}
    try:
        summary = json.loads(L0_SUMMARY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    lanes: dict[str, dict[str, Any]] = {}
    for row in summary.get("lane_rows", []):
        if isinstance(row, dict) and row.get("source_family") in TARGET_FAMILIES:
            lanes[str(row["source_family"])] = row
    return lanes


def build_input_scope_audit() -> list[dict[str, Any]]:
    l1_rows = read_csv(L1_PACKET_PATH)
    l0_rows = read_csv(L0_AUDIT_PATH)
    lane_rows = load_l0_lane_rows()
    l1_counts = Counter(row.get("endpoint_or_source_family", "") for row in l1_rows)
    l0_counts = Counter(row.get("source_family", "") for row in l0_rows)
    audit_rows = []
    for family in TARGET_FAMILIES:
        lane = lane_rows.get(family, {})
        l1_count = l1_counts.get(family, 0)
        l0_sample_count = l0_counts.get(family, 0)
        if l1_count <= 1 and l0_sample_count > l1_count:
            scope_status = "BLOCKED_L1_PACKET_SCOPE_TOO_NARROW"
            next_action = "expand_l1_packets_before_broader_l2_rows"
        else:
            scope_status = "READY_FOR_CURRENT_L1_SCOPE"
            next_action = "l2_can_consume_current_l1_rows"
        audit_rows.append({
            "task_id": TASK_ID,
            "source_family": family,
            "l1_packet_rows_available": l1_count,
            "l0_audit_sample_rows_available": l0_sample_count,
            "l0_lane_health": lane.get("health", ""),
            "l0_lane_progress_pct": lane.get("progress_pct", ""),
            "l0_lane_running": lane.get("running", ""),
            "l0_lane_complete": lane.get("complete", ""),
            "scope_status": scope_status,
            "next_action": next_action,
        })
    return audit_rows


def build_l3_read_rows(view_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    read_rows = []
    for row in view_rows:
        if row.get("admission_status") != "ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE":
            continue
        if row.get("mapping_scope") == "UNKNOWN":
            continue
        if row.get("is_canonical_event") != "1":
            continue
        read_row = {key: row.get(key, "") for key in L3_READ_COLUMNS}
        read_row["task_id"] = TASK_ID
        read_row["read_status"] = "L3_READABLE_CONTEXT_NOT_FEATURE"
        read_row["read_note"] = "safe_context_primitive_no_score_no_signal_no_return"
        read_rows.append(read_row)
    return read_rows


def build_mapping_review_queue(view_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    queue = []
    for row in view_rows:
        if row.get("mapping_scope") != "UNKNOWN" and not str(row.get("mapping_status", "")).startswith("BLOCKED"):
            continue
        queue.append({
            "task_id": TASK_ID,
            "l2_event_id": row.get("l2_event_id", ""),
            "l2_event_mapping_id": row.get("l2_event_mapping_id", ""),
            "source_family": row.get("source_family", ""),
            "source_packet_id": row.get("source_packet_id", ""),
            "provider": row.get("provider", ""),
            "publication_date": row.get("publication_date", ""),
            "mapping_scope": row.get("mapping_scope", ""),
            "mapping_status": row.get("mapping_status", ""),
            "candidate_symbol": "",
            "candidate_entity": "",
            "candidate_sector": "",
            "candidate_macro": "",
            "candidate_rule": "NO_DETERMINISTIC_CANDIDATE_FROM_CURRENT_L1_ROW",
            "review_status": "REVIEW_REQUIRED_NOT_L3_READABLE",
            "review_reason": "unknown_mapping_kept_for_review_not_feature",
        })
    return queue


def write_contracts() -> None:
    read_contract = """version: 1
task_id: TASK-4143
contract_name: l2_to_l3_swing_event_read_contract
purpose: L3 may read only safe L2 context primitives, not scores, signals, labels, or returns.
allowed_rows:
  - admission_status: ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE
  - is_canonical_event: "1"
  - mapping_scope: [TICKER, ENTITY, SECTOR, MACRO]
excluded_rows:
  - mapping_scope: UNKNOWN
  - admission_status: MAPPING_REVIEW_REQUIRED_NOT_FEATURE
  - dedup_status: DUPLICATE_BLOCKED
forbidden_columns:
  - sentiment_score
  - alpha_score
  - ranking
  - realized_return
  - forward_return
  - signal
  - order_intent
  - sizing
  - trading_authority_opened
  - paper_live_broker_order_opened
boundary:
  feature_materialization: closed
  trading_authority: closed
  broker_order_paper_live: closed
"""
    mapping_rules = """version: 1
task_id: TASK-4143
contract_name: l2_mapping_review_rules
allowed_mapping_scopes: [TICKER, ENTITY, SECTOR, MACRO, UNKNOWN]
rules:
  - exact L1 symbol may map to TICKER
  - explicit L1 macro context may map to MACRO
  - UNKNOWN rows remain in review queue
cut_now:
  - force ticker guess
  - LLM sentiment
  - full entity resolution system
  - sector-to-ticker automatic allocation
"""
    dedup_rules = """version: 1
task_id: TASK-4143
contract_name: l2_dedup_stale_window_rules
dedup:
  key_basis: publication_date + mapping_scope + mapping_key + event_type + candidate_id
  l3_exposure: canonical rows only
  duplicate_count_as_signal: forbidden
stale:
  active_primary: 0_to_20_days_after_activation
  active_secondary: 21_to_60_days_after_activation
  archive_context: older_than_60_days
  stale_as_negative_evidence: forbidden
effect_windows:
  declared_only: [1D, 5D, 20D, 60D]
  realized_or_forward_return: forbidden
"""
    (ARTIFACT_DIR / "l2_to_l3_swing_event_read_contract.yaml").write_text(read_contract, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "l2_mapping_rules.yaml").write_text(mapping_rules, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "l2_dedup_stale_window_rules.yaml").write_text(dedup_rules, encoding="utf-8", newline="\n")


def write_manifest() -> None:
    rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4143 task definition and closeout state", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4143 document registry entries", "modified"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "active_doc", "TASK-4143 active report pointer", "modified"),
        ("docs/active/CURRENT_TASKS.md", "active_doc", "TASK-4143 completion pointer", "modified"),
        ("docs/active/PROJECT_STATUS.md", "active_doc", "TASK-4143 status note", "modified"),
        ("scripts/run_l2_completion_4143.py", "script", "Build L2 completion package", "created"),
        ("scripts/validate_l2_completion_4143.py", "validator", "Validate L2 completion package", "created"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4143 report", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4143 artifact manifest", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4143 validation results", "created"),
        (f"docs/reports/{SLUG}/gpt_prompt.md", "gpt_evidence", "Prompt sent to GPT Pro", "created"),
        (f"docs/reports/{SLUG}/gpt_response.md", "gpt_evidence", "GPT Pro response captured from Chrome", "created"),
        (f"docs/reports/{SLUG}/l2_completion_summary.json", "summary", "Machine-readable TASK-4143 summary", "created"),
        (f"data/artifacts/{SLUG}/l2_to_l3_swing_event_read_contract.yaml", "artifact", "L3 read contract", "created"),
        (f"data/artifacts/{SLUG}/l2_to_l3_swing_event_read_view.csv", "artifact", "L3 read whitelist view", "created"),
        (f"data/artifacts/{SLUG}/l2_to_l3_swing_event_read_view.jsonl", "artifact", "L3 read whitelist view JSONL", "created"),
        (f"data/artifacts/{SLUG}/l2_mapping_review_queue.csv", "artifact", "Mapping review queue", "created"),
        (f"data/artifacts/{SLUG}/l2_input_scope_audit.csv", "artifact", "L0/L1 input scope audit", "created"),
        (f"data/artifacts/{SLUG}/l2_mapping_scope_summary.csv", "artifact", "Mapping scope summary", "created"),
        (f"data/artifacts/{SLUG}/l2_dedup_summary.csv", "artifact", "Dedup summary", "created"),
        (f"data/artifacts/{SLUG}/l2_stale_status_summary.csv", "artifact", "Stale status summary", "created"),
        (f"data/artifacts/{SLUG}/l2_completion_cut_list.csv", "artifact", "Overengineering cut list", "created"),
        (f"data/artifacts/{SLUG}/l2_completion_validation_report.json", "artifact", "Validator JSON report", "created"),
        (f"data/artifacts/{SLUG}/l2_completion_validation_report.md", "artifact", "Validator Markdown report", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "artifact", "Machine-readable validator report", "created"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [{"path": path, "type": typ, "purpose": purpose, "created_or_modified": state, "task_id": TASK_ID} for path, typ, purpose, state in rows],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )


def build_and_write() -> dict[str, Any]:
    from scripts.run_l2_swing_event_admission_4142 import build_and_write as build_admission

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    build_admission()
    view_rows = read_csv(SOURCE_ARTIFACT_DIR / "l2_swing_event_admission_view.csv")
    read_rows = build_l3_read_rows(view_rows)
    mapping_queue = build_mapping_review_queue(view_rows)
    input_scope = build_input_scope_audit()
    write_contracts()
    write_csv(ARTIFACT_DIR / "l2_to_l3_swing_event_read_view.csv", read_rows, L3_READ_COLUMNS)
    write_jsonl(ARTIFACT_DIR / "l2_to_l3_swing_event_read_view.jsonl", read_rows)
    write_csv(
        ARTIFACT_DIR / "l2_mapping_review_queue.csv",
        mapping_queue,
        ["task_id", "l2_event_id", "l2_event_mapping_id", "source_family", "source_packet_id", "provider", "publication_date", "mapping_scope", "mapping_status", "candidate_symbol", "candidate_entity", "candidate_sector", "candidate_macro", "candidate_rule", "review_status", "review_reason"],
    )
    write_csv(
        ARTIFACT_DIR / "l2_input_scope_audit.csv",
        input_scope,
        ["task_id", "source_family", "l1_packet_rows_available", "l0_audit_sample_rows_available", "l0_lane_health", "l0_lane_progress_pct", "l0_lane_running", "l0_lane_complete", "scope_status", "next_action"],
    )
    write_csv(ARTIFACT_DIR / "l2_mapping_scope_summary.csv", counter_rows(view_rows, "mapping_scope"), ["task_id", "mapping_scope", "count"])
    write_csv(ARTIFACT_DIR / "l2_dedup_summary.csv", counter_rows(view_rows, "dedup_status"), ["task_id", "dedup_status", "count"])
    write_csv(ARTIFACT_DIR / "l2_stale_status_summary.csv", counter_rows(view_rows, "stale_status"), ["task_id", "stale_status", "count"])
    cut_rows = [
        {"task_id": TASK_ID, "cut_item": "LLM sentiment", "reason": "L2 must not create bullish/bearish interpretation"},
        {"task_id": TASK_ID, "cut_item": "embedding dedup", "reason": "deterministic dedup is enough for current L2 boundary"},
        {"task_id": TASK_ID, "cut_item": "full entity resolution system", "reason": "too large; mapping review queue is sufficient now"},
        {"task_id": TASK_ID, "cut_item": "DB schema migration", "reason": "artifact-first L2 completion avoids dirty DB blast radius"},
        {"task_id": TASK_ID, "cut_item": "return/alpha/signal/ranking", "reason": "belongs to L3/L4/backtest or later decision layers"},
    ]
    write_csv(ARTIFACT_DIR / "l2_completion_cut_list.csv", cut_rows, ["task_id", "cut_item", "reason"])
    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "gpt_capture_status": "captured",
        "source_admission_rows": len(view_rows),
        "l3_read_rows": len(read_rows),
        "mapping_review_rows": len(mapping_queue),
        "input_scope_blocked_families": sum(1 for row in input_scope if str(row["scope_status"]).startswith("BLOCKED")),
        "feature_materialization_allowed_rows": 0,
        "trading_authority_opened_rows": 0,
        "paper_live_broker_order_opened_rows": 0,
        "overengineering_cut_items": len(cut_rows),
    }
    (REPORT_DIR / "l2_completion_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    report = "# TASK-4143 L2 Completion GPT Review And Read Contract\n\n"
    report += "## 결론\n\n"
    report += "GPT Pro 검수안은 L2 완성을 signal/score가 아니라 안전한 admission/read layer 완성으로 정의했다. Codex는 과도한 작업을 컷하고, L3 whitelist read view와 mapping review queue, input-scope audit, hard validator/QA 산출물로 범위를 닫았다.\n\n"
    report += "| 항목 | 값 |\n|---|---:|\n"
    for key in ["source_admission_rows", "l3_read_rows", "mapping_review_rows", "input_scope_blocked_families", "overengineering_cut_items"]:
        report += f"| {key} | {summary[key]} |\n"
    report += "\n## 컷한 것\n\n"
    for row in cut_rows:
        report += f"- `{row['cut_item']}`: {row['reason']}\n"
    report += "\n## L2 경계\n\n"
    report += "- L3 read view에는 whitelist 컬럼만 남겼다.\n"
    report += "- UNKNOWN mapping은 L3 read view가 아니라 review queue로 보낸다.\n"
    report += "- stale historical row는 archive/context로 보존하되 부정 증거로 쓰지 않는다.\n"
    report += "- feature materialization, trading authority, paper/live/broker/order는 열지 않았다.\n"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")
    write_manifest()
    return summary


def main() -> int:
    print(json.dumps(build_and_write(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
