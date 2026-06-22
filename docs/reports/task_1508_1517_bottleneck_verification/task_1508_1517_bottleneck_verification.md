# Task1508-1517 Bottleneck Verification

## Decision Summary

- Verdict: `L5_IS_A_MAJOR_BOTTLENECK_BUT_L2L3_BREADTH_REMAINS_INCOMPLETE`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Conclusion: L5 is a major bottleneck, but not the only bottleneck. L2/L3 has top-end signal; rank breadth still decays after the best few names.

## Quant Expert Report

Rank bucket scheduled-return audit:

| Rank bucket | Count | Avg net return | Median net return | Win rate | <= -20% | >= +20% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `rank_001_003` | 186 | 0.01297724 | 0.02307384 | 0.586022 | 3 | 7 |
| `rank_004_005` | 124 | 0.024146 | 0.02254265 | 0.580645 | 6 | 9 |
| `rank_006_010` | 310 | 0.00261659 | 0.00319281 | 0.509677 | 8 | 8 |
| `rank_011_020` | 620 | 0.00172619 | 0.00071247 | 0.509677 | 19 | 20 |
| `rank_021_050` | 1860 | 0.00817936 | 0.00649929 | 0.530645 | 48 | 71 |

Scheduled-only versus actual L5 replay:

| Policy | Scheduled final | Scheduled MDD | Actual final | Actual MDD | Actual minus scheduled |
| --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_v6_top10_v1` | 1658.2833 | -0.319686 | 1231.8647 | -0.322527 | -426.4186 |
| `semantic_v6_top3_v1` | 1858.5135 | -0.434494 | 1723.1987 | -0.420186 | -135.3148 |
| `semantic_v6_top5_v1` | 2457.5544 | -0.433025 | 1975.4892 | -0.42143 | -482.0652 |


## No-Background Decision-Maker Report

짧게 말하면, L5가 큰 병목인 건 맞다.

하지만 L5만 문제는 아니다.

L2/L3는 상위 3~5개를 고를 때 신호가 있다.

그런데 10개까지 넓히면 잡음이 섞인다.

그리고 L5는 언제 팔지, 언제 버틸지, 몇 개를 들고 갈지 판단이 아직 약하다.

그래서 다음 작업은 L5 entry/hold/exit/replacement를 고치는 게 맞다.

단, L2/L3 rank breadth도 같이 감시해야 한다.

## Artifact Manifest

- `task1509_candidate_scheduled_return_panel.csv`
- `task1510_rank_bucket_return_summary.csv`
- `task1511_selected_l5_delta_panel.csv`
- `task1512_l5_delta_summary.csv`
- `task1513_scheduled_only_replay_trades.csv`
- `task1513_scheduled_only_replay_equity.csv`
- `task1513_scheduled_only_replay_metrics.csv`
- `task1516_bottleneck_verdict.csv`
- `task1517_closeout.json`

Validation commands:

- `python scripts/trader_brain_1508_1517_bottleneck_verification_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
