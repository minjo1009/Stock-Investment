# OOS Acceptance Harness Contract

## Purpose

The OOS Acceptance Harness is an evaluation-only planning contract for future
walk-forward, out-of-sample, overfit, cost, slippage, and capacity review.

This first pass does not run replay, read prices, generate trades, compute PnL,
promote a strategy, create paper order intent, permit live orders, mutate broker
state, or change deployment status.

## Standing State

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN

## Evaluation Metrics

| Metric | Purpose |
| --- | --- |
| `oos_net_ir` | Out-of-sample net information ratio after cost assumptions. |
| `dsr` | Deflated Sharpe Ratio for multiple-testing adjustment. |
| `pbo` | Probability of backtest overfitting. |
| `threshold_churn` | Sensitivity of decisions near thresholds. |
| `worst_decile_loss` | Tail loss in the weakest decile. |
| `turnover_after_cost` | Turnover cost pressure after explicit cost assumptions. |
| `capacity` | Capacity under liquidity and participation constraints. |

## Required Plan Inputs

- Explicit dry adapter input ids.
- Candidate bundle ids and source graph ids.
- Point-in-time as-of timestamps.
- Market data source gate rows.
- Frozen split definitions.
- Frozen cost and slippage assumptions.
- Frozen parameter family before OOS evaluation.

## Hard Gates

- The harness plan is evaluation-only.
- No single OOS result can accept a strategy.
- No test result can permit deployment or real capital.
- Missing market data or missing raw source evidence blocks evaluation rather
  than being approximated.
- Future returns and outcomes may be used only for evaluation after assignment.
- Evaluation labels must not enter assignment, selection, sizing, or policy
  routing.
- The harness cannot create order intent, paper permission, live permission,
  broker mutation, replay execution, selector mutation, or sizing mutation in
  this first pass.

## Validation Authority

- `GOVERNANCE_HEALTH` for this contract and plan report.
- Future code may add `PACKAGE_HEALTH` only for harness planning utilities that
  do not run replay or compute PnL.
- Any future replay-related validator must preserve the backtest harness
  discipline footer.

PASS means the OOS harness plan boundary is recorded. PASS does not mean
strategy acceptance, deployment readiness, broker truth completion, live-source
readiness, paper-order permission, live-order permission, or real-capital
permission.

