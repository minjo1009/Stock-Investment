# Task3571-3580 DB Data Ops Audit

## Decision Summary

- Verdict: `DB_DATA_OPS_AUDIT_COMPLETE_WITH_P0_MANAGEMENT_GAPS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key findings:
  - SQLite integrity checks passed for all inspected DB files.
  - Active DB by config is `trading.db`.
  - Active DB market/runtime data is stale: DB market ticks/bars stop at `2026-06-03`, while current operating date is `2026-06-20`.
  - `control_state.run_mode` in `trading.db` is `LIVE_ENABLED` with `kill_switch_active=0`, which conflicts with the standing `FORBIDDEN` real-capital boundary.
  - Four root `trading-DESKTOP*.db` copies exist with schema and row-count drift.
  - `runtime_authority_evidence_ledger` and `paper_order_intents` have 0 rows, so evidence-backed PAPER_ELIGIBLE has code/tests but no current active-DB evidence.
- What changed:
  - created DB inventory artifact
  - created data family/cadence artifact
  - created DB management findings artifact
  - added a task validator and registry closeout
- What did not change:
  - no DB rows were modified
  - no source acquisition was run
  - no replay/backtest was run
  - no paper order or broker call was made

## Quant Expert Report

### Data source and source readiness

Inspected data stores:

- active runtime DB: `trading.db`
- root backup/conflict DBs: `trading-DESKTOP-*.db`
- artifact DBs: `data/task384*.db`, `data/task385*.db`, `data/task388*.db`, `docs/reports/task_371_source_time_capture/task_371_harness.db`
- raw file data lake under `data/raw/`
- frontend read-model catalogs under `frontend_data/catalog` and `apps/trader-brain-web/public/catalog`

Current data families:

| Family | Storage | Expected cadence | Current state |
| --- | --- | --- | --- |
| Runtime state/orders/fills/positions | `trading.db` | event-driven + diagnostic heartbeat | stale after 2026-06-03 for trading rows |
| Diagnostic scheduler state | `trading.db` | 5 min safety, 10 min brain, 30 min heavy-source disabled | one test bucket only |
| Market ticks/5m bars | `trading.db`, raw CSV/parquet | 5 min freshness guard / task refresh | DB max 2026-06-03 |
| Alpaca microstructure | raw CSV/parquet | task-triggered historical backfill | large raw lake, not active DB current |
| YFinance daily/intraday | raw CSV | daily/task refresh | available, not centralized into active source freshness |
| SEC filings/financing/dilution | raw htm/json/xml + artifacts | task-triggered; 30 min heavy-source candidate disabled | large raw source exists, strict gate still not accepted |
| Fundamentals/companyfacts | raw JSON | daily/weekly or filing event | task-scoped, no central DB freshness table |
| Macro/rates/liquidity | raw CSV/JSON + artifacts | daily/task; heavy-source candidate | available task-scoped |
| News/research/intelligence | raw HTML/PDF/TXT/JSON | event-driven or heavy-source candidate | partial, no current live authority |
| Broker truth reconciliation | `trading.db` + KIS paper status input | before retry / daily close | implemented but active DB rows are old |
| Frontend read model catalog | JSON/CSV | build loop 60 sec; app poll 30 sec | read-only surface, not source truth |
| Backtest/harness artifacts | SQLite/CSV/parquet artifacts | task-scoped only | structurally OK, not active runtime |

### Exact join keys

No joins were introduced.

Existing operational keys observed:

- scheduler cadence key: `<cadence>:<bucket_ts>`
- runtime heartbeat idempotency key: `l0l6-diagnostic:<cadence>:<bucket>:<state_hash_prefix>`
- order key: `orders.order_id`
- fill dedupe key: `fills.dedupe_key`
- broker reconciliation key: `orders.order_id == broker_order_id`
- paper intent key: `paper_order_intents.idempotency_key`
- authority evidence key: `runtime_authority_evidence_ledger.authority_hash`
- market data key: `symbol + bar_start_ts` for `market_bars_5m`

### Leakage audit

This was an operations audit only.

No missing source was converted to a negative label. No symbol/date/price/time fallback matching was used. No future return, outcome, PnL, or backtest result entered an assignment path.

### Split/OOS metrics

Not applicable. No replay or backtest was run.

### DB management assessment

What is healthy:

- All inspected SQLite DB files returned `PRAGMA integrity_check = ok`.
- `trading.db` is in WAL mode.
- Runtime tables have primary keys and several useful indexes.
- Scheduler leases, heartbeat idempotency, paper intent idempotency, and authority hash ledger structures exist.

What is not healthy:

- `control_state` conflicts with project governance: persisted run mode says `LIVE_ENABLED`, while standing status says real capital is `FORBIDDEN`.
- Active DB authority is ambiguous because multiple root DB copies have different schemas and row counts.
- There is no explicit DB authority manifest, migration table, backup/restore policy, or retention class.
- `PRAGMA user_version` is 0 across DBs, so schema versioning is not explicit.
- Source freshness is task-scoped rather than centrally persisted.
- Active DB market data is stale for current operations.
- Scheduler recurrence is not evidenced in DB beyond one diagnostic bucket.
- Broker truth reconciliation evidence is old.

### Missing pieces

Required next controls:

1. `db_authority_manifest.csv` or table:
   - active DB path
   - role
   - owner
   - backup paths
   - retention class
   - restore rule
   - last integrity check
2. `schema_migrations` table:
   - schema version
   - migration id
   - applied_at
   - checksum
   - owning module
3. `source_freshness` / `source_receipts` tables:
   - provider
   - source family
   - symbol/cik/series id
   - source_ts
   - capture_ts
   - available_to_brain_ts
   - raw path/hash
   - freshness SLA
   - strict/proxy admission state
4. `scheduler_run_ledger`:
   - expected bucket
   - actual start/finish
   - owner id
   - lease token
   - lag seconds
   - skipped reason
   - validation refs
5. `db_retention_policy`:
   - active runtime DB
   - host backup DB
   - artifact DB
   - smoke DB
   - disposable cache

### Cost/slippage stress where PnL changed

Not applicable.

### Remaining blockers

- Do not claim runtime freshness until `trading.db` source freshness is current and centrally visible.
- Do not create PAPER_ELIGIBLE local intents until authority evidence ledger has complete source freshness, snapshot, lineage, broker truth, kill-switch, permission, and validity-window evidence.
- Do not delete root DB copies until active DB authority and backup retention are explicit.
- Do not treat frontend catalog refresh as source refresh.

## No-Background Decision-Maker Report

### What happened

The DB layer is not corrupt. The problem is management discipline.

There are multiple DB copies, stale runtime data, no central freshness table, no explicit migration version, and one serious persisted-state mismatch: active `trading.db` says `LIVE_ENABLED` while project governance says real capital is forbidden.

### What data we have

The project has:

- paper/runtime order state
- market ticks and 5-minute bars
- indicator snapshots
- broker/order reconciliation rows
- SEC filings and company facts
- macro/rates/liquidity data
- yfinance/daily/intraday data
- Alpaca historical microstructure
- news/research/source text
- frontend read-only catalogs
- backtest/harness artifact DBs

### What is missing

The missing layer is a central DB/data authority system:

- one active DB declaration
- source freshness ledger
- schema migration ledger
- DB retention policy
- scheduler run ledger
- backup/restore rule

### Whether this changes capital/deployment readiness

No.

This audit reinforces that deployment readiness is still blocked.

## Artifact Manifest

### Inputs

- `trading.db`
- `trading-DESKTOP-*.db`
- `data/task384*.db`
- `data/task385*.db`
- `data/task388*.db`
- `docs/reports/task_371_source_time_capture/task_371_harness.db`
- `data/raw/`
- `configs/runtime_diagnostic_scheduler.json`
- `docs/llm_wiki/source_truth_map.md`
- `data/artifacts/task_3401_3410_l0_l6_realtime_ops_audit/realtime_cadence_recommendation.csv`

### Outputs

- `data/artifacts/task_3571_3580_db_data_ops_audit/db_inventory.csv`
- `data/artifacts/task_3571_3580_db_data_ops_audit/data_family_cadence.csv`
- `data/artifacts/task_3571_3580_db_data_ops_audit/db_management_findings.csv`
- `docs/reports/task_3571_3580_db_data_ops_audit/task_3571_3580_db_data_ops_audit.md`
- `docs/reports/task_3571_3580_db_data_ops_audit/task_3580_decision.csv`
- `scripts/trader_brain_3571_3580_db_data_ops_audit_validate.py`

### Validation commands

```powershell
python scripts/trader_brain_3571_3580_db_data_ops_audit_validate.py
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
```

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
