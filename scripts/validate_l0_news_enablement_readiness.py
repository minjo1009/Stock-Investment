from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.news_l0_l1 import BLOCKED, NEWS_PROVIDER_SPECS, READY_DIAGNOSTIC_ONLY, READY_DISCOVERY_ONLY
from tools.db.source_acquisition.news_registry_loader import validate_official_registry
from tools.db.source_acquisition.scheduler_override import BASE_CONFIG_PATH, FORCE_CLOSED_FIELDS, load_effective_scheduler_config
from tools.db.source_acquisition.secret_redaction import scan_repo_for_plaintext_marketaux_token


NEWS_JOB_NAMES = {"official_news_sources_15m", "gdelt_news_discovery_15m", "marketaux_news_free_30m"}


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_official_registry(root / "configs/source_registry/l0_official_public_releases.json"))
    config = load_effective_scheduler_config(base_path=root / BASE_CONFIG_PATH, override_path=root / "configs/local/__missing__.json", audit_path=None)
    jobs = {job["name"]: job for job in config.get("jobs", [])}
    for name in NEWS_JOB_NAMES:
        if name not in jobs:
            errors.append(f"missing scheduler job: {name}")
            continue
        if bool(jobs[name].get("enabled")):
            errors.append(f"{name}: conservative default must be disabled")
        if bool(jobs[name].get("allow_network")):
            errors.append(f"{name}: conservative default must have allow_network=false")
    if not (root / "configs/local_templates/db_source_acquisition_scheduler.override.example.json").exists():
        errors.append("missing local override example template")
    gitignore = (root / ".gitignore").read_text(encoding="utf-8", errors="ignore") if (root / ".gitignore").exists() else ""
    if "configs/local/" not in gitignore:
        errors.append(".gitignore must exclude configs/local/")
    for provider, role in {
        "official_public_releases": "official_primary",
        "gdelt_news_events": "news_discovery_proxy",
        "marketaux_news_free": "licensed_news_metadata_proxy",
    }.items():
        spec = NEWS_PROVIDER_SPECS.get(provider)
        if not spec:
            errors.append(f"missing provider spec: {provider}")
            continue
        if spec.get("provider_role") != role:
            errors.append(f"{provider}: provider_role must be {role}")
    if NEWS_PROVIDER_SPECS["gdelt_news_events"]["authority_class"] != "discovery_only":
        errors.append("GDELT must remain discovery-only")
    if NEWS_PROVIDER_SPECS["marketaux_news_free"]["authority_class"] != "metadata_discovery_only":
        errors.append("Marketaux must remain metadata/discovery-only")
    statuses = {BLOCKED, READY_DISCOVERY_ONLY, READY_DIAGNOSTIC_ONLY}
    if statuses != {"BLOCKED", "READY_DISCOVERY_ONLY", "READY_DIAGNOSTIC_ONLY"}:
        errors.append("L1 status constants missing expected semantics")
    token_hits = scan_repo_for_plaintext_marketaux_token(root)
    if token_hits:
        errors.append("Marketaux token-like value found in repo files: " + ", ".join(str(path) for path in token_hits[:5]))
    permissions = config.get("permissions", {})
    for field, closed in FORCE_CLOSED_FIELDS.items():
        if int(permissions.get(field, 0)) != closed:
            errors.append(f"permissions.{field} must remain closed")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[L0_NEWS_READINESS_ERROR] {error}")
        return 1
    print("[L0_NEWS_READINESS_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
