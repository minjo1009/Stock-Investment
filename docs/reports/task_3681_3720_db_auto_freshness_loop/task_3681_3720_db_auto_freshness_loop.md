# Task3681-3720 DB Auto Freshness Loop

## Decision Summary

- Verdict: `DB_AUTO_FRESHNESS_LOOP_EXPANDED_WITH_CACHED_EVIDENCE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - Registered jobs: 12
  - Freshness policies: 12
  - Latest runner result: 6 `SUCCESS`, 6 `SKIPPED`
  - Source receipts: 20
  - Reference hashes: 9
  - Lineage edges: 13
  - Scheduler distinct buckets: 5
  - Scheduler recurrence proven: true
  - Paper order intents: 0
  - Broker mutation attempts: 0
- What changed:
  - Added generic cached table snapshot evidence support to `tools.db.run_registered_loop_once`.
  - Added cached adapters for `broker_truth_reconciliation`, `market_ticks_intraday`, `runtime_strategy_decisions`, and `indicator_snapshots`.
  - Added registry/freshness policy jobs for `runtime_strategy_decisions` and `indicator_snapshots`.
  - Empty `authority_evidence_ledger` now writes explicit neutral skip evidence.
- Next action:
  - Implement actual acquisition loops for fresh market ticks/bars and external source families.

## Quant Expert Report

### Data source and source readiness

No live fetch was run.

This task only converted already-present cached DB tables into repeatable loop evidence:

- `market_bars_5m`
- `market_ticks`
- `reconciliation_runs`
- `runtime_strategy_decisions`
- `indicator_snapshots`
- `runtime_authority_evidence_ledger` when populated; currently empty and skipped

The evidence path records receipt/hash/lineage/freshness rows. It does not certify that the data is fresh. Current stale blockers remain:

- `authority_evidence_ledger`
- `broker_truth_reconciliation`
- `indicator_snapshots`
- `market_bars_5m`
- `market_ticks_intraday`
- `runtime_strategy_decisions`

### Exact join keys

Evidence path:

- `source_receipts.receipt_id`
- `reference_hashes.ref_id`
- `data_lineage_edges.source_receipt_id -> source_receipts.receipt_id`
- `data_lineage_edges.input_ref_id -> reference_hashes.ref_id`
- `source_freshness.evidence_ref -> source_receipts.receipt_id`
- `scheduler_run_ledger.cadence`

### Leakage audit

No labels, outcomes, PnL, replay output, selector tuning, sizing, lifecycle inference, symbol/date/price/time fallback, broker API call, live fetch, paper submit, or live submit was used.

Missing or empty sources remain neutral `SKIPPED` rows. Missing source is not negative evidence.

### Split/OOS metrics

Not applicable. No replay/backtest was run.

### Failure decomposition

Closed:

- `market_ticks_intraday` receipt/hash/lineage evidence exists.
- `broker_truth_reconciliation` receipt/hash/lineage evidence exists from cached `reconciliation_runs`.
- `runtime_strategy_decisions` is now registered and has receipt/hash/lineage evidence.
- `indicator_snapshots` is now registered and has receipt/hash/lineage evidence.
- Scheduler recurrence is now proven by at least 3 distinct buckets.

Still blocked:

- The above families remain `STALE`.
- `authority_evidence_ledger` has 0 rows.
- `daily_ohlcv`, `macro_rates`, and `sec_events` still need adapters/acquisition receipts.
- `catalog_report_artifacts` and `frontend_read_models` still need lineage adapters.
- Live/source acquisition loops are not installed yet.

### Cost/slippage stress where PnL changed

Not applicable.

### Remaining blockers

The next program should move from cached evidence to actual source acquisition:

1. market bars/ticks provider fetch loop with raw receipt and idempotent upsert.
2. broker truth fixture-to-paper-source promotion without broker mutation.
3. authority evidence ledger creation only after full evidence gates exist.
4. reporting/frontend lineage adapters.

## No-Background Decision-Maker Report

### What happened

The DB loop now manages more of the actual data brain. It can repeatedly scan cached market data, broker reconciliation records, indicators, and runtime decisions and leave verifiable evidence.

### Why it matters

Before this, several important DB tables existed but were not attached to the scheduler/receipt/lineage system. Now they are attached.

### Whether this changes capital/deployment readiness

No. The important sources are still stale, and authority evidence is empty.

### Plain-language next step

Build the real data acquisition loop that refreshes market bars/ticks and external source families, while preserving the same receipt/hash/lineage contract.

## Artifact Manifest

### Inputs

- `trading.db`
- `scheduler_job_registry`
- `source_freshness_policy`
- cached source tables listed above

### Outputs

- `tools/db/apply_management_schema.py`
- `tools/db/run_registered_loop_once.py`
- `tests/test_db_registered_loop_runner.py`
- `scripts/trader_brain_3681_3720_db_auto_freshness_loop_generate.py`
- `scripts/trader_brain_3681_3720_db_auto_freshness_loop_validate.py`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/db_auto_freshness_10_loop_plan.csv`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/registered_loop_run_result_after_contract_expansion.json`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/loop_contract_report_after_contract_expansion.json`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/db_health_metrics_after_contract_expansion.json`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/source_receipts_loop_families.csv`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/reference_hashes_loop_families.csv`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/data_lineage_edges_loop_families.csv`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/source_freshness_snapshot.csv`
- `data/artifacts/task_3681_3720_db_auto_freshness_loop/artifact_manifest.csv`

### Validation commands

```powershell
python -m unittest tests.test_db_registered_loop_runner
python -m tools.db.run_registered_loop_once
python -m tools.db.healthcheck --diagnostic-only --strict --require-management-schema
python scripts/trader_brain_3681_3720_db_auto_freshness_loop_validate.py
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
```

Test success does not modify strategy acceptance status.

Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
