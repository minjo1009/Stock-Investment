# Future Backtest Gate Contract

This contract defines what must be true before the Trader Brain research contracts can be connected to a future backtest. It does not execute a backtest.

## Current Status

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- Backtest execution from Task771: `NOT_EXECUTED`

## Required Before Any Future Backtest

1. Contract validation must pass for Task757 through Task771.
2. L1 source evidence must not jump directly to buy/sell/rank/sizing/backtest eligibility.
3. Primitive facts must remain source-local and non-directional.
4. Meaning direction hints must remain review metadata, not trade instructions.
5. Relation edges must not emit score, rank, or action.
6. Modifiers must not create candidates alone.
7. Compound interaction must emit `compound_state` only.
8. Candidate bundles must remain explanatory objects.
9. Same-timestamp slot comparison must not use global top5 rank or future PnL.
10. Resolver must not use GPT-only resolution, silent default pass, missing-to-negative, or future data.
11. Brain validation must detect layer jumps, forbidden outputs, missing-to-negative, and outcome leakage.
12. The engine strategy adapter and shell split lane must be separately completed before any production-like replay claim.
13. Any future backtest must have an explicit new task id, artifact manifest, leakage audit, OOS/split plan, cost/slippage plan, and QQQ/Task639 comparison plan.

## Forbidden At This Gate

- No buy/sell decision.
- No rank or score.
- No sizing or allocation.
- No actual slot selection.
- No backtest eligibility from contract success alone.
- No strategy acceptance.
- No deployment readiness.
- No broker or real-capital permission.

## Gate Output

The only allowed Task771 gate output is:

```text
future_backtest_gate_defined_not_executed
```

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
