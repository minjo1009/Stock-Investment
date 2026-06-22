# Task2851-2860 iOS Interval And Timing Basis Repair

## Decision Summary

- Verdict: `PRIMARY_PASS` for read-only iOS chart interval and timing-basis repair.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: trade detail now separates chart display interval from execution evidence, shows entry/exit timing decomposition, and makes VWAP explicitly auxiliary rather than the sole buy/sell basis.
- What did not change: no selector, replay, sizing, exit brain, paper order, broker mutation, or live-order capability changed.

## Quant Expert Report

### Data Source And Source Readiness

This is frontend/reporting work only. It uses existing chart bars, trade entry/exit prices, markers, and paper/shadow catalog fields already available to the app.

The app now makes these data limitations visible:

1. The selected chart interval is a UI aggregation view.
2. VWAP is displayed only when an actual VWAP field exists.
3. Missing VWAP or missing volume renders as `-`.
4. Entry/exit evidence shows fill price, nearest candle close, VWAP if present, volume if present, candle time, and fill-to-candle time difference.
5. If the nearest candle is too far from the fill timestamp, the detail view displays `NEAREST_BAR_TOO_FAR`.

### Expert Review Loop

Review-only expert packets were used before finalizing the implementation.

1. Chart UX reviewer: interval controls must not be confused with execution evidence. The UI should show fill timestamp versus nearest bar timestamp and time gap.
2. Data-contract reviewer: VWAP-to-close fallback forms are misleading because close is not VWAP. Missing VWAP must remain missing.
3. Mobile QA reviewer: not spawned due to available agent-thread limit. This does not block the code change because automated validation and Expo export remain the authority for this task.

### Leakage Audit

No assignment, backtest, replay, or signal calculation changed. The added fields are display-only and read from already-present trade/chart payloads.

### Split/OOS Metrics

Not applicable. No strategy or replay was run.

### Implementation Notes

Frontend changes:

- `apps/ios-trader-brain/src/components/price-chart.tsx`
- `apps/ios-trader-brain/src/app/trade/[id].tsx`

Validation changes:

- `scripts/trader_brain_2821_2830_ios_chart_scanner_controls_validate.py`

Key implementation choices:

1. Added `auto / 5m / 15m / 1h` chart interval control.
2. Kept interval as a chart-view setting, not an execution rule.
3. Removed VWAP fallback-to-close behavior from chart aggregation/readout.
4. Added timing-basis card for buy and sell points.
5. Added validator checks that block future VWAP-as-close fallback and live-order UI patterns.
6. Added render safety for missing runtime chart/bars/marker fields after Expo Go render failure report.

### Remaining Blockers

- True TradingView-grade pan/zoom remains out of scope.
- If runtime sources do not provide true 5m/15m/1h bars, the UI can only aggregate the bars it receives.
- Broker-grade fill reconstruction still requires backend fill/source quality, not just frontend display.

## No-Background Decision-Maker Report

### What Happened

차트에서 두 가지를 분리했습니다.

1. `1시간봉`은 보기용 집계입니다.
2. 매수/매도 타점 근거는 별도 표로 봅니다.

이제 상세 화면에서 확인할 수 있습니다.

1. 체결가
2. 당시 봉 종가
3. 당시 VWAP
4. VWAP 대비
5. 당시 거래량
6. 봉 시간
7. 체결 시각과 봉 시각 차이

VWAP이 없으면 종가로 대체하지 않고 `-`로 표시합니다.

### Why It Matters

전에는 앱이 “타점이 VWAP 하나로 계산된 것처럼” 보일 수 있었습니다.

이제는 VWAP이 보조 지표임을 명확히 표시합니다. 체결가, 봉, 거래량, 시간차를 같이 봅니다.

### Whether This Changes Capital/Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

### Plain-Language Next Step

아이폰 Expo Go에서 실제 화면으로 타점 근거 표와 1시간봉/15분봉/5분봉 전환이 읽기 좋은지 확인합니다.

## Artifact Manifest

### Inputs

- Existing Expo iOS cockpit app.
- Task2821-2830 chart/scanner controls.
- Task2831-2840 chart time-axis repair.
- Review-only expert feedback on chart interval and data-contract risk.

### Outputs

- `apps/ios-trader-brain/src/components/price-chart.tsx`
- `apps/ios-trader-brain/src/app/trade/[id].tsx`
- `scripts/trader_brain_2821_2830_ios_chart_scanner_controls_validate.py`
- `docs/reports/task_2851_2860_ios_interval_timing_basis_repair/task_2851_2860_ios_interval_timing_basis_repair.md`
- `docs/reports/task_2851_2860_ios_interval_timing_basis_repair/task_2860_decision.csv`

### Row Counts

- App source files touched: 2.
- Validator updated: 1.
- Replay rows changed: 0.
- Paper order rows changed: 0.
- Live order rows changed: 0.

### Validation Commands

- `python scripts/trader_brain_2821_2830_ios_chart_scanner_controls_validate.py`
- `npx tsc --noEmit`
- `npm run lint`
- `npx expo export --platform web --clear`
- `python scripts/task_registry_validate.py`

Post-fix rerun after render failure report:

- `npx tsc --noEmit`
- `npm run lint`
- `python scripts/trader_brain_2821_2830_ios_chart_scanner_controls_validate.py`
- `npx expo export --platform web --clear`

Validation does not imply strategy acceptance, deployment readiness, or real-capital permission.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
