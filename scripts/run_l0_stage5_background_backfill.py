from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4123"
SLUG = "task_4123_l0_stage_5_background_historical_backfill_from_2016"
DEFAULT_REPORT_DIR = ROOT / f"docs/reports/{SLUG}"
DEFAULT_RAW_DIR = ROOT / f"data/raw/{SLUG}"
DEFAULT_ARTIFACT_DIR = ROOT / f"data/artifacts/{SLUG}"


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_task_dirs(report_dir: Path, raw_dir: Path, artifact_dir: Path) -> None:
    for root in [report_dir / "command_results", raw_dir, artifact_dir]:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()


def run_command(name: str, args: list[str], report_dir: Path, timeout_seconds: int = 120) -> dict[str, Any]:
    started = now_z()
    proc = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout_seconds, check=False)
    result = {
        "name": name,
        "started_at": started,
        "finished_at": now_z(),
        "returncode": proc.returncode,
        "command": " ".join(args),
        "stdout_tail": proc.stdout[-6000:],
    }
    write_json(report_dir / "command_results" / f"{name}.json", result)
    return result


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def command_specs(raw_dir: Path, artifact_dir: Path) -> list[tuple[str, list[str]]]:
    context_artifacts = artifact_dir / "public_context_news_backfill"
    market_artifacts = artifact_dir / "public_market_macro_news_backfill"
    micro_artifacts = artifact_dir / "microstructure_backfill_batch"
    return [
        (
            "public_context_news_backfill",
            [
                sys.executable,
                "scripts/run_l0_public_context_news_collector.py",
                "--mode",
                "backfill",
                "--sources",
                "federal_register_documents",
                "--max-items-per-source",
                "2",
                "--max-fetches-per-source",
                "1",
                "--max-cycles",
                "1",
                "--request-sleep-seconds",
                "0",
                "--backfill-start-date",
                "2016-01-01",
                "--backfill-end-date",
                "2016-01-31",
                "--federal-register-per-page",
                "2",
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
                "500000",
            ],
        ),
        (
            "public_market_macro_news_backfill",
            [
                sys.executable,
                "scripts/run_l0_public_market_macro_news_collector.py",
                "--mode",
                "backfill",
                "--sources",
                "wikimedia_current_events",
                "--max-items-per-source",
                "2",
                "--max-fetches-per-source",
                "1",
                "--max-cycles",
                "1",
                "--request-sleep-seconds",
                "0",
                "--backfill-start-date",
                "2016-01-01",
                "--backfill-end-date",
                "2016-01-31",
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
                "2",
                "--max-bytes",
                "500000",
            ],
        ),
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
                "2016-01-04",
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
        ),
    ]


def event_rows(artifact_dir: Path, raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw_by_hash = {str(row.get("raw_sha256", "")): str(row.get("raw_path", "")) for row in raw_rows if row.get("raw_sha256")}
    event_paths = [
        artifact_dir / "public_context_news_backfill" / "collector_events.jsonl",
        artifact_dir / "public_market_macro_news_backfill" / "collector_events.jsonl",
    ]
    for event_path in event_paths:
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
        rows.append(
            {
                "task_id": TASK_ID,
                "job_name": path.parent.name,
                "progress_path": rel(path),
                "mode": payload.get("mode", ""),
                "status": payload.get("status", payload.get("last_status", "")),
                "processed_this_run": int(payload.get("processed_this_run", 0) or 0),
                "diagnostic_only_flag": int(payload.get("diagnostic_only_flag", 0) or 0),
                "trade_authority_flag": int(payload.get("trade_authority_flag", 1)),
                "broker_mutation_permitted_flag": int(payload.get("broker_mutation_permitted_flag", 1)),
                "real_capital_permitted_flag": int(payload.get("real_capital_permitted_flag", 1)),
            }
        )
    return rows


def write_protocol_tables(report_dir: Path, raw_dir: Path, artifact_dir: Path, command_results: list[dict[str, Any]]) -> dict[str, Any]:
    raw_rows = raw_file_rows(raw_dir)
    events = event_rows(artifact_dir, raw_rows)
    progress = progress_rows(artifact_dir)
    command_rows = [
        {
            "task_id": TASK_ID,
            "job_name": result["name"],
            "returncode": result["returncode"],
            "started_at": result["started_at"],
            "finished_at": result["finished_at"],
            "command_result_path": f"docs/reports/{SLUG}/command_results/{result['name']}.json",
            "bounded_background_cycle": 1,
        }
        for result in command_results
    ]
    write_csv(
        report_dir / "task_4123_scope_freeze.csv",
        [
            {
                "task_id": TASK_ID,
                "scope_type": "bounded_stage5_background_historical_backfill",
                "backfill_start_date": "2016-01-01",
                "backfill_end_date": "2016-01-31",
                "jobs": "public_context_news_backfill|public_market_macro_news_backfill|microstructure_backfill_batch",
                "full_2016_to_present_run_completed": 0,
                "persistent_process_left_running": 0,
                "status": "FROZEN_BOUNDED_PROOF",
            }
        ],
    )
    write_csv(
        report_dir / "task_4123_source_family_plan.csv",
        [
            {
                "task_id": TASK_ID,
                "job_name": "public_context_news_backfill",
                "source_family": "public_context_news_backfill",
                "source": "federal_register_documents",
                "implementation_mode": "python_collector_bounded_backfill",
                "authority_class": "official_macro_context",
            },
            {
                "task_id": TASK_ID,
                "job_name": "public_market_macro_news_backfill",
                "source_family": "public_market_macro_news_backfill",
                "source": "wikimedia_current_events",
                "implementation_mode": "python_collector_bounded_backfill",
                "authority_class": "public_event_archive_context",
            },
            {
                "task_id": TASK_ID,
                "job_name": "microstructure_backfill_batch",
                "source_family": "microstructure_quotes|microstructure_trades",
                "source": "alpaca_historical_microstructure",
                "implementation_mode": "python_collector_dry_run_coverage_proof",
                "authority_class": "credential_blockable_market_microstructure",
            },
        ],
    )
    api_rows = []
    for event in events:
        raw_path = str(event.get("raw_path", ""))
        api_rows.append(
            {
                "task_id": TASK_ID,
                "job_name": event.get("job_name", ""),
                "provider": event.get("provider", ""),
                "source_id": event.get("source_id", ""),
                "status": event.get("status", ""),
                "row_count": int(event.get("row_count", 0) or 0),
                "raw_path": raw_path,
                "raw_sha256": event.get("raw_sha256", ""),
                "network_call_status": "BOUNDED_PROVIDER_CALL_RECORDED",
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
    write_csv(report_dir / "task_4123_api_or_raw_call_ledger.csv", api_rows)
    write_csv(report_dir / "task_4123_command_ledger.csv", command_rows)
    write_csv(
        report_dir / "task_4123_raw_response_classification.csv",
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
    packets = []
    for idx, event in enumerate(events, start=1):
        packets.append(
            {
                "task_id": TASK_ID,
                "source_packet_id": f"TASK-4123-{idx:04d}",
                "candidate_id": "",
                "trade_spec_id": "",
                "symbol": "",
                "decision_asof_ts": "",
                "provider": event.get("provider", ""),
                "endpoint_or_source_family": event.get("source_family", event.get("provider", "")),
                "source_ts": "",
                "available_to_brain_ts": event.get("updated_at", ""),
                "source_time_basis": "provider_event_or_capture_time_requires_stage6_audit",
                "source_time_certified": 0,
                "raw_path": event.get("raw_path", ""),
                "raw_sha256": event.get("raw_sha256", ""),
                "strict_gate_pass": 0,
                "proxy_feature_allowed": 0,
                "missing_source_is_negative": 0,
                "assignment_uses_future_outcome": 0,
                "outcome_used_for_assignment": 0,
                "authority": "diagnostic_l0_backfill_only",
            }
        )
    write_csv(report_dir / "task_4123_normalized_source_packets.csv", packets, fieldnames=packet_fields)
    write_csv(
        report_dir / "task_4123_decision_asof_coverage.csv",
        [
            {
                "task_id": TASK_ID,
                "coverage_scope": "stage5_bounded_backfill",
                "rows_with_certified_source_time": 0,
                "coverage_status": "PENDING_STAGE6_SOURCE_TIME_AND_MAPPING_AUDIT",
            }
        ],
    )
    write_csv(
        report_dir / "task_4123_feature_admission_gate.csv",
        [
            {
                "task_id": TASK_ID,
                "strict_gate_pass": 0,
                "proxy_feature_allowed": 0,
                "feature_builder_enabled": 0,
                "l2_handoff_allowed": 0,
                "reason": "Stage 5 raw/background proof only; Stage 6 audit required.",
            }
        ],
    )
    gaps = []
    for progress_row in progress:
        status = str(progress_row.get("status", ""))
        if status in {"", "FAILED_RETRYABLE", "CREDENTIAL_BLOCKED", "RATE_LIMITED", "STOP_REQUESTED"}:
            gaps.append(
                {
                    "task_id": TASK_ID,
                    "job_name": progress_row.get("job_name", ""),
                    "gap": "bounded_backfill_incomplete_or_blocked",
                    "status": status,
                    "missing_source_is_negative": 0,
                }
            )
    gaps.append(
        {
            "task_id": TASK_ID,
            "job_name": "all",
            "gap": "full_2016_to_present_background_run_not_completed",
            "status": "EXPECTED_AFTER_BOUNDED_STAGE5_PROOF",
            "missing_source_is_negative": 0,
        }
    )
    write_csv(report_dir / "task_4123_source_gap_ledger.csv", gaps)
    write_csv(report_dir / "task_4123_progress_ledger.csv", progress)
    total_rows = sum(int(event.get("row_count", 0) or 0) for event in events)
    failed_commands = [row for row in command_rows if int(row["returncode"]) != 0]
    secret_failures = [row for row in raw_rows if row["secret_scan_status"] != "PASS"]
    summary = {
        "task_id": TASK_ID,
        "updated_at": now_z(),
        "stage5_status": "BACKGROUND_HISTORICAL_BACKFILL_BOUNDED_PROOF_EXECUTED" if not failed_commands and not secret_failures else "BACKGROUND_HISTORICAL_BACKFILL_BOUNDED_PROOF_FAILED",
        "bounded_background_collection_started": 1,
        "persistent_process_left_running": 0,
        "full_2016_to_present_run_completed": 0,
        "command_count": len(command_rows),
        "failed_command_count": len(failed_commands),
        "event_count": len(events),
        "raw_file_count": len(raw_rows),
        "total_event_rows": total_rows,
        "secret_failure_count": len(secret_failures),
        "db_mutation_made": 0,
        "broker_mutation_permitted": 0,
        "paper_promotion_permitted": 0,
        "live_order_enabled": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_stage": "l1_quality_coverage_audit_and_l2_handoff",
    }
    write_json(report_dir / "stage5_background_backfill_summary.json", summary)
    return summary


def run(report_dir: Path, raw_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    clean_task_dirs(report_dir, raw_dir, artifact_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    command_results = []
    for name, args in command_specs(raw_dir, artifact_dir):
        command_results.append(run_command(name, args, report_dir))
    return write_protocol_tables(report_dir, raw_dir, artifact_dir, command_results)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded L0 Stage 5 background historical backfill proof.")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    args = parser.parse_args()
    summary = run(args.report_dir, args.raw_dir, args.artifact_dir)
    print(
        "[L0_STAGE5_BACKGROUND_BACKFILL] "
        f"status={summary['stage5_status']} commands={summary['command_count']} "
        f"events={summary['event_count']} raw_files={summary['raw_file_count']} "
        f"rows={summary['total_event_rows']} persistent_process_left_running=0"
    )
    return 0 if summary["stage5_status"] == "BACKGROUND_HISTORICAL_BACKFILL_BOUNDED_PROOF_EXECUTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
