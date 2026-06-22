# Task1248-1257 Raw Text Policy Replay

## Decision Summary

- Verdict: `raw_text_policy_replay_executed_not_accepted`.
- Best policy: `raw_text_shadow_only_slot5_v1`.
- Best final equity: 2019.1196.
- Best CAGR: 0.145856.
- Best MDD: -0.367558.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task preregistered four raw-text route policies and replayed them over the Task1201 slot5 path.

| Policy | Final | CAGR | MDD | Beats QQQ | Beats Task1228 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `raw_text_balanced_risk_slot5_v1` | 1916.197 | 0.134299 | -0.345812 | 1 | 0 |
| `raw_text_shadow_only_slot5_v1` | 2019.1196 | 0.145856 | -0.367558 | 1 | 0 |
| `raw_text_strict_exit_slot5_v1` | 1696.6341 | 0.107864 | -0.292108 | 0 | 0 |
| `raw_text_watch_only_slot5_v1` | 1937.7027 | 0.136754 | -0.392374 | 1 | 0 |

Leakage audit:

- L1/L2 raw terminal routes came from Task1238-1247 as-of evidence.
- Future return, PnL, and realized outcome columns are not used for assignment.
- Post-entry prices are used only inside L5 exit simulation.

Remaining blockers:

- Results are diagnostic only.
- Source extractor is SEC-only and still lacks official exchange deficiency event feeds and non-SEC dynamic sources.
- Policy promotion requires route-level manual review before any broader replay.

## No-Background Decision-Maker Report

We let the brain trade with the new raw filing-text risk layer.

The result shows whether this evidence helps or hurts compared with the prior volatility-terminal replay.

This does not make the strategy accepted.

## Artifact Manifest

- `task1248_policy_catalog.csv`
- `task1249_policy_specs.csv`
- `task1250_replay_trades.csv`
- `task1251_replay_equity.csv`
- `task1252_replay_metrics.csv`
- `task1253_route_attribution.csv`
- `task1254_acceptance_gate.csv`
- `task1255_expert_closeout.csv`
- `task1257_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1248_1257_raw_text_policy_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1248_1257_raw_text_policy_replay`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
