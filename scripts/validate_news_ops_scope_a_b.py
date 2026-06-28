from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.scheduler_override import BASE_CONFIG_PATH, FORCE_CLOSED_FIELDS, load_effective_scheduler_config


NEWS_JOB_NAMES = {"official_news_sources_15m", "gdelt_news_discovery_15m", "marketaux_news_free_30m"}
TEMPLATE_OVERRIDE = Path("configs/local_templates/db_source_acquisition_scheduler.override.example.json")


def validate(mode: str) -> list[str]:
    errors: list[str] = []
    override = TEMPLATE_OVERRIDE if mode == "news_enabled_diagnostic" else Path("__missing_override__.json")
    config = load_effective_scheduler_config(base_path=BASE_CONFIG_PATH, override_path=override, audit_path=None)
    jobs = {job["name"]: job for job in config.get("jobs", [])}
    for name in NEWS_JOB_NAMES:
        if name not in jobs:
            errors.append(f"missing news job: {name}")
            continue
        job = jobs[name]
        if mode == "conservative":
            if bool(job.get("enabled")):
                errors.append(f"{name}: conservative mode must be disabled")
            if bool(job.get("allow_network")):
                errors.append(f"{name}: conservative mode must have allow_network=false")
        if mode == "news_enabled_diagnostic":
            if not bool(job.get("diagnostic_only")):
                errors.append(f"{name}: diagnostic_only must remain true")
        for field, closed_value in FORCE_CLOSED_FIELDS.items():
            if int(job.get(field, 0)) != closed_value:
                errors.append(f"{name}: {field} must remain {closed_value}")
    permissions = config.get("permissions", {})
    for field, closed_value in FORCE_CLOSED_FIELDS.items():
        if int(permissions.get(field, 0)) != closed_value:
            errors.append(f"permissions.{field} must remain {closed_value}")
    if config.get("strategy") != "NOT_ACCEPTED":
        errors.append("strategy must remain NOT_ACCEPTED")
    if config.get("deployment") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment must remain DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
    if config.get("real_capital") != "FORBIDDEN":
        errors.append("real_capital must remain FORBIDDEN")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["conservative", "news_enabled_diagnostic"], default="conservative")
    args = parser.parse_args()
    errors = validate(args.mode)
    if errors:
        for error in errors:
            print(f"[NEWS_OPS_SCOPE_ERROR] {error}")
        return 1
    print(f"[NEWS_OPS_SCOPE_OK] mode={args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
