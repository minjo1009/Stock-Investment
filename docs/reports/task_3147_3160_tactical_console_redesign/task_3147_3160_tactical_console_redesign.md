# Task3147-3160 Tactical Console Redesign

## Decision Summary

- Verdict: `tactical_console_redesign_completed_read_only`.
- Design mix: TradingView Tactical Console 70%, Toss-style Home 20%, Analysis/Risk 10%.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Scope: UI/UX only for the read-only Expo iOS cockpit; no selector, sizing, replay, paper order, live order, or broker mutation changed.
- Image report: `data/artifacts/task_3147_3160_tactical_console_redesign/tactical_console_redesign_report.png`.

## Quant Expert Report

### Data Source And Source Readiness

This task did not acquire new market data and did not change trading logic. It reuses the existing `CockpitData` contract, including:

- `trades[].id`
- `trades[].chart.bars`
- `trades[].chart.markers`
- `trades[].scannerChangePct`
- `trades[].scannerVolumeRatio`
- `trades[].sourceFreshnessState`
- `themeHeat`
- `tradeReview`
- `symbolCatalysts`
- `marketContext`
- `dataHealth`

Missing fields remain explicit missing/source states. No missing label is treated as a negative.

### UI/Data Contract Changes

- Home: compressed to total assets, account trend, market state, top 3 symbols, and primary blocker.
- Scanner: rebuilt as a dark tactical console with theme tape, saved scan rail, fixed numeric columns, dense rows, selected chart preview, and `trade.id -> detail` navigation.
- Detail: rebuilt as chart-first execution console with entry/current/VWAP/volume readouts, range/interval/toggle controls, and compact Brief/Risk/Source sections.
- Analysis: compressed into decision console, selected chart review, catalyst/invalidation, trade review, next events, and policy blocker.
- Chart: increased chart height, reduced card radius, reduced marker/VWAP visual competition, and removed broken separator text.

### Leakage Audit

Outcome/review fields such as `tradeReview`, MDD flags, and cost drag remain review-only UI context. They must not enter scanner assignment, candidate ranking, selector logic, replay logic, or strategy acceptance logic.

### Split/OOS Metrics

Not applicable. No replay, split/OOS, performance comparison, or strategy acceptance evaluation was run.

## No-Background Decision-Maker Report

The app now leans much more toward a TradingView-style tactical surface:

1. Scanner is a dense console, not a stack of cards.
2. Detail is chart-first, with OHLC/VWAP/volume visible before explanatory text.
3. Home stays Toss-like and short.
4. Analysis/Risk remain supporting review surfaces, not the center of the app.

This does not make the strategy accepted or deployable.

## Artifact Manifest

### Inputs

- Current Expo iOS cockpit under `apps/ios-trader-brain`.
- Existing Task3128-3140 hybrid app direction.
- Subagent QA gap report for TradingView 70% target.

### Outputs

- `apps/ios-trader-brain/src/app/(tabs)/index.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
- `apps/ios-trader-brain/src/app/(tabs)/analysis.tsx`
- `apps/ios-trader-brain/src/app/trade/[id].tsx`
- `apps/ios-trader-brain/src/components/price-chart.tsx`
- `scripts/trader_brain_3147_3160_tactical_console_redesign_validate.py`
- `data/artifacts/task_3147_3160_tactical_console_redesign/tactical_console_redesign_report.png`
- `data/artifacts/task_3147_3160_tactical_console_redesign/screenshots_live/*.png`

### Validation

- `python scripts/trader_brain_3147_3160_tactical_console_redesign_validate.py`
- `python scripts/task_registry_validate.py`
- `cd apps/ios-trader-brain; npx tsc --noEmit`
- `cd apps/ios-trader-brain; npm run lint`
- `cd apps/ios-trader-brain; npx expo export --platform web --clear`

Validation authority: `REPORTING_HEALTH` and frontend wiring only. Passing validation does not imply strategy acceptance, deployment readiness, or real-capital permission.
