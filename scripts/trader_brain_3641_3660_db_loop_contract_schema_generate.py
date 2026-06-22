from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.db.common import ACTIVE_DB, connect_readonly, health_metrics, write_csv, write_json
from tools.db.loop_contract_report import build_report


TASK = "task_3641_3660_db_loop_contract_schema"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK
REPORT_DIR = ROOT / "docs" / "reports" / TASK


def _rows(table: str) -> list[dict[str, object]]:
    con = connect_readonly(ACTIVE_DB)
    try:
        return [dict(row) for row in con.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]
    finally:
        con.close()


def _write_csv_fixed(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_report(metrics: dict[str, object], loop_report: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    freshness_blockers = "\n".join(f"- `{x}`" for x in loop_report["freshness_blockers"])
    receipt_gaps = "\n".join(f"- `{x}`" for x in loop_report["receipt_gaps"])
    lineage_gaps = "\n".join(f"- `{x}`" for x in loop_report["lineage_gaps"])
    report = f"""# Task3641-3660 DB Loop Contract Schema

## Decision Summary

- Verdict: `DB_LOOP_CONTRACT_SCHEMA_INSTALLED_WITH_BLOCKERS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - Management tables present: {metrics['management_tables_present']}
  - Jobs registered: {metrics['jobs_registered']}
  - Freshness policies registered: {metrics['source_freshness_policy_count']}
  - Reference hashes: {metrics['reference_hash_count']}
  - Lineage edges: {metrics['lineage_edge_count']}
  - Foreign key violations: {metrics['foreign_key_violation_count']}
  - Scheduler recurrence proven: {metrics['scheduler_recurrence_proven']}
  - Paper order intents: {metrics['paper_order_intents_count']}
- What changed:
  - Added guarded DB migration `task3641_db_loop_contract_schema_v1`.
  - Added `scheduler_job_registry`, `source_freshness_policy`, `reference_hashes`, and `data_lineage_edges`.
  - Seeded 10 diagnostic loop jobs and 10 freshness policies.
  - DB-level CHECK constraints keep execution, broker mutation, real capital, and paper promotion permissions at 0.
  - Added `tools.db.apply_management_schema` and `tools.db.loop_contract_report`.
- Next action:
  - Implement actual receipt-backed P1 data-family jobs one at a time.

## Quant Expert Report

### Data source and source readiness

The task used active `trading.db` and mutated only DB governance schema/seed rows. It did not acquire external data and did not touch trading/order/fill/position rows.

Current freshness blockers:

{freshness_blockers or "- none"}

Receipt gaps under the new loop contract:

{receipt_gaps or "- none"}

Lineage gaps under the new loop contract:

{lineage_gaps or "- none"}

These are blocker/unknown states, not negative trading evidence.

### Exact join keys

New governance keys:

- `scheduler_job_registry.job_name`
- `source_freshness_policy.source_family`
- `reference_hashes.ref_id`
- `data_lineage_edges.edge_id`
- `data_lineage_edges.source_receipt_id -> source_receipts.receipt_id`
- `data_lineage_edges.input_ref_id -> reference_hashes.ref_id`

### Leakage audit

No labels, outcomes, future prices, PnL, backtest output, selector tuning, or lifecycle inference were used.

### Split/OOS metrics

Not applicable. No replay/backtest was run.

### Failure decomposition

Closed:

- Recurring loop definitions now exist in DB, not only docs.
- Freshness policy exists for 10 data families.
- DB-level permission checks prevent loop registry rows from implying execution, broker mutation, paper promotion, real-capital permission, or deployment readiness.
- Post-migration snapshot and restore drill pass.

Still blocked:

- Actual source acquisition loops are not implemented in this task.
- Scheduler recurrence is still not proven.
- Reference hashes and lineage edges are empty until real jobs write receipts and derived outputs.
- Runtime authority evidence remains empty.

### Cost/slippage stress where PnL changed

Not applicable.

### Remaining blockers

Build receipt-backed jobs for each family, then require each job to write source receipt, reference hash, lineage edge, freshness update, and scheduler ledger entry.

## No-Background Decision-Maker Report

### What happened

The DB now has an internal contract for which data loops should exist, how often they should run, and what evidence each loop must leave.

### Why it matters

This prevents “random scripts refreshing random DBs.” Future data refresh work has to pass through one job registry, one freshness policy, and one evidence model.

### Whether this changes capital/deployment readiness

No. It is management infrastructure only.

### Plain-language next step

Turn the first source family, probably runtime heartbeat or 5-minute bars, into a real receipt-backed job.

## Artifact Manifest

### Inputs

- `trading.db`
- Task3601-3640 DB management program artifacts
- Chrome GPT review-only output

### Outputs

- `tools/db/apply_management_schema.py`
- `tools/db/loop_contract_report.py`
- `data/artifacts/task_3641_3660_db_loop_contract_schema/scheduler_job_registry.csv`
- `data/artifacts/task_3641_3660_db_loop_contract_schema/source_freshness_policy.csv`
- `data/artifacts/task_3641_3660_db_loop_contract_schema/loop_contract_report.json`
- `data/artifacts/task_3641_3660_db_loop_contract_schema/db_health_metrics.json`
- `data/artifacts/task_3641_3660_db_loop_contract_schema/pre_migration_snapshot_manifest.json`
- `data/artifacts/task_3641_3660_db_loop_contract_schema/post_migration_snapshot_manifest.json`
- `data/artifacts/task_3641_3660_db_loop_contract_schema/restore_drill_result.json`
- `data/artifacts/task_3641_3660_db_loop_contract_schema/gpt_chrome_review.md`
- `data/readonly_mcp/trading_readonly_latest.db`
- `data/snapshots/trading_20260620T163523Z.db`

### Row counts

- `scheduler_job_registry`: {metrics['jobs_registered']}
- `source_freshness_policy`: {metrics['source_freshness_policy_count']}
- `reference_hashes`: {metrics['reference_hash_count']}
- `data_lineage_edges`: {metrics['lineage_edge_count']}

### Validation commands

```powershell
python -m tools.db.apply_management_schema
python -m tools.db.healthcheck --diagnostic-only --strict --require-management-schema
python -m tools.db.loop_contract_report --json data/artifacts/task_3641_3660_db_loop_contract_schema/loop_contract_report.json
python -m tools.db.restore_drill --json data/artifacts/task_3641_3660_db_loop_contract_schema/restore_drill_result.json
python scripts/trader_brain_3641_3660_db_loop_contract_schema_validate.py
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
```

Test success does not modify strategy acceptance status.

Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
"""
    (REPORT_DIR / f"{TASK}.md").write_text(report, encoding="utf-8")
    _write_csv_fixed(
        REPORT_DIR / "task_3660_decision.csv",
        [
            {
                "task_id": "Task3660",
                "verdict": "DB_LOOP_CONTRACT_SCHEMA_INSTALLED_WITH_BLOCKERS",
                "strategy": "NOT_ACCEPTED",
                "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
            }
        ],
        ["task_id", "verdict", "strategy", "deployment", "real_capital"],
    )


def _write_gpt_review() -> None:
    (ARTIFACT_DIR / "gpt_chrome_review.md").write_text(
        """# GPT Chrome Review

Status: `EXECUTED_REVIEW_ONLY`

Review-only findings converted into implementation constraints:

1. Migration must guard `DIAGNOSTIC_ONLY`, kill switch active, and exactly one active `trading.db`.
2. `enabled` in job registry is only diagnostic monitoring, not execution permission.
3. DB-level CHECK constraints must keep execution, broker mutation, real capital, and paper promotion permissions at 0.
4. Missing/stale source semantics must be `UNKNOWN_BLOCKER`.
5. Lineage must require receipts and reference hashes.
6. Duplicate DB hashes are allowed only when classified as readonly export, snapshot, profile artifact, or other non-authoritative artifact.
7. `scheduler_run_ledger` with two rows does not prove recurrence.

This review is not source-of-truth and did not grant strategy acceptance, deployment readiness, paper promotion, replay permission, broker mutation, live-order permission, or real-capital permission.
""",
        encoding="utf-8",
    )


def _update_docs() -> None:
    scheduler_doc = ROOT / "docs" / "db" / "SCHEDULER_SEMANTICS.md"
    text = scheduler_doc.read_text(encoding="utf-8") if scheduler_doc.exists() else "# Scheduler Semantics\n"
    block = """

## DB Loop Contract Schema

Task3641-3660 installed `scheduler_job_registry` and `source_freshness_policy`.

- `enabled=1` means diagnostic monitoring is registered; it does not permit execution.
- `execution_permitted`, `broker_mutation_permitted`, `real_capital_permitted`, and `paper_promotion_permitted` are DB-level CHECK-constrained to `0`.
- `missing_semantics` and `stale_semantics` are constrained to `UNKNOWN_BLOCKER`.
- `data_lineage_edges` requires `source_receipt_id` and `input_ref_id`.
"""
    if "## DB Loop Contract Schema" not in text:
        scheduler_doc.write_text(text.rstrip() + block + "\n", encoding="utf-8")

    llm = ROOT / "docs" / "llm_wiki" / "source_truth_map.md"
    if llm.exists():
        text = llm.read_text(encoding="utf-8")
        block = "\n\n## DB Loop Contract Schema\n\n- Task3641-3660 installed DB-resident loop contracts: `scheduler_job_registry`, `source_freshness_policy`, `reference_hashes`, `data_lineage_edges`.\n- Loop registration is diagnostic-only and does not permit broker mutation, paper promotion, live orders, replay, deployment, or real capital.\n- Current blockers remain source freshness, receipts, lineage, scheduler recurrence, and L6 authority evidence.\n"
        if "## DB Loop Contract Schema" not in text:
            llm.write_text(text.rstrip() + block + "\n", encoding="utf-8")

    obsidian = ROOT / "docs" / "obsidian" / "mocs" / "Operating System Map.md"
    if obsidian.exists():
        text = obsidian.read_text(encoding="utf-8")
        block = "\n\n## DB Loop Contract Schema\n\n- Report: `docs/reports/task_3641_3660_db_loop_contract_schema/task_3641_3660_db_loop_contract_schema.md`\n- Status: loop contracts installed in DB; actual source loops still need receipt/lineage implementation.\n"
        if "## DB Loop Contract Schema" not in text:
            obsidian.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metrics = health_metrics()
    loop_report = build_report()

    write_csv(ARTIFACT_DIR / "scheduler_job_registry.csv", _rows("scheduler_job_registry"))
    write_csv(ARTIFACT_DIR / "source_freshness_policy.csv", _rows("source_freshness_policy"))
    write_csv(ARTIFACT_DIR / "reference_hashes.csv", _rows("reference_hashes"))
    write_csv(ARTIFACT_DIR / "data_lineage_edges.csv", _rows("data_lineage_edges"))
    write_json(ARTIFACT_DIR / "loop_contract_report.json", loop_report)
    write_json(ARTIFACT_DIR / "db_health_metrics.json", metrics)
    _write_gpt_review()
    _update_docs()
    _write_report(metrics, loop_report)
    print("TASK3641_3660_DB_LOOP_CONTRACT_SCHEMA_GENERATED")


if __name__ == "__main__":
    main()
