# L0 News Three-Source Full Backfill

## Decision Summary

- Verdict: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: not applicable. This is L0 news source collection infrastructure only.
- Key metrics: universe rows 12,041; target period 2016-01-01 through 2026-06-27; official known enabled endpoints 7; official symbols with verified endpoint 1; official symbols missing verified endpoint 12,040; GDELT estimated 15-minute archive files 367,872; Marketaux estimated 2,409 symbol batches x 11 year windows; Marketaux token present true.
- What changed: added a full news backfill planner/worker for `official_public_releases`, `gdelt_news_events`, and `marketaux_news_free`, with source-specific smoke tests, API-limit-safe cursors, background launcher, raw hashes, event ledger, and blocker artifacts.
- Next action: let the GDELT and Marketaux workers continue under the accelerated caps; verify official endpoints before claiming full official-public-release coverage for non-AAPL universe symbols.

## Quant Expert Report

### Data source and source readiness

- `official_public_releases`: smoke succeeded with Apple Newsroom RSS. Full-universe official coverage is blocked for symbols without verified official endpoint registry rows. Missing endpoints are recorded in `data/artifacts/l0_news_full_backfill/official_endpoint_missing_universe.csv`, not approximated from non-official sources.
- `gdelt_news_events`: smoke succeeded by exporting `20160101000000.export.CSV.zip` from the GDELT v2 archive. Background collection is running from 2016-01-01 in 15-minute archive chunks at 12 requests/minute.
- `marketaux_news_free`: token-backed smoke reached the provider and recorded an empty historical response without logging secrets. The worker is implemented as symbol-batch/year-window pagination with daily cap 95, below the documented free-plan 100 requests/day.

### Exact join keys

- Official raw key: provider, source_id, collection timestamp, raw_sha256.
- GDELT raw key: provider, archive timestamp `YYYYMMDDHHMMSS`, source kind `export.CSV.zip`, raw_sha256.
- Marketaux raw key: provider, symbol batch, published_after, published_before, page, raw_sha256.
- L1 quality key: provider, published_at, source_url, title, symbols/entities.

### Leakage audit

- GDELT and Marketaux remain discovery/metadata-only.
- Discovery rows have `trade_authority_flag=0`.
- No labels/outcomes are read by assignment logic.
- Missing official endpoints are blockers, not negative evidence.
- Broker mutation, paper/live order, real capital, replay, and feature-builder gates remain closed.

### Split/OOS metrics

- Not applicable. This task makes no strategy, backtest, OOS, PnL, or deployment claim.

### Failure decomposition

- Official: BLS RSS endpoints returned HTTP 403 in the first full run and are recorded as `FAILED_RETRYABLE`.
- GDELT: archive smoke and background exports succeeded; ticker/entity mapping remains downstream discovery metadata.
- Marketaux: token is present; early 2016 symbol batches may still produce `EMPTY_PROVIDER_RESPONSE`. The local 95/day cap prevents overrunning the free-plan allowance.

### Cost/slippage stress where PnL changed

- Not applicable. No PnL code changed.

### Remaining blockers

- Marketaux remains bounded by the 95/day local cap and will continue across UTC days.
- Official-public-release full-universe coverage requires endpoint verification for 12,040 symbols.
- GDELT archive collection is large and will require long-running background execution and later storage/coverage audits.

## No-Background Decision-Maker Report

The three news sources now have the same operational posture as the Alpaca lane: each has a smoke path, a resumable full-collection plan, and a background worker. The difference is that the sources have different real-world limits. GDELT proceeds through archive chunks, Marketaux proceeds under a 95/day local cap, and official releases cannot be claimed for the whole universe until each symbol has a verified official endpoint.

This does not make the trading system live-ready or strategy-ready. It only makes the source acquisition work observable and honest.

## Artifact Manifest

### Inputs

- `configs/source_registry/l0_official_public_releases.json`
- `configs/source_registry/l0_gdelt_queries.json`
- `configs/source_registry/l0_marketaux_queries.json`
- `data/raw/alpaca_active_us_equity_universe.csv`
- Official provider docs checked for GDELT archive/search scope and Marketaux limits.

### Outputs

- `tools/db/source_acquisition/news_full_backfill.py`
- `scripts/run_l0_news_full_backfill.py`
- `scripts/start_l0_news_full_backfill.ps1`
- `tests/test_l0_news_full_backfill.py`
- `data/artifacts/l0_news_full_backfill/full_backfill_plan.json`
- `data/artifacts/l0_news_full_backfill/official_endpoint_missing_universe.csv`
- `data/artifacts/l0_news_full_backfill/collector_events.jsonl`
- `data/artifacts/l0_news_full_backfill/collector_progress.json`
- `data/artifacts/l0_news_full_backfill/background_process.json`
- `data/raw/l0_news_full_backfill`
- `data/artifacts/l0_news_full_backfill_smoke`
- `data/raw/l0_news_full_backfill_smoke`

### Row counts

- Smoke official events: 1 exported.
- Smoke GDELT events: 1 exported.
- Smoke Marketaux events: 1 credential-blocked.
- Full worker snapshot after acceleration: 1,381 processed events, 1,220 exported, 34 empty, 126 failed/rate-limited historical events.
- GDELT archive zip files at acceleration snapshot: 1,220 exported events cumulative across the full-backfill ledger.
- Official endpoint missing blocker rows: 12,040 plus header.

### File sizes

- File sizes and hashes are recorded in this report directory's `artifact_manifest.csv`.

### Validation commands

- `python -m unittest tests.test_l0_news_full_backfill tests.test_l0_news_background_collector`
- `python -m py_compile tools/db/source_acquisition/news_full_backfill.py scripts/run_l0_news_full_backfill.py`
- `python scripts/run_l0_news_full_backfill.py --mode smoke --sources official --max-requests 1 ...`
- `python scripts/run_l0_news_full_backfill.py --mode smoke --sources gdelt --max-requests 1 ...`
- `python scripts/run_l0_news_full_backfill.py --mode smoke --sources marketaux --max-requests 1 ...`
- `python scripts/validate_l0_source_acquisition_hardening.py`
- `python scripts/task_registry_validate.py`

### Source hashes when applicable

- Smoke and full raw file hashes are recorded in their JSONL event ledgers.
