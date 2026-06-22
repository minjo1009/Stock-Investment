# Task1518-1537 L5 Position Operating Brain

## Decision Summary

- Verdict: `l5_position_operating_brain_implemented_not_accepted`.
- Best policy: `l5_operating_top3_v1`.
- Best final equity: 3081.1967.
- Best CAGR: 0.243648.
- Best MDD: -0.344776.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: L5 now has thesis states, top3/top5 entry gates, hold extension, separated exits, narrow replacement hurdle, cap-only sizing, and delta validation.

## Quant Expert Report

Actual L5 operating replay:

| Policy | Final | CAGR | MDD | Trades | Source exit | Price exit | Hold ext | Beats QQQ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `l5_operating_top3_v1` | 3081.1967 | 0.243648 | -0.344776 | 153 | 19 | 1 | 46 | 1 |
| `l5_operating_top5_v1` | 2239.8962 | 0.169129 | -0.298373 | 192 | 23 | 2 | 57 | 1 |

Scheduled-only versus actual L5 operating delta:

| Policy | Scheduled final | Actual final | Delta final | Scheduled MDD | Actual MDD | Delta positive | MDD improved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `l5_operating_top3_v1` | 1752.1633 | 3081.1967 | 1329.0334 | -0.368348 | -0.344776 | 1 | 1 |
| `l5_operating_top5_v1` | 1585.7106 | 2239.8962 | 654.1856 | -0.303953 | -0.298373 | 1 | 1 |


## No-Background Decision-Maker Report

L5를 단순 exit 규칙에서 포지션 운영 뇌로 바꿨다.

이제 후보마다 thesis 상태를 만든다.

살 후보만 top3/top5 안에서 들어간다.

보유 연장, source exit, price exit, scheduled exit을 분리했다.

비중 확대는 하지 않았다.

아직은 cap-only sizing만 했다.

그래도 전략 승인은 아니다.

## Artifact Manifest

- `task1518_expert_audit.csv`
- `task1519_l5_operating_preregistered_rules.csv`
- `task1520_thesis_state_machine.csv`
- `task1521_entry_gate_panel.csv`
- `task1522_policy_specs_pre_replacement.csv`
- `task1524_replacement_hurdle_panel.csv`
- `task1524_policy_specs_final.csv`
- `task1523_exit_decision_panel.csv`
- `task1525_replay_trades.csv`
- `task1525_replay_equity.csv`
- `task1525_replay_metrics.csv`
- `task1526_scheduled_only_trades.csv`
- `task1526_scheduled_only_equity.csv`
- `task1526_scheduled_only_metrics.csv`
- `task1527_l5_delta_audit.csv`
- `task1527_l5_delta_summary.csv`
- `task1528_summary.csv`
- `task1536_acceptance_gate.csv`
- `task1537_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1518_1537_l5_position_operating_brain_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
