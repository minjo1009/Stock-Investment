# Task868 Next Data Tasks

## Decision Summary

- Verdict: completed.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Next required tasks: calendar, corporate actions, PIT universe or explicit harness universe, 15m normalization, and trade-spec bridge.

## Quant Expert Report

Next tasks should be executed in this order:

1. Task870: certified exchange calendar `2021-01-01` through latest completed session plus forward buffer.
2. Task871: corporate actions for certified replay symbols.
3. Task872: explicit harness universe or point-in-time universe policy.
4. Task873: 15m schema normalization and regular-hours filtering.
5. Task874: controlled trade-spec contract from adapter input to replay row.
6. Task875: gate-aware controlled replay retry with QQQ benchmark.

## No-Background Decision-Maker Report

The next move is not “download more everything.” It is five named blockers in order.

## Artifact Manifest

- Output: this report and `post_attempt_gap_diagnosis.csv`.
- Validation command: `python scripts/trader_brain_860_869_backtest_cycle_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`

