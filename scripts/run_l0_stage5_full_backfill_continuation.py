from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4125"
SLUG = "task_4125_l0_stage_5_full_2016_to_present_backfill_continuation"
DEFAULT_REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
DEFAULT_RAW_DIR = ROOT / f"data/raw/{SLUG}"
DEFAULT_ARTIFACT_DIR = ROOT / f"data/artifacts/{SLUG}"
BACKFILL_START_DATE = "2016-01-01"
FEDERAL_REGISTER_DEFAULT_PER_PAGE = 100
GUARDIAN_DEFAULT_PAGE_SIZE = 50


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def today_utc() -> str:
    return datetime.now(UTC).date().isoformat()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def migrate_page_offsets(
    *,
    state_path: Path,
    source_key: str,
    offset_key: str,
    page_size_state_key: str,
    new_page_size: int,
    default_old_page_size: int,
) -> None:
    state = read_json(state_path)
    source_state = state.get("backfill", {}).get(source_key, {})
    offsets = source_state.get(offset_key, {})
    if not isinstance(source_state, dict) or not isinstance(offsets, dict) or not offsets:
        return
    old_page_size = int(source_state.get(page_size_state_key, default_old_page_size) or default_old_page_size)
    new_page_size = max(int(new_page_size), 1)
    if old_page_size == new_page_size:
        source_state[page_size_state_key] = new_page_size
        write_json(state_path, state)
        return
    backup = state_path.with_name(f"{state_path.stem}.{source_key}.{page_size_state_key}.{old_page_size}_to_{new_page_size}.backup.json")
    if not backup.exists():
        write_json(backup, state)
    migrated: dict[str, int] = {}
    for unit_id, page in offsets.items():
        page_num = max(int(page or 1), 1)
        fetched_before = max(page_num - 1, 0) * old_page_size
        new_page = max(math.floor(fetched_before / new_page_size) + 1, 1)
        migrated[str(unit_id)] = new_page
    source_state[offset_key] = migrated
    source_state[page_size_state_key] = new_page_size
    source_state.setdefault("migration_notes", []).append(
        {
            "migrated_at": now_z(),
            "offset_key": offset_key,
            "old_page_size": old_page_size,
            "new_page_size": new_page_size,
            "policy": "conservative_overlap_no_skip",
            "backup_path": rel(backup),
        }
    )
    write_json(state_path, state)


def migrate_task_state_for_page_size(
    artifact_dir: Path,
    *,
    context_sources: list[str],
    market_sources: list[str],
    federal_register_per_page: int,
    guardian_page_size: int,
) -> None:
    if "federal_register_documents" in context_sources:
        migrate_page_offsets(
            state_path=artifact_dir / "public_context_news_backfill" / "collector_state.json",
            source_key="federal_register_documents",
            offset_key="page_offsets",
            page_size_state_key="federal_register_per_page",
            new_page_size=federal_register_per_page,
            default_old_page_size=FEDERAL_REGISTER_DEFAULT_PER_PAGE,
        )
    if "guardian_open_platform" in market_sources:
        migrate_page_offsets(
            state_path=artifact_dir / "public_market_macro_news_backfill" / "collector_state.json",
            source_key="guardian_open_platform",
            offset_key="page_offsets",
            page_size_state_key="guardian_page_size",
            new_page_size=guardian_page_size,
            default_old_page_size=GUARDIAN_DEFAULT_PAGE_SIZE,
        )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def secret_like_text(path: Path) -> bool:
    if path.suffix.lower() not in {".json", ".jsonl", ".csv", ".txt", ".log"}:
        return False
    text = path.read_text(encoding="utf-8-sig", errors="ignore")[:200_000]
    patterns = [
        r"(?i)\bAuthorization\s*[:=]",
        r"(?i)\bBearer\s+[A-Za-z0-9._-]{10,}",
        r"(?i)\b(api[_-]?key|apikey|token|secret)\s*[:=]\s*[A-Za-z0-9._-]{12,}",
        r"\bsk-[A-Za-z0-9_-]{12,}",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def raw_file_rows(raw_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue
        rows.append(
            {
                "raw_path": rel(path),
                "raw_sha256": sha256_file(path),
                "raw_bytes": path.stat().st_size,
                "secret_scan_status": "PASS" if not secret_like_text(path) else "FAIL",
            }
        )
    return rows


def run_command(name: str, args: list[str], report_dir: Path, timeout_seconds: int) -> dict[str, Any]:
    started = now_z()
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
            check=False,
        )
        returncode = proc.returncode
        output = proc.stdout
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        output = str(exc.output or "")
    result = {
        "name": name,
        "started_at": started,
        "finished_at": now_z(),
        "returncode": returncode,
        "command": " ".join(args),
        "stdout_tail": output[-8000:],
    }
    write_json(report_dir / "command_results" / f"{name}.json", result)
    return result


def command_specs(
    raw_dir: Path,
    artifact_dir: Path,
    *,
    end_date: str,
    full_cycle: bool,
    max_items_per_source: int,
    max_fetches_per_source: int,
    max_cycles: int,
    request_sleep_seconds: float,
    cycle_sleep_seconds: int,
    context_sources: list[str],
    market_sources: list[str],
    include_microstructure: bool,
    federal_register_per_page: int,
    guardian_page_size: int,
) -> list[tuple[str, list[str], int]]:
    max_fetches = str(max_fetches_per_source)
    max_items = str(max_items_per_source)
    cycle_count = "0" if full_cycle else str(max_cycles)
    sleep_seconds = str(request_sleep_seconds)
    cycle_sleep = str(cycle_sleep_seconds)
    context_artifacts = artifact_dir / "public_context_news_backfill"
    market_artifacts = artifact_dir / "public_market_macro_news_backfill"
    micro_artifacts = artifact_dir / "microstructure_backfill_batch"
    specs: list[tuple[str, list[str], int]] = []
    if context_sources:
        specs.append(
            (
            "public_context_news_backfill",
            [
                sys.executable,
                "scripts/run_l0_public_context_news_collector.py",
                "--mode",
                "backfill",
                "--sources",
                *context_sources,
                "--max-items-per-source",
                max_items,
                "--max-fetches-per-source",
                max_fetches,
                "--max-cycles",
                cycle_count,
                "--request-sleep-seconds",
                sleep_seconds,
                "--cycle-sleep-seconds",
                cycle_sleep,
                "--backfill-start-date",
                BACKFILL_START_DATE,
                "--backfill-end-date",
                end_date,
                "--federal-register-per-page",
                str(federal_register_per_page),
                "--raw-dir",
                str(raw_dir / "public_context_news_backfill"),
                "--state-path",
                str(context_artifacts / "collector_state.json"),
                "--event-path",
                str(context_artifacts / "collector_events.jsonl"),
                "--progress-path",
                str(context_artifacts / "collector_progress.json"),
                "--plan-path",
                str(context_artifacts / "collection_plan.json"),
                "--stop-path",
                str(context_artifacts / "STOP"),
                "--log-path",
                str(context_artifacts / "collector.log"),
                "--max-bytes",
                "2000000",
            ],
            1800,
            )
        )
    if market_sources:
        specs.append(
            (
            "public_market_macro_news_backfill",
            [
                sys.executable,
                "scripts/run_l0_public_market_macro_news_collector.py",
                "--mode",
                "backfill",
                "--sources",
                *market_sources,
                "--max-items-per-source",
                max_items,
                "--max-fetches-per-source",
                max_fetches,
                "--max-cycles",
                cycle_count,
                "--request-sleep-seconds",
                sleep_seconds,
                "--cycle-sleep-seconds",
                cycle_sleep,
                "--backfill-start-date",
                BACKFILL_START_DATE,
                "--backfill-end-date",
                end_date,
                "--raw-dir",
                str(raw_dir / "public_market_macro_news_backfill"),
                "--state-path",
                str(market_artifacts / "collector_state.json"),
                "--event-path",
                str(market_artifacts / "collector_events.jsonl"),
                "--progress-path",
                str(market_artifacts / "collector_progress.json"),
                "--plan-path",
                str(market_artifacts / "collection_plan.json"),
                "--stop-path",
                str(market_artifacts / "STOP"),
                "--log-path",
                str(market_artifacts / "collector.log"),
                "--guardian-page-size",
                str(guardian_page_size),
                "--max-bytes",
                "2000000",
            ],
            1800,
            )
        )
    if include_microstructure:
        specs.append(
            (
            "microstructure_backfill_batch",
            [
                sys.executable,
                "scripts/run_task646_full_microstructure_backfill.py",
                "--mode",
                "smoke",
                "--symbols",
                "AAPL",
                "--session-dates",
                "2016-01-05",
                "--feed",
                "iex",
                "--max-chunks",
                "1",
                "--chunk-minutes",
                "15",
                "--out-dir",
                str(raw_dir / "microstructure_backfill_batch"),
                "--checkpoint-path",
                str(micro_artifacts / "microstructure_backfill_checkpoint.jsonl"),
                "--coverage-output-dir",
                str(micro_artifacts / "coverage"),
            ],
            180,
            )
        )
    return specs


def event_rows(artifact_dir: Path, raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_by_hash = {str(row.get("raw_sha256", "")): str(row.get("raw_path", "")) for row in raw_rows if row.get("raw_sha256")}
    rows: list[dict[str, Any]] = []
    for event_path in sorted(artifact_dir.rglob("collector_events.jsonl")):
        family = event_path.parent.name
        for event in read_jsonl(event_path):
            row = dict(event)
            raw_hash = str(row.get("raw_sha256", ""))
            if raw_hash in raw_by_hash:
                row["raw_path"] = raw_by_hash[raw_hash]
            row["job_name"] = family
            row["event_path"] = rel(event_path)
            rows.append(row)
    return rows


def progress_rows(artifact_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(artifact_dir.rglob("collector_progress.json")):
        payload = read_json(path)
        backfill = payload.get("backfill", {}) if isinstance(payload.get("backfill", {}), dict) else {}
        rows.append(
            {
                "task_id": TASK_ID,
                "job_name": path.parent.name,
                "progress_path": rel(path),
                "mode": payload.get("mode", ""),
                "status": payload.get("status", payload.get("last_status", "")),
                "processed_this_run": int(payload.get("processed_this_run", 0) or 0),
                "processed_events_total": int(payload.get("processed_events", 0) or 0),
                "exported_events_total": int(payload.get("exported_events", 0) or 0),
                "failed_events_total": int(payload.get("failed_events", 0) or 0),
                "source_backfill_state_count": len(backfill),
                "diagnostic_only_flag": int(payload.get("diagnostic_only_flag", 0) or 0),
                "trade_authority_flag": int(payload.get("trade_authority_flag", 1)),
                "broker_mutation_permitted_flag": int(payload.get("broker_mutation_permitted_flag", 1)),
                "real_capital_permitted_flag": int(payload.get("real_capital_permitted_flag", 1)),
            }
        )
    return rows


def coverage_rows(artifact_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(artifact_dir.rglob("collector_state.json")):
        state = read_json(path)
        backfill = state.get("backfill", {}) if isinstance(state.get("backfill", {}), dict) else {}
        for source_key, source_state in backfill.items():
            if not isinstance(source_state, dict):
                continue
            total_units = int(source_state.get("total_units", 0) or 0)
            pending_units = int(source_state.get("pending_units", 0) or 0)
            completed = len(source_state.get("completed_units", []) or [])
            rows.append(
                {
                    "task_id": TASK_ID,
                    "job_name": path.parent.name,
                    "source_key": source_key,
                    "start_date": source_state.get("start_date", BACKFILL_START_DATE),
                    "end_date": source_state.get("end_date", ""),
                    "total_units": total_units,
                    "completed_units": completed,
                    "pending_units": pending_units,
                    "coverage_complete": int(total_units > 0 and pending_units == 0),
                    "state_path": rel(path),
                }
            )
    if not rows:
        rows.append(
            {
                "task_id": TASK_ID,
                "job_name": "",
                "source_key": "",
                "start_date": BACKFILL_START_DATE,
                "end_date": "",
                "total_units": 0,
                "completed_units": 0,
                "pending_units": 0,
                "coverage_complete": 0,
                "state_path": "",
            }
        )
    return rows


def write_protocol_tables(
    report_dir: Path,
    raw_dir: Path,
    artifact_dir: Path,
    command_results: list[dict[str, Any]],
    *,
    end_date: str,
    full_cycle: bool,
) -> dict[str, Any]:
    raw_rows = raw_file_rows(raw_dir)
    events = event_rows(artifact_dir, raw_rows)
    progress = progress_rows(artifact_dir)
    coverage = coverage_rows(artifact_dir)
    full_complete = int(bool(coverage) and all(int(row.get("coverage_complete", 0) or 0) == 1 for row in coverage))
    command_rows = [
        {
            "task_id": TASK_ID,
            "job_name": result["name"],
            "returncode": result["returncode"],
            "started_at": result["started_at"],
            "finished_at": result["finished_at"],
            "command_result_path": f"docs/reports/{SLUG}/command_results/{result['name']}.json",
            "bounded_continuation_cycle": int(not full_cycle),
            "full_cycle_requested": int(full_cycle),
        }
        for result in command_results
    ]
    write_csv(
        report_dir / "task_4125_scope_freeze.csv",
        [
            {
                "task_id": TASK_ID,
                "scope_type": "full_2016_to_present_backfill_continuation",
                "backfill_start_date": BACKFILL_START_DATE,
                "backfill_end_date": end_date,
                "jobs": "public_context_news_backfill|public_market_macro_news_backfill|microstructure_backfill_batch",
                "full_2016_to_present_run_completed": full_complete,
                "persistent_process_left_running": 0,
                "status": "FROZEN_CONTINUATION",
            }
        ],
    )
    write_csv(
        report_dir / "task_4125_source_family_plan.csv",
        [
            {
                "task_id": TASK_ID,
                "job_name": "public_context_news_backfill",
                "source_family": "public_context_news_backfill",
                "sources": "federal_register_documents|federal_reserve_press_all|cftc_press_releases",
                "implementation_mode": "python_collector_resumable_historical_backfill",
                "authority_class": "official_macro_context",
            },
            {
                "task_id": TASK_ID,
                "job_name": "public_market_macro_news_backfill",
                "source_family": "public_market_macro_news_backfill",
                "sources": "wikimedia_current_events|guardian_open_platform",
                "implementation_mode": "python_collector_resumable_historical_backfill",
                "authority_class": "public_market_macro_context",
            },
            {
                "task_id": TASK_ID,
                "job_name": "microstructure_backfill_batch",
                "source_family": "microstructure_quotes|microstructure_trades",
                "sources": "alpaca_historical_microstructure",
                "implementation_mode": "python_collector_dry_run_coverage_proof_until_credentials_and_operator_window",
                "authority_class": "credential_blockable_market_microstructure",
            },
        ],
    )
    api_rows = []
    for event in events:
        api_rows.append(
            {
                "task_id": TASK_ID,
                "job_name": event.get("job_name", ""),
                "provider": event.get("provider", ""),
                "source_id": event.get("source_id", ""),
                "status": event.get("status", ""),
                "row_count": int(event.get("row_count", 0) or 0),
                "raw_path": event.get("raw_path", ""),
                "raw_sha256": event.get("raw_sha256", ""),
                "network_call_status": "PROVIDER_CALL_RECORDED_OR_RESUMED",
                "missing_source_is_negative": 0,
            }
        )
    if not api_rows:
        api_rows.append(
            {
                "task_id": TASK_ID,
                "job_name": "",
                "provider": "",
                "source_id": "",
                "status": "NO_EVENT_ROWS",
                "row_count": 0,
                "raw_path": "",
                "raw_sha256": "",
                "network_call_status": "NO_EVENT_ROWS",
                "missing_source_is_negative": 0,
            }
        )
    write_csv(report_dir / "task_4125_api_or_raw_call_ledger.csv", api_rows)
    write_csv(report_dir / "task_4125_command_ledger.csv", command_rows)
    write_csv(
        report_dir / "task_4125_raw_response_classification.csv",
        [
            {
                "task_id": TASK_ID,
                "raw_path": row["raw_path"],
                "raw_sha256": row["raw_sha256"],
                "raw_bytes": row["raw_bytes"],
                "secret_scan_status": row["secret_scan_status"],
                "classification": "RAW_BACKFILL_RESPONSE_OR_AUDIT_ARTIFACT",
                "strict_gate_opened": 0,
            }
            for row in raw_rows
        ],
    )
    packet_fields = [
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
    ]
    packets = [
        {
            "task_id": TASK_ID,
            "source_packet_id": f"TASK-4125-{idx:05d}",
            "candidate_id": "",
            "trade_spec_id": "",
            "symbol": "",
            "decision_asof_ts": "",
            "provider": event.get("provider", ""),
            "endpoint_or_source_family": event.get("source_family", event.get("provider", "")),
            "source_ts": "",
            "available_to_brain_ts": event.get("updated_at", ""),
            "source_time_basis": "provider_event_or_capture_time_requires_stage6_reaudit",
            "source_time_certified": 0,
            "raw_path": event.get("raw_path", ""),
            "raw_sha256": event.get("raw_sha256", ""),
            "strict_gate_pass": 0,
            "proxy_feature_allowed": 0,
            "missing_source_is_negative": 0,
            "assignment_uses_future_outcome": 0,
            "outcome_used_for_assignment": 0,
            "authority": "diagnostic_l0_backfill_continuation_only",
        }
        for idx, event in enumerate(events, start=1)
    ]
    write_csv(report_dir / "task_4125_normalized_source_packets.csv", packets, fieldnames=packet_fields)
    write_csv(
        report_dir / "task_4125_decision_asof_coverage.csv",
        [
            {
                "task_id": TASK_ID,
                "coverage_scope": "full_2016_to_present_backfill_continuation",
                "rows_with_certified_source_time": 0,
                "full_2016_to_present_run_completed": full_complete,
                "coverage_status": "COMPLETE" if full_complete else "IN_PROGRESS_FULL_2016_TO_PRESENT_NOT_COMPLETE",
            }
        ],
    )
    write_csv(
        report_dir / "task_4125_feature_admission_gate.csv",
        [
            {
                "task_id": TASK_ID,
                "strict_gate_pass": 0,
                "proxy_feature_allowed": 0,
                "feature_builder_enabled": 0,
                "l2_handoff_allowed": 0,
                "reason": "Full 2016-to-present coverage and Stage 6 reaudit are required before feature admission.",
            }
        ],
    )
    gap_rows = [
        {
            "task_id": TASK_ID,
            "job_name": row.get("job_name", ""),
            "source_key": row.get("source_key", ""),
            "gap": "pending_backfill_units",
            "status": "COMPLETE" if int(row.get("coverage_complete", 0) or 0) == 1 else "IN_PROGRESS",
            "pending_units": row.get("pending_units", 0),
            "missing_source_is_negative": 0,
        }
        for row in coverage
    ]
    if not full_complete:
        gap_rows.append(
            {
                "task_id": TASK_ID,
                "job_name": "all",
                "source_key": "all",
                "gap": "full_2016_to_present_background_run_not_completed",
                "status": "IN_PROGRESS",
                "pending_units": "",
                "missing_source_is_negative": 0,
            }
        )
    write_csv(report_dir / "task_4125_source_gap_ledger.csv", gap_rows)
    write_csv(report_dir / "task_4125_progress_ledger.csv", progress)
    write_csv(report_dir / "task_4125_coverage_progress.csv", coverage)
    failed_commands = [row for row in command_rows if int(row["returncode"]) != 0]
    secret_failures = [row for row in raw_rows if row["secret_scan_status"] != "PASS"]
    total_rows = sum(int(event.get("row_count", 0) or 0) for event in events)
    summary = {
        "task_id": TASK_ID,
        "updated_at": now_z(),
        "stage5_status": "FULL_2016_TO_PRESENT_BACKFILL_COMPLETE" if full_complete else "FULL_2016_TO_PRESENT_BACKFILL_CONTINUATION_IN_PROGRESS",
        "full_2016_to_present_run_completed": full_complete,
        "bounded_continuation_cycle_executed": int(not full_cycle),
        "persistent_process_left_running": 0,
        "command_count": len(command_rows),
        "failed_command_count": len(failed_commands),
        "event_count": len(events),
        "raw_file_count": len(raw_rows),
        "total_event_rows": total_rows,
        "coverage_source_count": len(coverage),
        "coverage_complete_count": sum(int(row.get("coverage_complete", 0) or 0) for row in coverage),
        "secret_failure_count": len(secret_failures),
        "db_mutation_made": 0,
        "broker_mutation_permitted": 0,
        "paper_promotion_permitted": 0,
        "live_order_enabled": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_required_step": "continue Stage 5 until coverage complete, then rerun Stage 6 L1 quality/coverage audit",
    }
    write_json(report_dir / "stage5_full_backfill_continuation_summary.json", summary)
    return summary


def write_report_files(report_dir: Path, summary: dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report.md").write_text(
        "\n".join(
            [
                "# TASK-4125 L0 Stage 5 Full 2016-to-Present Backfill Continuation",
                "",
                "## Goal",
                "",
                "Continue Stage 5 from the bounded proof toward the requested full 2016-to-present L0/L1 backfill.",
                "",
                "## Result",
                "",
                f"- Stage 5 status: `{summary['stage5_status']}`.",
                f"- Full 2016-to-present completed: `{summary['full_2016_to_present_run_completed']}`.",
                f"- Provider events observed: `{summary['event_count']}`.",
                f"- Raw files observed: `{summary['raw_file_count']}`.",
                f"- Event rows observed: `{summary['total_event_rows']}`.",
                "- Strict/proxy gates remain closed until full coverage and Stage 6 reaudit pass.",
                "",
                "## Safety",
                "",
                "No DB mutation, broker mutation, paper promotion, live order, strategy acceptance, deployment readiness, or real-capital permission was introduced.",
                "",
                "Test results do not modify strategy acceptance status.",
                "Strategy: NOT_ACCEPTED",
                "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "Real Capital: FORBIDDEN",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_rows = [
        {"path": "ops/task_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4125 task tracking", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "ops/doc_registry.yaml", "type": "REGISTRY", "purpose": "TASK-4125 docs registered", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "configs/db_source_acquisition_scheduler.json", "type": "CONFIG", "purpose": "Stage 5 continuation task recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/CURRENT_TASKS.md", "type": "SSOT", "purpose": "TASK-4125 moved from optional to active continuation", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/PROJECT_STATUS.md", "type": "SSOT", "purpose": "Full backfill continuation status recorded", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/active/ACTIVE_SSOT_INDEX.md", "type": "SSOT", "purpose": "TASK-4125 evidence registered", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "docs/architecture/l0_source_acquisition_project_management_plan.md", "type": "GOVERNANCE", "purpose": "Continuation rule added", "created_or_modified": "modified", "task_id": TASK_ID},
        {"path": "scripts/run_l0_stage5_full_backfill_continuation.py", "type": "SCRIPT", "purpose": "Resumable Stage 5 continuation runner", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": "scripts/validate_l0_stage5_full_backfill_continuation.py", "type": "VALIDATOR", "purpose": "Stage 5 continuation validator", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/report.md", "type": "TASK_REPORT", "purpose": "TASK-4125 report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/artifact_manifest.csv", "type": "ARTIFACT_MANIFEST", "purpose": "TASK-4125 artifact manifest", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/validation_results.md", "type": "VALIDATION_REPORT", "purpose": "TASK-4125 validation report", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/stage5_full_backfill_continuation_summary.json", "type": "REFERENCE", "purpose": "Stage 5 continuation summary", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_scope_freeze.csv", "type": "REFERENCE", "purpose": "Scope freeze", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_source_family_plan.csv", "type": "REFERENCE", "purpose": "Source family plan", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_api_or_raw_call_ledger.csv", "type": "REFERENCE", "purpose": "API/raw ledger", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_raw_response_classification.csv", "type": "REFERENCE", "purpose": "Raw response classification", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_normalized_source_packets.csv", "type": "REFERENCE", "purpose": "Normalized source packets", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_decision_asof_coverage.csv", "type": "REFERENCE", "purpose": "Decision-asof coverage", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_feature_admission_gate.csv", "type": "REFERENCE", "purpose": "Feature admission gate", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_source_gap_ledger.csv", "type": "REFERENCE", "purpose": "Source gap ledger", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_progress_ledger.csv", "type": "REFERENCE", "purpose": "Progress ledger", "created_or_modified": "created", "task_id": TASK_ID},
        {"path": f"docs/reports/{SLUG}/task_4125_coverage_progress.csv", "type": "REFERENCE", "purpose": "Coverage progress", "created_or_modified": "created", "task_id": TASK_ID},
    ]
    write_csv(report_dir / "artifact_manifest.csv", manifest_rows, fieldnames=["path", "type", "purpose", "created_or_modified", "task_id"])
    (report_dir / "validation_results.md").write_text(
        "\n".join(
            [
                "# TASK-4125 Validation Results",
                "",
                "## Latest Run",
                "",
                f"- Stage 5 status: `{summary['stage5_status']}`.",
                f"- Provider events: `{summary['event_count']}`.",
                f"- Raw files: `{summary['raw_file_count']}`.",
                f"- Observed rows: `{summary['total_event_rows']}`.",
                f"- Coverage complete: `{summary['coverage_complete_count']}/{summary['coverage_source_count']}`.",
                "",
                "## Required Validation",
                "",
                "- `python -m compileall scripts/run_l0_stage5_full_backfill_continuation.py scripts/validate_l0_stage5_full_backfill_continuation.py`",
                "- `python scripts/validate_l0_stage5_full_backfill_continuation.py`",
                "- `python scripts/validate_l0_source_acquisition_project_management.py`",
                "- `python scripts/ops/validate_task_registry.py`",
                "- `python scripts/ops/validate_doc_registry.py --soft`",
                "- `python scripts/ops/validate_required_artifacts.py --task TASK-4125`",
                "- `python scripts/ops/validate_task_scope.py --task TASK-4125`",
                "",
                "Closeout remains intentionally open until full 2016-to-present coverage completes and Stage 6 reaudit passes.",
                "",
                "## Operator Notes",
                "",
                "A combined Federal Register plus Guardian continuation attempt advanced saved collector state but exceeded the previous per-command 600 second runner timeout while Guardian was still running. The runner now records future timeouts as command-ledger failures instead of crashing, and reports can be regenerated from current task-scoped raw/artifact state without additional provider calls.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def run(
    report_dir: Path,
    raw_dir: Path,
    artifact_dir: Path,
    *,
    end_date: str,
    full_cycle: bool,
    max_items_per_source: int = 20,
    max_fetches_per_source: int = 2,
    max_cycles: int = 1,
    request_sleep_seconds: float = 0.1,
    cycle_sleep_seconds: int = 1,
    context_sources: list[str] | None = None,
    market_sources: list[str] | None = None,
    include_microstructure: bool = True,
    federal_register_per_page: int = 100,
    guardian_page_size: int = 50,
) -> dict[str, Any]:
    report_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    selected_context_sources = ["federal_register_documents", "federal_reserve_press_all", "cftc_press_releases"] if context_sources is None else context_sources
    selected_market_sources = ["wikimedia_current_events", "guardian_open_platform"] if market_sources is None else market_sources
    migrate_task_state_for_page_size(
        artifact_dir,
        context_sources=selected_context_sources,
        market_sources=selected_market_sources,
        federal_register_per_page=max(federal_register_per_page, 1),
        guardian_page_size=max(guardian_page_size, 1),
    )
    command_results = []
    for name, args, timeout in command_specs(
        raw_dir,
        artifact_dir,
        end_date=end_date,
        full_cycle=full_cycle,
        max_items_per_source=max(max_items_per_source, 1),
        max_fetches_per_source=max(max_fetches_per_source, 1),
        max_cycles=max(max_cycles, 1),
        request_sleep_seconds=max(request_sleep_seconds, 0.0),
        cycle_sleep_seconds=max(cycle_sleep_seconds, 0),
        context_sources=selected_context_sources,
        market_sources=selected_market_sources,
        include_microstructure=include_microstructure,
        federal_register_per_page=max(federal_register_per_page, 1),
        guardian_page_size=max(guardian_page_size, 1),
    ):
        command_results.append(run_command(name, args, report_dir, timeout))
    summary = write_protocol_tables(report_dir, raw_dir, artifact_dir, command_results, end_date=end_date, full_cycle=full_cycle)
    write_report_files(report_dir, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Continue L0 Stage 5 full 2016-to-present backfill with resumable collectors.")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--backfill-end-date", default=today_utc())
    parser.add_argument("--full-cycle", action="store_true", help="Do not bound collector cycles; intended only for operator-supervised long windows.")
    parser.add_argument("--max-items-per-source", type=int, default=20)
    parser.add_argument("--max-fetches-per-source", type=int, default=2)
    parser.add_argument("--max-cycles", type=int, default=1)
    parser.add_argument("--request-sleep-seconds", type=float, default=0.1)
    parser.add_argument("--cycle-sleep-seconds", type=int, default=1)
    parser.add_argument("--context-sources", nargs="*", default=None)
    parser.add_argument("--market-sources", nargs="*", default=None)
    parser.add_argument("--skip-context", action="store_true")
    parser.add_argument("--skip-market", action="store_true")
    parser.add_argument("--skip-microstructure", action="store_true")
    parser.add_argument("--federal-register-per-page", type=int, default=100)
    parser.add_argument("--guardian-page-size", type=int, default=50)
    args = parser.parse_args()
    summary = run(
        args.report_dir,
        args.raw_dir,
        args.artifact_dir,
        end_date=args.backfill_end_date,
        full_cycle=args.full_cycle,
        max_items_per_source=args.max_items_per_source,
        max_fetches_per_source=args.max_fetches_per_source,
        max_cycles=args.max_cycles,
        request_sleep_seconds=args.request_sleep_seconds,
        cycle_sleep_seconds=args.cycle_sleep_seconds,
        context_sources=[] if args.skip_context else args.context_sources,
        market_sources=[] if args.skip_market else args.market_sources,
        include_microstructure=not args.skip_microstructure,
        federal_register_per_page=args.federal_register_per_page,
        guardian_page_size=args.guardian_page_size,
    )
    print(
        "[L0_STAGE5_FULL_BACKFILL_CONTINUATION] "
        f"status={summary['stage5_status']} commands={summary['command_count']} "
        f"events={summary['event_count']} raw_files={summary['raw_file_count']} "
        f"rows={summary['total_event_rows']} full_2016_to_present={summary['full_2016_to_present_run_completed']}"
    )
    return 0 if int(summary["failed_command_count"]) == 0 and int(summary["secret_failure_count"]) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
