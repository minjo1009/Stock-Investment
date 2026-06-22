# Task1358-1377 Trader Judgment Core Recovery

## Decision Summary

- Verdict: `trader_judgment_core_recovery_implemented_diagnostic_not_accepted`.
- Best policy: `payoff_core_top5_v1`.
- Best final equity: 1930.9623.
- Best CAGR: 0.135987.
- Best MDD: -0.349072.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: materiality, surprise/expectation proxy, source independence, mechanism edges, payoff rank, replacement audit, split freeze, overfit guard, and limited dynamic exit receipt were implemented.
- Next action: replace proxy surprise with PIT analyst/estimate data and expand dynamic exit beyond hard SEC events.

## Quant Expert Report

- Data source and source readiness: Task1318 full-candidate source evidence, Task1201 trade specs/price gates, SEC submissions metadata for post-entry hard-event receipt.
- Exact join keys: `candidate_source_id`, `trade_spec_id`, `decision_asof_ts`, `evidence_id`.
- Leakage audit: L2-L4 assignment does not use future return, realized PnL, or exit price. Replacement outcome rows are marked audit-only. L5 dynamic exits use only post-entry SEC filing receipt before execution date.
- Split/OOS metrics: split calendar is frozen into train 2021-2023, validation 2024, OOS 2025-2026Q1. OOS tuning is blocked.
- Failure decomposition: analyst PIT, customer confirmation, and true expectation surprise remain gaps.
- Cost/slippage stress: round-trip cost remains 20.0 bps.

Policy metrics:

| Policy | Final | CAGR | MDD | Beats Baseline | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `payoff_core_top10_v1` | 1660.2374 | 0.103219 | -0.258405 | 1 | 0 | 0 | 1 |
| `payoff_core_top5_v1` | 1930.9623 | 0.135987 | -0.349072 | 0 | 1 | 0 | 0 |
| `payoff_hurdle_top10_v1` | 1501.3395 | 0.081921 | -0.287977 | 1 | 0 | 0 | 1 |

## No-Background Decision-Maker Report

We restored the missing trader-judgment core as a diagnostic layer.

It now asks whether an event is material, fresh, independently confirmed, and tied to a payoff path.

The replay still does not approve the strategy.

## Artifact Manifest

- `task1358_core_requirement_map.csv`
- `task1359_split_freeze.csv`
- `task1360_replacement_pair_audit.csv`
- `task1361_l2_materiality_surprise_primitives.csv`
- `task1362_l3_mechanism_edges.csv`
- `task1363_l4_payoff_rank_panel.csv`
- `task1364_l5_dynamic_exit_receipts.csv`
- `task1365_overfit_guard_ledger.csv`
- `task1366_policy_catalog.csv`
- `task1367_l5_policy_specs.csv`
- `task1368_replay_trades.csv`
- `task1369_replay_equity.csv`
- `task1370_replay_metrics.csv`
- `task1372_acceptance_gate.csv`
- `task1377_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1358_1377_trader_judgment_core_recovery_validate.py`
- `python -m unittest tests.test_trader_brain_1358_1377_trader_judgment_core_recovery`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
