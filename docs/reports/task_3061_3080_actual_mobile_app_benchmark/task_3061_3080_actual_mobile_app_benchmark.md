# Task3061-3080 Actual Mobile App Benchmark Correction

## Decision Summary

- Verdict: `actual_mobile_app_benchmark_correction_completed_read_only`.
- Supersedes: the Task3041 image board is not reliable enough because it mixed documentation/webpage captures with benchmark UI. Use this Task3061 pack instead.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 69 official App Store screenshots downloaded, 4 TradingView phone cards cropped from the official App Store page, 5 current app screenshots compared, 1 corrected visual board generated, app code changes 0, replay performed 0, paper order intents 0, live orders 0.
- Corrected image report: `data/artifacts/task_3061_3080_actual_mobile_app_benchmark/actual_mobile_app_ui_benchmark_report.png`.

## Quant Expert Report

### Data Source And Source Readiness

This is UI/UX reference research only. The corrected benchmark uses real mobile app screenshots:

- Apple iTunes/App Store lookup API screenshot URLs.
- TradingView official App Store page phone-card crops where lookup returned 0 screenshot URLs.
- Current local iOS cockpit screenshots from Task3021-3040.

No trading raw source, replay, selector, label, lifecycle, order, fill, or broker data was changed.

### Exact Join Keys

No joins were added. No runtime data contract was changed.

### Leakage Audit

No labels, future outcomes, or evaluation fields were used in assignment logic. Missing labels were not converted into negatives.

### Split/OOS Metrics

Not applicable. No backtest or split/OOS evaluation was run.

### UI Failure Correction

The previous image board was rejected because its benchmark columns contained documentation pages and desktop/web captures. That was the wrong visual evidence for mobile app UI/UX.

The corrected board uses only:

- Actual App Store mobile screenshots from Toss, Robinhood, Coinbase, Schwab, Yahoo Finance, thinkorswim, MetaTrader, Investing.com, and NetBenefits.
- Cropped TradingView phone screenshot cards from the official App Store page.
- Our current app screenshots.

### Corrected Tab Findings

- Home: use account/asset glance, one trend, and minimal lock/status. Fix right clipping and add 7D trend/top blocker sentence.
- Trades: use watchlist rows, compact columns, saved lists, and collapsible filters. Add relative volume, turnover, bucket rank, and one-line evidence.
- Detail: use chart-first mobile detail patterns. Add selected OHLC/VWAP/range delta and repair clipping.
- Risk: use portfolio protection, balance trend, and security-state patterns. Add source freshness, MDD/cost versus limit, symbol blockers, and non-color warning cues.
- Settings: use secure account/account setup/checklist patterns. Show connector health as checklist with last success/fail, SLA, checksum/schema, and raw/as-of/fixture labels.

### Remaining Blockers

- This pack is still reference research. It does not implement the next UI pass.
- Risk and Settings references are the closest actual mobile screenshots available from public App Store material; many apps do not expose deep settings screens publicly.
- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.

## No-Background Decision-Maker Report

### What Happened

The bad image report was replaced.

The new image report uses real mobile app screenshots only. It compares those against our current Home, Trades, Detail, Risk, and Settings screens.

### What It Means

The next design pass should use the Task3061 image report, not the Task3041 board.

### Whether This Changes Capital Or Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`

## Artifact Manifest

### Inputs

- App Store lookup/API screenshots under `data/artifacts/task_3061_3080_actual_mobile_app_benchmark/raw_appstore_screenshots/`.
- TradingView official App Store page crop under `data/artifacts/task_3061_3080_actual_mobile_app_benchmark/curated_references/`.
- Current app screenshots under `data/artifacts/task_3021_3040_ios_concise_navigation_redesign/screenshots_live/`.

### Outputs

- `data/artifacts/task_3061_3080_actual_mobile_app_benchmark/actual_mobile_app_ui_benchmark_report.png`
- `data/artifacts/task_3061_3080_actual_mobile_app_benchmark/actual_appstore_contact_sheet.png`
- `data/artifacts/task_3061_3080_actual_mobile_app_benchmark/actual_mobile_appstore_screenshot_manifest.csv`
- `data/artifacts/task_3061_3080_actual_mobile_app_benchmark/curated_mobile_app_reference_matrix.csv`
- `data/artifacts/task_3061_3080_actual_mobile_app_benchmark/artifact_manifest.md`
- `docs/reports/task_3061_3080_actual_mobile_app_benchmark/task_3061_3080_actual_mobile_app_benchmark.md`
- `docs/reports/task_3061_3080_actual_mobile_app_benchmark/task_3080_decision.csv`
- `scripts/trader_brain_3061_3080_actual_mobile_app_benchmark_validate.py`

### Validation

- `python scripts/trader_brain_3061_3080_actual_mobile_app_benchmark_validate.py`
- `python scripts/task_registry_validate.py`

Validation authority: `REPORTING_HEALTH` and `GOVERNANCE_HEALTH` only. Passing validation does not mean strategy acceptance, deployment readiness, or real-capital permission.
