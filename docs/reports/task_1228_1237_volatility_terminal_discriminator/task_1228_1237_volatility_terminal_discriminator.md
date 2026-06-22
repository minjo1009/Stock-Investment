# Task1228-1237 Volatility Terminal Discriminator

## Decision Summary

- Verdict: `volatility_terminal_discriminator_executed_not_accepted`.
- Final equity: 2019.1196.
- CAGR: 0.145856.
- MDD: -0.367558.
- Beats Task1201 slot5: 1.
- Beats QQQ: 1.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task replaces the broad volatility penalty with a prior-knowable discriminator.

Routing:

| Route | Rows |
| --- | ---: |
| `high_vol_upside` | 39 |
| `mixed_transition` | 2 |
| `ordinary_pass` | 268 |
| `product_sleeve` | 1 |

Key rules:

- High volatility alone is never a terminal-risk signal.
- High volatility with positive 126d/252d momentum and adequate liquidity routes to `high_vol_upside`.
- Terminal/collapse risk requires multiple independent distress signs.
- Product-sleeve rows are allowed but separated.

Leakage boundary:

- 2026Q1 returns and collapse labels are not used for assignment.
- PnL, net return, exit reason, and post-entry prices are not used for L0-L3 routing.
- Post-entry prices are used only by L5 exit simulation.

## No-Background Decision-Maker Report

We stopped treating volatility itself as bad.

The brain now tries to separate exciting volatility from survival-risk volatility.

This is still diagnostic only.

## Artifact Manifest

- `task1228_source_catalog.csv`
- `task1229_l0_instrument_gate.csv`
- `task1230_l1_prior_knowable_signals.csv`
- `task1231_l2_volatility_terminal_discriminator.csv`
- `task1232_l3_route_edges.csv`
- `task1233_policy_specs.csv`
- `task1234_replay_trades.csv`
- `task1234_replay_equity.csv`
- `task1234_replay_metrics.csv`
- `task1235_route_distribution.csv`
- `task1236_acceptance_gate.csv`
- `task1237_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1228_1237_volatility_terminal_discriminator_validate.py`
- `python -m unittest tests.test_trader_brain_1228_1237_volatility_terminal_discriminator`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
