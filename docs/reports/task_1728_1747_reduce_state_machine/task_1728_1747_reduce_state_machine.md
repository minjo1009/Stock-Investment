# Task1728-1747 Reduce State Machine

## Decision Summary

- Verdict: `reduce_state_machine_implemented_diagnostic_only`.
- Best policy: `reduce_state_machine_top3_v1`.
- Best final equity: 2278.8662.
- Best CAGR: 0.173043.
- Best MDD: -0.341442.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | Hold | Reduce | Reduce Then Exit | Exit | CAGR Target | MDD Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `reduce_state_machine_top3_v1` | 2278.8662 | 0.173043 | -0.341442 | 3525.2985 | -0.32335 | -1246.4323 | -0.018092 | 160 | 122 | 20 | 17 | 1 | 0 | 0 |
| `reduce_state_machine_top5_v1` | 2076.6931 | 0.152116 | -0.285698 | 2638.334 | -0.286708 | -561.6409 | 0.00101 | 217 | 167 | 25 | 21 | 4 | 0 | 1 |

Split/OOS diagnostics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `reduce_state_machine_top3_v1` | IS_2021_2023 | 1452.8863 | 0.452886 | -0.341442 |
| `reduce_state_machine_top3_v1` | OOS_2024_2026Q1 | 2278.8662 | 1.278866 | -0.144139 |
| `reduce_state_machine_top5_v1` | IS_2021_2023 | 1371.3225 | 0.371322 | -0.285698 |
| `reduce_state_machine_top5_v1` | OOS_2024_2026Q1 | 2076.6931 | 1.076693 | -0.096897 |

Failure / attribution:

- `reduce_state`: hold count=289 pnl= cagr= mdd=
- `reduce_state`: failed_reduce_to_exit count=38 pnl= cagr= mdd=
- `reduce_state`: damage_reduce count=26 pnl= cagr= mdd=
- `reduce_state`: preventive_reduce count=19 pnl= cagr= mdd=
- `reduce_state`: direct_exit count=5 pnl= cagr= mdd=
- `runtime_action`: hold count=289 pnl= cagr= mdd=
- `runtime_action`: reduce count=45 pnl= cagr= mdd=
- `runtime_action`: reduce_then_exit count=38 pnl= cagr= mdd=
- `runtime_action`: exit count=5 pnl= cagr= mdd=
- `action_pnl`: exit count=5 pnl=-125.4536 cagr= mdd=
- `action_pnl`: hold count=289 pnl=5221.0519 cagr= mdd=
- `action_pnl`: reduce count=45 pnl=-936.2924 cagr= mdd=
- `action_pnl`: reduce_then_exit count=38 pnl=-1803.7468 cagr= mdd=
- `target_failure`: reduce_state_machine_top3_v1 count= pnl= cagr=0.173043 mdd=-0.341442
- `target_failure`: reduce_state_machine_top5_v1 count= pnl= cagr=0.152116 mdd=-0.285698

## No-Background Decision-Maker Report

1. Reduce is now a state machine, not a weaker exit.
2. The machine can reduce early, reduce after damage, or exit remaining exposure if recovery fails.
3. This tests the user's core diagnosis: late/weak reduce was a direct cause of drawdown.
4. The replay is diagnostic only and does not approve strategy.

## Artifact Manifest

- `task1728_expert_review.csv`
- `task1729_reduce_contract.csv`
- `task1730_reduce_state_panel.csv`
- `task1731_reduce_state_replay_trades.csv/equity`
- `task1732_reduce_state_replay_metrics.csv`
- `task1733_split_oos_metrics.csv`
- `task1734_failure_attribution.csv`
- `task1746_acceptance_gate.csv`
- `task1747_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1728_1747_reduce_state_machine_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```