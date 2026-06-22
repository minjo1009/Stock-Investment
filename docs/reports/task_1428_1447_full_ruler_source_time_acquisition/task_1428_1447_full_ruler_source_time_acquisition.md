# Task1428-1447 Full Ruler Source-Time Acquisition

## Decision Summary

- Verdict: `full_ruler_source_time_acquisition_diagnostic_not_accepted`.
- SEC companyfacts unique CIK plan: 280.
- SEC companyfacts successful/cached files: 280.
- Verified denominator rows: 267 -> 3052.
- Materiality source-gap rows: 2933 -> 1713.
- Best policy: `ruler_top3_v1`.
- Best final equity: 2112.7778.
- Best CAGR: 0.155968.
- Best MDD: -0.385207.
- Strategy acceptance status: `NOT_ACCEPTED`.

## Quant Expert Report

- Data source: official SEC companyfacts API plus prior Task1201/1318/1408 artifacts.
- Time rule: each fact can only enter assignment if its `filed` date is at or before `decision_asof_ts`.
- No inferred lifecycle matching, no symbol/date proximity fallback, and no missing data treated as negative evidence.
- Same top3/top5/top10 replay structure was reused to test whether broader ruler coverage changes the result.
- Analyst PIT remains unavailable; non-SEC historical source receipts remain partial.

Policy metrics:

| Policy | Final | CAGR | MDD | Trades | Source Exit | Price Exit | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ruler_top10_v1` | 1313.0893 | 0.054196 | -0.346523 | 620 | 164 | 25 | 0 | 0 | 0 |
| `ruler_top3_v1` | 2112.7778 | 0.155968 | -0.385207 | 186 | 48 | 7 | 1 | 0 | 0 |
| `ruler_top5_v1` | 1252.0887 | 0.044524 | -0.396678 | 310 | 87 | 14 | 0 | 0 | 0 |

## No-Background Decision-Maker Report

필수 정보 전수 확보를 한 단계 진행했다.

핵심은 더 깊은 정보를 새로 실험한 게 아니다.

기존 ruler 구조에 필요한 SEC denominator 정보를 후보 CIK 전수 기준으로 붙였다.

그래도 전략은 아직 승인되지 않았다.

## Artifact Manifest

- `task1428_source_time_schema.csv`
- `task1429_candidate_cik_download_plan.csv`
- `task1430_sec_companyfacts_download_ledger.csv`
- `task1431_source_time_panel.csv`
- `task1432_coverage_comparison.csv`
- `task1446_replay_metrics.csv`
- `task1447_acceptance_gate.csv`
- `task1447_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1428_1447_full_ruler_source_time_acquisition_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
