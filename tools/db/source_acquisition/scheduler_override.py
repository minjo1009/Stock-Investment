from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from tools.db.source_acquisition.secret_redaction import find_secret_paths


BASE_CONFIG_PATH = Path("configs/db_source_acquisition_scheduler.json")
DEFAULT_OVERRIDE_PATH = Path("configs/local/db_source_acquisition_scheduler.override.json")
DEFAULT_AUDIT_PATH = Path("data/artifacts/l0_source_acquisition/effective_scheduler_config_audit.json")

FORBIDDEN_VALUE_FIELDS = {
    "strategy": {"ACCEPTED", "READY", "DEPLOYMENT_READY"},
    "deployment": {"READY", "DEPLOYMENT_READY", "PRODUCTION_READY"},
    "real_capital": {"ALLOWED", "ENABLED", "PERMITTED"},
}

FORBIDDEN_TRUTHY_FIELDS = {
    "execution_permitted",
    "broker_mutation_permitted",
    "paper_promotion_permitted",
    "real_capital_permitted",
    "live_order_enabled",
    "replay_permission_granted",
    "buy_sell_signal_generation_permitted",
    "order_intent_permitted",
    "broker_submit_enabled",
    "broker_cancel_enabled",
}

FORCE_CLOSED_FIELDS = {
    "execution_permitted": 0,
    "broker_mutation_permitted": 0,
    "paper_promotion_permitted": 0,
    "real_capital_permitted": 0,
    "live_order_enabled": 0,
    "replay_permission_granted": 0,
    "buy_sell_signal_generation_permitted": 0,
}

SAFE_TOP_LEVEL_OVERRIDES = {"posture", "jobs", "permissions"}
SAFE_JOB_FIELDS = {
    "name",
    "enabled",
    "allow_network",
    "interval_minutes",
    "symbols",
    "macro_series",
    "feed",
    "mode",
    "max_symbols",
    "max_dates",
    "max_chunks",
    "chunk_minutes",
    "max_requests_per_minute",
    "articles_per_request",
    "daily_request_cap",
    "diagnostic_only",
    "feature_builder_enabled",
}


class SchedulerOverrideError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_effective_scheduler_config(
    *,
    base_path: Path = BASE_CONFIG_PATH,
    override_path: Path = DEFAULT_OVERRIDE_PATH,
    audit_path: Path | None = DEFAULT_AUDIT_PATH,
) -> dict[str, Any]:
    base = read_json(base_path)
    override = read_json(override_path) if override_path.exists() else {}
    effective = merge_scheduler_override(base, override)
    if audit_path is not None:
        write_effective_config_audit(effective, base_path=base_path, override_path=override_path, override_present=bool(override), audit_path=audit_path)
    return effective


def merge_scheduler_override(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    validate_override_payload(override)
    effective = copy.deepcopy(base)
    if not override:
        _force_permissions_closed(effective)
        return effective
    unknown = set(override) - SAFE_TOP_LEVEL_OVERRIDES
    if unknown:
        raise SchedulerOverrideError(f"unsupported top-level override fields: {sorted(unknown)}")
    if "posture" in override:
        effective["posture"] = str(override["posture"])
    if "permissions" in override:
        permissions = effective.setdefault("permissions", {})
        for key, value in override.get("permissions", {}).items():
            if key in FORCE_CLOSED_FIELDS and int(bool(value)):
                raise SchedulerOverrideError(f"permission-opening override rejected: permissions.{key}")
            if key == "diagnostic_only":
                permissions[key] = bool(value)
    if "jobs" in override:
        _merge_jobs(effective, override["jobs"])
    _force_permissions_closed(effective)
    return effective


def validate_override_payload(override: dict[str, Any]) -> None:
    secret_paths = find_secret_paths(override)
    if secret_paths:
        raise SchedulerOverrideError(f"secret-like override values are not allowed: {secret_paths}")
    forbidden_paths = _find_forbidden_permission_paths(override)
    if forbidden_paths:
        raise SchedulerOverrideError(f"permission-opening override rejected: {forbidden_paths}")


def _merge_jobs(effective: dict[str, Any], override_jobs: list[dict[str, Any]]) -> None:
    if not isinstance(override_jobs, list):
        raise SchedulerOverrideError("jobs override must be a list")
    jobs = effective.setdefault("jobs", [])
    by_name = {job.get("name"): job for job in jobs if isinstance(job, dict)}
    for override_job in override_jobs:
        if not isinstance(override_job, dict) or not override_job.get("name"):
            raise SchedulerOverrideError("each job override must include a name")
        unknown = set(override_job) - SAFE_JOB_FIELDS
        if unknown:
            raise SchedulerOverrideError(f"{override_job.get('name')}: unsupported job override fields: {sorted(unknown)}")
        name = override_job["name"]
        if name not in by_name:
            raise SchedulerOverrideError(f"unknown scheduler job override: {name}")
        target = by_name[name]
        for key, value in override_job.items():
            if key == "name":
                continue
            target[key] = value
        target["diagnostic_only"] = True


def _force_permissions_closed(payload: dict[str, Any]) -> None:
    permissions = payload.setdefault("permissions", {})
    permissions["diagnostic_only"] = True
    for key, value in FORCE_CLOSED_FIELDS.items():
        permissions[key] = value
    for job in payload.get("jobs", []):
        if not isinstance(job, dict):
            continue
        job["diagnostic_only"] = True
        for key, value in FORCE_CLOSED_FIELDS.items():
            job[key] = value
        if "feature_builder_enabled" in job:
            job["feature_builder_enabled"] = bool(job["feature_builder_enabled"]) and False


def _find_forbidden_permission_paths(payload: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            normalized_key = str(key)
            if normalized_key in FORBIDDEN_TRUTHY_FIELDS and bool(value):
                hits.append(path)
            if normalized_key in FORBIDDEN_VALUE_FIELDS and str(value).upper() in FORBIDDEN_VALUE_FIELDS[normalized_key]:
                hits.append(path)
            hits.extend(_find_forbidden_permission_paths(value, prefix=path))
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            hits.extend(_find_forbidden_permission_paths(value, prefix=f"{prefix}[{idx}]"))
    return hits


def write_effective_config_audit(
    effective: dict[str, Any],
    *,
    base_path: Path,
    override_path: Path,
    override_present: bool,
    audit_path: Path,
) -> dict[str, Any]:
    jobs = [job for job in effective.get("jobs", []) if isinstance(job, dict)]
    enabled = [str(job.get("name")) for job in jobs if bool(job.get("enabled"))]
    network = [str(job.get("name")) for job in jobs if bool(job.get("allow_network"))]
    families: set[str] = set()
    for job in jobs:
        if bool(job.get("enabled")):
            families.update(str(item) for item in job.get("families", []))
    permissions = effective.get("permissions", {})
    permissions_closed = all(int(permissions.get(key, 0)) == value for key, value in FORCE_CLOSED_FIELDS.items())
    status_preserved = (
        effective.get("strategy") == "NOT_ACCEPTED"
        and effective.get("deployment") == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"
        and effective.get("real_capital") == "FORBIDDEN"
    )
    audit = {
        "base_config_path": str(base_path),
        "override_config_path": str(override_path),
        "override_present": bool(override_present),
        "jobs_enabled": enabled,
        "jobs_network_allowed": network,
        "families_enabled": sorted(families),
        "permissions_closed": bool(permissions_closed),
        "status_preserved": bool(status_preserved),
        "secrets_detected_false": len(find_secret_paths(effective)) == 0,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    return audit
