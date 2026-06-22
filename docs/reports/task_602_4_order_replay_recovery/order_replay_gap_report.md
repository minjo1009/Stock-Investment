# T602-4 Order Replay Gap Report

## Decision Summary

- Verdict: STRETCH
- Strategy acceptance status: NOT_ACCEPTED
- Key metrics:
- Decision Match: 952/952 match_rate=1.0 status=PASS
- Order Match: 54/54 match_rate=1.0 status=STRETCH
- Fill Match: 48/48 match_rate=1.0 status=PASS
- Position Match: 23/24 match_rate=0.958333 status=STRETCH
- What changed: Order Match now evaluates exact order row reconstruction by order_id/run_id/status evidence, not decision lineage presence.
- Next action: governance review and registry update by the allowed owner after write-scope release.

## Current Match

- Decision Match: 952/952 match_rate=1.0 status=PASS
- Order Match: 54/54 match_rate=1.0 status=STRETCH
- Fill Match: 48/48 match_rate=1.0 status=PASS
- Position Match: 23/24 match_rate=0.958333 status=STRETCH

## Gap Breakdown

- Order rows: 54
- Order mismatch rows after exact order_id recovery: 0
- Decision lineage missing rows: 6
- BUY cancel/unknown ORDER_NOT_FOUND rows: 6
- Runtime SELL rows with intent_key: 23
- Rows with exact fill.order_id evidence: 48

## Root Cause

The prior Order Match calculation treated missing decision lineage (`intent_key`) as an Order Match failure. The six known gap rows are exact runtime order rows with order_id, run_id, status, raw_status, and environment evidence in `orders`; they are Decision lineage gaps, not missing order rows.

## Fix Applied

- Runtime orders with existing order_id are reconstructed by exact order_id/run_id/status evidence.
- Missing intent_key rows remain visible in `order_replay_diff.csv` as `Decision lineage missing`.
- Fill/order linkage uses exact `fill.order_id -> order.order_id` only.
- No symbol/date/price/time proximity fallback is used.

## Acceptance Impact

- Order acceptance status: STRETCH
- Order match rate: 1.0
- T602-4 target achieved if order_match_rate > 0.95; current result is above that threshold.
- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY until governance and broker-truth gates are complete.

## Quant Expert Report

- Data source and source readiness: `orders`, `fills`, `position_lifecycle`, `runtime_strategy_decisions`, and optional `paper_order_execution_events` from `trading.db`.
- Exact join keys: `orders.order_id`, `orders.run_id`, `fills.order_id`, `position_lifecycle.entry_order_id`, `position_lifecycle.exit_order_id`.
- Leakage audit: labels/outcomes are not used in order assignment logic.
- Split/OOS metrics: not applicable; this is replay infrastructure recovery, not strategy validation.
- Failure decomposition: remaining order-layer gap is lineage metadata only, recorded separately from Order Match.
- Cost/slippage stress: not applicable because no PnL claim changed.
- Remaining blockers: registry/readiness updates are outside the user-approved write scope.

## No-Background Decision-Maker Report

Order replay was failing because six cancelled or unknown orders had no decision lineage key. Those orders still exist as exact runtime order records, so the order layer can now account for them without inventing a decision match.

This improves replay diagnostics but does not make the strategy deployable. The next plain-language step is governance review of the exact-ID recovery packet.

## Artifact Manifest

See `artifact_manifest.csv`.
