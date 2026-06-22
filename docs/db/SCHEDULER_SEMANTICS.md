# Scheduler Semantics

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

## DB Loop Contract Schema

Task3641-3660 installed `scheduler_job_registry` and `source_freshness_policy`.

- `enabled=1` means diagnostic monitoring is registered; it does not permit execution.
- `execution_permitted`, `broker_mutation_permitted`, `real_capital_permitted`, and `paper_promotion_permitted` are DB-level CHECK-constrained to `0`.
- `missing_semantics` and `stale_semantics` are constrained to `UNKNOWN_BLOCKER`.
- `data_lineage_edges` requires `source_receipt_id` and `input_ref_id`.

## Registered Loop Runner

Task3651-3670 added `tools.db.run_registered_loop_once`.

- Default mode is dry-run.
- `--apply` writes diagnostic loop evidence only.
- `diagnostic_runtime_heartbeats_refresh` writes internal heartbeat evidence.
- Adapter-free jobs write `SKIPPED` with `NO_ADAPTER_REGISTERED_DIAGNOSTIC_ONLY`.
- `SKIPPED` is evidence that the loop ran; it is not source freshness recovery.

## Cached Market Bars Adapter

Task3671-3680 added `market_bars_5m_refresh` behind the registered loop runner as cached snapshot evidence only.

- No live fetch is allowed in this adapter.
- It reads only `trading.db::market_bars_5m`.
- It writes raw metadata receipt, deterministic table hash, lineage edge, source freshness row, and scheduler ledger row.
- Missing or empty cached source writes `SKIPPED` with `NO_CACHED_MARKET_BARS_5M_SOURCE`.
- A successful cached snapshot does not open gates. `strict_gate_allowed=0` and `proxy_allowed=0` remain required.
- If cached bars are stale, `source_freshness.freshness_status` remains `STALE`.

## Cached Table Evidence Adapters

Task3681-3720 generalized cached DB table evidence behind the same runner.

- Covered cached families:
  - `broker_truth_reconciliation` from `reconciliation_runs`
  - `indicator_snapshots` from `indicator_snapshots`
  - `market_ticks_intraday` from `market_ticks`
  - `runtime_strategy_decisions` from `runtime_strategy_decisions`
- Empty `authority_evidence_ledger` writes neutral `SKIPPED` evidence with `NO_CACHED_AUTHORITY_EVIDENCE_LEDGER_SOURCE`.
- These adapters do not call broker APIs, market-data APIs, selector, sizing, replay, paper submit, or live submit.
- Cached evidence can close receipt/hash/lineage gaps, but it cannot recover freshness when source timestamps are stale.

## Source Acquisition Runtime Loop

Task3721-3760 added `tools.db.run_source_acquisition_once`.

- Default mode is dry-run.
- `--apply` is required for DB mutation.
- Provider network calls require `--allow-network`.
- Current provider/cache families:
  - `market_bars_5m` from yfinance 5m provider into `market_bars_5m`
  - `market_ticks_intraday` from yfinance latest 5m proxy into `market_ticks`
  - `daily_ohlcv` from yfinance daily provider into `daily_ohlcv`
  - `macro_rates` from FRED CSV into `macro_rates`
  - `sec_events` from SEC live provider when `SEC_USER_AGENT` is configured, or from governed cached fixture packets
- Source tables use idempotent keys:
  - `daily_ohlcv`: `(provider, symbol, session_date)`
  - `macro_rates`: `(provider, series_id, observation_date, vintage_ts)`
  - `sec_events`: `(provider, accession_no, form_type, event_type)`
- All source acquisition writes raw payload metadata, `source_receipts`, `reference_hashes`, `data_lineage_edges`, `source_freshness`, and `scheduler_run_ledger`.
- `strict_gate_allowed=0` and `proxy_allowed=0` remain required until a separate certification task opens a named gate.
- Task3721-3760 also extends the registered loop so all 12 registered jobs have adapter evidence, including blocked `authority_evidence_ledger` generation and read-only frontend/catalog lineage.

## DB Source Acquisition Scheduler And Fresh Loop Validator

Task3761-3800 adds the operator-owned source acquisition scheduler surface and the first diagnostic fresh-loop derivation chain.

- `configs/db_source_acquisition_scheduler.json` defines source acquisition jobs.
- `scripts/run_db_source_acquisition_scheduler.ps1` repeatedly calls `tools.db.run_source_acquisition_once` and then `tools.db.run_registered_loop_once`.
- `scripts/install_db_source_acquisition_scheduler_task.ps1` installs `TraderBrainDbSourceAcquisitionScheduler` without starting it unless `-StartNow` is explicitly passed.
- Current install result is `StartupFolderFallback` with `READY_AT_NEXT_LOGON`.
- The registered DB loop now derives:
  - `market_bars_5m -> indicator_snapshots`
  - `indicator_snapshots -> runtime_strategy_decisions`
  - `broker_truth_reconciliation` as a current `BLOCKED` diagnostic row when no broker truth source is configured.
- Derived indicator rows force `entry_allowed=0` and `selected_for_portfolio=0`.
- Derived runtime rows force `decision_status=BLOCKED`, `side=NONE`, and `quantity=0`.
- Broker truth diagnostic rows force `block_new_orders=1`, do not call broker APIs, and do not claim broker truth completion.
- `SEC_USER_AGENT` is required for SEC live validation. Missing user-agent is recorded as `SEC_USER_AGENT_MISSING`, not as a negative source.
- `scripts/trader_brain_3761_3800_db_source_scheduler_config_freshness_validate.py` checks source evidence, lineage, and gate-open conditions while requiring active gates to remain closed.

