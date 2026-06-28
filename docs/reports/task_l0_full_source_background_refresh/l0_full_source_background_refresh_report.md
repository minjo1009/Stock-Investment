# L0 Full Source Background Refresh

## Decision Summary

- Verdict: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: not applicable. This is L0 source collection infrastructure only.
- Key metrics at snapshot: Alpaca IEX microstructure accelerated collector running under PID 15832; full news collector running under PID 22388; news full-backfill ledger has 1,381 processed events with Marketaux token present and local cap 95/day.
- What changed: corrected the Alpaca-only refresh gap by adding and starting a separate L0 news background collector for `official_public_releases`, `gdelt_news_events`, and `marketaux_news_free`.
- Next action: let both background collectors continue; monitor Marketaux daily cap behavior, GDELT archive progress, and official endpoint blockers.

## Quant Expert Report

### Data source and source readiness

- `official_public_releases`: enabled in local operator override and collected by `scripts/start_l0_news_background_collector.ps1`. Five official source captures succeeded at snapshot. BLS RSS endpoints returned HTTP 403 and are recorded as retryable source blockers, not approximated.
- `gdelt_news_events`: enabled as discovery-only. The first full-universe cursor attempt hit a retryable query/provider issue and GDELT cooldown is now respected. GDELT remains `READY_DISCOVERY_ONLY` when structurally valid, never authority.
- `marketaux_news_free`: enabled as metadata/discovery-only with token-backed collection under the local 95/day cap. No token was printed or written.
- `microstructure_quotes` / `microstructure_trades`: Alpaca IEX full-period/full-universe accelerated 15-minute background collector remains active and writes chunked raw files under `data/raw/alpaca_historical_microstructure_backfill`.

### Exact join keys

- News raw event identity: provider, source_id, collection timestamp, raw_sha256.
- News L1 evaluation keys: provider, published_at, source_url, title, symbols/entities.
- Microstructure chunk identity: provider, feed, source_type, symbol, session_date, chunk_start_ts, chunk_end_ts, chunk_id.

### Leakage audit

- News discovery sources do not enter trade-supporting evidence.
- GDELT and Marketaux remain discovery/metadata-only.
- Microstructure feature builder remains blocked.
- Broker mutation, paper promotion, live order, real capital, and replay permissions remain closed.

### Split/OOS metrics

- Not applicable. No strategy, backtest, or deployment claim is made.

### Failure decomposition

- Official BLS RSS: `FAILED_RETRYABLE` due HTTP 403.
- GDELT: `FAILED_RETRYABLE` from provider response/cooldown path; collector was patched to prefer company-name queries over too-short symbol-only queries.
- Marketaux: token is present; early historical batches can be empty and the worker stops Marketaux calls for the UTC day after the 95/day local cap is reached.
- Alpaca microstructure: active background collector had `failed_chunks=0` at snapshot.

### Cost/slippage stress where PnL changed

- Not applicable. No PnL logic changed.

### Remaining blockers

- Marketaux remains bounded by the 95/day local cap.
- GDELT full-universe traversal remains discovery-only and archive-bound, now running at 12 rpm.
- Final source coverage acceptance requires later coverage aggregation after background collectors run longer.

## No-Background Decision-Maker Report

You were right: Alpaca was only one source lane. The system is now collecting official public releases where reachable, tracking GDELT as discovery-only, and collecting Marketaux metadata under a 95/day cap after token setup.

This still does not make trading live-ready. It only makes source collection broader, observable, and auditable.

## Artifact Manifest

### Inputs

- `configs/db_source_acquisition_scheduler.json`
- `configs/local/db_source_acquisition_scheduler.override.json`
- `configs/source_registry/l0_official_public_releases.json`
- `configs/source_registry/l0_gdelt_queries.json`
- `configs/source_registry/l0_marketaux_queries.json`
- `data/raw/alpaca_active_us_equity_universe.csv`

### Outputs

- `tools/db/source_acquisition/news_background_collector.py`
- `scripts/run_l0_news_background_collector.py`
- `scripts/start_l0_news_background_collector.ps1`
- `data/raw/l0_news`
- `data/artifacts/l0_news_background_queue/collector_events.jsonl`
- `data/artifacts/l0_news_background_queue/collector_progress.json`
- `data/artifacts/l0_news_background_queue/background_process.json`
- `logs/l0_news_background_collector.log`
- `data/raw/alpaca_historical_microstructure_backfill`
- `data/artifacts/microstructure_backfill_queue_15m/collector_progress.json`

### Row counts

- News full-backfill ledger at acceleration snapshot: 1,381 processed events.
- News raw files continue under `data/raw/l0_news_full_backfill`.
- Microstructure accelerated progress at snapshot: 569 logical 15-minute chunks processed, 29 processed in the restarted run, 0 failed chunks.

### Validation commands

- `python -m unittest tests.test_l0_news_background_collector tests.test_l0_microstructure_background_collector tests.test_db_source_acquisition_runner tests.test_l0_source_acquisition_hardening`
- `python -m py_compile tools/db/source_acquisition/news_background_collector.py scripts/run_l0_news_background_collector.py tools/db/source_acquisition/microstructure_background_collector.py scripts/run_l0_microstructure_background_collector.py`
- `python -m tools.db.apply_management_schema --apply`
- `python tools/db/run_source_acquisition_once.py --execute`
- `python scripts/validate_l0_source_acquisition_hardening.py`

### Source hashes when applicable

- News raw hashes are recorded in `data/artifacts/l0_news_background_queue/collector_events.jsonl`.
- Microstructure chunk hashes are recorded in `data/artifacts/microstructure_backfill_queue_15m/collector_events.jsonl` and `data/artifacts/microstructure/microstructure_backfill_checkpoint.jsonl`.
