# Task3128-3140 Hybrid Investment App Redesign

## Decision Summary

- Verdict: `hybrid_investment_app_redesign_completed_read_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Direction: TradingView tactical scanner/chart core + Toss-style account Home + PM/CIO analysis and risk boards.
- Key metrics: 5 primary tabs, 2 new tabs (`analysis`, `market`), 5 screenshot captures, 5 optional data blocks added, replay performed 0, paper order intents created 0, live orders created 0.
- Image report: `data/artifacts/task_3128_3140_hybrid_investment_app_redesign/hybrid_investment_app_redesign_report.png`.

## Quant Expert Report

### Data Source And Source Readiness

This is frontend and typed UI contract work. No trading raw source was acquired. No replay, selector, sizing, label, lifecycle, order, fill, or broker logic changed.

The app data contract now accepts optional read-only product blocks:

- `marketContext`
- `themeHeat`
- `eventTimeline`
- `symbolCatalysts`
- `tradeReview`

When runtime does not provide these blocks, the normalizer reports source-not-attached states instead of inferring missing values.

### Exact Join Keys

- Home -> scanner rows: `trades[].id`, `symbol`, `scannerChangePct`, `sourceFreshnessState`.
- Scanner -> Detail: `trade.id`.
- Analysis -> selected trade review: `tradeReview.tradeId`, `tradeReview.symbol`.
- Analysis -> catalyst: `symbolCatalysts.symbol`.
- Market -> scanner theme grouping: `themeHeat.themeId`, `themeHeat.topSymbols`.
- Risk -> system health: `dataHealth.connectors`, `dataHealth.requiredFiles`, `dataHealth.riskMetrics`.

### Leakage Audit

Outcome and drawdown fields in `tradeReview` are review-only. They must not enter scanner assignment, candidate ranking, selector logic, or strategy acceptance logic.

Missing labels and missing source blocks remain explicit missing/source-not-attached states.

### Split/OOS Metrics

Not applicable. No backtest, replay, split/OOS evaluation, or performance comparison was run.

### UI/Data Contract Changes

- Home: rebuilt around account summary, asset trend, market regime strip, top 3 watch items, and safety state.
- Scanner: retains TradingView-style dark scanner and adds `themeHeat` above dense rows.
- Analysis: new tab for decision ribbon, selected trade chart review, catalyst/invalidation, cost/MDD review, event timeline, and policy blocker.
- Market: new tab for regime, index/volatility, macro rows, theme heatlist, and event timeline.
- Risk: rebuilt as PM/CIO risk board with macro risk, limits, cost/drawdown review, source freshness, symbol blockers, and required files.
- Tabs: changed to `홈 / 스캔 / 분석 / 시장 / 위험`.

### Remaining Blockers

- Actual backend runtime still needs to emit richer `marketContext`, `themeHeat`, `eventTimeline`, `symbolCatalysts`, and `tradeReview` rows.
- iPhone/Expo Go device QA was not run in this pass.
- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.

## No-Background Decision-Maker Report

### What Happened

The app was redesigned around a real investment workflow:

1. Home answers what matters now.
2. Scanner helps scan symbols fast.
3. Analysis explains why a position is held, watched, or blocked.
4. Market explains the surrounding regime and themes.
5. Risk shows blockers, drawdown/cost context, data freshness, and live-order locks.

### Whether This Changes Capital Or Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`

## Artifact Manifest

### Inputs

- Task3061 actual mobile app benchmark correction.
- Product Design/subagent synthesis for TradingView/Toss/PM-CIO hybrid direction.
- Existing iOS cockpit source under `apps/ios-trader-brain`.

### Outputs

- `apps/ios-trader-brain/src/types/cockpit.ts`
- `apps/ios-trader-brain/src/lib/cockpit-data.ts`
- `apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts`
- `apps/ios-trader-brain/src/app/(tabs)/_layout.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/index.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/analysis.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/market.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/risk.tsx`
- `scripts/trader_brain_3128_3140_hybrid_investment_app_redesign_validate.py`
- `data/artifacts/task_3128_3140_hybrid_investment_app_redesign/hybrid_investment_app_redesign_report.png`
- `data/artifacts/task_3128_3140_hybrid_investment_app_redesign/screenshots_live/*.png`

### Validation

- `cd apps/ios-trader-brain; npx tsc --noEmit`
- `cd apps/ios-trader-brain; npm run lint`
- `cd apps/ios-trader-brain; npx expo export --platform web --clear`
- `python scripts/trader_brain_3128_3140_hybrid_investment_app_redesign_validate.py`
- `python scripts/task_registry_validate.py`

Validation authority: `REPORTING_HEALTH` and `GOVERNANCE_HEALTH` only. Passing validation does not mean strategy acceptance, deployment readiness, or real-capital permission.
