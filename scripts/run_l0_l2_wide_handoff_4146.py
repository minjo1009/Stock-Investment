from __future__ import annotations

import csv
import glob
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4146"
SLUG = "task_4146_l0_l2_wide_packetization_handoff"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG

EVENT_LEDGER_SPECS = [
    ("public_context_news_feeds", ROOT / "data/artifacts/l0_public_context_news_backfill/collector_events.jsonl"),
    ("public_newswire_feeds", ROOT / "data/artifacts/l0_public_newswire_backfill/collector_events.jsonl"),
    ("public_newswire_feeds", ROOT / "data/artifacts/l0_public_newswire_backfill_shards/*/*/collector_events.jsonl"),
    ("public_market_macro_news_feeds", ROOT / "data/artifacts/l0_public_market_macro_news_backfill/collector_events.jsonl"),
]
RECALL_OVERLAY_PATHS = [
    ROOT / "data/artifacts/task_4164_l0_runtime_consistency_recall_propagation/businesswire/l0_public_newswire_recall_overlay.csv",
    ROOT / "data/artifacts/task_4164_l0_runtime_consistency_recall_propagation/prnewswire/l0_public_newswire_recall_overlay.csv",
    ROOT / "data/artifacts/task_4163_gn_filtering_recall_audit/l0_public_newswire_recall_overlay.csv",
]
LANE_RELIABILITY_PATH = ROOT / "data/artifacts/l0_backfill_orchestration/lane_reliability.csv"
SUPERVISOR_RECOMMENDATIONS_PATH = ROOT / "data/artifacts/l0_backfill_orchestration/supervisor_recommendations.json"
CURRENT_ALERTS_PATH = ROOT / "data/artifacts/l0_backfill_orchestration/current_alerts.json"

TARGET_FAMILIES = {
    "public_context_news_feeds",
    "public_market_macro_news_feeds",
    "public_newswire_feeds",
}

SOURCE_LEDGER_COLUMNS = [
    "task_id",
    "source_family",
    "source_id",
    "source_key",
    "provider",
    "status",
    "raw_path",
    "raw_sha256",
    "raw_path_exists",
    "row_count",
    "l1_context_ready_count",
    "l1_ready_discovery_only_count",
    "l1_blocked_count",
    "mapped_rows",
    "blocked_unmapped_rows",
    "blocked_ambiguous_rows",
    "newswire_recall_review_rows",
    "entity_candidate_review_rows",
    "updated_at",
    "diagnostic_only_flag",
    "trade_authority_flag",
    "broker_mutation_permitted_flag",
    "real_capital_permitted_flag",
]

PACKET_COLUMNS = [
    "task_id",
    "source_packet_id",
    "candidate_id",
    "trade_spec_id",
    "symbol",
    "decision_asof_ts",
    "provider",
    "endpoint_or_source_family",
    "source_ts",
    "available_to_brain_ts",
    "source_time_basis",
    "source_time_certified",
    "raw_path",
    "raw_sha256",
    "strict_gate_pass",
    "proxy_feature_allowed",
    "missing_source_is_negative",
    "assignment_uses_future_outcome",
    "outcome_used_for_assignment",
    "authority",
    "raw_locator_type",
    "mapping_status",
    "macro_context_candidate",
    "candidate_hint_only",
    "l1_gate_classification",
    "l2_allowed_scope",
    "blocker_reason",
    "l0_row_count",
    "l1_context_ready_count",
    "l1_ready_discovery_only_count",
    "l1_blocked_count",
    "mapped_rows",
    "blocked_unmapped_rows",
    "newswire_recall_review_rows",
    "entity_candidate_review_rows",
]

L2_COLUMNS = [
    "task_id",
    "l2_wide_event_id",
    "source_packet_id",
    "source_family",
    "raw_path",
    "raw_sha256",
    "provider",
    "source_ts",
    "available_to_brain_ts",
    "decision_asof_ts",
    "mapping_scope",
    "mapping_status",
    "event_domain",
    "admission_status",
    "l3_read_allowed",
    "review_queue_allowed",
    "feature_candidate_materialization_allowed",
    "feature_materialization_scope",
    "feature_candidate_count",
    "review_candidate_count",
    "newswire_recall_review_count",
    "entity_candidate_review_count",
    "blocked_candidate_count",
    "block_reason",
    "trading_authority_opened",
    "paper_live_broker_order_opened",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            return p.relative_to(ROOT).as_posix()
        except ValueError:
            return p.as_posix()
    return p.as_posix()


def stable_hash(payload: Any, length: int = 18) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def parse_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"$p=Get-Process -Id {pid} -ErrorAction SilentlyContinue; if ($p) {{ '1' }} else {{ '0' }}",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        return result.stdout.strip().endswith("1")
    try:
        import os

        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def event_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def event_paths(path: Path) -> list[Path]:
    text = str(path)
    if any(token in text for token in ("*", "?", "[")):
        return [Path(item) for item in sorted(glob.glob(text))]
    return [path]


def normalized_raw_path(value: str) -> str:
    return value.replace("\\", "/")


def load_recall_overlay_counts() -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"newswire_recall_review_rows": 0, "entity_candidate_review_rows": 0})
    for path in RECALL_OVERLAY_PATHS:
        for row in read_csv(path):
            raw_path = normalized_raw_path(str(row.get("raw_path", "")))
            if not raw_path:
                continue
            counts[raw_path]["newswire_recall_review_rows"] += 1
            if str(row.get("new_entity_mapping_status", "")) == "ENTITY_CANDIDATE_REVIEW":
                counts[raw_path]["entity_candidate_review_rows"] += 1
    return dict(counts)


def source_key_from_row(row: dict[str, Any]) -> str:
    notes = str(row.get("notes", ""))
    match = re.search(r"source_key=([^;]+)", notes)
    if match:
        return match.group(1)
    source_id = str(row.get("source_id", ""))
    if "::" in source_id:
        return source_id.split("::", 1)[0]
    raw_path = str(row.get("raw_path", ""))
    for part in re.split(r"[\\/]", raw_path):
        if part.startswith("source="):
            return part.split("=", 1)[1]
    return ""


def notes_count(row: dict[str, Any], key: str) -> int:
    notes = str(row.get("notes", ""))
    match = re.search(rf"{re.escape(key)}=([0-9]+)", notes)
    return int(match.group(1)) if match else 0


def captured_at_from_raw_path(raw_path: str) -> str:
    for part in re.split(r"[\\/]", raw_path):
        if part.startswith("captured_at="):
            value = part.split("=", 1)[1]
            try:
                dt = datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                return dt.isoformat().replace("+00:00", "Z")
            except ValueError:
                return ""
    return ""


def normalize_source_event(row: dict[str, Any], family_hint: str, recall_overlay_counts: dict[str, dict[str, int]] | None = None) -> dict[str, Any]:
    raw_path_text = str(row.get("raw_path", ""))
    raw_path = ROOT / raw_path_text if raw_path_text else Path("")
    source_key = source_key_from_row(row)
    l1_context = parse_int(row.get("l1_context_ready_count"))
    l1_discovery = parse_int(row.get("l1_ready_discovery_only_count"))
    l1_blocked = parse_int(row.get("l1_blocked_count"))
    mapped = parse_int(row.get("mapped_rows")) or notes_count(row, "mapped_rows")
    blocked_unmapped = parse_int(row.get("blocked_unmapped_rows")) or notes_count(row, "blocked_unmapped_rows")
    blocked_ambiguous = parse_int(row.get("blocked_ambiguous_rows")) or notes_count(row, "blocked_ambiguous_rows")
    recall_review = parse_int(row.get("newswire_recall_review_rows")) or notes_count(row, "newswire_recall_review_rows")
    entity_review = parse_int(row.get("entity_candidate_review_rows")) or notes_count(row, "entity_candidate_review_rows")
    overlay = (recall_overlay_counts or {}).get(normalized_raw_path(raw_path_text), {})
    recall_review = max(recall_review, parse_int(overlay.get("newswire_recall_review_rows")))
    entity_review = max(entity_review, parse_int(overlay.get("entity_candidate_review_rows")))
    return {
        "task_id": TASK_ID,
        "source_family": str(row.get("source_family") or family_hint),
        "source_id": str(row.get("source_id", "")),
        "source_key": source_key,
        "provider": str(row.get("provider") or family_hint),
        "status": str(row.get("status", "")),
        "raw_path": normalized_raw_path(raw_path_text),
        "raw_sha256": str(row.get("raw_sha256", "")),
        "raw_path_exists": "1" if raw_path_text and raw_path.exists() else "0",
        "row_count": parse_int(row.get("row_count")),
        "l1_context_ready_count": l1_context,
        "l1_ready_discovery_only_count": l1_discovery,
        "l1_blocked_count": l1_blocked,
        "mapped_rows": mapped,
        "blocked_unmapped_rows": blocked_unmapped,
        "blocked_ambiguous_rows": blocked_ambiguous,
        "newswire_recall_review_rows": recall_review,
        "entity_candidate_review_rows": entity_review,
        "updated_at": str(row.get("updated_at", "")),
        "diagnostic_only_flag": parse_int(row.get("diagnostic_only_flag")),
        "trade_authority_flag": parse_int(row.get("trade_authority_flag")),
        "broker_mutation_permitted_flag": parse_int(row.get("broker_mutation_permitted_flag")),
        "real_capital_permitted_flag": parse_int(row.get("real_capital_permitted_flag")),
    }


def build_l0_source_ledger() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    recall_overlay_counts = load_recall_overlay_counts()
    for family, path in EVENT_LEDGER_SPECS:
        for event_path in event_paths(path):
            for event in event_rows(event_path):
                normalized = normalize_source_event(event, family, recall_overlay_counts)
                if normalized["source_family"] not in TARGET_FAMILIES:
                    continue
                key = (str(normalized["source_family"]), str(normalized["raw_path"]))
                if key in seen:
                    continue
                seen.add(key)
                rows.append(normalized)
    rows.sort(key=lambda row: (str(row["source_family"]), str(row["source_key"]), str(row["updated_at"]), str(row["raw_path"])))
    return rows


def classify_l1(row: dict[str, Any]) -> dict[str, str]:
    family = str(row["source_family"])
    status = str(row["status"])
    raw_ok = row.get("raw_path_exists") == "1" and bool(row.get("raw_sha256"))
    ready_count = parse_int(row.get("l1_context_ready_count")) + parse_int(row.get("l1_ready_discovery_only_count"))
    if status not in {"EXPORTED", "BACKFILL_COMPLETE"}:
        return {"classification": "BLOCKED_L0_STATUS", "reason": f"l0_status:{status}", "mapping_status": "NOT_EVALUATED", "scope": "blocked"}
    if parse_int(row.get("row_count")) <= 0 and ready_count <= 0:
        return {"classification": "BLOCKED_EMPTY_PROVIDER_RESPONSE", "reason": "l0_row_count_zero", "mapping_status": "NOT_EVALUATED", "scope": "blocked"}
    if not raw_ok:
        return {"classification": "BLOCKED_RAW_INTEGRITY", "reason": "raw_path_or_sha_missing", "mapping_status": "NOT_EVALUATED", "scope": "blocked"}
    if family == "public_newswire_feeds":
        if parse_int(row.get("mapped_rows")) > 0 or parse_int(row.get("l1_context_ready_count")) > 0:
            return {"classification": "DISCOVERY_MAPPED_CONTEXT_READY", "reason": "", "mapping_status": "NEWSWIRE_MAPPED_BY_L0_COLLECTOR", "scope": "NEWSWIRE_MAPPING_REVIEW_OR_CONTEXT"}
        if parse_int(row.get("l1_ready_discovery_only_count")) > 0:
            return {"classification": "DISCOVERY_ONLY", "reason": "", "mapping_status": "CANDIDATE_HINT_NON_AUTHORITY", "scope": "DISCOVERY_REVIEW_QUEUE_ONLY"}
        if parse_int(row.get("newswire_recall_review_rows")) > 0 or parse_int(row.get("entity_candidate_review_rows")) > 0:
            return {"classification": "DISCOVERY_ONLY", "reason": "", "mapping_status": "RECALL_OVERLAY_REVIEW_NON_AUTHORITY", "scope": "DISCOVERY_REVIEW_QUEUE_ONLY"}
        return {"classification": "BLOCKED_MAPPING", "reason": "newswire_unmapped", "mapping_status": "BLOCKED_UNKNOWN", "scope": "blocked"}
    if parse_int(row.get("l1_context_ready_count")) > 0 or ready_count > 0:
        return {"classification": "CONTEXT_ONLY_CERTIFIED", "reason": "", "mapping_status": "MACRO_CONTEXT_NO_SYMBOL_REQUIRED", "scope": "MACRO_CONTEXT_ONLY"}
    return {"classification": "BLOCKED_EMPTY_PROVIDER_RESPONSE", "reason": "no_l1_ready_rows_reported", "mapping_status": "NOT_EVALUATED", "scope": "blocked"}


def l1_packet(row: dict[str, Any]) -> dict[str, Any]:
    gate = classify_l1(row)
    available = row.get("updated_at") or captured_at_from_raw_path(str(row.get("raw_path", ""))) or utc_now()
    # Batch-level rows inherit L0 collector L1 counts. They are wide handoff packets,
    # not article-level publication-time claims.
    packet_id = "l1wide_" + stable_hash({"raw_path": row.get("raw_path"), "sha": row.get("raw_sha256")})
    return {
        "task_id": TASK_ID,
        "source_packet_id": packet_id,
        "candidate_id": row.get("source_id") or packet_id,
        "trade_spec_id": "",
        "symbol": "",
        "decision_asof_ts": available,
        "provider": row.get("provider", ""),
        "endpoint_or_source_family": row.get("source_family", ""),
        "source_ts": available,
        "available_to_brain_ts": available,
        "source_time_basis": "l0_collector_batch_l1_ready_counts_not_article_timestamp",
        "source_time_certified": "1" if not gate["classification"].startswith("BLOCKED") else "0",
        "raw_path": row.get("raw_path", ""),
        "raw_sha256": row.get("raw_sha256", ""),
        "strict_gate_pass": "0",
        "proxy_feature_allowed": "0",
        "missing_source_is_negative": "0",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": "PUBLIC_CONTEXT_PRIMARY" if row.get("source_family") != "public_newswire_feeds" else "DISCOVERY_HINT",
        "raw_locator_type": "file_sha256_from_l0_event_ledger",
        "mapping_status": gate["mapping_status"],
        "macro_context_candidate": "1" if row.get("source_family") != "public_newswire_feeds" else "0",
        "candidate_hint_only": "1" if row.get("source_family") == "public_newswire_feeds" else "0",
        "l1_gate_classification": gate["classification"],
        "l2_allowed_scope": gate["scope"],
        "blocker_reason": gate["reason"],
        "l0_row_count": row.get("row_count", 0),
        "l1_context_ready_count": row.get("l1_context_ready_count", 0),
        "l1_ready_discovery_only_count": row.get("l1_ready_discovery_only_count", 0),
        "l1_blocked_count": row.get("l1_blocked_count", 0),
        "mapped_rows": row.get("mapped_rows", 0),
        "blocked_unmapped_rows": row.get("blocked_unmapped_rows", 0),
        "newswire_recall_review_rows": row.get("newswire_recall_review_rows", 0),
        "entity_candidate_review_rows": row.get("entity_candidate_review_rows", 0),
    }


def l2_row(packet: dict[str, Any]) -> dict[str, Any]:
    family = packet["endpoint_or_source_family"]
    classification = packet["l1_gate_classification"]
    context_count = parse_int(packet.get("l1_context_ready_count"))
    discovery_count = parse_int(packet.get("l1_ready_discovery_only_count"))
    mapped_count = parse_int(packet.get("mapped_rows")) or context_count
    blocked_count = parse_int(packet.get("l1_blocked_count")) + parse_int(packet.get("blocked_unmapped_rows"))
    recall_review_count = parse_int(packet.get("newswire_recall_review_rows"))
    entity_review_count = parse_int(packet.get("entity_candidate_review_rows"))
    feature_count = 0
    review_count = 0
    mapping_scope = "MACRO" if family != "public_newswire_feeds" else "UNKNOWN"
    event_domain = "MACRO_CONTEXT" if family != "public_newswire_feeds" else "NEWSWIRE_DISCOVERY"
    if classification == "CONTEXT_ONLY_CERTIFIED":
        admission = "L2_CONTEXT_WIDE_ADMITTED"
        feature_count = context_count or discovery_count or parse_int(packet.get("l0_row_count"))
        mapping_scope = "MACRO"
    elif classification == "DISCOVERY_MAPPED_CONTEXT_READY":
        admission = "L2_NEWSWIRE_MAPPED_REVIEW_READY"
        feature_count = mapped_count
        review_count = max(discovery_count, mapped_count, recall_review_count)
        mapping_scope = "ENTITY_OR_TICKER_CANDIDATE"
    elif classification == "DISCOVERY_ONLY":
        admission = "L2_DISCOVERY_REVIEW_READY"
        review_count = max(discovery_count, recall_review_count)
    else:
        admission = "BLOCKED_" + classification.replace("BLOCKED_", "")
    feature_allowed = "1" if admission in {"L2_CONTEXT_WIDE_ADMITTED", "L2_NEWSWIRE_MAPPED_REVIEW_READY"} and feature_count > 0 else "0"
    return {
        "task_id": TASK_ID,
        "l2_wide_event_id": "l2wide_" + stable_hash({"source_packet_id": packet["source_packet_id"], "admission": admission}),
        "source_packet_id": packet["source_packet_id"],
        "source_family": family,
        "raw_path": packet["raw_path"],
        "raw_sha256": packet["raw_sha256"],
        "provider": packet["provider"],
        "source_ts": packet["source_ts"],
        "available_to_brain_ts": packet["available_to_brain_ts"],
        "decision_asof_ts": packet["decision_asof_ts"],
        "mapping_scope": mapping_scope,
        "mapping_status": packet["mapping_status"],
        "event_domain": event_domain,
        "admission_status": admission,
        "l3_read_allowed": "1" if admission.startswith("L2_") else "0",
        "review_queue_allowed": "1" if "REVIEW" in admission else "0",
        "feature_candidate_materialization_allowed": feature_allowed,
        "feature_materialization_scope": "diagnostic_batch_candidate_only_no_signal" if feature_allowed == "1" else "closed",
        "feature_candidate_count": feature_count,
        "review_candidate_count": review_count,
        "newswire_recall_review_count": recall_review_count,
        "entity_candidate_review_count": entity_review_count,
        "blocked_candidate_count": blocked_count,
        "block_reason": packet["blocker_reason"] if admission.startswith("BLOCKED") else "",
        "trading_authority_opened": "0",
        "paper_live_broker_order_opened": "0",
    }


def lane_recovery_rows() -> list[dict[str, Any]]:
    reliability = {row.get("lane"): row for row in read_csv(LANE_RELIABILITY_PATH)}
    recommendations = read_json(SUPERVISOR_RECOMMENDATIONS_PATH, [])
    if not isinstance(recommendations, list):
        recommendations = []
    rec_by_lane = {row.get("lane"): row for row in recommendations if isinstance(row, dict)}
    rows: list[dict[str, Any]] = []
    for lane in ["public_newswire_backfill", "public_market_macro_news_backfill", "public_context_news_backfill", "daily", "five_min"]:
        lane_row = reliability.get(lane, {})
        rec = rec_by_lane.get(lane, {})
        status_path = {
            "public_newswire_backfill": ROOT / "data/artifacts/l0_public_newswire_backfill_shards/background_process.json",
            "public_market_macro_news_backfill": ROOT / "data/artifacts/l0_public_market_macro_news_backfill/background_process.json",
            "public_context_news_backfill": ROOT / "data/artifacts/l0_public_context_news_backfill/background_process.json",
            "daily": ROOT / "data/artifacts/l0_bar_daily_full_backfill/background_process.json",
            "five_min": ROOT / "data/artifacts/l0_bar_full_backfill/background_process_5m.json",
        }[lane]
        status = read_json(status_path, {})
        pid = parse_int(status.get("pid")) if isinstance(status, dict) else 0
        alive = int(pid_alive(pid))
        complete = parse_int(lane_row.get("complete"))
        rows.append({
            "task_id": TASK_ID,
            "lane": lane,
            "health_at_audit": lane_row.get("health", ""),
            "running_at_audit": lane_row.get("running", ""),
            "complete_at_audit": lane_row.get("complete", ""),
            "progress_pct_at_audit": lane_row.get("progress_pct", ""),
            "recommendation": rec.get("action", ""),
            "recommendation_allowed": rec.get("allowed", ""),
            "recommendation_reason": rec.get("reason", ""),
            "background_status_path": rel(status_path),
            "background_pid_recorded_after_supervisor": pid,
            "background_pid_alive_after_supervisor": alive,
            "restart_status": "SHARDED_LAUNCHER_CONFIRMED_ALIVE" if lane == "public_newswire_backfill" and alive else "RESTART_CONFIRMED_ALIVE" if alive else "COMPLETE_OR_NO_LIVE_PID" if complete else "INCOMPLETE_WORKER_NOT_ALIVE",
        })
    return rows


def write_manifest() -> None:
    rows = [
        ("ops/task_registry.yaml", "registry", "TASK-4146 task definition and closeout state", "modified"),
        ("ops/doc_registry.yaml", "registry", "TASK-4146 document registry entries", "modified"),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "active_doc", "TASK-4146 active report pointer", "modified"),
        ("docs/active/CURRENT_TASKS.md", "active_doc", "TASK-4146 completion pointer", "modified"),
        ("docs/active/PROJECT_STATUS.md", "active_doc", "TASK-4146 status note", "modified"),
        ("scripts/run_l0_l2_wide_handoff_4146.py", "script", "Build wide L0-L1-L2 handoff artifacts", "created"),
        ("scripts/validate_l0_l2_wide_handoff_4146.py", "validator", "Validate wide L0-L1-L2 handoff artifacts", "created"),
        ("scripts/run_l0_l2_wide_handoff_loop_4146.ps1", "script", "Run continuous wide handoff loop", "created"),
        ("scripts/start_l0_l2_wide_handoff_loop_4146.ps1", "script", "Start continuous wide handoff loop", "created"),
        ("data/artifacts/l0_backfill_orchestration/supervisor_ledger.jsonl", "runtime_evidence", "Stopped lane restart evidence", "modified"),
        ("data/artifacts/l0_public_newswire_backfill_shards/background_process.json", "runtime_evidence", "Newswire sharded launcher PID evidence", "modified"),
        ("data/artifacts/l0_public_market_macro_news_backfill/background_process.json", "runtime_evidence", "Market/macro restart PID evidence", "modified"),
        (f"data/artifacts/{SLUG}/continuous_handoff_loop_status.json", "runtime_evidence", "Continuous wide handoff loop status", "created"),
        ("logs/task_4146_l0_l2_wide_handoff_loop.log", "runtime_evidence", "Continuous wide handoff loop log", "created"),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4146 report", "created"),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4146 artifact manifest", "created"),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4146 validation results", "created"),
        (f"docs/reports/{SLUG}/l0_l2_wide_handoff_summary.json", "summary", "Machine-readable TASK-4146 summary", "created"),
        (f"data/artifacts/{SLUG}/l0_wide_source_ledger.csv", "artifact", "Wide L0 source ledger", "created"),
        (f"data/artifacts/{SLUG}/l1_wide_normalized_source_packets.csv", "artifact", "Wide L1 normalized source packets", "created"),
        (f"data/artifacts/{SLUG}/l2_wide_admission_view.csv", "artifact", "Wide L2 admission view", "created"),
        (f"data/artifacts/{SLUG}/l2_feature_materialization_candidates.csv", "artifact", "Diagnostic feature candidate materialization rows", "created"),
        (f"data/artifacts/{SLUG}/l0_stopped_lane_recovery.csv", "artifact", "Stopped/incomplete lane recovery evidence", "created"),
        (f"data/artifacts/{SLUG}/continuous_handoff_plan.csv", "artifact", "Continuous handoff run plan", "created"),
        (f"data/artifacts/{SLUG}/source_family_rollup.csv", "artifact", "Source family rollup", "created"),
        (f"data/artifacts/{SLUG}/validator_report.json", "artifact", "Machine-readable validator report", "created"),
    ]
    write_csv(
        REPORT_DIR / "artifact_manifest.csv",
        [{"path": path, "type": typ, "purpose": purpose, "created_or_modified": state, "task_id": TASK_ID} for path, typ, purpose, state in rows],
        ["path", "type", "purpose", "created_or_modified", "task_id"],
    )


def build_and_write() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    l0_rows = build_l0_source_ledger()
    l1_rows = [l1_packet(row) for row in l0_rows]
    l2_rows = [l2_row(row) for row in l1_rows]
    feature_rows = [row for row in l2_rows if row["feature_candidate_materialization_allowed"] == "1"]
    lane_rows = lane_recovery_rows()
    continuous_rows = [
        {"task_id": TASK_ID, "step_order": 1, "step": "L0 collectors write collector_events.jsonl/raw files", "command": "existing background collectors", "activation_status": "background_lanes_running_or_restarted"},
        {"task_id": TASK_ID, "step_order": 2, "step": "Build wide L1/L2 handoff", "command": "python scripts/run_l0_l2_wide_handoff_4146.py", "activation_status": "ready"},
        {"task_id": TASK_ID, "step_order": 3, "step": "Validate wide handoff", "command": "python scripts/validate_l0_l2_wide_handoff_4146.py", "activation_status": "ready"},
        {"task_id": TASK_ID, "step_order": 4, "step": "Continuous post-L0 handoff loop refreshes wide counts", "command": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_l0_l2_wide_handoff_loop_4146.ps1 -IntervalSeconds 900", "activation_status": "started_background_loop"},
    ]
    family_rollup = []
    for family in sorted(TARGET_FAMILIES):
        family_l0 = [row for row in l0_rows if row["source_family"] == family]
        family_l1 = [row for row in l1_rows if row["endpoint_or_source_family"] == family]
        family_l2 = [row for row in l2_rows if row["source_family"] == family]
        family_rollup.append({
            "task_id": TASK_ID,
            "source_family": family,
            "l0_batch_rows": len(family_l0),
            "l0_raw_item_rows_reported": sum(parse_int(row.get("row_count")) for row in family_l0),
            "l1_packet_rows": len(family_l1),
            "l1_ready_packet_rows": sum(1 for row in family_l1 if not str(row["l1_gate_classification"]).startswith("BLOCKED")),
            "l2_admitted_or_review_rows": sum(1 for row in family_l2 if str(row["admission_status"]).startswith("L2_")),
            "feature_candidate_materialization_rows": sum(1 for row in family_l2 if row["feature_candidate_materialization_allowed"] == "1"),
            "feature_candidate_count": sum(parse_int(row.get("feature_candidate_count")) for row in family_l2),
            "blocked_l1_packet_rows": sum(1 for row in family_l1 if str(row["l1_gate_classification"]).startswith("BLOCKED")),
        })
    write_csv(ARTIFACT_DIR / "l0_wide_source_ledger.csv", l0_rows, SOURCE_LEDGER_COLUMNS)
    write_csv(ARTIFACT_DIR / "l1_wide_normalized_source_packets.csv", l1_rows, PACKET_COLUMNS)
    write_csv(ARTIFACT_DIR / "l2_wide_admission_view.csv", l2_rows, L2_COLUMNS)
    write_csv(ARTIFACT_DIR / "l2_feature_materialization_candidates.csv", feature_rows, L2_COLUMNS)
    write_csv(
        ARTIFACT_DIR / "l0_stopped_lane_recovery.csv",
        lane_rows,
        ["task_id", "lane", "health_at_audit", "running_at_audit", "complete_at_audit", "progress_pct_at_audit", "recommendation", "recommendation_allowed", "recommendation_reason", "background_status_path", "background_pid_recorded_after_supervisor", "background_pid_alive_after_supervisor", "restart_status"],
    )
    write_csv(ARTIFACT_DIR / "continuous_handoff_plan.csv", continuous_rows, ["task_id", "step_order", "step", "command", "activation_status"])
    write_csv(ARTIFACT_DIR / "source_family_rollup.csv", family_rollup, ["task_id", "source_family", "l0_batch_rows", "l0_raw_item_rows_reported", "l1_packet_rows", "l1_ready_packet_rows", "l2_admitted_or_review_rows", "feature_candidate_materialization_rows", "feature_candidate_count", "blocked_l1_packet_rows"])
    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "l0_batch_rows": len(l0_rows),
        "l0_raw_item_rows_reported": sum(parse_int(row.get("row_count")) for row in l0_rows),
        "l1_packet_rows": len(l1_rows),
        "l1_ready_packet_rows": sum(1 for row in l1_rows if not str(row["l1_gate_classification"]).startswith("BLOCKED")),
        "l1_blocked_packet_rows": sum(1 for row in l1_rows if str(row["l1_gate_classification"]).startswith("BLOCKED")),
        "l2_rows": len(l2_rows),
        "l2_admitted_or_review_rows": sum(1 for row in l2_rows if str(row["admission_status"]).startswith("L2_")),
        "feature_candidate_materialization_rows": len(feature_rows),
        "feature_candidate_count": sum(parse_int(row.get("feature_candidate_count")) for row in feature_rows),
        "stopped_lane_restart_pid_rows": sum(1 for row in lane_rows if parse_int(row.get("background_pid_recorded_after_supervisor")) > 0),
        "stopped_lane_restart_pid_alive_rows": sum(1 for row in lane_rows if parse_int(row.get("background_pid_alive_after_supervisor")) > 0),
        "trading_authority_opened_rows": sum(1 for row in l2_rows if row["trading_authority_opened"] != "0"),
        "paper_live_broker_order_opened_rows": sum(1 for row in l2_rows if row["paper_live_broker_order_opened"] != "0"),
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    write_json(REPORT_DIR / "l0_l2_wide_handoff_summary.json", summary)
    report = "# TASK-4146 L0-L2 Wide Packetization And Handoff\n\n"
    report += "## 결론\n\n"
    report += "L0 raw/backfill event ledger를 L1/L2가 넓게 먹도록 batch-level wide handoff를 만들었다. 기존 3-row L1/L2 샘플 한계를 넘겨, L0 collector event ledger 전체를 L1 packet과 L2 admission/materialization 후보로 연결한다. 이 materialization은 진단용 feature candidate이며 trading signal/order 권한은 열지 않는다.\n\n"
    report += "| 항목 | 값 |\n|---|---:|\n"
    for key in ["l0_batch_rows", "l0_raw_item_rows_reported", "l1_packet_rows", "l1_ready_packet_rows", "l1_blocked_packet_rows", "l2_admitted_or_review_rows", "feature_candidate_materialization_rows", "feature_candidate_count", "stopped_lane_restart_pid_rows", "stopped_lane_restart_pid_alive_rows"]:
        report += f"| {key} | {summary[key]} |\n"
    report += "\n## Source Family Rollup\n\n"
    report += "| Source | L0 batches | L0 items | L1 packets | L1 ready | L2 admitted/review | Feature rows | Feature count | Blocked L1 |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
    for row in family_rollup:
        report += f"| `{row['source_family']}` | {row['l0_batch_rows']} | {row['l0_raw_item_rows_reported']} | {row['l1_packet_rows']} | {row['l1_ready_packet_rows']} | {row['l2_admitted_or_review_rows']} | {row['feature_candidate_materialization_rows']} | {row['feature_candidate_count']} | {row['blocked_l1_packet_rows']} |\n"
    report += "\n## 운영 원칙\n\n"
    report += "- L2가 L0 raw를 직접 읽는 대신, L0 event ledger -> L1 wide packet -> L2 wide admission 순서로 연결한다.\n"
    report += "- feature materialization은 진단용 후보 count와 lineage만 열고, score/signal/order/broker/paper-live는 열지 않는다.\n"
    report += "- Chrome crawling은 여전히 smoke-only이며 runtime collector는 Python/background collector가 담당한다.\n"
    report += "- stopped incomplete lane은 기존 supervisor로 restart 요청하고, PID 기록뿐 아니라 실제 pid alive evidence를 남긴다.\n"
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")
    write_manifest()
    return summary


def main() -> int:
    print(json.dumps(build_and_write(), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
