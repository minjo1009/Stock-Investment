from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .common import health_metrics, write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Run diagnostic-only DB governance health checks.")
    parser.add_argument("--diagnostic-only", action="store_true", help="Require diagnostic-only fail-closed state.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on governance contract failures.")
    parser.add_argument("--require-management-schema", action="store_true", help="Require DB loop contract tables.")
    parser.add_argument("--require-fresh-sources", action="store_true", help="Fail when source freshness blockers exist.")
    parser.add_argument("--require-recurrence", action="store_true", help="Fail when scheduler recurrence is not proven.")
    parser.add_argument("--json", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()

    metrics = health_metrics()
    failures: list[str] = []
    if args.diagnostic_only and metrics["control_guard_status"] != "PASS_FAIL_CLOSED":
        failures.append("control_state_not_fail_closed")
    if metrics["db_active_manifest_count"] != 1:
        failures.append("active_manifest_count_not_one")
    if metrics["unknown_db_count"] != 0:
        failures.append("unknown_db_files_require_quarantine")
    if metrics["active_db_integrity"] != "ok":
        failures.append("active_db_integrity_not_ok")
    if metrics["broker_mutation_attempt_count"] != 0:
        failures.append("broker_mutation_attempt_detected")
    if metrics.get("foreign_key_violation_count", 0) != 0:
        failures.append("foreign_key_violations_detected")
    if args.require_management_schema and not metrics.get("management_tables_present"):
        failures.append("management_schema_tables_missing")
    if args.require_fresh_sources and metrics["stale_source_count"] != 0:
        failures.append("source_freshness_blockers_present")
    if args.require_recurrence and not metrics.get("scheduler_recurrence_proven"):
        failures.append("scheduler_recurrence_not_proven")

    metrics["strict_failures"] = failures
    metrics["healthcheck_status"] = "PASS" if not failures else "FAIL"
    if args.json:
        write_json(args.json, metrics)
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    if args.strict and failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
