# Task3761-3800 DB Source Scheduler Config Freshness Validator

## Decision Summary

- Verdict: `DB_SOURCE_SCHEDULER_AND_FRESH_LOOP_VALIDATOR_INSTALLED_WITH_BLOCKERS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed:
  - Added an operator-owned DB source acquisition scheduler config and Windows install/run scripts.
  - Ran one governed source scheduler loop.
  - Connected `market_bars_5m -> indicator_snapshots -> runtime_strategy_decisions` as diagnostic-only derived DB loops.
  - Connected broker truth reconciliation to a current `BLOCKED` diagnostic source row without broker API calls or mutation.
  - Added SEC live adapter validation path; current environment records `SEC_USER_AGENT_MISSING`.
  - Added a freshness gate validator that proves evidence/lineage conditions while keeping active gates closed.
- Key metrics:
  - Diagnostic indicator rows: 75, entry permissions 0, selected rows 0.
  - Diagnostic runtime decision rows: 75, quantity 0, entry permissions 0.
  - Diagnostic broker truth blocker rows: 2, latest status `BLOCKED`, severity `CRITICAL`, `block_new_orders=1`.
  - Active gate-open candidates: 0.
  - Scheduler install result: `StartupFolderFallback`, `READY_AT_NEXT_LOGON`.
- Next action:
  - Provide an operator-owned `SEC_USER_AGENT` before live SEC source validation can pass.
  - Add lease/input-fingerprint idempotency and failure-ledger rows for source acquisition scheduler loops.
  - Replace diagnostic broker blocker with real operator-provided broker truth fixture/source when available.

## Quant Expert Report

### Data Source And Source Readiness

- Source acquisition scheduler:
  - `configs/db_source_acquisition_scheduler.json` registers 5-minute intraday market source acquisition, 60-minute heavy source acquisition, and 5-minute registered DB loop evidence.
  - `scripts/run_db_source_acquisition_scheduler.ps1` calls only `tools.db.run_source_acquisition_once` and `tools.db.run_registered_loop_once`.
  - Network is explicitly job-scoped; global default is `default_allow_network=false`.
- SEC live:
  - The path is implemented through `tools.db.run_source_acquisition_once --family sec_events --allow-network`.
  - Current run records `SEC_USER_AGENT_MISSING`; no fake user-agent was created.
- Indicator snapshots:
  - Derived from existing `market_bars_5m`.
  - `entry_allowed=0`, `selected_for_portfolio=0`, action `OBSERVE`, side `NONE`.
  - Parent market bars are still stale, so indicator freshness remains `STALE`.
- Runtime strategy decisions:
  - Derived from latest diagnostic indicator snapshots.
  - Decision rows are `BLOCKED`, side `NONE`, quantity `0`, no label use, no dummy fallback.
  - Runtime loop freshness is current because the diagnostic loop ran, but it does not permit orders.
- Broker truth reconciliation:
  - Current source connection writes a `BLOCKED` reconciliation row with no broker API call and no broker mutation.
  - This is current blocker evidence, not broker truth completion.

### Exact Join Keys

- `market_bars_5m`: `bar_id = symbol:bar_start_ts`.
- `indicator_snapshots`: `snapshot_id = diag-indicator:<symbol>:<bar_end_ts>`.
- `runtime_strategy_decisions`: `decision_id = diag-runtime:<snapshot_id>`.
- `reconciliation_runs`: `reconciliation_id = diag-broker-truth:<bucket>`.
- `source_freshness.evidence_ref` joins to `source_receipts.receipt_id`.
- `data_lineage_edges.source_receipt_id` points to the same receipt used by freshness evidence.

### Leakage Audit

- Missing source remains neutral blocker.
- No replay, selector, sizing, broker submit, paper order, live order, or account mutation was performed.
- Writers record evidence only. The validator checks whether gate conditions could be satisfied; active `strict_gate_allowed` and `proxy_allowed` remain 0.
- GPT/Chrome and subagents were review-only and did not become source of truth.
- SEC live path did not proceed without operator-owned `SEC_USER_AGENT`.

### Split/OOS Metrics

Not applicable. This task is DB operations infrastructure only.

### Failure Decomposition

- SEC live remains blocked by missing `SEC_USER_AGENT`.
- Market bars/ticks remain stale by source timestamp; weekend/closed-market provider acquisition did not create current intraday market source timestamps.
- Indicator snapshots inherit market bar staleness.
- Broker truth is current as a blocker row only; real broker truth source is not connected.
- Source scheduler is installed through Startup folder fallback, not Windows ScheduledTask service registration.
- Lease/input-fingerprint idempotency and failure ledger behavior remain P1/P0 hardening work.

### Remaining Blockers

- No live SEC success until `SEC_USER_AGENT` is configured.
- No real broker truth fixture/source attached yet.
- No source scheduler lease and `DUPLICATE_INPUT_HASH` skip path yet.
- No failure ledger row on every exception path yet.
- Source gates remain closed.
- Paper/live trading remains forbidden.

## No-Background Decision-Maker Report

- What happened: the DB now has a recurring source-acquisition scheduler surface and a validator-backed fresh-loop chain from market bars to indicators to runtime decisions.
- Why it matters: DB rows can be refreshed repeatedly and traced with receipts, hashes, lineage, freshness, and scheduler ledger evidence.
- Whether this changes capital/deployment readiness: no. This is diagnostic DB infrastructure only.
- Plain-language next step: configure SEC user-agent and attach real broker truth evidence, then harden scheduler leases/idempotency.

## Artifact Manifest

- Inputs:
  - `tools/db/run_source_acquisition_once.py`
  - `tools/db/run_registered_loop_once.py`
  - `configs/db_source_acquisition_scheduler.json`
  - `scripts/run_db_source_acquisition_scheduler.ps1`
  - `scripts/install_db_source_acquisition_scheduler_task.ps1`
  - `trading.db`
- Outputs:
  - `data/artifacts/task_3761_3800_db_source_scheduler_config_freshness_validator/artifact_manifest.csv`
  - `data/artifacts/task_3761_3800_db_source_scheduler_config_freshness_validator/source_scheduler_config_audit.json`
  - `data/artifacts/task_3761_3800_db_source_scheduler_config_freshness_validator/source_freshness_after_task.csv`
  - `data/artifacts/task_3761_3800_db_source_scheduler_config_freshness_validator/source_freshness_gate_condition_audit.csv`
  - `data/artifacts/task_3761_3800_db_source_scheduler_config_freshness_validator/scheduler_run_ledger_task_rows.csv`
  - `data/artifacts/task_3761_3800_db_source_scheduler_config_freshness_validator/sec_live_adapter_attempt.json`
  - `data/artifacts/task_3761_3800_db_source_scheduler_config_freshness_validator/operator_scheduler_install_result.txt`
  - `docs/reports/task_3761_3800_db_source_scheduler_config_freshness_validator/task_3800_decision.csv`
- Validation commands:
  - `python -m py_compile tools/db/run_registered_loop_once.py tools/db/run_source_acquisition_once.py scripts/trader_brain_3761_3800_db_source_scheduler_config_freshness_validate.py`
  - `python -m unittest tests.test_db_registered_loop_runner tests.test_db_source_acquisition_runner tests.test_db_source_acquisition_scheduler_scripts`
  - `python scripts/trader_brain_3761_3800_db_source_scheduler_config_freshness_validate.py`
  - `python scripts/task_registry_validate.py`
  - `python scripts/operating_closeout_validate.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
