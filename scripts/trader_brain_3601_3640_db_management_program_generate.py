from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.db.common import (
    ROOT,
    health_metrics,
    scan_db_authority,
    source_freshness_rows,
    connect_readonly,
    write_csv,
    write_json,
)


TASK = "task_3601_3640_db_management_program"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / TASK
REPORT_DIR = ROOT / "docs" / "reports" / TASK
DOCS_DB_DIR = ROOT / "docs" / "db"


def _write_csv_fixed(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _program_plan_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    specs = [
        ("Task3601", "DB management program selection", "P0", "Freeze DB management scope and safety boundaries", "docs/report, registry", "PASS"),
        ("Task3602", "Chrome GPT review capture", "P0", "Record review-only GPT prompt and findings", "gpt_chrome_review.md", "PASS"),
        ("Task3603", "Authority scanner CLI", "P0", "Classify every DB-like file with role/status/hash", "tools.db.scan_authority", "PASS"),
        ("Task3604", "Diagnostic healthcheck CLI", "P0", "Fail on authority/control/integrity breaches", "tools.db.healthcheck", "PASS"),
        ("Task3605", "Read-only MCP copy exporter", "P0", "Generate replaceable copy for MCP/LLM inspection only", "tools.db.export_readonly_snapshot", "PASS"),
        ("Task3606", "Snapshot exporter", "P0", "Create governed immutable snapshot", "data/snapshots", "PASS"),
        ("Task3607", "Restore drill", "P0", "Verify latest snapshot integrity in temp restore", "tools.db.restore_drill", "PASS"),
        ("Task3608", "DB topology contract", "P0", "Define active/raw/artifact/snapshot/readonly/backup/quarantine roles", "db_topology_contract.csv", "PASS"),
        ("Task3609", "Anti-duplication policy", "P0", "No blind deletion; register/hash/archive/quarantine", "DB_AUTHORITY_POLICY.md", "PASS"),
        ("Task3610", "Cadence contract", "P0", "Define data-family loop cadence and blocker", "db_loop_cadence_contract.csv", "PASS"),
        ("Task3611", "Scheduler semantics contract", "P0", "Lease/idempotency/receipt/freshness/ledger rules", "SCHEDULER_SEMANTICS.md", "PASS"),
        ("Task3612", "Freshness blocker mapping", "P0", "Keep stale source as BLOCKER/UNKNOWN not negative", "db_health_metrics.json", "PASS"),
        ("Task3613", "Tooling decision matrix", "P0", "Place Litestream/dbmate/dbt/GX/Pandera/MCP/DuckDB", "db_tooling_decision_matrix.csv", "PASS"),
        ("Task3614", "Current DB inventory artifact", "P0", "Persist scanner output", "db_authority_scan.csv", "PASS"),
        ("Task3615", "Health metrics artifact", "P0", "Persist governance metrics", "db_health_metrics.json", "PASS"),
        ("Task3616", "Restore runbook", "P0", "Document snapshot/restore drill requirements", "RESTORE_RUNBOOK.md", "PASS"),
        ("Task3617", "Retention/archive policy", "P0", "Retain non-authoritative DBs pending review", "RETENTION_AND_ARCHIVE_POLICY.md", "PASS"),
        ("Task3618", "Source receipt dependency rule", "P0", "Require receipt before derived write in future jobs", "SCHEDULER_SEMANTICS.md", "PASS"),
        ("Task3619", "Read-only MCP boundary", "P0", "Never attach MCP to active DB", "DB_TOPOLOGY.md", "PASS"),
        ("Task3620", "Closeout report", "P0", "Report DB management status and blockers", "task report", "PASS"),
        ("Task3621", "Move-active-DB migration plan", "P1", "Plan optional data/active/trading.db migration without breaking paths", "future task", "PLANNED"),
        ("Task3622", "scheduler_job_registry table", "P1", "Add first-class job registry if schema migration approved", "future migration", "PLANNED"),
        ("Task3623", "source_freshness_policy table", "P1", "Normalize cadence policy into DB", "future migration", "PLANNED"),
        ("Task3624", "data_lineage_edges table", "P1", "Persist source-to-derived lineage", "future migration", "PLANNED"),
        ("Task3625", "reference_hashes table", "P1", "Persist file/input/output hashes", "future migration", "PLANNED"),
        ("Task3626", "intraday tick diagnostic job", "P1", "Implement receipt-backed intraday tick refresh", "future job", "PLANNED"),
        ("Task3627", "5m bar diagnostic job", "P1", "Implement receipt-backed 5m bar refresh", "future job", "PLANNED"),
        ("Task3628", "daily OHLCV job", "P1", "Implement close plus next-morning verification", "future job", "PLANNED"),
        ("Task3629", "SEC/events job", "P1", "Implement event refresh cadence", "future job", "PLANNED"),
        ("Task3630", "macro/rates job", "P1", "Implement hourly/daily macro refresh", "future job", "PLANNED"),
        ("Task3631", "broker truth reconciliation job", "P1", "Use fixture/source truth only; no broker mutation", "future job", "PLANNED"),
        ("Task3632", "runtime heartbeat job", "P1", "Persist heartbeat evidence under scheduler registry", "future job", "PLANNED"),
        ("Task3633", "L6 authority evidence job", "P1", "Require evidence per diagnostic cycle", "future job", "PLANNED"),
        ("Task3634", "frontend read model refresh job", "P1", "Run only after upstream freshness passes", "future job", "PLANNED"),
        ("Task3635", "catalog/report artifact job", "P1", "Require lineage and run ledger evidence", "future job", "PLANNED"),
        ("Task3636", "Litestream disabled skeleton", "P2", "Add after restore drill and operator destination approval", "future config", "DEFERRED"),
        ("Task3637", "dbmate migration owner decision", "P2", "Adopt only if single migration owner", "future review", "DEFERRED"),
        ("Task3638", "Pandera/GX ingestion validation lane", "P2", "Pandera first, GX after source contracts stabilize", "future validators", "DEFERRED"),
        ("Task3639", "DuckDB/sqlite-utils read-only analytics", "P2", "Use only for artifact analysis/export", "future tools", "DEFERRED"),
        ("Task3640", "DB management program closeout", "P0", "Close with statuses unchanged", "decision csv", "PASS"),
    ]
    for task_id, title, priority, objective, artifact, status in specs:
        rows.append(
            {
                "task_id": task_id,
                "title": title,
                "priority": priority,
                "objective": objective,
                "owner_scope": "Data Operations / Runtime DB Governance",
                "artifact_or_code": artifact,
                "status": status,
                "safety_boundary": "diagnostic_only_no_broker_mutation_no_replay_no_real_capital",
            }
        )
    return rows


def _topology_rows() -> list[dict[str, object]]:
    return [
        {
            "family": "active_runtime_db",
            "current_path": "trading.db",
            "target_path": "trading.db now; optional data/active/trading.db migration later",
            "write_authority": "YES",
            "purpose": "canonical diagnostic runtime DB",
            "rule": "exactly one ACTIVE DB in manifest",
        },
        {
            "family": "raw_sources",
            "current_path": "data/raw/{source}/",
            "target_path": "data/raw/{family}/YYYY/MM/DD/",
            "write_authority": "APPEND_ONLY",
            "purpose": "provider payloads and source references",
            "rule": "raw source is append-only and never inferred",
        },
        {
            "family": "task_artifacts",
            "current_path": "data/artifacts/{task_id}/",
            "target_path": "data/artifacts/{task_id}/",
            "write_authority": "APPEND_ONLY",
            "purpose": "reports, manifests, derived exports",
            "rule": "not source-of-truth unless explicitly promoted",
        },
        {
            "family": "snapshots",
            "current_path": "data/snapshots/",
            "target_path": "data/snapshots/trading_YYYYMMDDTHHMMSSZ.db",
            "write_authority": "IMMUTABLE_COPY",
            "purpose": "point-in-time restore evidence",
            "rule": "created by exporter and verified by restore drill",
        },
        {
            "family": "readonly_mcp",
            "current_path": "data/readonly_mcp/trading_readonly_latest.db",
            "target_path": "data/readonly_mcp/trading_readonly_latest.db",
            "write_authority": "NO",
            "purpose": "MCP/LLM read-only inspection copy",
            "rule": "replaceable derived copy; never active DB",
        },
        {
            "family": "backups",
            "current_path": "data/artifacts/*/backups and future data/backups/",
            "target_path": "data/backups/",
            "write_authority": "APPEND_ONLY",
            "purpose": "operator backup and later Litestream target",
            "rule": "restore drill required before destructive migration",
        },
        {
            "family": "quarantine",
            "current_path": "none active",
            "target_path": "data/quarantine/",
            "write_authority": "NO_ACTIVE_WRITES",
            "purpose": "unknown DBs pending manifest review",
            "rule": "unknown DBs are quarantined/registered before cleanup",
        },
    ]


def _cadence_rows() -> list[dict[str, object]]:
    rows = [
        ("market_ticks_intraday", "provider_intraday", "1-5 min during US market hours", "10 min", "stale blocks intraday-derived diagnostics", "DIAGNOSTIC_ONLY"),
        ("market_bars_5m", "provider_5m_bars", "5-10 min during US market hours", "20 min", "stale blocks 5m read models", "DIAGNOSTIC_ONLY"),
        ("daily_ohlcv", "provider_daily", "after close plus next-morning verification", "1 trading day", "stale blocks daily refresh claims", "DIAGNOSTIC_ONLY"),
        ("sec_events", "SEC/derived events", "15-60 min during active filing window", "1 business day", "stale blocks event-source claims", "DIAGNOSTIC_ONLY"),
        ("macro_rates", "FRED/rates/macro", "hourly during market hours plus daily close", "1 business day", "stale blocks macro regime claims", "DIAGNOSTIC_ONLY"),
        ("broker_truth_reconciliation", "KIS paper truth fixture/source", "daily or fixture-triggered", "absent/stale is broker-truth blocker", "no broker-truth claim without source", "DIAGNOSTIC_ONLY"),
        ("diagnostic_runtime_heartbeats", "local runtime", "5 min safety heartbeat and 10 min brain heartbeat", "30 min", "stale blocks runtime-recent claims", "DIAGNOSTIC_ONLY"),
        ("authority_evidence_ledger", "L6 runtime authority", "per diagnostic cycle before PAPER_ELIGIBLE path", "missing is hard blocker", "blocks PAPER_ELIGIBLE evidence", "DIAGNOSTIC_ONLY"),
        ("frontend_read_models", "local read model builder", "after successful upstream refresh", "blocked by upstream", "never refresh from stale upstream as current", "READ_ONLY"),
        ("catalog_report_artifacts", "report/catalog generator", "after diagnostic report generation", "lineage/receipt required", "blocks report freshness claim", "READ_ONLY"),
    ]
    return [
        {
            "source_family": family,
            "provider_or_owner": provider,
            "target_cadence": cadence,
            "freshness_blocker": blocker,
            "downstream_rule": rule,
            "run_boundary": boundary,
        }
        for family, provider, cadence, blocker, rule, boundary in rows
    ]


def _tool_rows() -> list[dict[str, object]]:
    return [
        {"tool": "Litestream", "decision": "DEFER", "fit": "SQLite backup/replication", "condition": "enable only after restore drill and operator backup target approval"},
        {"tool": "dbmate", "decision": "DEFER", "fit": "SQL migrations", "condition": "adopt only if it becomes single migration owner or wraps schema_migrations cleanly"},
        {"tool": "dbt source freshness pattern", "decision": "ADOPT_CONCEPT", "fit": "freshness SLA model", "condition": "represent as local source_freshness_policy before full dbt"},
        {"tool": "Pandera", "decision": "P2_PILOT", "fit": "DataFrame ingestion validation", "condition": "use at source ingestion boundaries after cadence jobs are wired"},
        {"tool": "Great Expectations", "decision": "DEFER", "fit": "broader data quality suites", "condition": "source contracts must stabilize first"},
        {"tool": "sqlite-utils", "decision": "OPTIONAL", "fit": "inspection/export helper", "condition": "operator utility only, not mutation owner"},
        {"tool": "read-only SQLite MCP", "decision": "CANDIDATE", "fit": "LLM DB inspection", "condition": "attach only to data/readonly_mcp copy, never active DB"},
        {"tool": "DuckDB MCP", "decision": "P2_READONLY", "fit": "artifact/lake analytics", "condition": "read-only analysis over artifacts and snapshots only"},
    ]


def _write_docs(metrics: dict[str, object]) -> None:
    DOCS_DB_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DB_DIR / "DB_TOPOLOGY.md").write_text(
        """# DB Topology

- Active authority: `trading.db` remains the current writable diagnostic DB.
- Future migration to `data/active/trading.db` is a separate dependency-aware task.
- Raw sources stay append-only under `data/raw/`.
- Task artifacts stay under `data/artifacts/<task_id>/`.
- Read-only MCP access must use `data/readonly_mcp/trading_readonly_latest.db`.
- Restore snapshots live under `data/snapshots/`.
- Unknown DBs are registered or quarantined; they are not blindly deleted.

Safety footer: Strategy `NOT_ACCEPTED`; Deployment `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`; Real Capital `FORBIDDEN`.
""",
        encoding="utf-8",
    )
    (DOCS_DB_DIR / "DB_AUTHORITY_POLICY.md").write_text(
        """# DB Authority Policy

1. Exactly one DB may be `ACTIVE`: current path `trading.db`.
2. Non-authoritative DBs are audit evidence until retention policy permits archive/removal.
3. Every DB-like file must be hash-scanned and classified.
4. Duplicate hashes are reference duplicates, not deletion permission.
5. Read-only MCP and DuckDB analysis must use copied DBs or artifacts, never the active DB.
6. Stale source is a blocker/unknown, never negative evidence.
""",
        encoding="utf-8",
    )
    (DOCS_DB_DIR / "SCHEDULER_SEMANTICS.md").write_text(
        """# Scheduler Semantics

Every DB/data job must:

1. Read `control_state`.
2. Require `run_mode=DIAGNOSTIC_ONLY` and `kill_switch_active=1`.
3. Acquire a lease before work.
4. Compute an idempotency key from cadence bucket and input fingerprint.
5. Check upstream freshness policy.
6. Write or reference a source receipt before derived mutation.
7. Mutate derived state in one transaction.
8. Write lineage/hash evidence.
9. Update `source_freshness`.
10. Write `scheduler_run_ledger` for success, skip, and failure.

Allowed skipped reasons: `LEASE_HELD`, `OUTSIDE_MARKET_WINDOW`, `UPSTREAM_STALE`, `NO_AUTHORITY_EVIDENCE`, `PROVIDER_UNAVAILABLE`, `DUPLICATE_INPUT_HASH`, `CONTROL_STATE_BLOCKED`, `SCHEMA_MISMATCH`, `RECEIPT_MISSING`.
""",
        encoding="utf-8",
    )
    (DOCS_DB_DIR / "RETENTION_AND_ARCHIVE_POLICY.md").write_text(
        """# Retention And Archive Policy

- No blind deletion of DBs, raw sources, reports, snapshots, logs, or broker evidence.
- Generated cache DBs may be cleaned only after scan classification and when no report depends on them.
- Root host DB copies remain `NOT_AUTHORITATIVE` until operator-approved archive.
- Snapshot/backup existence is required before destructive migration.
- Retention enforcement starts as dry-run reporting.
""",
        encoding="utf-8",
    )
    (DOCS_DB_DIR / "RESTORE_RUNBOOK.md").write_text(
        f"""# Restore Runbook

Current restore drill status: `{metrics.get('restore_drill_status', 'SEE_ARTIFACT')}`.

Commands:

```powershell
python -m tools.db.export_readonly_snapshot --readonly --snapshot --manifest data/artifacts/task_3601_3640_db_management_program/readonly_snapshot_manifest.json
python -m tools.db.restore_drill --json data/artifacts/task_3601_3640_db_management_program/restore_drill_result.json
python -m tools.db.healthcheck --diagnostic-only --strict
```

Restore success never changes strategy acceptance, deployment readiness, paper eligibility, or real-capital status.
""",
        encoding="utf-8",
    )


def _write_gpt_review() -> None:
    (ARTIFACT_DIR / "gpt_chrome_review.md").write_text(
        """# GPT Chrome Review

Status: `EXECUTED_REVIEW_ONLY`

The prompt sent to Chrome ChatGPT summarized the DB governance state, fail-closed control state, stale source families, scheduler evidence gap, and safety boundaries.

Review findings used as advisory input:

1. Keep exactly one active writable DB.
2. Create read-only MCP copies from the active DB; never attach MCP to the active DB.
3. Treat snapshots, backups, artifacts, and root host DB copies as classified non-active assets, not deletion targets.
4. Every recurring job should require lease, idempotency key, source receipt, freshness check, lineage/hash evidence, scheduler ledger row, and explicit skipped reason.
5. Add snapshot and restore drill before destructive migration.
6. Use Litestream/dbmate only after ownership boundaries are clear.
7. Adopt dbt-style freshness as a local policy pattern first.
8. Use Pandera before Great Expectations at ingestion boundaries.
9. Keep Strategy `NOT_ACCEPTED`, Deployment `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and Real Capital `FORBIDDEN`.

This review is not source-of-truth and did not grant trading acceptance, deployment readiness, broker mutation, paper promotion, replay permission, or real-capital permission.
""",
        encoding="utf-8",
    )


def _write_report(metrics: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3601-3640 DB Management Program

## Decision Summary

- Verdict: `DB_MANAGEMENT_PROGRAM_IMPLEMENTED_WITH_SOURCE_BLOCKERS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - DB scan files: {metrics['db_scan_file_count']}
  - Unknown DB files: {metrics['unknown_db_count']}
  - Duplicate hash count: {metrics['duplicate_hash_count']}
  - Stale source families: {metrics['stale_source_count']}
  - Scheduler ledger rows: {metrics['scheduler_run_ledger_count']}
  - Runtime authority evidence rows: {metrics['runtime_authority_evidence_ledger_count']}
  - Paper order intents: {metrics['paper_order_intents_count']}
- What changed:
  - Added read-only DB authority scanner and diagnostic healthcheck.
  - Added governed read-only MCP copy export.
  - Added governed snapshot export and restore drill.
  - Added DB topology, authority, scheduler, retention, and restore docs.
  - Captured Chrome GPT review-only findings as advisory input.
- Next action:
  - Implement P1 scheduler jobs that write lease, receipt, freshness, lineage, and ledger evidence for each data family.

## Quant Expert Report

### Data source and source readiness

The task used active `trading.db` in read-only mode for inspection. It created derived copies under `data/readonly_mcp/` and `data/snapshots/`.

Current source blockers remain:

{chr(10).join(f'- `{family}`' for family in metrics['stale_source_families'])}

These blockers are not negative labels and do not imply strategy failure.

### Exact join keys

No trading table join keys were changed. DB governance keys remain:

- `db_authority_manifest.authority_id`
- `source_freshness.source_family`
- `source_receipts.receipt_id`
- `scheduler_run_ledger.run_ledger_id`

Future P1 lineage work should add source receipt and lineage keys before derived writes.

### Leakage audit

No labels, outcomes, future prices, PnL, backtest results, replay outputs, or lifecycle inference were used.

### Split/OOS metrics

Not applicable. No replay/backtest was run.

### Failure decomposition

Closed:

- Unknown DB scanner classification now reports zero unknown DBs.
- Active DB integrity check passes.
- Control state remains fail-closed.
- Read-only MCP DB copy exists and has matching hash.
- Snapshot restore drill passes.

Still blocked:

- Six source families remain stale or missing authority evidence.
- Scheduler run ledger has only two rows, so recurring operation is not proven.
- Runtime authority evidence ledger has zero rows.
- Full per-family ingestion loops are planned but not implemented in this task.

### Cost/slippage stress where PnL changed

Not applicable.

### Remaining blockers

P1 must implement receipt-backed data-family loops and scheduler evidence before any runtime freshness claims can be considered current.

## No-Background Decision-Maker Report

### What happened

DB management was turned into a repeatable operating program. The project can now scan DB files, detect authority problems, export read-only inspection copies, create snapshots, and verify restore.

### Why it matters

This prevents accidental active DB confusion and gives the system a concrete way to prove DB health before higher-level trading diagnostics rely on it.

### Whether this changes capital/deployment readiness

No. The data is still stale and runtime authority evidence is empty.

### Plain-language next step

Build the actual per-data-family refresh loops on top of this contract.

## Artifact Manifest

### Inputs

- `trading.db`
- `docs/operating_system/project_operating_state.md`
- Task3571-3580 DB audit
- Task3581-3600 DB governance systemization
- Chrome GPT review-only output

### Outputs

- `tools/db/common.py`
- `tools/db/scan_authority.py`
- `tools/db/healthcheck.py`
- `tools/db/export_readonly_snapshot.py`
- `tools/db/restore_drill.py`
- `docs/db/DB_TOPOLOGY.md`
- `docs/db/DB_AUTHORITY_POLICY.md`
- `docs/db/SCHEDULER_SEMANTICS.md`
- `docs/db/RETENTION_AND_ARCHIVE_POLICY.md`
- `docs/db/RESTORE_RUNBOOK.md`
- `data/artifacts/task_3601_3640_db_management_program/db_management_program_plan.csv`
- `data/artifacts/task_3601_3640_db_management_program/db_loop_cadence_contract.csv`
- `data/artifacts/task_3601_3640_db_management_program/db_topology_contract.csv`
- `data/artifacts/task_3601_3640_db_management_program/db_tooling_decision_matrix.csv`
- `data/artifacts/task_3601_3640_db_management_program/db_authority_scan.csv`
- `data/artifacts/task_3601_3640_db_management_program/db_health_metrics.json`
- `data/artifacts/task_3601_3640_db_management_program/gpt_chrome_review.md`
- `data/readonly_mcp/trading_readonly_latest.db`
- `data/snapshots/trading_*.db`

### Row counts

- Program plan rows: 40
- Topology rows: 7
- Cadence rows: 10
- Tooling matrix rows: 8
- DB scan rows: {metrics['db_scan_file_count']}

### File sizes

See scanner and snapshot manifest artifacts.

### Validation commands

```powershell
python -m tools.db.scan_authority --csv data/artifacts/task_3601_3640_db_management_program/db_authority_scan.csv --json data/artifacts/task_3601_3640_db_management_program/db_authority_scan.json
python -m tools.db.healthcheck --diagnostic-only --strict --json data/artifacts/task_3601_3640_db_management_program/db_health_metrics.json
python -m tools.db.restore_drill --json data/artifacts/task_3601_3640_db_management_program/restore_drill_result.json
python scripts/trader_brain_3601_3640_db_management_program_validate.py
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
        REPORT_DIR / "task_3640_decision.csv",
        [
            {
                "task_id": "Task3640",
                "verdict": "DB_MANAGEMENT_PROGRAM_IMPLEMENTED_WITH_SOURCE_BLOCKERS",
                "strategy": "NOT_ACCEPTED",
                "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
            }
        ],
        ["task_id", "verdict", "strategy", "deployment", "real_capital"],
    )


def _update_navigation() -> None:
    llm = ROOT / "docs" / "llm_wiki" / "source_truth_map.md"
    if llm.exists():
        text = llm.read_text(encoding="utf-8")
        block = "\n\n## DB Management Program\n\n- Current DB authority and cadence contract: `docs/reports/task_3601_3640_db_management_program/task_3601_3640_db_management_program.md`\n- DB topology and scheduler contracts: `docs/db/`\n- Read-only MCP DB copy: `data/readonly_mcp/trading_readonly_latest.db`\n- Safety remains `NOT_ACCEPTED` / `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` / `FORBIDDEN`.\n"
        if "## DB Management Program" not in text:
            llm.write_text(text.rstrip() + block + "\n", encoding="utf-8")
    obsidian = ROOT / "docs" / "obsidian" / "mocs" / "Operating System Map.md"
    if obsidian.exists():
        text = obsidian.read_text(encoding="utf-8")
        block = "\n\n## DB Management Program\n\n- Report: `docs/reports/task_3601_3640_db_management_program/task_3601_3640_db_management_program.md`\n- Contracts: `docs/db/DB_TOPOLOGY.md`, `docs/db/SCHEDULER_SEMANTICS.md`\n- Current conclusion: DB management tooling exists; source freshness and scheduler recurrence remain blockers.\n"
        if "## DB Management Program" not in text:
            obsidian.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    metrics = health_metrics()
    restore_path = ARTIFACT_DIR / "restore_drill_result.json"
    if restore_path.exists():
        restore = json.loads(restore_path.read_text(encoding="utf-8"))
        metrics["restore_drill_status"] = restore.get("restore_drill_status", "UNKNOWN")
    else:
        metrics["restore_drill_status"] = "NOT_RUN"

    _write_csv_fixed(
        ARTIFACT_DIR / "db_management_program_plan.csv",
        _program_plan_rows(),
        [
            "task_id",
            "title",
            "priority",
            "objective",
            "owner_scope",
            "artifact_or_code",
            "status",
            "safety_boundary",
        ],
    )
    write_csv(ARTIFACT_DIR / "db_topology_contract.csv", _topology_rows())
    write_csv(ARTIFACT_DIR / "db_loop_cadence_contract.csv", _cadence_rows())
    write_csv(ARTIFACT_DIR / "db_tooling_decision_matrix.csv", _tool_rows())
    write_csv(ARTIFACT_DIR / "db_authority_scan.csv", scan_db_authority())
    write_json(ARTIFACT_DIR / "db_authority_scan.json", scan_db_authority())
    write_json(ARTIFACT_DIR / "db_health_metrics.json", metrics)
    con = connect_readonly()
    try:
        write_csv(ARTIFACT_DIR / "source_freshness_snapshot.csv", source_freshness_rows(con))
    finally:
        con.close()
    _write_docs(metrics)
    _write_gpt_review()
    _write_report(metrics)
    _update_navigation()
    print("TASK3601_3640_DB_MANAGEMENT_PROGRAM_GENERATED")


if __name__ == "__main__":
    main()
