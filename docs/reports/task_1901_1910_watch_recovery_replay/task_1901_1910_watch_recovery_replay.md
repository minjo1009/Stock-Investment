# Task1901-1910 Watch Recovery Replay

## Decision Summary

- Verdict: `watch_recovery_replay_complete_target_not_met`.
- Best policy: `watch_recovery_top3_v1`.
- Best final equity: 3256.0927.
- Best CAGR: 0.257024.
- Best MDD: -0.240886.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Replay contract:

- Only `normal_winner_volatility_watch` and `upgrade_candidate_watch` are restored to full or near-full hold.
- `damage_watch`, `information_gap_watch`, and `overhang_watch` remain unchanged from Task1878-1885.
- Replay uses prior controlled winner-defense trade returns only; no new price matching.
- PnL, drawdown, and return fields are audit-only.

| Policy | Final | CAGR | MDD | Desk Final | Delta vs Desk | Base Final | Delta vs Base | Trades | Joint Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `watch_recovery_top3_v1` | 3256.0927 | 0.257024 | -0.240886 | 3204.0915 | 52.0012 | 3944.5457 | -688.453 | 156 | 0 |
| `watch_recovery_top5_v1` | 2461.6248 | 0.190709 | -0.176857 | 2476.2303 | -14.6055 | 2822.4123 | -360.7875 | 206 | 0 |

Split/OOS metrics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `watch_recovery_top3_v1` | IS_2021_2023 | 1668.9401 | 0.66894 | -0.240886 |
| `watch_recovery_top3_v1` | OOS_2024_2026Q1 | 3256.0927 | 2.256093 | -0.163644 |
| `watch_recovery_top5_v1` | IS_2021_2023 | 1477.9078 | 0.477908 | -0.176857 |
| `watch_recovery_top5_v1` | OOS_2024_2026Q1 | 2461.6248 | 1.461625 | -0.109733 |

Cost/slippage stress:

| Policy | Cost bps | Stressed Final | Beats QQQ |
| --- | ---: | ---: | ---: |
| `watch_recovery_top3_v1` | 0 | 3256.0927 | 1 |
| `watch_recovery_top3_v1` | 25 | 2811.636 | 1 |
| `watch_recovery_top3_v1` | 50 | 2367.1794 | 1 |
| `watch_recovery_top3_v1` | 100 | 1478.2661 | 0 |
| `watch_recovery_top5_v1` | 0 | 2461.6248 | 1 |
| `watch_recovery_top5_v1` | 25 | 2017.9169 | 1 |
| `watch_recovery_top5_v1` | 50 | 1574.2091 | 0 |
| `watch_recovery_top5_v1` | 100 | 686.7933 | 0 |

## No-Background Decision-Maker Report

1. We tested only the 36 good-watch candidates.
2. Damage-watch names stayed defensive.
3. This is still diagnostic, not live approval.
4. If CAGR improves but MDD explodes, the recovery rule is not good enough.

## Artifact Manifest

- `task1901_input_manifest.csv`
- `task1902_frozen_policy_config.csv`
- `task1903_recovery_candidate_audit.csv`
- `task1904_watch_recovery_budget.csv`
- `task1905_watch_recovery_replay_trades.csv/equity`
- `task1906_watch_recovery_metrics.csv/split_oos`
- `task1907_cost_stress_metrics.csv`
- `task1908_failure_attribution.csv`
- `task1909_acceptance_gate.csv`
- `task1910_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1901_1910_watch_recovery_replay_validate.py`
- `python scripts/task_registry_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```