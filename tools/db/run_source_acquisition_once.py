from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from tools.db.source_acquisition.news_registry_loader import enabled_official_sources
from tools.db.source_acquisition.scheduler_override import DEFAULT_OVERRIDE_PATH, load_effective_scheduler_config


def planned_jobs(config: dict) -> list[dict]:
    return [job for job in config.get("jobs", []) if bool(job.get("enabled"))]


def run_once(*, override_path: Path = DEFAULT_OVERRIDE_PATH, dry_run: bool = True) -> dict[str, object]:
    config = load_effective_scheduler_config(override_path=override_path)
    jobs = planned_jobs(config)
    official_sources = enabled_official_sources()
    return {
        "dry_run": bool(dry_run),
        "enabled_job_count": len(jobs),
        "enabled_jobs": [job.get("name") for job in jobs],
        "official_source_count": len(official_sources),
        "diagnostic_only": True,
        "execution_permitted": 0,
        "broker_mutation_permitted": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one governed L0 source acquisition pass.")
    parser.add_argument("--override-path", type=Path, default=DEFAULT_OVERRIDE_PATH)
    parser.add_argument("--execute", action="store_true", help="Reserved for operator collection; default is dry-run audit.")
    args = parser.parse_args()
    result = run_once(override_path=args.override_path, dry_run=not args.execute)
    print(
        "[SOURCE_ACQUISITION_ONCE] "
        f"dry_run={result['dry_run']} enabled_jobs={result['enabled_jobs']} "
        "diagnostic_only=True execution_permitted=0 broker_mutation_permitted=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
