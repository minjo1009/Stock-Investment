# Task3041-3060 Tab Benchmark Context

## Decision Summary

- Verdict: `tab_benchmark_context_pack_completed_read_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 5 tabs benchmarked, 5 explorer packets completed, 17 benchmark screenshots captured, 1 visual comparison board generated, replay performed 0, paper order intents created 0, live orders created 0.
- What changed: no app code changed. The task gathered tab-specific UI/UX benchmark context and compared it with the current read-only iOS cockpit screenshots.
- Image report: `data/artifacts/task_3041_3060_tab_benchmark_context/tab_benchmark_image_report.png`.
- Next action: use this pack to plan the next UI implementation pass, especially overflow repair, saved scanner views, selected chart-point/range summaries, risk freshness, and connector health.

## Quant Expert Report

### Data Source And Source Readiness

This task is UI/UX research and reporting. It does not acquire trading raw sources, run replay, change selector logic, or change execution logic.

Benchmark sources were public UI/reference pages from Apple, TradingView, Toss, IBKR, and Fidelity. These sources are design references only. They are not source-of-truth for trading data or strategy validation.

### Exact Join Keys

No joins were added. No app runtime data contract was changed.

### Leakage Audit

No labels, outcomes, future returns, or assignment logic were touched. Missing labels were not converted into negatives.

### Split/OOS Metrics

Not applicable. No split/OOS, backtest, replay, cost/slippage, or performance comparison was run.

### Failure Decomposition

The current iOS cockpit is directionally aligned with the selected references, but tab-level gaps remain:

- Home: the glance-first model is right, but right-side overflow and missing 7-day account trend/top blocker summary weaken first-screen clarity.
- Trades: the risk-first scanner is right, but it lacks saved scan views, collapsible filters, relative volume, turnover, and bucket rank.
- Detail: chart-first and Evidence/Risk/Sources tabs are right, but selected point/range summaries and clipping repair are needed.
- Risk: blocker-board direction is right, but source freshness, limit-relative risk values, symbol blockers, and non-color warning cues are missing.
- Settings: diagnostic-only and Strict BLOCKED are visible, but connector-level health, freshness SLA, checksum/schema results, and raw/as-of/fixture distinction are missing.

### Cost/Slippage Stress

Not applicable. No PnL, cost, slippage, order, fill, or broker-truth logic changed.

### Recommended DB Contract Additions

- Home: `day_change_pct`, `account_history_7d`, `source_age_seconds`, `top_blocker_code`, `lead_volume_ratio`, `market_regime_label`.
- Trades: `scan_bucket`, `bucket_reason_code`, `rank_in_bucket`, `relative_volume`, `turnover`, `primary_evidence_sentence`, `catalyst_type`.
- Detail: `selected_point_ohlcv`, `selected_point_vwap`, `selected_range_start_utc`, `selected_range_end_utc`, `selected_range_delta_pct`, `entry_vwap_gap_pct`.
- Risk: `risk_status`, `top_blocker_code`, `source_age_minutes`, `stale_threshold_minutes`, `max_drawdown`, `mdd_limit`, `cost_drag`, `symbol_blocker_codes`.
- Settings: `connector_health`, `safety_locks`, `required_files`, `last_success_utc`, `lag_minutes`, `freshness_sla_minutes`, `source_hash`, `schema_version`.

### Remaining Blockers

- Benchmark captures are visual references only and may not represent each product's full native app behavior.
- Some Apple HIG pages require JavaScript and were used primarily as linked design principles rather than full visual screenshots.
- No implementation patch was made in this task.
- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.

## No-Background Decision-Maker Report

### What Happened

Five agents gathered benchmark context separately by tab:

- Home: Toss and Apple Stocks style glance screen.
- Trades: TradingView scanner/watchlist patterns.
- Detail: Apple Stocks and TradingView chart interaction patterns.
- Risk: Apple feedback plus IBKR/Fidelity risk-board patterns.
- Settings: Apple/Toss/TradingView connection and safety patterns.

### What It Means

The current app direction is not wrong. The next UI pass should not add more scroll. It should sharpen each tab around one job:

- Home: one account answer.
- Trades: one scan answer.
- Detail: one chart answer.
- Risk: one blocker answer.
- Settings: one connector/safety answer.

### Whether This Changes Capital Or Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`

### Plain-Language Next Step

Use the image board and CSV matrix as the input for the next implementation plan. The first implementation targets should be overflow repair, compact scan-view controls, selected chart summaries, risk freshness, and connector health.

## Artifact Manifest

### Inputs

- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/screenshots_live/01_home.png`
- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/screenshots_live/02_trades.png`
- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/screenshots_live/03_detail.png`
- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/screenshots_live/04_risk.png`
- `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/screenshots_live/05_settings.png`
- `docs/ownership/subagent_packet_standard.md`
- `docs/architecture/test_validation_canonicalization_map.md`

### Outputs

- `docs/reports/task_3041_3060_tab_benchmark_context/task_3041_3060_tab_benchmark_context.md`
- `docs/reports/task_3041_3060_tab_benchmark_context/task_3060_decision.csv`
- `data/artifacts/task_3041_3060_tab_benchmark_context/tab_benchmark_image_report.png`
- `data/artifacts/task_3041_3060_tab_benchmark_context/tab_benchmark_comparison.csv`
- `data/artifacts/task_3041_3060_tab_benchmark_context/benchmark_source_manifest.csv`
- `data/artifacts/task_3041_3060_tab_benchmark_context/subagent_packet_summary.csv`
- `data/artifacts/task_3041_3060_tab_benchmark_context/artifact_manifest.md`
- `data/artifacts/task_3041_3060_tab_benchmark_context/screenshots_benchmark/*.png`

### Validation

- `python scripts/trader_brain_3041_3060_tab_benchmark_context_validate.py`
- `python scripts/task_registry_validate.py`

Validation authority: `REPORTING_HEALTH` and `GOVERNANCE_HEALTH` only. Passing validation does not mean strategy acceptance, deployment readiness, or real-capital permission.
