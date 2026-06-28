# Decision Summary

- Verdict: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`; this task changes data acquisition only and opens no deployment or real-capital gate.
- What changed: quote/trade tick full-universe collection is postponed; the prior tick collector was stopped with `STOP_REQUESTED`. A new Alpaca historical bar collector now runs daily and 5m bar lanes in the shapes needed by L1 and L2.
- Current background state: 5m bar collector PID `8936`, daily shard collectors PIDs `4924`, `15804`, `14628`, `2372`, news collector PID `22388`, and keep-awake PID `1152` are running.
- Next action: let the bar/news collectors continue, monitor `collector_progress.json`, and treat Alpaca empty 5m windows as missing source evidence rather than approximating.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Backfill full-universe L0 daily and 5m bar data from 2016-01-01 through the latest complete market date, in L1/L2-consumable form, while quote/trade ticks remain postponed. |
| Target Metrics | Universe 12,040 active/tradable symbols; daily estimated 12,040 request units; 5m estimated 385,280 request units; total estimated 397,320 request units; target progress 100% with rate-limit events tracked. |
| Forbidden Actions | No inferred lifecycle matching; no fake source; no missing-source approximation; no label leakage; no strategy or deployment claim. |
| Available Raw Sources | `data/raw/alpaca_active_us_equity_universe.csv`; `data/raw/l0_reference/` assets/calendar/clock snapshot; Alpaca historical bars credential; existing `trading.db::market_bars_5m`; Marketaux token in `.env`; running GDELT/Marketaux/official news collector. |
| Missing Raw Sources | Full quote/trade tick collection is intentionally postponed; official issuer endpoint coverage is missing for most symbols; Alpaca IEX 5m returns empty for some older windows and must remain explicit missing coverage. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance |
| Output Directory | `docs/reports/task_l0_bar_full_universe_l1_l2_backfill/` |
| Large Artifact Directory | `data/artifacts/l0_bar_full_backfill/` |
| Validation | `python -m py_compile ...`; `python -m unittest tests.test_task_337_historical_intraday_backfill tests.test_l0_bar_full_backfill tests.test_l0_reference_snapshot tests.test_l0_collection_status`; live smoke in `data/artifacts/l0_bar_full_backfill_smoke/`; read-only Alpaca reference snapshot; `python scripts/report_l0_collection_status.py`. |
| Completion Criteria | Daily and 5m lanes reach 100% or provider-missing windows are exhaustively recorded; news collector remains governed; registry and manifests are current. |

# Quant Expert Report

## Data Source And Source Readiness

Daily bars are written to `data/raw/us_daily_alpaca_full_universe/<SYMBOL>.csv` with the loader-compatible schema `timestamp, open, high, low, close, volume, symbol`. This is L1/backtest-compatible raw CSV, but it does not alter the protected existing `data/raw/us_daily` files.

5m bars are inserted into `trading.db::market_bars_5m`, which is the existing L2 live runtime input table. The key remains `bar_id = symbol:bar_start_ts`, with source columns preserved.

The live smoke collected one daily row and 72 5m rows for `A` on 2026-06-26. Full collection then started on 2016-01-01. Early 5m windows for `A` before 2020 produced `EMPTY_PROVIDER_RESPONSE`; later windows exported rows. This is recorded as provider evidence, not approximated.

## Current Progress Snapshot

- Bar plan: 12,040 symbols, 2016-01-01 to 2026-06-26, 397,320 request units.
- Combined collector was stopped at `STOP_REQUESTED` and split into two workers to remove daily/5m head-of-line blocking.
- Consolidated status is written to `data/artifacts/l0_collection_status/current_status.json` and `data/artifacts/l0_collection_status/current_status.md`; it now includes explicit 1m bar scope status and news progress by Official/GDELT/Marketaux source.
- The daily worker was split into 4 shard workers at 15 rpm each, preserving the same 60 rpm daily throttle while reducing request latency bottlenecks.
- Snapshot around 2026-06-28T02:51Z: daily raw output had 358 CSV files, failed 0, rate-limited 0; daily progress about 2.9734%. Shards were still skipping already-collected early symbols before reaching new export territory.
- 5m worker snapshot: 773 processed request units, failed 0, rate-limited 0; 5m progress about 0.1877%; `market_bars_5m` held 417,903 total rows across 96 symbols.
- 1m bars are not in the current L1/L2 minimum required scope because current consumers are wired to daily CSV and `market_bars_5m`; a full-universe 1m backfill is about 5x the 5m request/storage surface and should be a separate optional lane only if an L1/L2 contract requires it.
- News source snapshot around 2026-06-28T03:09Z: Official endpoint refresh 7/7 with 5 latest exported and 2 retryable failures; GDELT 2,578/367,872 chunks; Marketaux 94/26,499 minimum request units and waiting on the 2026-06-28 daily cap reset.
- Reference snapshot: `PRIMARY_PASS`; 13,914 active assets, 19,249 inactive assets, 33,163 combined asset rows, 2,635 calendar sessions, and one clock/status snapshot exported.
- ETA: daily shard workers together are configured at 60 rpm and should now be limited more by API/response latency than a single process; 5m worker configured at 60 rpm shows about 107 configured hours remaining and an observed early ETA near 276 hours because old empty windows and large response windows have uneven latency.

## Exact Join Keys

- Daily L1 key: `symbol`, `timestamp`.
- 5m L2 key: `bar_id`, derived exactly as `symbol:bar_start_ts`; natural key `symbol`, `bar_start_ts`.
- Reference assets key: `symbol`; reference calendar key: `date`.
- News lanes use provider/source IDs and raw paths only; no trading label join is performed here.

## Leakage Audit

No labels, outcomes, broker fills, position lifecycle, or future returns are read or written by this task. The collector only captures provider bars and source events. Missing labels are not converted to negatives.

## Split/OOS Metrics

Not applicable. This is source acquisition infrastructure only.

## Cost/Slippage Stress

Not applicable. No PnL, fill, order, or slippage claim is made.

## Remaining Blockers

- Quote/trade tick full-universe collection is postponed by user decision.
- Alpaca IEX may not provide full 2016~present 5m coverage for all symbols/windows. Empty windows are recorded and remain data-readiness blockers unless another source is added.
- Official news/public-release historical coverage remains blocked where symbol-specific official archive endpoints are not verified.

# No-Background Decision-Maker Report

We stopped trying to download every quote/trade tick because that path is too heavy right now. Instead, the system is now collecting the bar data the project can actually use soon: daily bars for L1/backtests and 5-minute bars for L2/runtime primitives.

One-minute bars are deliberately excluded from this minimum path for now. They remain an optional future lane, not a silent gap in the current L1/L2 contract.

This does not make the strategy live-ready. It improves the data foundation. Missing older 5m data and missing official archives are being recorded honestly instead of filled in.

The collectors are running in the background while the laptop stays awake. If the observed speed stays too low after a larger sample, the next practical improvement is partitioned background workers under the same aggregate API throttle.

# Artifact Manifest

See `artifact_manifest.csv` in this report directory for tracked inputs, outputs, validation, and progress files.
