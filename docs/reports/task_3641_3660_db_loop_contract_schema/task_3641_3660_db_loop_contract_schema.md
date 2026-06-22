# Task3641-3660 DB Loop Contract Schema

## Decision Summary

- Verdict: `DB_LOOP_CONTRACT_SCHEMA_INSTALLED_WITH_BLOCKERS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - Management tables present: True
  - Jobs registered: 10
  - Freshness policies registered: 10
  - Reference hashes: 0
  - Lineage edges: 0
  - Foreign key violations: 0
  - Scheduler recurrence proven: False
  - Paper order intents: 0
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

- `authority_evidence_ledger`
- `broker_truth_reconciliation`
- `indicator_snapshots`
- `market_bars_5m`
- `market_ticks_intraday`
- `runtime_strategy_decisions`

Receipt gaps under the new loop contract:

- `daily_ohlcv`
- `macro_rates`
- `sec_events`

Lineage gaps under the new loop contract:

- `authority_evidence_ledger`
- `broker_truth_reconciliation`
- `catalog_report_artifacts`
- `daily_ohlcv`
- `frontend_read_models`
- `macro_rates`
- `market_bars_5m`
- `market_ticks_intraday`
- `sec_events`

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

- `scheduler_job_registry`: 10
- `source_freshness_policy`: 10
- `reference_hashes`: 0
- `data_lineage_edges`: 0

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
