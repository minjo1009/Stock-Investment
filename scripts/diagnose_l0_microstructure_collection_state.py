from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.data.env_loader import load_repo_env
from tools.db.source_acquisition.microstructure_checkpoint import MicrostructureCheckpointStore
from tools.db.source_acquisition.microstructure_coverage import DEFAULT_OUTPUT_DIR
from tools.db.source_acquisition.scheduler_override import BASE_CONFIG_PATH, DEFAULT_OVERRIDE_PATH, load_effective_scheduler_config


def _latest_file_timestamp(paths: list[Path]) -> str:
    files = [path for path in paths if path.exists()]
    if not files:
        return ""
    latest = max(files, key=lambda path: path.stat().st_mtime)
    return latest.name


def _latest_checkpoint(source_type: str | None = None) -> dict:
    rows = MicrostructureCheckpointStore().load()
    if source_type:
        rows = [row for row in rows if row.get("source_type") == source_type and row.get("status") == "EXPORTED"]
    if not rows:
        return {}
    return sorted(rows, key=lambda row: str(row.get("updated_at", "")))[-1]


def diagnose() -> dict[str, object]:
    config = load_effective_scheduler_config(base_path=BASE_CONFIG_PATH, override_path=DEFAULT_OVERRIDE_PATH, audit_path=None)
    job = next((job for job in config.get("jobs", []) if job.get("name") == "microstructure_backfill_batch"), {})
    load_repo_env()
    key_present = bool(os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY"))
    secret_present = bool(os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY"))
    heartbeat_path = DEFAULT_OUTPUT_DIR / "microstructure_collection_heartbeat.json"
    heartbeat = json.loads(heartbeat_path.read_text(encoding="utf-8")) if heartbeat_path.exists() else {}
    return {
        "scheduler_config_has_microstructure_job": bool(job),
        "microstructure_job_enabled": bool(job.get("enabled")),
        "microstructure_job_allow_network": bool(job.get("allow_network")),
        "operator_override_exists": DEFAULT_OVERRIDE_PATH.exists(),
        "windows_scheduled_task_exists": "NOT_CHECKED_NON_MUTATING_DIAGNOSTIC",
        "startup_folder_fallback_exists": _startup_folder_fallback_exists(),
        "latest_scheduler_log_timestamp": _latest_file_timestamp(list((ROOT / "logs").glob("*source*")) if (ROOT / "logs").exists() else []),
        "latest_source_acquisition_ledger_row": "NOT_AVAILABLE_WITHOUT_DB_QUERY",
        "latest_microstructure_checkpoint_row": _latest_checkpoint(),
        "latest_successful_quote_chunk": _latest_checkpoint("quotes"),
        "latest_successful_trade_chunk": _latest_checkpoint("trades"),
        "latest_failure_category": _latest_failure_category(),
        "alpaca_credentials_present": bool(key_present and secret_present),
        "feed_configured": job.get("feed", ""),
        "quote_coverage_rate": heartbeat.get("quote_coverage_rate", 0.0),
        "trade_coverage_rate": heartbeat.get("trade_coverage_rate", 0.0),
        "feature_builder_enabled": 0,
        "broker_mutation_permitted": 0,
    }


def _startup_folder_fallback_exists() -> bool:
    startup = os.environ.get("APPDATA")
    if not startup:
        return False
    folder = Path(startup) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return any(path.name.lower().startswith("db_source_acquisition") for path in folder.glob("*")) if folder.exists() else False


def _latest_failure_category() -> str:
    rows = MicrostructureCheckpointStore().load()
    failures = [row for row in rows if str(row.get("status", "")).startswith("FAILED") or row.get("status") in {"RATE_LIMITED", "CREDENTIAL_BLOCKED", "EMPTY_PROVIDER_RESPONSE", "QUARANTINED"}]
    if not failures:
        return ""
    latest = sorted(failures, key=lambda row: str(row.get("updated_at", "")))[-1]
    return str(latest.get("error_category") or latest.get("status") or "")


def main() -> int:
    print(json.dumps(diagnose(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
