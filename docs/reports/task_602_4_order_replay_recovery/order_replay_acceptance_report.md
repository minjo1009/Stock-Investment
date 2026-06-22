# T602-4 Order Replay Acceptance Report

## Decision Summary

- Verdict: STRETCH
- Strategy acceptance status: NOT_ACCEPTED
- Key metrics: order_match_rate=1.0, decision_match_rate=1.0, fill_match_rate=1.0, position_match_rate=0.958333
- What changed: exact order row reconstruction is separated from decision lineage completeness.
- Next action: update registry/readiness documents when write scope permits.

## Current Match

- Decision Match: 952/952 match_rate=1.0 status=PASS
- Order Match: 54/54 match_rate=1.0 status=STRETCH
- Fill Match: 48/48 match_rate=1.0 status=PASS
- Position Match: 23/24 match_rate=0.958333 status=STRETCH

## Gap Breakdown

- Decision lineage missing rows: 6
- Order mismatch rows: 0
- Cancel/unknown ORDER_NOT_FOUND rows tracked as lineage gaps: 6

## Root Cause

Order Match was previously coupled to `intent_key`. That made missing Decision lineage look like missing order replay, even when exact order rows existed in `orders`.

## Fix Applied

The validator now scores Order Match from exact order row reconstruction using order_id, run_id, and lifecycle/order status evidence. `intent_key` absence is reported but does not become an inferred decision match or a proximity fallback.

## Acceptance Impact

- T602-4 acceptance threshold: PASS if order_match_rate > 0.95, STRETCH if > 0.99, FAIL if < 0.90.
- Current order_match_rate: 1.0.
- Current order status: STRETCH.
- Inferred matching used: 0.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Deployment status remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.

## Quant Expert Report

- Data source and source readiness: current runtime SQLite tables only.
- Exact join keys: exact order_id/run_id/status for Order Match and exact order_id for fill links.
- Leakage audit: outcomes and labels are evaluation-only and not used in reconstruction.
- Split/OOS metrics: not applicable for replay recovery.
- Failure decomposition: no order row mismatch remains; six Decision lineage gaps remain visible.
- Cost/slippage stress: not applicable.
- Remaining blockers: operating registry/readiness updates are required but excluded by write scope.

## No-Background Decision-Maker Report

The order layer now replays the runtime order table itself. The six old problem rows are still imperfect because they lack decision lineage, but they are no longer lost as orders.

This is a replay infrastructure improvement, not a capital deployment approval.

## Artifact Manifest

See `artifact_manifest.csv`.
