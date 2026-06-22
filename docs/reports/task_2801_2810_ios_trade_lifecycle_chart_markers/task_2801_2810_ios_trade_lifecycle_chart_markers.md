# Task2801-2810 iOS Trade Lifecycle Chart Markers

## Decision Summary

- Verdict: `PRIMARY_PASS` for read-only iOS trade lifecycle chart implementation.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: chart markers added, closed-trade review support added, live-catalog auto refresh added, app code changed only under `apps/ios-trader-brain`.
- What changed: symbol detail charts can now display buy/sell/current markers, shaded holding window, marker timeline, buy/sell reasons, and closed-trade review context.
- Next action: run iPhone visual QA in Expo Go and, if approved, add source-backed real-time bars from the paper runtime catalog.

## Quant Expert Report

### Data Source And Source Readiness

This is UI/paper-cockpit work. It does not alter trading data, selector logic, replay logic, or strategy outputs.

Runtime input remains:

- `paper_ops_runtime_catalog.json`
- `paper_trade_detail_view.json`
- Fixture fallback under `apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts`

New optional fields:

- `exitAt`
- `exitPrice`
- `realizedPnlUsd`
- `realizedPnlPct`
- `sellReason`
- `tradeReviewSummary`
- `chart.markers[]`

If runtime catalog does not provide markers, the app derives safe read-only markers from entry/exit/current fields.

### Exact Join Keys

Not applicable. No trading-row join was changed.

### Leakage Audit

Outcome and lifecycle fields are displayed for audit/review only in the UI. They are not used for assignment, selector, sizing, replay, or paper order mutation.

### Split/OOS Metrics

Not applicable. No replay or backtest was run.

### Failure Decomposition

Previous app detail screen had chart bars and thesis/risk/source tabs, but it did not clearly show where the brain bought or sold. This made it hard to answer:

1. Where did the brain enter?
2. Where did it exit?
3. What was the reason at each point?
4. Was the trade still open or already closed?

Task2801 fixes that read-only explanation gap.

### Cost/Slippage Stress

Not applicable.

### Remaining Blockers

- True market real-time streaming is not implemented in this task.
- Live market data requires a certified data source and source-readiness contract.
- Browser screenshot QA was not completed because Playwright was not installed in the local app dependencies.

## No-Background Decision-Maker Report

### What Happened

이제 종목 상세 차트에 매수/매도/현재 지점이 표시됩니다.

보유 중인 종목은 `보유종목 실시간 차트`로 보입니다.

매매가 끝난 종목은 `매수~매도 리뷰 차트`로 보입니다.

### Why It Matters

이제 사용자가 볼 수 있습니다.

- 어디서 샀는지
- 어디서 팔았는지
- 왜 샀는지
- 왜 팔았는지
- 매수 전후와 매도 이후 가격 흐름이 어땠는지

### Whether This Changes Capital/Deployment Readiness

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Artifact Manifest

### Inputs

- Existing Expo iOS app.
- Existing paper cockpit fixture/runtime data contract.

### Outputs

- `apps/ios-trader-brain/src/types/cockpit.ts`
- `apps/ios-trader-brain/src/lib/cockpit-data.ts`
- `apps/ios-trader-brain/src/lib/use-cockpit.ts`
- `apps/ios-trader-brain/src/components/price-chart.tsx`
- `apps/ios-trader-brain/src/app/trade/[id].tsx`
- `apps/ios-trader-brain/src/components/symbol-row.tsx`
- `apps/ios-trader-brain/src/fixtures/cockpit-fixture.ts`
- `scripts/trader_brain_2801_2810_ios_trade_lifecycle_chart_markers_validate.py`

### Validation Commands

- `python scripts/trader_brain_2801_2810_ios_trade_lifecycle_chart_markers_validate.py`
- `npx tsc --noEmit`
- `npm run lint`
- `npx expo export --platform web --clear`
- `python scripts/task_registry_validate.py`

### Source Hashes

Not recorded. This task is frontend implementation, not raw source acquisition.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
