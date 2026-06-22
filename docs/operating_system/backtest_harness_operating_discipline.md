# Backtest Harness Operating Discipline

## Purpose

This document is mandatory reading before any backtest-related work.

The backtest harness is a validation instrument. It is not a trading system, not a strategy acceptance mechanism, and not a deployment gate.

## End Goal

The harness should eventually verify whether dry adapter inputs derived from candidate bundles can survive a controlled, reproducible, leakage-safe, split/OOS-aware, cost/slippage-stressed replay.

The harness must preserve the full chain:

```text
source evidence
-> economic meaning
-> relationship graph
-> candidate bundle
-> dry adapter input
-> harness input manifest
-> controlled replay plan
-> split/OOS and cost/slippage evidence
-> governance review
```

## Standing Status

```text
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```

No harness artifact can change these statuses by itself.

## Required Inputs

Backtest harness work may only start from explicit repo-native inputs:

- dry adapter input rows
- source graph ids
- candidate bundle ids
- source/evidence ids
- as-of timestamps
- graph packet manifest rows
- replay config ids
- market data source gate rows

## Forbidden Inputs

- inferred lifecycle matches
- symbol/date/price/time proximity fallback
- missing label to negative conversion
- missing raw source approximation
- future price, future label, or future source data
- runtime synthetic SELL rows as broker truth
- GPT/Chrome statements as source-of-truth

## Harness Layers

1. Input manifest layer
   - Declares which dry adapter inputs are under review.
   - Does not imply tradability.

2. Source-time gate
   - Separates source published time, source received time, node asof, edge asof, bundle asof, adapter created time, and future tradable-after time.

3. Market data source gate
   - Declares required market data families.
   - Missing market data blocks replay rather than being approximated.

4. Replay config layer
   - Freezes entry/exit, hold, split, cost, and slippage assumptions.
   - Config is diagnostic until owner-approved.

5. No-execution dry harness
   - Produces run plans and audit summaries only.
   - Does not read prices, generate trades, compute PnL, or call a backtest engine.
   - No price data lookup.
   - No trade generation.
   - No PnL.

6. Split/OOS and cost/slippage plan
   - Must exist before any controlled replay run.
   - A single interval result cannot promote a strategy.

7. Failure decomposition layer
   - Classifies failure by source, graph, timing, market data, cost, slippage, regime, and contradiction.

8. Artifact audit gate
   - Every output row must trace to input id, adapter input id, bundle id, source graph id, config id, and run id.

9. Governance closeout
   - PASS means the named harness check found no regression.
   - PASS does not mean strategy acceptance, deployment readiness, broker truth, backtest validity, source completeness, or real-capital permission.

## Required Backtest Work Read Order

Before any backtest-related task:

1. `docs/operating_system/project_operating_state.md`
2. `docs/operating_system/backtest_harness_operating_discipline.md`
3. Latest relevant task report or file being edited

Open `docs/architecture/test_validation_canonicalization_map.md` before claiming validation status.

Open `docs/architecture/project_status_authority_matrix.md` before any wording that could affect acceptance, deployment, real capital, or readiness.

## Required Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
