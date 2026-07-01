from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4142"
SLUG = "task_4142_l2_swing_event_admission"
ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
L1_PACKET_PATH = ROOT / "data" / "artifacts" / "task_4133_l1_development_plan" / "l1_normalized_source_packets_sample.csv"
SWING_POLICY_PATH = ROOT / "data" / "artifacts" / "task_4140_swing_news_macro_newswire_feature_admission" / "swing_feature_admission_policy.csv"

TARGET_FAMILIES = {
    "public_context_news_feeds",
    "public_market_macro_news_feeds",
    "public_newswire_feeds",
}

VIEW_COLUMNS = [
    "task_id",
    "l2_event_id",
    "l2_event_mapping_id",
    "source_family",
    "source_packet_id",
    "candidate_id",
    "raw_path",
    "raw_sha256",
    "provider",
    "endpoint_or_source_family",
    "source_ts",
    "publication_date",
    "publication_time_precision",
    "is_publication_time_imputed",
    "available_to_brain_ts",
    "decision_asof_ts",
    "activation_policy",
    "activation_decision_date",
    "source_time_basis",
    "source_time_certified",
    "mapping_scope",
    "mapping_key",
    "symbol",
    "entity_id",
    "sector_key",
    "macro_key",
    "mapping_confidence_rule",
    "mapping_status",
    "dedup_key",
    "event_cluster_id",
    "is_canonical_event",
    "duplicate_of_event_id",
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
    "admission_status",
    "block_reason",
    "l3_read_allowed",
    "feature_materialization_allowed",
    "trading_authority_opened",
    "paper_live_broker_order_opened",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: Any, length: int = 16) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_date(dt: datetime | None) -> str:
    return dt.date().isoformat() if dt else ""


def add_days(date_text: str, days: int) -> str:
    if not date_text:
        return ""
    parsed = datetime.strptime(date_text, "%Y-%m-%d").date()
    return (parsed + timedelta(days=days)).isoformat()


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


def load_swing_policy() -> dict[str, dict[str, str]]:
    return {row["source_family"]: row for row in read_csv(SWING_POLICY_PATH)}


def publication_precision(row: dict[str, str], source_dt: datetime | None) -> tuple[str, str]:
    raw_path = row.get("raw_path", "")
    source_text = row.get("source_ts", "")
    if "wikimedia_current_events" in raw_path:
        return "IMPUTED_NOMINAL", "1"
    if not source_text:
        return "UNKNOWN", "0"
    if len(source_text.strip()) == 10:
        return "DAY", "0"
    if source_dt and source_dt.hour == 0 and source_dt.minute == 0 and source_dt.second == 0:
        return "DAY", "0"
    return "SECOND", "0"


def mapping_fields(row: dict[str, str]) -> dict[str, str]:
    family = row["endpoint_or_source_family"]
    symbol = row.get("symbol", "").strip().upper()
    mapping_status = row.get("mapping_status", "")
    if symbol:
        return {
            "mapping_scope": "TICKER",
            "mapping_key": symbol,
            "symbol": symbol,
            "entity_id": "",
            "sector_key": "",
            "macro_key": "",
            "mapping_confidence_rule": "L1_SYMBOL_EXACT",
            "mapping_status": "MAPPED",
        }
    if "MACRO_CONTEXT" in mapping_status or row.get("macro_context_candidate") == "1" or family == "public_market_macro_news_feeds":
        macro_key = "public_market_macro" if family == "public_market_macro_news_feeds" else "public_context_macro"
        return {
            "mapping_scope": "MACRO",
            "mapping_key": macro_key,
            "symbol": "",
            "entity_id": "",
            "sector_key": "",
            "macro_key": macro_key,
            "mapping_confidence_rule": "L1_MACRO_CONTEXT",
            "mapping_status": "MAPPED",
        }
    return {
        "mapping_scope": "UNKNOWN",
        "mapping_key": "",
        "symbol": "",
        "entity_id": "",
        "sector_key": "",
        "macro_key": "",
        "mapping_confidence_rule": "NO_HIGH_CONFIDENCE_MAPPING",
        "mapping_status": "BLOCKED_UNKNOWN",
    }


def event_meaning(row: dict[str, str], mapping_scope: str) -> tuple[str, str, str, str]:
    family = row["endpoint_or_source_family"]
    if family == "public_market_macro_news_feeds" or mapping_scope == "MACRO":
        return "MACRO", "MACRO_CONTEXT", "macro_context", "TAGGED"
    if family == "public_newswire_feeds":
        return "COMPANY", "NEWSWIRE_DISCOVERY", "newswire|company_event_candidate", "UNTAGGED_ALLOWED"
    return "POLICY", "PUBLIC_CONTEXT", "public_context|policy_or_macro_candidate", "UNTAGGED_ALLOWED"


def stale_fields(activation_date: str, decision_dt: datetime | None) -> tuple[str, dict[str, str]]:
    windows = {
        "window_1d_start_date": activation_date,
        "window_1d_end_date": add_days(activation_date, 1),
        "window_5d_start_date": activation_date,
        "window_5d_end_date": add_days(activation_date, 5),
        "window_20d_start_date": activation_date,
        "window_20d_end_date": add_days(activation_date, 20),
        "window_60d_start_date": activation_date,
        "window_60d_end_date": add_days(activation_date, 60),
    }
    if not activation_date or not decision_dt:
        return "BLOCKED_TIMING_UNKNOWN", windows
    activation_dt = datetime.strptime(activation_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    age_days = (decision_dt.date() - activation_dt.date()).days
    if age_days < 0:
        return "PENDING_NEXT_DAILY_DECISION", windows
    if age_days <= 20:
        return "ACTIVE_PRIMARY", windows
    if age_days <= 60:
        return "ACTIVE_SECONDARY", windows
    return "ARCHIVE_CONTEXT_ONLY", windows


def base_block_reason(row: dict[str, str], source_dt: datetime | None, available_dt: datetime | None, decision_dt: datetime | None) -> str:
    if row.get("source_time_certified") != "1":
        return "BLOCKED_SOURCE_TIME"
    if not row.get("raw_path") or not row.get("raw_sha256"):
        return "BLOCKED_RAW_INTEGRITY"
    if row.get("missing_source_is_negative") != "0" or row.get("assignment_uses_future_outcome") != "0" or row.get("outcome_used_for_assignment") != "0":
        return "BLOCKED_LEAKAGE_RISK"
    if row.get("l1_gate_classification", "").startswith("BLOCKED"):
        return "BLOCKED_SOURCE_TIME"
    if source_dt and available_dt and decision_dt and not (source_dt <= available_dt <= decision_dt):
        return "BLOCKED_LEAKAGE_RISK"
    if not (source_dt and available_dt and decision_dt):
        return "BLOCKED_SOURCE_TIME"
    return ""


def build_view_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    policy = load_swing_policy()
    source_rows = [
        row for row in read_csv(L1_PACKET_PATH)
        if row.get("endpoint_or_source_family") in TARGET_FAMILIES
    ]
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        family = row["endpoint_or_source_family"]
        family_policy = policy.get(family, {})
        source_dt = parse_ts(row.get("source_ts"))
        available_dt = parse_ts(row.get("available_to_brain_ts"))
        decision_dt = parse_ts(row.get("decision_asof_ts"))
        publication_date = iso_date(source_dt)
        precision, is_imputed = publication_precision(row, source_dt)
        activation_policy = family_policy.get("activation_policy", "NEXT_TRADING_SESSION_OR_NEXT_DAILY_DECISION")
        activation_date = add_days(publication_date, 1)
        mapping = mapping_fields(row)
        event_domain, event_type, topic_tags, economic_status = event_meaning(row, mapping["mapping_scope"])
        stale_status, windows = stale_fields(activation_date, decision_dt)
        dedup_key = stable_hash({
            "family": family,
            "publication_date": publication_date,
            "mapping_scope": mapping["mapping_scope"],
            "mapping_key": mapping["mapping_key"],
            "event_type": event_type,
            "candidate_id": row.get("candidate_id", ""),
        }, length=20)
        event_cluster_id = "l2cluster_" + stable_hash({"dedup_key": dedup_key}, length=16)
        l2_event_id = "l2event_" + stable_hash({"cluster": event_cluster_id}, length=16)
        l2_event_mapping_id = "l2map_" + stable_hash({"event": l2_event_id, "scope": mapping["mapping_scope"], "key": mapping["mapping_key"]}, length=16)
        block_reason = base_block_reason(row, source_dt, available_dt, decision_dt)
        if not block_reason and family_policy.get("swing_feature_candidate_now") != "1":
            block_reason = "BLOCKED_POLICY_MISMATCH"
        review_reason = ""
        if not block_reason and mapping["mapping_scope"] == "UNKNOWN":
            review_reason = "MAPPING_REVIEW_REQUIRED_NOT_FEATURE"
        if not block_reason and stale_status == "BLOCKED_TIMING_UNKNOWN":
            block_reason = "BLOCKED_SOURCE_TIME"
        admission_status = block_reason or review_reason or "ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE"
        rows.append({
            "task_id": TASK_ID,
            "l2_event_id": l2_event_id,
            "l2_event_mapping_id": l2_event_mapping_id,
            "source_family": family,
            "source_packet_id": row.get("source_packet_id", ""),
            "candidate_id": row.get("candidate_id", ""),
            "raw_path": row.get("raw_path", ""),
            "raw_sha256": row.get("raw_sha256", ""),
            "provider": row.get("provider", ""),
            "endpoint_or_source_family": family,
            "source_ts": row.get("source_ts", ""),
            "publication_date": publication_date,
            "publication_time_precision": precision,
            "is_publication_time_imputed": is_imputed,
            "available_to_brain_ts": row.get("available_to_brain_ts", ""),
            "decision_asof_ts": row.get("decision_asof_ts", ""),
            "activation_policy": activation_policy,
            "activation_decision_date": activation_date,
            "source_time_basis": row.get("source_time_basis", ""),
            "source_time_certified": row.get("source_time_certified", ""),
            **mapping,
            "dedup_key": dedup_key,
            "event_cluster_id": event_cluster_id,
            "is_canonical_event": "1",
            "duplicate_of_event_id": "",
            "cluster_member_count": "1",
            "dedup_status": "UNIQUE",
            "event_domain": event_domain,
            "event_type": event_type,
            "topic_tags": topic_tags,
            "economic_meaning_status": economic_status,
            "primary_effect_window": family_policy.get("primary_effect_window", "20D"),
            "secondary_effect_windows": family_policy.get("secondary_effect_windows", "1D|5D|60D"),
            **windows,
            "stale_status": stale_status,
            "admission_status": admission_status,
            "block_reason": "" if admission_status in {"ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE", "MAPPING_REVIEW_REQUIRED_NOT_FEATURE"} else admission_status,
            "l3_read_allowed": "1" if admission_status in {"ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE", "MAPPING_REVIEW_REQUIRED_NOT_FEATURE"} else "0",
            "feature_materialization_allowed": "0",
            "trading_authority_opened": "0",
            "paper_live_broker_order_opened": "0",
        })

    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        clusters[str(row["dedup_key"])].append(row)
    dedup_rows: list[dict[str, Any]] = []
    for dedup_key, members in clusters.items():
        canonical = members[0]
        for idx, row in enumerate(members):
            row["cluster_member_count"] = str(len(members))
            if idx == 0:
                row["is_canonical_event"] = "1"
                row["dedup_status"] = "CANONICAL" if len(members) > 1 else "UNIQUE"
            else:
                row["is_canonical_event"] = "0"
                row["duplicate_of_event_id"] = canonical["l2_event_id"]
                row["dedup_status"] = "DUPLICATE_BLOCKED"
                row["admission_status"] = "BLOCKED_DUPLICATE_NON_CANONICAL"
                row["block_reason"] = "BLOCKED_DUPLICATE_NON_CANONICAL"
                row["l3_read_allowed"] = "0"
        dedup_rows.append({
            "task_id": TASK_ID,
            "dedup_key": dedup_key,
            "event_cluster_id": canonical["event_cluster_id"],
            "canonical_l2_event_id": canonical["l2_event_id"],
            "cluster_member_count": len(members),
            "source_families": "|".join(sorted({str(m["source_family"]) for m in members})),
            "dedup_status": "CLUSTERED" if len(members) > 1 else "UNIQUE",
        })
    return rows, dedup_rows


def summary_rows(view_rows: list[dict[str, Any]], key: str, count_name: str = "count") -> list[dict[str, Any]]:
    counts = Counter(str(row.get(key, "")) for row in view_rows)
    return [{"task_id": TASK_ID, key: item, count_name: count} for item, count in sorted(counts.items())]


def build_and_write() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    view_rows, dedup_rows = build_view_rows()
    write_csv(ARTIFACT_DIR / "l2_swing_event_admission_view.csv", view_rows, VIEW_COLUMNS)
    write_jsonl(ARTIFACT_DIR / "l2_swing_event_admission_view.jsonl", view_rows)
    mapping_issues = [row for row in view_rows if row["mapping_scope"] == "UNKNOWN" or row["mapping_status"] != "MAPPED"]
    write_csv(ARTIFACT_DIR / "l2_mapping_issues.csv", mapping_issues, VIEW_COLUMNS)
    write_csv(
        ARTIFACT_DIR / "l2_dedup_clusters.csv",
        dedup_rows,
        ["task_id", "dedup_key", "event_cluster_id", "canonical_l2_event_id", "cluster_member_count", "source_families", "dedup_status"],
    )
    write_csv(ARTIFACT_DIR / "l2_block_reason_summary.csv", summary_rows(view_rows, "admission_status"), ["task_id", "admission_status", "count"])
    family_rows = []
    for family in sorted(TARGET_FAMILIES):
        family_view = [row for row in view_rows if row["source_family"] == family]
        family_rows.append({
            "task_id": TASK_ID,
            "source_family": family,
            "input_rows": len(family_view),
            "admitted_rows": sum(1 for row in family_view if row["admission_status"] == "ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE"),
            "review_rows": sum(1 for row in family_view if str(row["admission_status"]).startswith("MAPPING_REVIEW")),
            "blocked_rows": sum(1 for row in family_view if str(row["admission_status"]).startswith("BLOCKED")),
            "mapping_unknown_rows": sum(1 for row in family_view if row["mapping_scope"] == "UNKNOWN"),
            "archive_context_rows": sum(1 for row in family_view if row["stale_status"] == "ARCHIVE_CONTEXT_ONLY"),
        })
    write_csv(
        ARTIFACT_DIR / "l2_family_count_summary.csv",
        family_rows,
        ["task_id", "source_family", "input_rows", "admitted_rows", "review_rows", "blocked_rows", "mapping_unknown_rows", "archive_context_rows"],
    )
    validation_report = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "input_rows": len(view_rows),
        "admitted_rows": sum(1 for row in view_rows if row["admission_status"] == "ADMITTED_FOR_L3_RESEARCH_NOT_FEATURE"),
        "review_rows": sum(1 for row in view_rows if str(row["admission_status"]).startswith("MAPPING_REVIEW")),
        "blocked_rows": sum(1 for row in view_rows if str(row["admission_status"]).startswith("BLOCKED")),
        "mapping_issue_rows": len(mapping_issues),
        "dedup_clusters": len(dedup_rows),
        "feature_materialization_allowed_rows": sum(1 for row in view_rows if row["feature_materialization_allowed"] != "0"),
        "trading_authority_opened_rows": sum(1 for row in view_rows if row["trading_authority_opened"] != "0"),
        "paper_live_broker_order_opened_rows": sum(1 for row in view_rows if row["paper_live_broker_order_opened"] != "0"),
    }
    (ARTIFACT_DIR / "l2_swing_event_admission_validation_report.json").write_text(
        json.dumps(validation_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    report_md = "# TASK-4142 L2 Swing Event Admission Validation Report\n\n"
    report_md += "| 항목 | 값 |\n|---|---:|\n"
    for key in ["input_rows", "admitted_rows", "review_rows", "blocked_rows", "mapping_issue_rows", "dedup_clusters"]:
        report_md += f"| {key} | {validation_report[key]} |\n"
    report_md += "\n## Source Family Summary\n\n"
    report_md += "| Source | Input | Admitted | Review | Blocked | Unknown Mapping | Archive Context |\n|---|---:|---:|---:|---:|---:|---:|\n"
    for row in family_rows:
        report_md += f"| `{row['source_family']}` | {row['input_rows']} | {row['admitted_rows']} | {row['review_rows']} | {row['blocked_rows']} | {row['mapping_unknown_rows']} | {row['archive_context_rows']} |\n"
    report_md += "\n## Boundary\n\n- feature materialization: closed\n- trading authority: closed\n- paper/live/broker/order: closed\n- outcome/return/alpha/ranking columns: not produced\n"
    (ARTIFACT_DIR / "l2_swing_event_admission_validation_report.md").write_text(report_md, encoding="utf-8", newline="\n")
    write_report(view_rows, family_rows)
    write_manifest()
    summary = {
        **validation_report,
        "target_families": sorted(TARGET_FAMILIES),
        "primary_effect_window": "20D",
        "secondary_effect_windows": ["1D", "5D", "60D"],
        "view_path": f"data/artifacts/{SLUG}/l2_swing_event_admission_view.csv",
    }
    (REPORT_DIR / "l2_swing_event_admission_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    return summary


def clean_task_report(view_rows: list[dict[str, Any]], family_rows: list[dict[str, Any]]) -> str:
    report = "# TASK-4142 L2 Swing Event Admission View\n\n"
    report += "## 결론\n\n"
    report += "GPT Pro 설계에 따라 L2의 첫 view를 만들었다. 이 view는 뉴스/매크로/뉴스와이어를 점수화하지 않고, L3가 읽을 수 있는 이벤트 후보인지와 아직 검토가 필요한 이유만 정리한다.\n\n"
    report += "| 원칙 | 결과 |\n|---|---|\n"
    report += "| 뉴스/매크로/뉴스와이어 | 스윙 event 후보로 처리 |\n"
    report += "| 분/초 timestamp | 필수 조건 아님 |\n"
    report += "| day-level / imputed time | 명시적으로 표시 |\n"
    report += "| mapping unknown | hard block이 아니라 mapping review 상태 |\n"
    report += "| stale historical row | active feature가 아니라 archive/context 상태 |\n"
    report += "| feature score/signal | 만들지 않음 |\n"
    report += "| broker/paper/live/order | 열지 않음 |\n\n"
    report += "## Family Summary\n\n"
    report += "| Source | Input | Admitted | Review | Blocked | Unknown Mapping | Archive Context |\n|---|---:|---:|---:|---:|---:|---:|\n"
    for row in family_rows:
        report += f"| `{row['source_family']}` | {row['input_rows']} | {row['admitted_rows']} | {row['review_rows']} | {row['blocked_rows']} | {row['mapping_unknown_rows']} | {row['archive_context_rows']} |\n"
    report += "\n## Sample Rows\n\n"
    report += "| Source | Mapping | Stale | Admission | Reason |\n|---|---|---|---|---|\n"
    for row in view_rows[:8]:
        report += f"| `{row['source_family']}` | `{row['mapping_scope']}` | `{row['stale_status']}` | `{row['admission_status']}` | `{row['block_reason']}` |\n"
    report += "\n## 다음 단계\n\n"
    report += "1. 실제 L0/L1 전체 row로 view 입력 범위를 넓힌다.\n"
    report += "2. deterministic mapping rule을 ticker/entity/sector/macro별로 보강한다.\n"
    report += "3. dedup cluster를 headline/content hash 기반으로 고도화한다.\n"
    report += "4. L3 read contract sample로 넘긴다.\n"
    return report


def write_report(view_rows: list[dict[str, Any]], family_rows: list[dict[str, Any]]) -> None:
    report = "# TASK-4142 L2 Swing Event Admission View\n\n"
    report += "## 결론\n\n"
    report += "GPT Pro 설계대로 L2 첫 view를 만들었다. 이 view는 뉴스/매크로/뉴스와이어를 점수화하지 않고, L3가 읽을 수 있는 후보인지 admission 상태만 정리한다.\n\n"
    report += "| 원칙 | 결과 |\n|---|---|\n"
    report += "| 뉴스/매크로/뉴스와이어 | 스윙 event 후보로 처리 |\n"
    report += "| 분/초 timestamp | 필수 조건 아님 |\n"
    report += "| day-level / imputed time | 명시적으로 표시 |\n"
    report += "| mapping unknown | feature admission block |\n"
    report += "| stale | active feature가 아니라 archive/context 상태로 표시 |\n"
    report += "| feature score/signal | 만들지 않음 |\n"
    report += "| broker/paper/live/order | 열지 않음 |\n\n"
    report += "## Family Summary\n\n"
    report += "| Source | Input | Admitted | Review | Blocked | Unknown Mapping | Archive Context |\n|---|---:|---:|---:|---:|---:|---:|\n"
    for row in family_rows:
        report += f"| `{row['source_family']}` | {row['input_rows']} | {row['admitted_rows']} | {row['review_rows']} | {row['blocked_rows']} | {row['mapping_unknown_rows']} | {row['archive_context_rows']} |\n"
    report += "\n## Sample Rows\n\n"
    report += "| Source | Mapping | Stale | Admission | Reason |\n|---|---|---|---|---|\n"
    for row in view_rows[:8]:
        report += f"| `{row['source_family']}` | `{row['mapping_scope']}` | `{row['stale_status']}` | `{row['admission_status']}` | `{row['block_reason']}` |\n"
    report += "\n## 다음 단계\n\n"
    report += "1. 실제 L0/L1 전체 row로 view 입력 범위를 넓힌다.\n"
    report += "2. deterministic mapping rule을 ticker/entity/sector/macro별로 보강한다.\n"
    report += "3. dedup cluster를 headline/content hash 기반으로 고도화한다.\n"
    report += "4. L3 read contract sample로 넘어간다.\n"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "report.md").write_text(clean_task_report(view_rows, family_rows), encoding="utf-8", newline="\n")


def write_manifest() -> None:
    rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4142 task definition and closeout state", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4142 document registry entries", "modified"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "active_doc", "TASK-4142 active report pointer", "modified"),
        ("docs/active/CURRENT_TASKS.md", "active_doc", "TASK-4142 completion pointer", "modified"),
        ("docs/active/PROJECT_STATUS.md", "active_doc", "TASK-4142 status note", "modified"),
        ("scripts/run_l2_swing_event_admission_4142.py", "script", "Build L2 swing event admission view", "created"),
        ("scripts/validate_l2_swing_event_admission_4142.py", "validator", "Validate L2 swing event admission view", "created"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4142 report", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4142 artifact manifest", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4142 validation results", "created"),
        (f"docs/reports/{SLUG}/l2_swing_event_admission_summary.json", "summary", "Machine-readable TASK-4142 summary", "created"),
        (f"data/artifacts/{SLUG}/l2_swing_event_admission_view.csv", "artifact", "L2 swing event admission view CSV", "created"),
        (f"data/artifacts/{SLUG}/l2_swing_event_admission_view.jsonl", "artifact", "L2 swing event admission view JSONL", "created"),
        (f"data/artifacts/{SLUG}/l2_swing_event_admission_validation_report.json", "artifact", "Admission validation JSON report", "created"),
        (f"data/artifacts/{SLUG}/l2_swing_event_admission_validation_report.md", "artifact", "Admission validation Markdown report", "created"),
        (f"data/artifacts/{SLUG}/l2_mapping_issues.csv", "artifact", "Mapping issue rows", "created"),
        (f"data/artifacts/{SLUG}/l2_dedup_clusters.csv", "artifact", "Dedup cluster rows", "created"),
        (f"data/artifacts/{SLUG}/l2_block_reason_summary.csv", "artifact", "Block reason summary", "created"),
        (f"data/artifacts/{SLUG}/l2_family_count_summary.csv", "artifact", "Source family count summary", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "artifact", "Machine-readable validator report", "created"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [
            {"path": path, "type": typ, "purpose": purpose, "created_or_modified": state, "task_id": TASK_ID}
            for path, typ, purpose, state in rows
        ],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )


def main() -> int:
    print(json.dumps(build_and_write(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
