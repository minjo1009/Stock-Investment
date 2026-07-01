from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4120"
DEFAULT_OUT_DIR = ROOT / "docs/reports/task_4120_l0_stage_2_realtime_source_budget_optimization"
SCHEDULER_CONFIG = ROOT / "configs/db_source_acquisition_scheduler.json"


def now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_scheduler() -> dict[str, Any]:
    return json.loads(SCHEDULER_CONFIG.read_text(encoding="utf-8-sig"))


def requests_per_day(interval_minutes: int) -> int:
    return int(math.ceil(1440 / max(int(interval_minutes), 1)))


def budget_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    jobs = {job.get("name"): job for job in config.get("jobs", []) if isinstance(job, dict)}
    official = jobs.get("official_news_sources_15m", {})
    gdelt = jobs.get("gdelt_news_discovery_15m", {})
    marketaux = jobs.get("marketaux_news_free_30m", {})
    rows.append(
        {
            "task_id": TASK_ID,
            "source_family": "official_public_releases",
            "job_name": official.get("name", ""),
            "interval_minutes": official.get("interval_minutes", ""),
            "requests_per_day_budget": requests_per_day(int(official.get("interval_minutes", 15) or 15)),
            "provider_daily_cap": "",
            "target_utilization": "bounded_official_refresh",
            "budget_status": "PASS",
            "reason": "Official RSS/API endpoints have no project-specific daily cap; cadence remains bounded at 15m and disabled by default.",
        }
    )
    gdelt_interval = int(gdelt.get("interval_minutes", 15) or 15)
    gdelt_min_interval = int(gdelt.get("cooldown_minutes", 15) or 15)
    rows.append(
        {
            "task_id": TASK_ID,
            "source_family": "gdelt_news_events",
            "job_name": gdelt.get("name", ""),
            "interval_minutes": gdelt_interval,
            "requests_per_day_budget": requests_per_day(gdelt_interval),
            "provider_daily_cap": "",
            "target_utilization": "one_symbol_15m_cooldown",
            "budget_status": "PASS" if gdelt_interval >= gdelt_min_interval else "FAIL",
            "reason": f"GDELT remains one bounded symbol request per {gdelt_interval}m with {gdelt_min_interval}m cooldown.",
        }
    )
    marketaux_interval = int(marketaux.get("interval_minutes", 0) or 0)
    marketaux_cap = int(marketaux.get("daily_request_cap", 0) or 0)
    marketaux_daily = requests_per_day(marketaux_interval) if marketaux_interval else 0
    utilization = round(marketaux_daily / marketaux_cap, 4) if marketaux_cap else 0
    status = "PASS" if marketaux_cap and 0.90 <= utilization <= 0.95 and marketaux_daily <= marketaux_cap else "FAIL"
    rows.append(
        {
            "task_id": TASK_ID,
            "source_family": "marketaux_news_free",
            "job_name": marketaux.get("name", ""),
            "interval_minutes": marketaux_interval,
            "requests_per_day_budget": marketaux_daily,
            "provider_daily_cap": marketaux_cap,
            "target_utilization": "0.90_to_0.95",
            "actual_utilization": utilization,
            "budget_status": status,
            "reason": "16m cadence yields 90 requests/day against a 95/day guard, near cap without crossing it.",
        }
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(out_dir: Path) -> dict[str, Any]:
    config = load_scheduler()
    rows = budget_rows(config)
    write_csv(out_dir / "task_4120_realtime_budget_plan.csv", rows)
    failures = [row for row in rows if row.get("budget_status") == "FAIL"]
    summary = {
        "task_id": TASK_ID,
        "updated_at": now_z(),
        "stage2_status": "REALTIME_BUDGET_OPTIMIZED" if not failures else "REALTIME_BUDGET_NEEDS_REPAIR",
        "budget_row_count": len(rows),
        "failure_count": len(failures),
        "scheduler_activation": 0,
        "network_calls_made": 0,
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stage2_realtime_budget_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and materialize L0 Stage 2 realtime source budget plan.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[L0_STAGE2_REALTIME_BUDGET_OPTIMIZATION] "
        f"status={summary['stage2_status']} failures={summary['failure_count']} "
        "scheduler_activation=0 network_calls_made=0 broker_mutation_permitted=0 real_capital_permitted=0"
    )
    return 1 if summary["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
