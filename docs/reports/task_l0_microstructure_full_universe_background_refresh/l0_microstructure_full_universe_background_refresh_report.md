# L0 Microstructure Full-Universe Background Refresh

## Decision Summary

- Verdict: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: not applicable. This task collects raw L0 quote/trade source data only.
- Key metrics: universe source has 12,041 active/tradable rows and 12,040 unique collection symbols after dedupe; target period is 2016-01-01 through the latest complete US market session, initialized as 2026-06-26; active accelerated chunk size is 15 market minutes; source types are quotes and trades; default feed is Alpaca IEX.
- What changed: added a resumable background collector that writes non-overwriting chunk raw files, records append-only chunk events, keeps a cursor state/progress heartbeat, honors a stop file, skips legacy source_type/symbol files already present under existing raw roots, and skips chunked backfill data only when the exact chunk raw path already exists.
- Next action: let the accelerated 15-minute collector continue and monitor `data/artifacts/microstructure_backfill_queue_15m/collector_progress.json` plus `logs/l0_microstructure_background_collector_15m.log`.

## Quant Expert Report

### Data source and source readiness

- Raw provider: Alpaca historical stock quotes/trades API.
- Feed: IEX by default because the real quote/trade smoke succeeded on IEX and the free/test feed is available without SIP subscription assumptions.
- Universe: `data/raw/alpaca_active_us_equity_universe.csv`, filtered to active/tradable symbols. Current source row count: 12,041. Current unique collection symbol count: 12,040.
- Target raw output: `data/raw/alpaca_historical_microstructure_backfill/feed=<feed>/source_type=<quotes|trades>/symbol=<SYMBOL>/session_date=<YYYY-MM-DD>/chunk_start=<UTC>_chunk_end=<UTC>.csv`.
- Existing held raw: legacy symbol-level files under `data/raw/alpaca_historical_microstructure` and `data/raw/alpaca_historical_microstructure_smoke` are scanned before collection. Existing legacy source_type/symbol pairs are skipped unless the collector is explicitly run with `--include-existing-symbols`. Chunked files under `data/raw/alpaca_historical_microstructure_backfill` are not treated as whole-symbol coverage; they are skipped only when the exact chunk path already exists.

### Exact join keys

- Raw chunk identity: provider, feed, source_type, symbol, chunk_start_ts, chunk_end_ts.
- Checkpoint/event key: `chunk_id = sha256(provider|feed|source_type|symbol|chunk_start_ts|chunk_end_ts)[:24]`.
- Raw quote timestamp: `quote_ts`.
- Raw trade timestamp: `trade_ts` plus `trade_id` when present.

### Leakage audit

- Labels/outcomes are not read by the collector.
- Assignment logic uses only source scope, symbol, session date, chunk time, existing raw presence, and chunk status.
- Feature builders remain blocked: `feature_builder_allowed_flag=0`.
- Broker/order mutation remains blocked: `broker_mutation_permitted_flag=0`.

### Split/OOS metrics

- Not applicable. This is source acquisition infrastructure only and does not make strategy claims.

### Failure decomposition

- API rate limits are recorded as `RATE_LIMITED` events and the worker sleeps before continuing.
- Missing credentials or subscription blocks are recorded as `CREDENTIAL_BLOCKED` and stop the run.
- Empty provider responses are recorded as `EMPTY_PROVIDER_RESPONSE`, not converted into negative examples.
- Existing raw is recorded/skipped as `SKIPPED_EXISTS`; it is not recollected.

### Cost/slippage stress where PnL changed

- Not applicable. No PnL, simulation, capital, broker, or order lifecycle logic changed.

### Remaining blockers

- Full-period/full-universe completion is still long-running, but the active accelerated target is trading_days x 12,041 symbols x 26 fifteen-minute chunks x 2 source types, down from the prior 390 one-minute chunk plan.
- This report is complete for background execution readiness, not for final coverage acceptance.
- Final acceptance still requires coverage artifact refresh after the collector has accumulated sufficient raw chunks.

## No-Background Decision-Maker Report

The small smoke tests already proved that real quote and trade chunks can be collected. The next request was much larger: refresh the full period for the full universe, while avoiding data already held. That is too large for a one-shot foreground run, so the work now runs as a resumable background collection job.

This does not make the trading system live-ready. It only gathers raw quote/trade evidence so later research can measure microstructure coverage without fabricated labels or proxy data.

The plain-language next step is to let the background process run, check the progress JSON/log, and only promote later strategy work after raw coverage and integrity reports are refreshed.

## Artifact Manifest

### Inputs

- `data/raw/alpaca_active_us_equity_universe.csv`: full active/tradable universe, 12,041 rows and 12,040 unique collection symbols.
- `data/raw/alpaca_historical_microstructure`: held raw source root, 77 CSV files at task start.
- `data/raw/alpaca_historical_microstructure_smoke`: held smoke source root, 2 CSV files at task start.
- `data/artifacts/microstructure/microstructure_backfill_checkpoint.jsonl`: existing real smoke checkpoint plus later exported chunk checkpoints.

### Outputs

- `tools/db/source_acquisition/microstructure_background_collector.py`: reusable collector core.
- `scripts/run_l0_microstructure_background_collector.py`: resumable CLI worker.
- `scripts/start_l0_microstructure_background_collector.ps1`: hidden Windows background launcher.
- `data/raw/alpaca_historical_microstructure_backfill`: chunked quote/trade raw output root.
- `data/artifacts/microstructure_backfill_queue/collector_state.json`: preserved 1-minute cursor state.
- `data/artifacts/microstructure_backfill_queue_15m/collector_state.json`: active accelerated 15-minute cursor state.
- `data/artifacts/microstructure_backfill_queue_15m/collector_events.jsonl`: append-only accelerated chunk event ledger.
- `data/artifacts/microstructure_backfill_queue_15m/collector_progress.json`: latest accelerated progress heartbeat.
- `data/artifacts/microstructure_backfill_queue_15m/background_process.json`: accelerated background process metadata.
- `logs/l0_microstructure_background_collector_15m.log`: accelerated worker start/exit heartbeat log.

### Row counts

- Initial universe rows: 12,041.
- Initial unique collection symbols: 12,040.
- Initial held legacy raw CSV files: 77.
- Initial held smoke raw CSV files: 2.
- Accelerated 15-minute collector row counts are expected to grow after execution starts and are tracked in `microstructure_backfill_queue_15m/collector_progress.json`.

### File sizes

- File sizes and hashes are recorded in this directory's `artifact_manifest.csv`.

### Validation commands

- `python -m unittest tests.test_l0_microstructure_background_collector`
- `python -m py_compile tools/db/source_acquisition/microstructure_background_collector.py scripts/run_l0_microstructure_background_collector.py`
- `python scripts/validate_l0_source_acquisition_hardening.py`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`

### Source hashes when applicable

- Raw chunk hashes are recorded per exported chunk in `data/artifacts/microstructure_backfill_queue_15m/collector_events.jsonl` and for exported chunks in `data/artifacts/microstructure/microstructure_backfill_checkpoint.jsonl`.
