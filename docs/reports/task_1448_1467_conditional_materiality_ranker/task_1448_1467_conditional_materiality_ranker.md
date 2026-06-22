# Task1448-1467 Conditional Materiality Ranker

## Decision Summary

- Verdict: `conditional_materiality_ranker_diagnostic_not_accepted`.
- Best policy: `conditional_materiality_top10_v1`.
- Best final equity: 1096.2926.
- Best CAGR: 0.017973.
- Best MDD: -0.322251.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: high materiality is no longer a standalone bonus. It is gated by event family, small-cap cap, strict expectation, and strict absorption.
- Next action: review v5 displacement audit and acquire true expectation/source-receipt data before any acceptance claim.

## Quant Expert Report

- Data source: Task1428 full-coverage SEC companyfacts denominator panel and Task1318 source evidence.
- Pre-registration: score rules, caps, tie-breakers, and replay policies were fixed before this replay.
- Leakage audit: realized returns appear only in Task1458 audit columns and are not used for assignment.
- Expert review: institutional, sector, and backend reviews are review-only and not source-of-truth.
- Replay setup: top3/top5/top10, entry/exit, cost, benchmark, and universe are unchanged.

Policy metrics:

| Policy | Final | CAGR | MDD | Trades | Source Exit | Price Exit | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `conditional_materiality_top10_v1` | 1096.2926 | 0.017973 | -0.322251 | 620 | 153 | 31 | 0 | 0 | 0 |
| `conditional_materiality_top3_v1` | 816.0934 | -0.038613 | -0.58481 | 186 | 44 | 10 | 0 | 0 | 0 |
| `conditional_materiality_top5_v1` | 1035.7408 | 0.006828 | -0.433406 | 310 | 83 | 16 | 0 | 0 | 0 |

## No-Background Decision-Maker Report

처방은 구현했다.

materiality를 단독 점수에서 조건부 점수로 바꿨다.

결과는 diagnostic이다.

전략은 아직 승인되지 않았다.

## Artifact Manifest

- `task1448_expert_review_synthesis.csv`
- `task1449_v5_preregistered_spec.csv`
- `task1450_event_family_panel.csv`
- `task1453_conditional_materiality_score_panel.csv`
- `task1454_payoff_ranker_v5.csv`
- `task1455_policy_specs.csv`
- `task1456_replay_trades.csv`
- `task1456_replay_equity.csv`
- `task1456_replay_metrics.csv`
- `task1458_displacement_audit.csv`
- `task1459_summary.csv`
- `task1466_acceptance_gate.csv`
- `task1467_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1448_1467_conditional_materiality_ranker_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
