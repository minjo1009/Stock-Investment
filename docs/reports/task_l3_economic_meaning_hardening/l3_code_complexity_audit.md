# L3 Code Complexity Audit

## Decision Summary

Verdict: L3 needs a runtime-owned diagnostic v2 package, but the change should
be staged. This task adds the package and compatibility shims without deleting
historical reports or performing a destructive refactor.

Strategy acceptance status: `NOT_ACCEPTED`.

Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

## Current Responsibility Audit

### `src/backtest/pragmatic_economic_meaning_layer.py`

The incoming task specification identifies this file as the historical location
for much of the Task742 economic interpretation rule logic. In this local
workspace snapshot the file is not present, so this task does not migrate or
edit it. The architectural issue remains valid: economic interpretation rules
belong in runtime brain/L3 contracts when they are used by a runtime decision
stack.

### `src/backtest/build_task742_pragmatic_economic_meaning_layer.py`

The incoming task specification identifies this as the Task742 build runner. In
this local workspace snapshot the file is not present, so this task treats
Task742 as a legacy input format and adds a historical-only wrapper under
`src/brain/l3/adapters/task742_legacy_adapter.py`.

### `src/brain/meaning_adapter.py`

This file was absent in the local workspace and was added as a legacy
compatibility shim. It maps Task742-style rows into `EconomicMeaning` objects.
Its numeric confidence output is explicitly a static weight, not calibrated
probability.

### `src/brain/relation_adapter.py`

This file was absent in the local workspace and was added as a legacy
compatibility shim. It preserves the conservative all-or-nothing behavior where
any legacy `not_ready` meaning produces `BLOCKED_NOT_READY`.

### `src/brain/l2_to_meaning_adapter.py`

This local file already existed. It loads canonical L2 primitive facts through
the L2 store and is the right bridge for runtime L3 input. The new
`src/brain/l3/adapters/l2_primitive_adapter.py` builds on that contract.

## Why Interpretation Should Move To `src/brain/l3`

The L3 layer is the first layer that turns primitive facts into economic
meaning. Keeping that logic in a backtest or research module blurs:

- historical research input versus live source-time certified input
- static confidence versus calibrated probability
- all-or-nothing relation edges versus evidence-edge graph scoring
- diagnostic review states versus trading signals

Runtime-owned contracts make the boundary testable. They also let validators
prove that L3 emits no BUY/SELL, rank, sizing, or order intent.

## Staged Refactor Plan

1. Preserve legacy Task742 adapters and tests.
2. Add `src/brain/l3` contracts, confidence components, source reliability,
   event priors, freshness decay, source gap taxonomy, evidence edges,
   contradiction detection, and graph aggregation.
3. Connect canonical L2 primitive facts into L3 v2 through a diagnostic-only
   adapter.
4. Add validators that enforce static confidence separation and no trade output.
5. Later, migrate historical Task742 economic rules into `src/brain/l3` only
   after the old backtest runner and output manifests are mapped dependency by
   dependency.

## Non-Goals

- No deletion of historical Task reports.
- No strategy acceptance.
- No deployment readiness.
- No paper or live trading permission.
- No broker mutation.
- No large backtest/research refactor in this task.
