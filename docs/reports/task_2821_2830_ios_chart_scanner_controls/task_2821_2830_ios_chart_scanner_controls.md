# Task2821-2830 iOS Chart Scanner Controls

## Decision Summary

- Verdict: `PRIMARY_PASS` for the requested read-only iOS chart/scanner control upgrade.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 4 bounded frontend/data/QA subagent packets reviewed; chart now supports crosshair-style touch selection, OHLC/VWAP/volume readout, marker/VWAP/volume toggles, expanded chart mode, and range-specific interval aggregation; trade scanner now supports compact/detail mode, hold/watch/risk/rejected groups, and price/change/PnL/risk/volume/source column toggles.
- What changed: mobile paper/shadow cockpit became a higher-density TradingView-style read-only review surface without adding live order capability.
- Next action: run device QA on Expo Go and then connect the scanner to live paper runtime catalog rows with the same schema.

## Quant Expert Report

### Data Source And Source Readiness

This is frontend/reporting work only.

Added UI-facing optional fields:

- `ChartBar.intervalLabel`
- `ChartBar.intervalKey`
- `ChartBar.rangeKey`
- `ChartBar.changeUsd`
- `ChartBar.changePct`
- `ChartBar.volumeChangePct`
- `TradeIntent.scannerRangeKey`
- `TradeIntent.scannerIntervalLabel`
- `TradeIntent.scannerChangeUsd`
- `TradeIntent.scannerChangePct`
- `TradeIntent.scannerVolume`
- `TradeIntent.scannerVolumeRatio`
- `TradeIntent.sourceFreshnessState`
- `TradeIntent.sourceGeneratedUtc`
- `TradeIntent.latestBarAt`
- `TradeIntent.sourceAgeSeconds`
- `TradeIntent.scannerRiskState`
- `TradeIntent.riskSeverity`
- `TradeIntent.riskReason`

Runtime catalog normalization accepts these fields when present. Missing values render as `-` or `UNKNOWN_SOURCE_FRESHNESS`; they are not inferred as negative signals.

### Exact Join Keys

Not applicable. No replay join, lifecycle match, selector match, or backtest row matching changed.

### Leakage Audit

All newly displayed fields are UI explanation and scanner display fields. They are not fed into selector, sizing, replay, assignment, paper order creation, or acceptance logic.

### Split/OOS Metrics

Not applicable. No backtest was run.

### Failure Decomposition

Subagent review found:

1. Detail chart needed interaction controls before it could approximate TradingView usage.
2. Range buttons needed interval behavior, not only state changes.
3. Marker visibility needed explicit toggling for buy/sell/current review.
4. Trade list needed trader scanner structure: compact/detail, candidate groups, and column selection.
5. Korean fixture/runtime fallback copy was still broken in multiple touched files.

Implemented fixes:

1. `PriceChart` now aggregates bars by range-specific intervals and exposes touch selection.
2. OHLC/VWAP/volume readout updates from the selected bar.
3. Detail screen exposes marker, VWAP, volume, and expanded chart controls.
4. Trades tab groups rows into hold/watch/risk/rejected and renders no-trade reasons separately.
5. `SymbolRow` supports compact/detail modes and price/change/PnL/risk/volume/source column toggles.
6. Runtime normalizer and fixture fallback were cleaned for Korean display and scanner fields.

### Cost/Slippage Stress

Not applicable. No PnL or replay changed.

### Remaining Blockers

- Still not full TradingView: no pinch zoom, pan, drawing tools, indicator library, or broker-grade live quote stream.
- Current chart interaction is Expo-Go-compatible touch selection, not a native high-performance chart engine.
- Real-time market data provider is still outside this task.

## No-Background Decision-Maker Report

### What Happened

The iPhone app now has a more serious trading review surface.

1. Chart touch now shows the selected candle's O/H/L/C, VWAP, and volume.
2. Markers, VWAP, volume, and expanded chart mode can be toggled.
3. Range buttons now change the aggregation interval.
4. Trade list can switch between compact and detail view.
5. Candidates are separated into hold, watch, risk, and rejected.
6. Scanner columns can be turned on/off.

### Why It Matters

The app is now closer to a trading cockpit instead of a static report.

It still does not place orders. It helps answer:

- What did the brain buy?
- Why did it buy?
- What changed after entry?
- Is this normal winner volatility or risk?
- Which rejected candidates were blocked and why?

### Whether This Changes Capital/Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

### Plain-Language Next Step

Test on the iPhone with Expo Go, then connect the same scanner fields to the real paper-runtime catalog instead of only fixture fallback.

## Artifact Manifest

### Inputs

- Existing Expo iOS app under `apps/ios-trader-brain`.
- Task2811-2820 frontend state.
- Four bounded subagent packets for chart UX, scanner UX, data contract, and mobile QA.

### Outputs

- `apps/ios-trader-brain/src/components/price-chart.tsx`
- `apps/ios-trader-brain/src/app/trade/[id].tsx`
- `apps/ios-trader-brain/src/app/(tabs)/trades.tsx`
- `apps/ios-trader-brain/src/components/symbol-row.tsx`
- `apps/ios-trader-brain/src/types/cockpit.ts`
- `apps/ios-trader-brain/src/lib/cockpit-data.ts`
- `apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts`
- `scripts/trader_brain_2821_2830_ios_chart_scanner_controls_validate.py`

### Row Counts

- App source files touched: 7.
- Validator added: 1.
- Replay rows changed: 0.
- Paper order rows changed: 0.
- Live order rows changed: 0.

### Validation Commands

- `python scripts/trader_brain_2821_2830_ios_chart_scanner_controls_validate.py`
- `npx tsc --noEmit`
- `npm run lint`
- `npx expo export --platform web --clear`
- `python scripts/task_registry_validate.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
