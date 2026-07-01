from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.microstructure_checkpoint import CHECKPOINT_FIELDS
from tools.db.source_acquisition.microstructure_coverage import COVERAGE_FILES
from tools.db.source_acquisition.scheduler_override import BASE_CONFIG_PATH, FORCE_CLOSED_FIELDS, load_effective_scheduler_config
from tools.db.source_acquisition.secret_redaction import scan_repo_for_plaintext_marketaux_token


REQUIRED_CHECKPOINT_FIELDS = {
    "checkpoint_id",
    "provider",
    "feed",
    "source_type",
    "symbol",
    "session_date",
    "chunk_start_ts",
    "chunk_end_ts",
    "chunk_id",
    "status",
    "attempt_count",
    "last_attempt_ts",
    "last_success_ts",
    "row_count",
    "raw_path",
    "raw_sha256",
    "error_category",
    "error_message_redacted",
    "created_at",
    "updated_at",
}
TOKEN_SCAN_PATHS = [
    Path("configs/db_source_acquisition_scheduler.json"),
    Path("configs/local_templates/db_source_acquisition_scheduler.override.example.json"),
    Path("configs/source_registry"),
    Path("tools/db/source_acquisition"),
    Path("scripts/validate_l0_microstructure_collection_readiness.py"),
]


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for path in [
        "src/data/alpaca_historical_microstructure_export.py",
        "scripts/run_task646_full_microstructure_backfill.py",
        "tools/db/source_acquisition/microstructure_checkpoint.py",
        "tools/db/source_acquisition/microstructure_coverage.py",
    ]:
        if not (root / path).exists():
            errors.append(f"missing required microstructure file: {path}")
    config = load_effective_scheduler_config(base_path=root / BASE_CONFIG_PATH, override_path=root / "configs/local/__missing__.json", audit_path=None)
    jobs = {job["name"]: job for job in config.get("jobs", [])}
    job = jobs.get("microstructure_backfill_batch")
    if not job:
        errors.append("missing microstructure_backfill_batch scheduler job")
    else:
        if bool(job.get("enabled")):
            errors.append("microstructure job must be disabled by default")
        if bool(job.get("allow_network")):
            errors.append("microstructure job must have allow_network=false by default")
        if set(job.get("families", [])) != {"microstructure_quotes", "microstructure_trades"}:
            errors.append("microstructure job must include quote/trade families")
        if bool(job.get("feature_builder_enabled")):
            errors.append("microstructure feature builder must remain blocked")
    template_path = root / "configs/local_templates/db_source_acquisition_scheduler.override.example.json"
    if not template_path.exists():
        errors.append("missing operator override template")
    registry = config.get("source_families", {})
    for family in ["microstructure_quotes", "microstructure_trades", "microstructure_catalog", "microstructure_coverage_audit", "market_bar_proxy_intraday"]:
        if family not in registry:
            errors.append(f"missing source family definition: {family}")
    if registry.get("market_bar_proxy_intraday", {}).get("authority_class") != "bar_proxy_not_exchange_tick_truth":
        errors.append("yfinance/5m proxy must not be represented as exchange tick truth")
    missing_checkpoint = REQUIRED_CHECKPOINT_FIELDS - set(CHECKPOINT_FIELDS)
    if missing_checkpoint:
        errors.append(f"checkpoint schema missing fields: {sorted(missing_checkpoint)}")
    for filename in COVERAGE_FILES.values():
        if not filename.startswith("microstructure_"):
            errors.append(f"unexpected coverage artifact name: {filename}")
    if scan_repo_for_plaintext_marketaux_token(root, TOKEN_SCAN_PATHS):
        errors.append("secret-like Marketaux value found in repo files")
    permissions = config.get("permissions", {})
    for field, closed in FORCE_CLOSED_FIELDS.items():
        if int(permissions.get(field, 0)) != closed:
            errors.append(f"permissions.{field} must remain closed")
    operating_state = (root / "ops/operating_state.yaml").read_text(encoding="utf-8", errors="ignore")
    for phrase in ["strategy_status: NOT_ACCEPTED", "deployment_status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "real_capital: FORBIDDEN"]:
        if phrase not in operating_state:
            errors.append(f"operating state missing preserved status: {phrase}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_MICROSTRUCTURE_READINESS_ERROR] {error}")
        return 1
    print("[L0_MICROSTRUCTURE_READINESS_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
