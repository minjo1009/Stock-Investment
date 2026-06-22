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


TASK = "task_3651_3670_db_registered_loop_runner"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK
REPORT_DIR = ROOT / "docs" / "reports" / TASK


def _query(sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    con = connect_readonly(ACTIVE_DB)
    try:
        return [dict(row) for row in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def _write_csv_fixed(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _run_result() -> dict[str, object]:
    path = ARTIFACT_DIR / "registered_loop_run_result.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_gpt_review() -> None:
    (ARTIFACT_DIR / "gpt_chrome_review.md").write_text(
        """# GPT Chrome Review

Status: `EXECUTED_REVIEW_ONLY`

Review-only conclusion:

1. Implement `tools.db.run_registered_loop_once` first.
2. Do not wire market data, broker truth, runtime decisions, or authority evidence before the common loop substrate exists.
3. Adapter-free jobs should write `SKIPPED` ledger evidence with exact reason, not pretend freshness recovered.
4. Implement only one real adapter in this slice: `diagnostic_runtime_heartbeats`.
5. The heartbeat adapter may write source receipt, reference hash, lineage edge, source freshness, and scheduler ledger evidence.
6. `SKIPPED` and heartbeat `SUCCESS` must not imply strategy acceptance, deployment readiness, broker mutation, paper promotion, replay permission, live-order permission, or real-capital permission.

This review is not source-of-truth.
""",
        encoding="utf-8",
    )


def _write_docs() -> None:
    scheduler_doc = ROOT / "docs" / "db" / "SCHEDULER_SEMANTICS.md"
    text = scheduler_doc.read_text(encoding="utf-8") if scheduler_doc.exists() else "# Scheduler Semantics\n"
    block = """

## Registered Loop Runner

Task3651-3670 added `tools.db.run_registered_loop_once`.

- Default mode is dry-run.
- `--apply` writes diagnostic loop evidence only.
- Only `diagnostic_runtime_heartbeats_refresh` has a real adapter in this slice.
- Adapter-free jobs write `SKIPPED` with `NO_ADAPTER_REGISTERED_DIAGNOSTIC_ONLY`.
- `SKIPPED` is evidence that the loop ran; it is not source freshness recovery.
"""
    if "## Registered Loop Runner" not in text:
        scheduler_doc.write_text(text.rstrip() + block + "\n", encoding="utf-8")

    llm = ROOT / "docs" / "llm_wiki" / "README.md"
    if llm.exists():
        text = llm.read_text(encoding="utf-8")
        old = "- latest DB operations line is Task3601-3660: DB management tooling, read-only MCP copy/snapshot/restore drill, and DB-resident loop contracts are installed; actual source loops, source receipts, lineage edges, scheduler recurrence proof, and L6 authority evidence remain blockers"
        new = "- latest DB operations line is Task3601-3670: DB management tooling, DB-resident loop contracts, and a generic registered loop runner are installed; the first internal heartbeat now writes receipt/hash/lineage evidence, while market data, broker truth, runtime decisions, authority evidence, and recurrence proof remain blockers"
        if old in text:
            llm.write_text(text.replace(old, new), encoding="utf-8")

    vault = ROOT / "docs" / "obsidian" / "Vault Home.md"
    if vault.exists():
        text = vault.read_text(encoding="utf-8")
        text = text.replace(
            "Task3601-3640 DB Management Program, then Task3641-3660 DB Loop Contract Schema",
            "Task3601-3640 DB Management Program, Task3641-3660 DB Loop Contract Schema, then Task3651-3670 Registered Loop Runner",
        )
        text = text.replace(
            "Task3641-3660 now stores DB loop contracts in `scheduler_job_registry` and `source_freshness_policy` with DB-level no-execution/no-broker/no-paper-promotion/no-real-capital constraints. Runtime promotion remains blocked until actual source loops write receipts, lineage, scheduler recurrence, broker truth evidence, and authority evidence.",
            "Task3651-3670 added a generic registered loop runner; the first internal heartbeat now writes receipt/hash/lineage/freshness evidence, while adapter-free jobs write explicit SKIPPED ledger rows. Runtime promotion remains blocked until market/broker/authority adapters, recurrence proof, broker truth evidence, and authority evidence are implemented.",
        )
        if "DB Registered Loop Runner" not in text:
            text = text.replace(
                "- [DB Loop Contract Schema](../reports/task_3641_3660_db_loop_contract_schema/task_3641_3660_db_loop_contract_schema.md)",
                "- [DB Loop Contract Schema](../reports/task_3641_3660_db_loop_contract_schema/task_3641_3660_db_loop_contract_schema.md)\n- [DB Registered Loop Runner](../reports/task_3651_3670_db_registered_loop_runner/task_3651_3670_db_registered_loop_runner.md)",
            )
        vault.write_text(text, encoding="utf-8")


def _write_report(metrics: dict[str, object], loop_report: dict[str, object], run_result: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3651-3670 DB Registered Loop Runner

## Decision Summary

- Verdict: `DB_REGISTERED_LOOP_RUNNER_INSTALLED_WITH_HEARTBEAT_EVIDENCE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - Jobs seen: {run_result.get('jobs_seen')}
  - Runner success count: {run_result.get('success_count')}
  - Runner skipped count: {run_result.get('skipped_count')}
  - Source receipts count: {metrics['source_receipts_count']}
  - Reference hashes count: {metrics['reference_hash_count']}
  - Data lineage edge count: {metrics['lineage_edge_count']}
  - Scheduler ledger rows: {metrics['scheduler_run_ledger_count']}
  - Scheduler distinct buckets: {metrics['scheduler_distinct_bucket_count']}
  - Scheduler recurrence proven: {metrics['scheduler_recurrence_proven']}
- What changed:
  - Added `tools.db.run_registered_loop_once`.
  - Default mode is dry-run.
  - `--apply` records diagnostic-only loop evidence.
  - Internal heartbeat adapter writes source receipt, reference hash, lineage edge, source freshness, and scheduler ledger rows.
  - Adapter-free jobs write explicit `SKIPPED` rows with reason `NO_ADAPTER_REGISTERED_DIAGNOSTIC_ONLY`.
- Next action:
  - Implement the next real adapter behind this runner, one family at a time.

## Quant Expert Report

### Data source and source readiness

The only actual source adapter in this task is `diagnostic_runtime_heartbeats`. It writes an internal diagnostic heartbeat raw JSON under `data/raw/diagnostic_runtime_heartbeats/`.

Market data, broker truth, runtime decisions, and authority evidence were not wired.

Current freshness blockers remain:

{chr(10).join(f"- `{item}`" for item in loop_report.get('freshness_blockers', []))}

### Exact join keys

New evidence path:

- `source_receipts.receipt_id`
- `reference_hashes.ref_id`
- `data_lineage_edges.source_receipt_id -> source_receipts.receipt_id`
- `data_lineage_edges.input_ref_id -> reference_hashes.ref_id`
- `scheduler_run_ledger.run_ledger_id`

### Leakage audit

No labels, outcomes, future prices, PnL, replay output, selector tuning, broker truth inference, or lifecycle inference were used.

### Split/OOS metrics

Not applicable. No replay/backtest was run.

### Failure decomposition

Closed:

- `reference_hashes` is no longer zero.
- `data_lineage_edges` is no longer zero.
- Registered jobs now emit scheduler ledger evidence.
- Adapter-free jobs have explicit skip reasons instead of silent absence.

Still blocked:

- Scheduler recurrence is not proven because distinct buckets are still below 3.
- Market ticks, 5m bars, broker truth, runtime decisions, and authority evidence remain stale or missing.
- SKIPPED rows do not recover freshness.

### Cost/slippage stress where PnL changed

Not applicable.

### Remaining blockers

Implement next adapters one by one behind `tools.db.run_registered_loop_once`.

## No-Background Decision-Maker Report

### What happened

The DB loop system now actually runs once and leaves evidence. One internal heartbeat succeeds; jobs without source adapters are explicitly skipped.

### Why it matters

The system no longer has only a plan. It has a common loop runner and the first receipt/hash/lineage/freshness evidence path.

### Whether this changes capital/deployment readiness

No. It is still diagnostic-only.

### Plain-language next step

Attach the first real external or fixture-backed source adapter to the same runner.

## Artifact Manifest

### Inputs

- `trading.db`
- Task3641-3660 loop contract schema
- Chrome GPT review-only output

### Outputs

- `tools/db/run_registered_loop_once.py`
- `tests/test_db_registered_loop_runner.py`
- `data/raw/diagnostic_runtime_heartbeats/`
- `data/artifacts/task_3651_3670_db_registered_loop_runner/registered_loop_run_result.json`
- `data/artifacts/task_3651_3670_db_registered_loop_runner/loop_contract_report.json`
- `data/artifacts/task_3651_3670_db_registered_loop_runner/db_health_metrics.json`
- `data/artifacts/task_3651_3670_db_registered_loop_runner/gpt_chrome_review.md`
- `data/artifacts/task_3651_3670_db_registered_loop_runner/scheduler_run_ledger_task_rows.csv`
- `data/artifacts/task_3651_3670_db_registered_loop_runner/source_receipts_heartbeat.csv`
- `data/artifacts/task_3651_3670_db_registered_loop_runner/reference_hashes_heartbeat.csv`
- `data/artifacts/task_3651_3670_db_registered_loop_runner/data_lineage_edges_heartbeat.csv`

### Validation commands

```powershell
python -m unittest tests.test_db_registered_loop_runner
python -m tools.db.run_registered_loop_once
python -m tools.db.healthcheck --diagnostic-only --strict --require-management-schema
python scripts/trader_brain_3651_3670_db_registered_loop_runner_validate.py
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
        REPORT_DIR / "task_3670_decision.csv",
        [
            {
                "task_id": "Task3670",
                "verdict": "DB_REGISTERED_LOOP_RUNNER_INSTALLED_WITH_HEARTBEAT_EVIDENCE",
                "strategy": "NOT_ACCEPTED",
                "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
            }
        ],
        ["task_id", "verdict", "strategy", "deployment", "real_capital"],
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metrics = health_metrics()
    loop_report = build_report()
    run_result = _run_result()
    bucket = str(run_result.get("bucket_ts", ""))

    write_json(ARTIFACT_DIR / "loop_contract_report.json", loop_report)
    write_json(ARTIFACT_DIR / "db_health_metrics.json", metrics)
    write_csv(
        ARTIFACT_DIR / "scheduler_run_ledger_task_rows.csv",
        _query("SELECT * FROM scheduler_run_ledger WHERE expected_bucket_ts=? ORDER BY cadence", (bucket,)),
    )
    write_csv(
        ARTIFACT_DIR / "source_receipts_heartbeat.csv",
        _query("SELECT * FROM source_receipts WHERE source_family='diagnostic_runtime_heartbeats' ORDER BY created_at DESC LIMIT 5"),
    )
    write_csv(
        ARTIFACT_DIR / "reference_hashes_heartbeat.csv",
        _query("SELECT * FROM reference_hashes WHERE source_family='diagnostic_runtime_heartbeats' ORDER BY created_at DESC LIMIT 5"),
    )
    write_csv(
        ARTIFACT_DIR / "data_lineage_edges_heartbeat.csv",
        _query("SELECT * FROM data_lineage_edges WHERE source_family='diagnostic_runtime_heartbeats' ORDER BY created_at DESC LIMIT 5"),
    )
    _write_gpt_review()
    _write_docs()
    _write_report(metrics, loop_report, run_result)
    print("TASK3651_3670_DB_REGISTERED_LOOP_RUNNER_GENERATED")


if __name__ == "__main__":
    main()

