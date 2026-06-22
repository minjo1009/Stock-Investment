# Task590 Runtime Market Data Source Unification

## Decision Summary

- Verdict: PRIMARY_PASS.
- Strategy acceptance status: DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY.
- Objective: make paper-trading account, trade, and entry-chart views use the same runtime market-data lineage instead of falling back to one-off backtest intraday CSVs.
- Target metrics: Task589 paper entry context exports runtime OHLC windows from `trading.db.market_bars_5m`; frontend renders each paper decision with the runtime OHLC source, decision evidence, and indicator snapshot context.
- What changed: Task589 EOD evidence now carries `source_snapshot_id` and indicator snapshot rows; the trader terminal catalog now prioritizes `trading.db.market_bars_5m` for paper entry OHLC windows and only falls back to `data/raw/us_intraday/*.csv` when runtime bars are absent; the frontend paper trade detail view renders OHLC entry decision charts and runtime indicator panels.
- Forbidden actions respected: no inferred lifecycle matching, no symbol/date/price/time fallback for trade lifecycle, no fake market source, no missing labels treated as negatives, and no deployment-readiness claim.
- Next action: persist runtime regime and intraday-continuation state into the same source snapshot lineage so the frontend can show those states as captured runtime facts instead of `NOT_CAPTURED_IN_RUNTIME_DB`.

## Quant Expert Report

### Data source and source readiness

- Available runtime source: `trading.db`.
- Runtime source tables observed on 2026-05-21 KST:
  - `market_ticks`: 1,095 rows from `2026-04-24T15:46:51.838281Z` to `2026-05-20T16:53:26.914774Z`.
  - `market_bars_5m`: 26,198 rows from `2021-06-07T14:30:00Z` to `2026-05-20T16:50:00Z`.
  - `indicator_snapshots`: 2,651 rows from `2026-04-24T15:46:51.838281Z` to `2026-05-20T16:53:26.914774Z`.
  - `runtime_strategy_decisions`: 205 rows from `2026-05-19T15:52:33.652229Z` to `2026-05-20T16:53:34.674520Z`.
- Runtime OHLC readiness is partial-source: current paper UI windows use 5-minute OHLC bars derived from runtime KIS quote/current-price capture, not SIP trade-volume OHLC. This is valid for paper runtime observability but not enough for firm-grade microstructure claims.
- Missing runtime source: regime classification and intraday-continuation classification are not yet persisted in `indicator_snapshots` or `runtime_strategy_decisions`. The UI intentionally reports `NOT_CAPTURED_IN_RUNTIME_DB` instead of inferring those labels from backtest artifacts.

### Exact join keys

- Paper trade detail to runtime decision evidence: exact `decision_id`.
- Runtime decision evidence to indicator snapshot: exact `source_snapshot_id`.
- Entry chart source window: same `symbol` and decision `created_at` window against `trading.db.market_bars_5m`, with source metadata recorded as `trading_db_market_bars_5m`.
- No trade lifecycle matching was added or inferred. Broker/order/fill lifecycle remains governed by the existing Task585/Task589 exact IDs.

### Leakage audit

- Entry chart context is display and audit context only.
- Outcome fields and PnL fields are not used to assign trade signals or rebuild decisions.
- Missing runtime regime and intraday labels are not approximated from future bars or labels.
- Runtime OHLC fallback to raw CSV is only a source availability fallback for visualization, and the catalog marks the source type explicitly.

### Split/OOS metrics

- Not applicable. This task changes live/paper data plumbing and visualization lineage, not strategy selection.

### Failure decomposition

- Previous failure mode: paper-trading UI could show empty OHLC entry windows for 2026 runtime decisions because the catalog searched one-off historical raw intraday CSVs first.
- Fixed failure mode: paper entry context now reads `trading.db.market_bars_5m` first, so current paper decisions have runtime source windows when bars exist.
- Remaining failure mode: KIS quote-derived 5-minute bars have incomplete volume/microstructure semantics. They are not a substitute for SIP/NBBO/depth capture.
- Remaining failure mode: runtime regime and intraday-continuation states are not captured as first-class runtime fields yet.

### Cost/slippage stress where PnL changed

- Not applicable. No PnL model, slippage model, sizing model, or execution policy was changed.

### Remaining blockers

- Persist regime engine output into runtime snapshots.
- Persist intraday-continuation engine output into runtime snapshots.
- Add a source contract test that fails when paper entry context falls back to raw CSV while runtime bars exist.
- Upgrade market data from KIS quote-derived observability to a firm-grade live source where SIP/NBBO/depth/receive timestamp are required.

## No-Background Decision-Maker Report

- What happened: the paper-trading UI now uses the same runtime database that the automated paper system writes during market hours, instead of depending on old one-off backtest chart files.
- Why it matters: when a paper trade or no-trade decision appears in the frontend, the OHLC chart and indicator panel now point back to the runtime source used around that decision time.
- Whether this changes capital/deployment readiness: no. This is DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY because the current runtime bars are quote-derived observability data, not complete firm-grade market microstructure data.
- Plain-language next step: add regime and intraday-continuation classifications to the runtime snapshot table so every decision shows not just price indicators, but also the market-state reasoning captured at the time.

## Artifact Manifest

See `artifact_manifest.csv`.
