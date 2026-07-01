from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4132"
ARTIFACT_DIR = ROOT / "data/artifacts/l0_backfill_orchestration"
STATUS_JSON = ROOT / "data/artifacts/l0_collection_status/current_status.json"
STATE_PATH = ARTIFACT_DIR / "reliability_state.json"

LANES = [
    ("daily", "daily_bars", "daily", "raw_csv_files", "data/artifacts/l0_bar_daily_full_backfill/collector_events.jsonl", "data/artifacts/l0_bar_daily_full_backfill/STOP"),
    ("five_min", "five_min_bars", "five_min", "completed_units", "data/artifacts/l0_bar_full_backfill/collector_events.jsonl", "data/artifacts/l0_bar_full_backfill/STOP"),
    ("public_context_news_backfill", "public_context_news_backfill", "public_context_news_backfill", "completed_units", "data/artifacts/l0_public_context_news_backfill/collector_events.jsonl", "data/artifacts/l0_public_context_news_backfill/STOP"),
    ("public_newswire_backfill", "public_newswire_backfill", "public_newswire_backfill", "completed_units", "data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json", "data/artifacts/l0_public_newswire_backfill_shards/STOP"),
    ("public_market_macro_news_backfill", "public_market_macro_news_backfill", "public_market_macro_news_backfill", "completed_units", "data/artifacts/l0_public_market_macro_news_backfill/collector_events.jsonl", "data/artifacts/l0_public_market_macro_news_backfill/STOP"),
]

LANE_STATUS_PATHS = {
    "daily": ROOT / "data/artifacts/l0_bar_daily_full_backfill/background_process.json",
    "five_min": ROOT / "data/artifacts/l0_bar_full_backfill/background_process_5m.json",
    "public_context_news_backfill": ROOT / "data/artifacts/l0_public_context_news_backfill/background_process.json",
    "public_newswire_backfill": ROOT / "data/artifacts/l0_public_newswire_backfill_shards/background_process.json",
    "public_market_macro_news_backfill": ROOT / "data/artifacts/l0_public_market_macro_news_backfill/background_process.json",
}


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_ts(value: Any) -> datetime | None:
    text = str(value or "")
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def age_minutes(value: Any) -> float | None:
    ts = parse_ts(value)
    if ts is None:
        return None
    return round(max((datetime.now(UTC) - ts).total_seconds(), 0.0) / 60.0, 2)


def load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def numeric(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        try:
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
        except Exception:
            return False
        return result.stdout.strip().endswith("1")
    try:
        import os

        os.kill(pid, 0)
        return True
    except OSError:
        return False


def tail_events(path: Path, limit: int = 20) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(size - 512_000, 0))
            text = handle.read().decode("utf-8", errors="ignore")
    except OSError:
        return []
    rows: list[dict[str, Any]] = []
    for line in text.splitlines()[-limit:]:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def last_event(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        payload = load_json(path)
        if isinstance(payload, dict):
            updated = str(payload.get("generated_at") or payload.get("updated_at") or "")
            return {"updated_at": updated, "status": payload.get("status", "")}
    latest: dict[str, Any] = {}
    for event in tail_events(path):
        updated = str(event.get("updated_at") or event.get("captured_at") or event.get("capture_ts") or "")
        if updated and updated >= str(latest.get("updated_at") or ""):
            latest = dict(event)
            latest["updated_at"] = updated
    return latest


def is_incomplete(node: dict[str, Any]) -> bool:
    if str(node.get("status", "")).upper() in {"BACKFILL_COMPLETE", "EXHAUSTED"}:
        return False
    if numeric(node.get("progress_pct")) >= 99.999:
        return False
    if numeric(node.get("remaining_request_units")) > 0:
        return True
    if numeric(node.get("pending_units")) > 0:
        return True
    if numeric(node.get("pending_archive_urls")) > 0:
        return True
    total = numeric(node.get("total_units"))
    done = numeric(node.get("completed_units"))
    return total > 0 and done < total


def source_failure_rows(status: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lane, status_key, _bg_key, _metric, _events, _stop in LANES:
        node = status.get(status_key, {})
        if not isinstance(node, dict):
            continue
        counts = node.get("event_status_counts", {}) if isinstance(node.get("event_status_counts"), dict) else {}
        states = node.get("source_states", {}) if isinstance(node.get("source_states"), dict) else {}
        for source_key, source_node in sorted(states.items()):
            if not isinstance(source_node, dict):
                continue
            rows.append(
                {
                    "task_id": TASK_ID,
                    "lane": lane,
                    "source_key": source_key,
                    "completed_units": int(numeric(source_node.get("completed_units") or source_node.get("completed_archive_urls"))),
                    "total_units": int(numeric(source_node.get("total_units") or source_node.get("total_archive_urls"))),
                    "pending_units": int(numeric(source_node.get("pending_units") or source_node.get("pending_archive_urls"))),
                    "active_offsets": int(numeric(source_node.get("active_page_offsets") or source_node.get("active_archive_offsets"))),
                    "lane_status_counts": json.dumps(counts, sort_keys=True),
                    "diagnostic_only_flag": 1,
                    "trade_authority_flag": 0,
                    "broker_mutation_permitted_flag": 0,
                    "real_capital_permitted_flag": 0,
                }
            )
    return rows


def raw_audit_rows(limit_per_lane: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lane, _status_key, _bg_key, _metric, event_path, _stop in LANES:
        if event_path.endswith(".json"):
            continue
        for event in tail_events(ROOT / event_path, limit=limit_per_lane):
            raw_path = str(event.get("raw_path") or "")
            full = ROOT / raw_path if raw_path else None
            rows.append(
                {
                    "task_id": TASK_ID,
                    "lane": lane,
                    "source_id": event.get("source_id", ""),
                    "status": event.get("status", ""),
                    "raw_path": raw_path,
                    "raw_path_exists": int(bool(full and full.exists())),
                    "raw_sha256_present": int(bool(event.get("raw_sha256"))),
                    "raw_sha256_match": "NOT_RECALCULATED_IN_HOURLY_AUDIT",
                    "source_ts_present": int(bool(event.get("source_ts") or event.get("published_at") or event.get("source_published_at"))),
                    "capture_or_updated_ts_present": int(bool(event.get("capture_ts") or event.get("captured_at") or event.get("updated_at"))),
                    "available_to_brain_ts_present": int(bool(event.get("available_to_brain_ts"))),
                    "missing_source_is_negative": int(event.get("missing_source_is_negative", 0) or 0),
                    "assignment_uses_future_outcome": int(event.get("assignment_uses_future_outcome", 0) or 0),
                    "outcome_used_for_assignment": int(event.get("outcome_used_for_assignment", 0) or 0),
                    "diagnostic_only_flag": 1,
                    "trade_authority_flag": 0,
                    "broker_mutation_permitted_flag": 0,
                    "real_capital_permitted_flag": 0,
                }
            )
    return rows


def build(status: dict[str, Any], previous: dict[str, Any], stall_minutes: int, raw_limit: int) -> dict[str, Any]:
    previous_lanes = previous.get("lanes", {}) if isinstance(previous.get("lanes"), dict) else {}
    lane_rows: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    recommendations: list[dict[str, Any]] = []
    lanes: dict[str, Any] = {}
    bg = status.get("background_processes", {}) if isinstance(status.get("background_processes"), dict) else {}

    for lane, status_key, bg_key, metric_key, event_path, stop_path in LANES:
        node = status.get(status_key, {}) if isinstance(status.get(status_key), dict) else {}
        proc = bg.get(bg_key, {}) if isinstance(bg.get(bg_key), dict) else {}
        direct_status = load_json(LANE_STATUS_PATHS.get(lane, ROOT / "missing"))
        direct_pid = int(numeric(direct_status.get("pid"))) if isinstance(direct_status, dict) else 0
        direct_pid_alive = pid_alive(direct_pid)
        running = direct_pid_alive if direct_pid > 0 else bool(proc.get("running"))
        started_at = direct_status.get("started_at") if isinstance(direct_status, dict) and direct_status.get("started_at") else proc.get("started_at")
        started_age = age_minutes(started_at)
        metric_value = numeric(node.get(metric_key))
        prev_metric = numeric(previous_lanes.get(lane, {}).get("metric_value")) if previous_lanes else metric_value
        delta = round(metric_value - prev_metric, 6)
        latest = last_event(ROOT / event_path)
        event_age = age_minutes(latest.get("updated_at"))
        complete = not is_incomplete(node)
        stop_exists = (ROOT / stop_path).exists()
        recently_started = bool(started_age is not None and started_age < stall_minutes)
        stalled = bool(
            running
            and not complete
            and not recently_started
            and delta <= 0
            and event_age is not None
            and event_age >= stall_minutes
        )
        health = "COMPLETE" if complete else "STALLED" if stalled else "RUNNING" if running else "STOPPED"
        row = {
            "task_id": TASK_ID,
            "lane": lane,
            "health": health,
            "running": int(running),
            "pid_recorded": direct_pid,
            "pid_alive": int(direct_pid_alive),
            "complete": int(complete),
            "stalled": int(stalled),
            "stop_file_exists": int(stop_exists),
            "metric_name": metric_key,
            "metric_value": metric_value,
            "metric_delta_since_last_audit": delta,
            "progress_pct": node.get("progress_pct"),
            "completed_units": node.get("completed_units"),
            "total_units": node.get("total_units"),
            "last_status": node.get("last_status") or node.get("status") or "",
            "last_event_at": latest.get("updated_at", ""),
            "last_event_age_minutes": event_age,
            "process_started_age_minutes": started_age,
            "last_event_status": latest.get("status", ""),
            "diagnostic_only_flag": 1,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        }
        lane_rows.append(row)
        lanes[lane] = row
        if not running and not complete:
            alerts.append({"task_id": TASK_ID, "severity": "P0", "lane": lane, "alert": "lane_not_running_incomplete", "message": "Incomplete lane has no running background process."})
            if not stop_exists:
                recommendations.append({"task_id": TASK_ID, "lane": lane, "action": "RESTART_STOPPED_INCOMPLETE_LANE", "allowed": 1})
        if stalled:
            alerts.append({"task_id": TASK_ID, "severity": "P1", "lane": lane, "alert": "lane_stalled", "message": "Running lane has no progress delta and stale events."})

    five = status.get("five_min_bars", {}) if isinstance(status.get("five_min_bars"), dict) else {}
    five_progress = load_json(ROOT / "data/artifacts/l0_bar_full_backfill/collector_progress.json")
    raw_rows = raw_audit_rows(raw_limit)
    raw_summary = {
        "sample_rows": len(raw_rows),
        "raw_path_missing_rows": sum(1 for row in raw_rows if row["raw_path"] and not row["raw_path_exists"]),
        "raw_hash_present_rows": sum(1 for row in raw_rows if row["raw_sha256_present"]),
        "source_ts_present_rows": sum(1 for row in raw_rows if row["source_ts_present"]),
        "available_to_brain_ts_present_rows": sum(1 for row in raw_rows if row["available_to_brain_ts_present"]),
        "future_assignment_flag_rows": sum(1 for row in raw_rows if row["missing_source_is_negative"] or row["assignment_uses_future_outcome"] or row["outcome_used_for_assignment"]),
    }
    return {
        "task_id": TASK_ID,
        "generated_at": now_z(),
        "stall_threshold_minutes": stall_minutes,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "lanes": lanes,
        "lane_rows": lane_rows,
        "alerts": alerts,
        "source_failure_rows": source_failure_rows(status),
        "five_min_checkpoint": {
            "task_id": TASK_ID,
            "lane": "five_min",
            "progress_pct": five.get("progress_pct"),
            "completed_units": five.get("completed_units"),
            "total_units": five.get("total_units"),
            "remaining_request_units": five.get("remaining_request_units"),
            "five_min_symbol_index": five_progress.get("five_min_symbol_index"),
            "five_min_block_index": five_progress.get("five_min_block_index"),
            "five_min_blocks_per_symbol": five_progress.get("five_min_blocks_per_symbol"),
            "five_min_rows_written": five_progress.get("five_min_rows_written"),
            "market_bars_5m": five.get("market_bars_5m", {}),
            "diagnostic_only_flag": 1,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        },
        "supervisor_recommendations": recommendations,
        "raw_audit": raw_summary,
        "raw_rows": raw_rows,
        "diagnostic_only_flag": 1,
        "trade_authority_flag": 0,
        "broker_mutation_permitted_flag": 0,
        "real_capital_permitted_flag": 0,
    }


def write_alert_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = ["# L0 Current Alerts", "", f"- Updated at: {payload['generated_at']}", ""]
    alerts = payload.get("alerts", [])
    if alerts:
        lines.extend(["## Alerts", ""])
        for item in alerts:
            lines.append(f"- {item.get('severity')} `{item.get('lane')}` {item.get('alert')}: {item.get('message')}")
    else:
        lines.extend(["## Alerts", "", "- No current P0/P1 reliability alerts."])
    lines.extend(["", "## Lane Health", ""])
    for row in payload.get("lane_rows", []):
        lines.append(f"- `{row['lane']}`: {row['health']}, running={row['running']}, delta={row['metric_delta_since_last_audit']}, last_event_age_min={row['last_event_age_minutes']}")
    lines.extend(["", "Strategy: NOT_ACCEPTED", "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "Real Capital: FORBIDDEN"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    status = load_json(STATUS_JSON)
    previous = load_json(args.state_path)
    payload = build(status, previous, args.stall_minutes, args.raw_sample_limit)
    if args.write:
        write_json(ARTIFACT_DIR / "enhanced_latest_summary.json", {k: v for k, v in payload.items() if k != "raw_rows"})
        write_json(ARTIFACT_DIR / "current_alerts.json", {"task_id": TASK_ID, "generated_at": payload["generated_at"], "alerts": payload["alerts"]})
        write_alert_markdown(ARTIFACT_DIR / "current_alerts.md", payload)
        write_csv(ARTIFACT_DIR / "lane_reliability.csv", payload["lane_rows"])
        write_csv(ARTIFACT_DIR / "source_failure_summary.csv", payload["source_failure_rows"])
        write_csv(ARTIFACT_DIR / "raw_cache_source_time_audit.csv", payload["raw_rows"])
        write_json(ARTIFACT_DIR / "five_min_checkpoint_summary.json", payload["five_min_checkpoint"])
        write_json(ARTIFACT_DIR / "supervisor_recommendations.json", payload["supervisor_recommendations"])
        write_json(args.state_path, {"task_id": TASK_ID, "updated_at": payload["generated_at"], "lanes": {k: {"metric_value": v["metric_value"]} for k, v in payload["lanes"].items()}})
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--stall-minutes", type=int, default=90)
    parser.add_argument("--raw-sample-limit", type=int, default=10)
    parser.add_argument("--state-path", type=Path, default=STATE_PATH)
    return parser.parse_args()


def main() -> int:
    payload = run(parse_args())
    print(
        "[L0_BACKFILL_RELIABILITY] "
        f"lanes={len(payload['lanes'])} alerts={len(payload['alerts'])} "
        f"recommendations={len(payload['supervisor_recommendations'])} "
        "diagnostic_only=1 trade_authority_flag=0 broker_mutation_permitted_flag=0 real_capital_permitted_flag=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
