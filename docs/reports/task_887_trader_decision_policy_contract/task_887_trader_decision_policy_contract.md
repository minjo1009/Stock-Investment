# Task887 Trader Decision Policy Contract

## Decision Summary

- Verdict: planned.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: define the first explicit Trader Brain decision policy for historical replay.

## Quant Expert Report

Allowed decision states:

- `skip`
- `watch`
- `reduce`
- `activate`

Allowed sizing states:

- `zero`
- `small`
- `normal`
- `capped`

Policy must be based on graph state, contradiction state, theme state, uncertainty, and pre-entry price context. It cannot use realized future performance.

Policy freeze requirements before OOS:

- `policy_version`
- rebalance clock
- hold or exit rule
- max gross exposure
- max theme exposure
- max symbol exposure
- cost model id
- slippage model id
- contradiction handling rule
- source-gap handling rule

`reduce` is allowed only when an existing open position is present. A flat portfolio cannot create a synthetic SELL through `reduce`.

## No-Background Decision-Maker Report

This is the missing trader judgment layer. It decides whether a thesis is worth acting on and how much exposure is allowed.

## Artifact Manifest

- Planned output: `trader_decision_policy_contract.csv`.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
