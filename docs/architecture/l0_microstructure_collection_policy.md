# L0 Microstructure Collection Policy

## Decision

Microstructure L0 collection is raw data infrastructure only. It does not create L2 features, orderflow alpha, replay permission, paper trading permission, live trading permission, or broker mutation permission.

## Terminology

`market_bars_5m` means OHLCV bar data. It is not orderflow.

`market_bar_proxy_intraday` means a yfinance-style latest 5m bar proxy. It is not exchange tick truth.

`microstructure_quotes` means quote or NBBO-style data with bid, ask, bid size, ask size, spread, and imbalance fields.

`microstructure_trades` means trade prints with price, size, exchange, conditions, and trade id.

`microstructure_orderbook_depth` means L2/depth data. It is out of scope until a real depth provider exists.

`broker_truth` means broker orders, fills, rejects, and positions. It is separate from market microstructure.

## Scheduler Integration

The default scheduler includes `microstructure_backfill_batch`, disabled with `allow_network=false`.

Operator override may enable diagnostic collection in smoke or bounded batch mode. Historical full backfill is long-running and requires chunk-level checkpointing.

The active staged roadmap is `docs/architecture/l0_source_acquisition_project_management_plan.md`.
Microstructure work enters through Stage 1 smoke, Stage 2 provider budget
tuning, Stage 4 chunk/checkpoint optimization, Stage 5 background backfill, and
Stage 6 coverage audit. It must not skip directly from smoke to feature use.

## Backfill Modes

- `smoke`: one symbol, one date, one quote chunk, one trade chunk.
- `bounded_batch`: limited symbols, dates, and chunks.
- `historical_backfill`: long-running operator mode, disabled by default.
- `incremental_catchup`: future phase.
- `near_real_time_stream`: out of scope for this task.

Historical collection may use a 2016 start date only after Stage 4 proves
chunking, resume, retry, quarantine, raw-hash, and coverage behavior. A backfill
run is code-based Python collection, not Codex/GPT runtime collection.

## Checkpoint And Coverage

Chunk state is recorded in `data/artifacts/microstructure/microstructure_backfill_checkpoint.jsonl` with exported, retryable failure, permanent failure, rate limit, credential blocked, empty provider response, and quarantine statuses.

Coverage artifacts are written under `data/artifacts/microstructure/`:

- `microstructure_raw_catalog.csv`
- `microstructure_coverage_by_symbol.csv`
- `microstructure_coverage_by_date.csv`
- `microstructure_coverage_by_symbol_date.csv`
- `microstructure_integrity_audit.csv`
- `microstructure_missing_reason.csv`
- `microstructure_collection_heartbeat.json`
- `microstructure_collection_failure_ledger.csv`

Feature builder remains blocked until a separate accepted gate explicitly approves it.

Coverage PASS does not imply strategy acceptance, replay permission, paper
trading readiness, live trading readiness, broker mutation permission, or
real-capital permission.
