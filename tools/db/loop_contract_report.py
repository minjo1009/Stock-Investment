from __future__ import annotations

import argparse
import json
from pathlib import Path

from .common import (
    ACTIVE_DB,
    STATUS_DEPLOYMENT,
    STATUS_NOT_ACCEPTED,
    STATUS_REAL_CAPITAL,
    connect_readonly,
    health_metrics,
    table_exists,
    write_json,
)


def _rows(con, table: str) -> list[dict[str, object]]:
    if not table_exists(con, table):
        return []
    return [dict(row) for row in con.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]


def build_report() -> dict[str, object]:
    metrics = health_metrics()
    con = connect_readonly(ACTIVE_DB)
    try:
        jobs = _rows(con, "scheduler_job_registry")
        policies = _rows(con, "source_freshness_policy")
        freshness = _rows(con, "source_freshness")
        source_receipts = _rows(con, "source_receipts")
        lineage = _rows(con, "data_lineage_edges")
    finally:
        con.close()

    receipt_families = {row.get("source_family") for row in source_receipts}
    lineage_families = {row.get("source_family") for row in lineage}
    receipt_gaps = [
        row["source_family"]
        for row in jobs
        if int(row.get("requires_receipt", 0)) == 1 and row["source_family"] not in receipt_families
    ]
    lineage_gaps = [
        row["source_family"]
        for row in jobs
        if int(row.get("requires_lineage", 0)) == 1 and row["source_family"] not in lineage_families
    ]
    freshness_blockers = [
        row.get("source_family")
        for row in freshness
        if row.get("freshness_status") in {"STALE", "NO_AUTHORITY_EVIDENCE", "MISSING"}
    ]
    return {
        "db_authority": "ACTIVE_SINGLE_CONFIRMED" if metrics["db_active_manifest_count"] == 1 else "BLOCKED",
        "active_db": "trading.db",
        "run_mode": metrics["control_run_mode"],
        "kill_switch_active": metrics["control_kill_switch_active"],
        "strategy": STATUS_NOT_ACCEPTED,
        "deployment": STATUS_DEPLOYMENT,
        "real_capital": STATUS_REAL_CAPITAL,
        "jobs_registered": len(jobs),
        "freshness_policies_registered": len(policies),
        "freshness_blockers": freshness_blockers,
        "receipt_gaps": sorted(set(receipt_gaps)),
        "lineage_gaps": sorted(set(lineage_gaps)),
        "scheduler_recurrence_proven": metrics["scheduler_recurrence_proven"],
        "runtime_authority_evidence_rows": metrics["runtime_authority_evidence_ledger_count"],
        "paper_order_intents_count": metrics["paper_order_intents_count"],
        "acceptance_granted": False,
        "deployment_ready": False,
        "broker_mutation_permitted": False,
        "real_capital_permitted": False,
        "status": "CONTRACT_INSTALLED_WITH_BLOCKERS",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Report DB loop contract state.")
    parser.add_argument("--json", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        write_json(args.json, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

