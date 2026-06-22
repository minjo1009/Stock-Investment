# Task 086 — Paper Pilot Sample Accumulation Plan

## 1. Purpose

Paper Pilot PASS 판정에 필요한 최소 표본과 운영 판정 기준을 고정한다.  
핵심은 성과 개선이 아니라 운영 안정성 검증이며, 최소 샘플 미달 상태에서는 PASS를 금지한다.

## 2. Execution Schedule

- US market open session only
- 1~2 runs per trading day
- avoid first 5 minutes after market open
- avoid last 10 minutes before market close
- run for minimum 5 trading days

## 3. Minimum Sample Requirements

PASS 판단 전 최소 기준:

- minimum_trading_days: `5`
- minimum_order_attempts: `10`
- minimum_filled_orders: `5`
- minimum_cancel_events: `1`
- minimum_eod_reviews: `5`
- minimum_reconciliation_checks: `5`

## 4. Metrics to Track

반드시 추적:

- order attempts
- submitted orders
- filled orders
- cancelled orders
- partial fills
- late fills
- UNKNOWN events
- reconciliation mismatch
- average slippage
- max slippage
- fill rate
- cancel success rate
- timeout rate
- realized PnL
- paper PF
- paper MDD

## 5. PASS / WARNING / FAIL Rules

PASS:

- UNKNOWN events = 0
- reconciliation critical = 0
- cancel success rate = 100% for observed cancel events
- fill rate within acceptable range
- average slippage within expected range
- no daily loss breach
- all EOD reviews completed

WARNING:

- sample size insufficient
- minor non-critical mismatch
- slippage drift but no halt condition
- no cancel sample observed yet

FAIL:

- UNKNOWN event occurs
- reconciliation critical mismatch
- unresolved late fill
- cancel loop fails
- broker/local position mismatch
- market order path triggered
- daily loss breached

## 6. Backtest vs Paper Reality Gap

비교 기준:

- S4 backtest PF: `1.6989`
- S4 backtest Sharpe: `1.1402`
- S4 backtest MDD: `1,071.44`
- Paper metrics are diagnostic only until sample size is met

## 7. Re-run Command

```powershell
$env:PYTHONPATH="src"
python -m app.task_085_paper_pilot --run-paper --json-out docs/reports/task_085/task_085_paper_pilot.json --md-out docs/reports/task_085/task_085_paper_pilot.md
```

## 8. Final Decision Framework

- Before minimum sample: cannot be PASS
- After minimum sample:
  - PASS -> consider ultra-small live dry-cap test
  - WARNING -> continue paper sample
  - FAIL -> halt and fix operational defect

