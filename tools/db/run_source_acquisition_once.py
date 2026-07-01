from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.news_registry_loader import enabled_official_sources
from tools.db.source_acquisition.scheduler_override import DEFAULT_OVERRIDE_PATH, load_effective_scheduler_config


def planned_jobs(config: dict) -> list[dict]:
    return [job for job in config.get("jobs", []) if bool(job.get("enabled"))]


def run_once(
    *,
    base_path: Path = Path("configs/db_source_acquisition_scheduler.json"),
    override_path: Path = DEFAULT_OVERRIDE_PATH,
    dry_run: bool = True,
    bucket: str | None = None,
    families: list[str] | None = None,
    symbols: list[str] | None = None,
    macro_series: list[str] | None = None,
    allow_network: bool = False,
    requested_apply: bool = False,
) -> dict[str, object]:
    config = load_effective_scheduler_config(base_path=base_path, override_path=override_path)
    jobs = planned_jobs(config)
    official_sources = enabled_official_sources()
    requested_families = sorted(set(families or []))
    requested_symbols = sorted(set(symbols or []))
    requested_macro_series = sorted(set(macro_series or []))
    return {
        "capture_ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "config_path": str(base_path),
        "override_path": str(override_path),
        "bucket": bucket or "",
        "dry_run": bool(dry_run),
        "requested_apply": bool(requested_apply),
        "requested_families": requested_families,
        "requested_symbols": requested_symbols,
        "requested_macro_series": requested_macro_series,
        "allow_network_requested": bool(allow_network),
        "enabled_job_count": len(jobs),
        "enabled_jobs": [job.get("name") for job in jobs],
        "official_source_count": len(official_sources),
        "collection_apply_mode": "AUDIT_ONLY_NO_PROVIDER_EXECUTION",
        "network_calls_made": 0,
        "db_mutation_made": 0,
        "diagnostic_only": True,
        "execution_permitted": 0,
        "broker_mutation_permitted": 0,
        "paper_promotion_permitted": 0,
        "live_order_enabled": 0,
        "real_capital_permitted": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one governed L0 source acquisition pass.")
    parser.add_argument("--config-path", type=Path, default=Path("configs/db_source_acquisition_scheduler.json"))
    parser.add_argument("--override-path", type=Path, default=DEFAULT_OVERRIDE_PATH)
    parser.add_argument("--execute", action="store_true", help="Reserved for operator collection; default is dry-run audit.")
    parser.add_argument("--apply", action="store_true", help="Scheduler compatibility flag; remains audit-only in this guarded runner.")
    parser.add_argument("--bucket", default="")
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--family", action="append", default=[])
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--macro-series", action="append", default=[])
    args = parser.parse_args()
    result = run_once(
        base_path=args.config_path,
        override_path=args.override_path,
        dry_run=not args.execute and not args.apply,
        bucket=args.bucket,
        families=args.family,
        symbols=args.symbol,
        macro_series=args.macro_series,
        allow_network=args.allow_network,
        requested_apply=args.apply,
    )
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "[SOURCE_ACQUISITION_ONCE] "
        f"dry_run={result['dry_run']} requested_apply={result['requested_apply']} "
        f"families={result['requested_families']} enabled_jobs={result['enabled_jobs']} "
        "collection_apply_mode=AUDIT_ONLY_NO_PROVIDER_EXECUTION network_calls_made=0 "
        "diagnostic_only=True execution_permitted=0 broker_mutation_permitted=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
