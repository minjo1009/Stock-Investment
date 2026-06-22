# Task2831-2840 iOS Chart Time Axis Repair

## Decision Summary

- Verdict: `PRIMARY_PASS` for the requested chart time-axis repair.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 2 chart components repaired; price chart now renders time labels under the x-axis for 1D/5D/1M/All ranges; account trend chart now renders date labels under the x-axis.
- What changed: chart interpretation improved without changing strategy, replay, paper orders, or live-order capability.
- Next action: device QA in Expo Go to confirm labels do not overlap on the user's iPhone viewport.

## Quant Expert Report

### Data Source And Source Readiness

This task is frontend/reporting work only. No market data, paper runtime data, source extraction, replay, or selector data changed.

### Exact Join Keys

Not applicable. No row matching changed.

### Leakage Audit

No assignment, replay, or signal logic changed. Time labels are rendered from chart/account history timestamps already present in the UI payload.

### Split/OOS Metrics

Not applicable. No backtest was run.

### Failure Decomposition

The prior chart UI showed price and volume but did not label the horizontal time axis. This made it harder to judge whether a buy/sell marker happened before, during, or after a move.

Implemented fixes:

1. `PriceChart` now has `axisLabel()` and `axisIndices()` helpers.
2. `PriceChart` renders four bottom x-axis labels where possible.
3. `1D` shows intraday time, `5D` shows date/hour, `1M` shows date, and `All` shows year/date.
4. `AccountTrendChart` now renders start/mid/end date labels.
5. Broken Korean labels in `AccountTrendChart` were repaired.

### Cost/Slippage Stress

Not applicable.

### Remaining Blockers

- Mini sparklines intentionally remain unlabeled because their width is too small for readable time labels.
- Full TradingView-grade pan/zoom remains outside this task.

## No-Background Decision-Maker Report

### What Happened

차트 아래에 시간이 들어가게 고쳤습니다.

1. 종목 가격 차트 아래에 시간/날짜가 표시됩니다.
2. 계좌 추이 차트 아래에도 날짜가 표시됩니다.
3. 1D, 5D, 1M, All 범위에 따라 라벨 형식이 달라집니다.

### Why It Matters

이제 매수/매도 지점이 “언제”였는지 바로 볼 수 있습니다. 차트 흐름을 읽는 데 필요한 기본 정보가 보강됐습니다.

### Whether This Changes Capital/Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

### Plain-Language Next Step

아이폰 Expo Go에서 실제 화면 폭 기준으로 라벨 겹침 여부를 확인합니다.

## Artifact Manifest

### Inputs

- Existing Expo iOS app.
- Task2821-2830 chart/scanner control state.

### Outputs

- `apps/ios-trader-brain/src/components/price-chart.tsx`
- `apps/ios-trader-brain/src/components/account-trend-chart.tsx`
- `scripts/trader_brain_2821_2830_ios_chart_scanner_controls_validate.py`

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

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
