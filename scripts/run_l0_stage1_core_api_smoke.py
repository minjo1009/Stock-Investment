from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.news_l0_l1 import evaluate_news_l1_row, marketaux_token_audit  # noqa: E402
from tools.db.source_acquisition.news_registry_loader import (  # noqa: E402
    GDELT_REGISTRY_PATH,
    MARKETAUX_REGISTRY_PATH,
    OFFICIAL_REGISTRY_PATH,
    enabled_official_sources,
    load_registry,
    validate_official_registry,
)
from tools.db.source_acquisition.secret_redaction import redact_text  # noqa: E402


TASK_ID = "TASK-4118"
DEFAULT_OUT_DIR = ROOT / "docs/reports/task_4118_l0_stage_1_official_core_api_smoke_stabilization"
SCHEDULER_CONFIG = ROOT / "configs/db_source_acquisition_scheduler.json"
CORE_FILES = [
    ROOT / "tools/db/news_l0_l1.py",
    ROOT / "tools/db/source_acquisition/news_background_collector.py",
    ROOT / "tools/db/source_acquisition/news_registry_loader.py",
    ROOT / "src/data/alpaca_historical_microstructure_export.py",
    ROOT / "tools/db/source_acquisition/microstructure_background_collector.py",
    ROOT / "configs/source_registry/l0_official_public_releases.json",
    ROOT / "configs/source_registry/l0_gdelt_queries.json",
    ROOT / "configs/source_registry/l0_marketaux_queries.json",
]
FORBIDDEN_STATUS_FIELDS = [
    "execution_permitted",
    "broker_mutation_permitted",
    "paper_promotion_permitted",
    "real_capital_permitted",
    "live_order_enabled",
    "replay_permission_granted",
    "buy_sell_signal_generation_permitted",
]


@dataclass(frozen=True)
class SmokeResult:
    family: str
    status: str
    severity: str
    reason: str
    network_call_made: int = 0
    request_budget_status: str = "NOT_APPLICABLE"

    def as_row(self) -> dict[str, Any]:
        return {
            "task_id": TASK_ID,
            "source_family": self.family,
            "status": self.status,
            "severity": self.severity,
            "reason": redact_text(self.reason),
            "network_call_made": self.network_call_made,
            "request_budget_status": self.request_budget_status,
            "diagnostic_only_flag": 1,
            "trade_authority_flag": 0,
            "broker_mutation_permitted_flag": 0,
            "real_capital_permitted_flag": 0,
        }


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def materialization_status(path: Path) -> tuple[str, str]:
    try:
        if not path.exists():
            return "MISSING", "path does not exist"
        _ = path.read_bytes()[:1]
    except OSError as exc:
        return "BLOCKED_LOCAL_MATERIALIZATION", type(exc).__name__
    return "PRESENT", "readable"


def load_scheduler() -> dict[str, Any]:
    return json.loads(SCHEDULER_CONFIG.read_text(encoding="utf-8-sig"))


def scheduler_safety_results(config: dict[str, Any]) -> list[SmokeResult]:
    results: list[SmokeResult] = []
    if config.get("strategy") != "NOT_ACCEPTED":
        results.append(SmokeResult("scheduler", "FAIL", "P0", "strategy status changed"))
    if config.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        results.append(SmokeResult("scheduler", "FAIL", "P0", "deployment status changed"))
    if config.get("real_capital") != "FORBIDDEN":
        results.append(SmokeResult("scheduler", "FAIL", "P0", "real capital status changed"))
    permissions = config.get("permissions", {})
    for field in FORBIDDEN_STATUS_FIELDS:
        if int(bool(permissions.get(field, 0))) != 0:
            results.append(SmokeResult("scheduler", "FAIL", "P0", f"permission open: {field}"))
    for job in config.get("jobs", []):
        if bool(job.get("enabled")):
            results.append(SmokeResult("scheduler", "FAIL", "P0", f"base job enabled: {job.get('name')}"))
        if bool(job.get("allow_network")):
            results.append(SmokeResult("scheduler", "FAIL", "P0", f"base job allows network: {job.get('name')}"))
    if not results:
        results.append(SmokeResult("scheduler", "PASS", "INFO", "base scheduler remains disabled and diagnostic-only"))
    return results


def official_results() -> list[SmokeResult]:
    results: list[SmokeResult] = []
    registry_errors = validate_official_registry(OFFICIAL_REGISTRY_PATH)
    if registry_errors:
        results.extend(SmokeResult("official_public_releases", "FAIL", "P1", error) for error in registry_errors)
        return results
    sources = enabled_official_sources(OFFICIAL_REGISTRY_PATH)
    if not sources:
        return [SmokeResult("official_public_releases", "FAIL", "P1", "no enabled official sources")]
    rows = [
        {
            "provider": "official_public_releases",
            "published_at": now_z(),
            "source_url": source.get("url", ""),
            "title": f"smoke contract row for {source.get('source_id')}",
            "symbols": source.get("symbol_scope") or source.get("macro_scope") or ["MACRO"],
        }
        for source in sources[:3]
    ]
    blocked = [evaluate_news_l1_row(row) for row in rows if evaluate_news_l1_row(row).promotion_status == "BLOCKED"]
    if blocked:
        return [SmokeResult("official_public_releases", "FAIL", "P1", "synthetic official L1 contract row blocked")]
    return [SmokeResult("official_public_releases", "PASS", "INFO", f"enabled official sources={len(sources)}; synthetic L1 contract rows ready")]


def gdelt_results() -> list[SmokeResult]:
    registry = load_registry(GDELT_REGISTRY_PATH)
    errors: list[SmokeResult] = []
    if registry.get("provider") != "gdelt":
        errors.append(SmokeResult("gdelt_news_events", "FAIL", "P1", "GDELT registry provider mismatch"))
    max_records = int(registry.get("max_records", 0) or 0)
    timespan = int(registry.get("timespan_minutes", 0) or 0)
    cooldown = int(registry.get("cooldown_minutes", 0) or 0)
    if not 1 <= max_records <= 25:
        errors.append(SmokeResult("gdelt_news_events", "FAIL", "P1", f"max_records out of smoke bounds: {max_records}"))
    if timespan != 15:
        errors.append(SmokeResult("gdelt_news_events", "FAIL", "P1", f"timespan_minutes must be 15 for stage1 smoke: {timespan}"))
    if cooldown < 15:
        errors.append(SmokeResult("gdelt_news_events", "FAIL", "P1", f"cooldown too short: {cooldown}"))
    if errors:
        return errors
    row = {
        "provider": "gdelt_news_events",
        "published_at": now_z(),
        "source_url": "https://example.invalid/gdelt-smoke",
        "title": "GDELT smoke contract row",
        "symbols": ["AAPL"],
    }
    evaluation = evaluate_news_l1_row(row)
    if evaluation.promotion_status != "READY_DISCOVERY_ONLY":
        return [SmokeResult("gdelt_news_events", "FAIL", "P1", f"unexpected L1 status: {evaluation.promotion_status}")]
    return [SmokeResult("gdelt_news_events", "PASS", "INFO", "bounded registry and discovery-only L1 contract pass")]


def marketaux_results() -> list[SmokeResult]:
    registry = load_registry(MARKETAUX_REGISTRY_PATH)
    results: list[SmokeResult] = []
    if registry.get("provider") != "marketaux":
        results.append(SmokeResult("marketaux_news_free", "FAIL", "P1", "Marketaux registry provider mismatch"))
    if int(registry.get("articles_per_request", 0) or 0) > 3:
        results.append(SmokeResult("marketaux_news_free", "FAIL", "P1", "articles_per_request exceeds stage1 smoke bound"))
    if int(registry.get("daily_request_cap", 0) or 0) > 95:
        results.append(SmokeResult("marketaux_news_free", "FAIL", "P1", "daily_request_cap exceeds configured free-tier guard"))
    audit = marketaux_token_audit()
    if not audit["present"]:
        results.append(SmokeResult("marketaux_news_free", "BLOCKED", "P2", "Marketaux token missing; network smoke blocked until local env token exists", request_budget_status="CREDENTIAL_BLOCKED"))
    row = {
        "provider": "marketaux_news_free",
        "published_at": now_z(),
        "source_url": "https://example.invalid/marketaux-smoke",
        "title": "Marketaux smoke contract row",
        "symbols": ["AAPL"],
    }
    evaluation = evaluate_news_l1_row(row)
    if evaluation.promotion_status != "READY_DISCOVERY_ONLY":
        results.append(SmokeResult("marketaux_news_free", "FAIL", "P1", f"unexpected L1 status: {evaluation.promotion_status}"))
    if not results:
        results.append(SmokeResult("marketaux_news_free", "PASS", "INFO", "quota registry, token audit, and discovery-only L1 contract pass"))
    return results


def microstructure_results() -> list[SmokeResult]:
    key_present = bool(os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY"))
    secret_present = bool(os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY"))
    if not key_present or not secret_present:
        return [
            SmokeResult(
                "microstructure_quotes_trades",
                "BLOCKED",
                "P2",
                "Alpaca credentials missing from process env; network smoke blocked but code preflight can continue",
                request_budget_status="CREDENTIAL_BLOCKED",
            )
        ]
    return [SmokeResult("microstructure_quotes_trades", "PASS", "INFO", "Alpaca credential presence detected without logging secret values")]


def materialization_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in CORE_FILES:
        status, reason = materialization_status(path)
        row: dict[str, Any] = {
            "task_id": TASK_ID,
            "path": path.relative_to(ROOT).as_posix(),
            "status": status,
            "reason": reason,
            "sha256": "",
        }
        if status == "PRESENT":
            row["sha256"] = sha256_file(path)
        rows.append(row)
    return rows


def run_preflight(out_dir: Path) -> dict[str, Any]:
    config = load_scheduler()
    results: list[SmokeResult] = []
    results.extend(scheduler_safety_results(config))
    results.extend(official_results())
    results.extend(gdelt_results())
    results.extend(marketaux_results())
    results.extend(microstructure_results())
    materialized = materialization_rows()

    source_family_rows = [
        {
            "task_id": TASK_ID,
            "source_family": "official_public_releases",
            "stage": 1,
            "mode": "python_http_rss_api_smoke",
            "network_default": "disabled",
            "authority": "official_primary_diagnostic_only",
        },
        {
            "task_id": TASK_ID,
            "source_family": "gdelt_news_events",
            "stage": 1,
            "mode": "python_api_smoke",
            "network_default": "disabled",
            "authority": "discovery_only",
        },
        {
            "task_id": TASK_ID,
            "source_family": "marketaux_news_free",
            "stage": 1,
            "mode": "python_api_smoke",
            "network_default": "disabled",
            "authority": "metadata_discovery_only",
        },
        {
            "task_id": TASK_ID,
            "source_family": "microstructure_quotes_trades",
            "stage": 1,
            "mode": "python_alpaca_historical_smoke",
            "network_default": "disabled",
            "authority": "raw_microstructure_diagnostic_only",
        },
    ]
    scope_rows = [
        {
            "task_id": TASK_ID,
            "stage": 1,
            "scope": "official_core_api_smoke_stabilization",
            "symbols": "AAPL,MSFT,NVDA,AMD,QQQ for scheduler smoke scope; AAPL-only where provider bound requires",
            "network_calls_made": 0,
            "db_mutation_made": 0,
            "broker_mutation_made": 0,
        }
    ]
    ledger_rows = [result.as_row() for result in results]
    raw_classification_rows = [
        {
            "task_id": TASK_ID,
            "source_family": result.family,
            "raw_response_status": "NOT_REQUESTED_PREFLIGHT" if result.network_call_made == 0 else "REQUESTED",
            "blocker_status": result.status if result.status in {"BLOCKED", "FAIL"} else "",
            "reason": result.reason,
        }
        for result in results
    ]
    normalized_rows = []
    for family in ["official_public_releases", "gdelt_news_events", "marketaux_news_free"]:
        provider = family
        row = {
            "task_id": TASK_ID,
            "source_packet_id": f"{TASK_ID}:{family}:synthetic_contract",
            "candidate_id": "",
            "trade_spec_id": "",
            "symbol": "AAPL" if family != "official_public_releases" else "AAPL|MACRO",
            "decision_asof_ts": now_z(),
            "provider": provider,
            "endpoint_or_source_family": family,
            "source_ts": now_z(),
            "available_to_brain_ts": now_z(),
            "source_time_basis": "synthetic_contract_preflight",
            "source_time_certified": 0,
            "raw_path": "",
            "raw_sha256": "",
            "strict_gate_pass": 0,
            "proxy_feature_allowed": 0,
            "missing_source_is_negative": 0,
            "assignment_uses_future_outcome": 0,
            "outcome_used_for_assignment": 0,
            "authority": "diagnostic_contract_only",
        }
        normalized_rows.append(row)
    decision_rows = [
        {
            "task_id": TASK_ID,
            "coverage_name": "stage1_preflight",
            "decision": "NETWORK_SMOKE_PENDING",
            "reason": "Preflight validates config and L1 contracts; no API calls made by default",
        }
    ]
    gate_rows = [
        {
            "task_id": TASK_ID,
            "gate": "stage1_to_stage2",
            "status": "BLOCKED_UNTIL_NETWORK_SMOKE_EVIDENCE",
            "reason": "Provider smoke commands must run with explicit operator network permission before cadence optimization",
        }
    ]
    gap_rows = [
        result.as_row()
        for result in results
        if result.status in {"BLOCKED", "FAIL"} or result.severity in {"P1", "P2"}
    ]

    write_csv(out_dir / "task_4118_scope_freeze.csv", scope_rows, list(scope_rows[0].keys()))
    write_csv(out_dir / "task_4118_source_family_plan.csv", source_family_rows, list(source_family_rows[0].keys()))
    write_csv(out_dir / "task_4118_api_or_raw_call_ledger.csv", ledger_rows, list(ledger_rows[0].keys()))
    write_csv(out_dir / "task_4118_raw_response_classification.csv", raw_classification_rows, list(raw_classification_rows[0].keys()))
    write_csv(out_dir / "task_4118_normalized_source_packets.csv", normalized_rows, list(normalized_rows[0].keys()))
    write_csv(out_dir / "task_4118_decision_asof_coverage.csv", decision_rows, list(decision_rows[0].keys()))
    write_csv(out_dir / "task_4118_feature_admission_gate.csv", gate_rows, list(gate_rows[0].keys()))
    write_csv(out_dir / "task_4118_source_gap_ledger.csv", gap_rows, list(gap_rows[0].keys()) if gap_rows else list(ledger_rows[0].keys()))
    write_csv(out_dir / "task_4118_materialization_audit.csv", materialized, list(materialized[0].keys()))

    summary = {
        "task_id": TASK_ID,
        "updated_at": now_z(),
        "network_calls_made": 0,
        "fail_count": sum(1 for result in results if result.status == "FAIL"),
        "blocked_count": sum(1 for result in results if result.status == "BLOCKED"),
        "pass_count": sum(1 for result in results if result.status == "PASS"),
        "materialization_blocked_count": sum(1 for row in materialized if row["status"] == "BLOCKED_LOCAL_MATERIALIZATION"),
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "stage1_status": "PREFLIGHT_PASS_NETWORK_SMOKE_PENDING",
    }
    (out_dir / "stage1_smoke_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run L0 Stage 1 official/core API smoke preflight without network calls.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    summary = run_preflight(args.out_dir)
    print(
        "[L0_STAGE1_CORE_API_SMOKE_PREFLIGHT] "
        f"status={summary['stage1_status']} pass={summary['pass_count']} "
        f"blocked={summary['blocked_count']} fail={summary['fail_count']} "
        f"materialization_blocked={summary['materialization_blocked_count']} "
        "network_calls_made=0 diagnostic_only=1 broker_mutation_permitted=0 real_capital_permitted=0"
    )
    return 1 if summary["fail_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
