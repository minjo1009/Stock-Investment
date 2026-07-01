# TASK-4166 L0-L4 Operational Linkage Hardening

## Summary

TASK-4166 fixed the current L0-L4 operational and handoff issues found after the public newswire runtime cutover.

Main result:

- L0 reliability alerts are now `0`.
- Daily bars are treated as request-complete `100.0%`, while the `74` empty-provider symbols stay visible as quality metadata.
- Public newswire operational status now reads the sharded launcher and no longer reports the legacy lane as stopped.
- L3 and L4 were rebuilt from the current L1/L2 wide artifacts.
- L3 now consumes previously unrepresented L2 wide candidates as diagnostic proto relation/coverage rows instead of silently leaving them outside the graph surface.
- L4 now packages the expanded L3 output as diagnostic draft bundles, still with all trading authority closed.

## What Changed

| Area | Before | After |
|---|---|---|
| Newswire operational alert | `public_newswire_backfill` could be reported stopped because status readers used the legacy monolithic path | status/audit use `l0_public_newswire_backfill_shards` PID and aggregate |
| Daily bar completion | status was overwritten by raw CSV file count `11966 / 12040`, producing `99.3854%` and incomplete alert | request units stay `12040 / 12040`, progress `100.0%`; raw CSV coverage and empty-provider units are separate fields |
| L3 latest L1/L2 linkage | manifest hash could be stale after L1/L2 wide handoff regeneration | L3 rebuilt and current L1/L2 hashes match |
| L3 relation quality | L3 mostly used pre-existing `l3_meanings`; new L2 wide candidates were not broadly visible | unrepresented L2 wide candidates become `SOURCE_EVENT_CLUSTER`, `MACRO_FACTOR`, or explicit `COVERAGE_GAP` rows |
| L4 draft quality | L4 reflected the older L3 graph surface | L4 rebuilt from expanded L3 with blockers preserved |

## Current State

| Layer | State | Notes |
|---|---|---|
| L0 | Operationally cleaner | no current P0/P1 reliability alerts |
| L1 | Current wide handoff active | latest L1 wide rows are consumed by L3/L4 manifests |
| L2 | Current wide candidates active | latest L2 wide candidates are consumed by L3/L4 manifests |
| L3 | Expanded diagnostic relation graph | `11,079` graphs, `17,276` edges, `4,627` coverage gaps |
| L4 | Expanded diagnostic thesis draft package | `11,079` bundles, `17,276` evidence links, `52,311` blockers |

## L0 Details

| Lane | Status | Evidence |
|---|---|---|
| daily | COMPLETE | `12040 / 12040`, progress `100.0%` |
| five_min | RUNNING | progress `28.8964%` |
| public_context_news_backfill | RUNNING | progress `99.3333%` |
| public_newswire_backfill | RUNNING | sharded PID `16236`, progress `52.5482%` |
| public_market_macro_news_backfill | RUNNING | progress `64.9276%` |

The daily lane still records `11966` raw CSV files and `74` empty provider responses. This is not hidden. The operational fix is that empty-provider responses no longer make the completed request lane look incomplete.

## L3 Details

| Metric | Before | After |
|---|---:|---:|
| relation edges | 7,150 | 17,276 |
| event clusters | 1,850 | 6,913 |
| relation graphs | 5,398 | 11,079 |
| coverage gaps | 181 | 4,627 |

Coverage gaps by reason:

| Reason | Count |
|---|---:|
| `L2_BLOCKED_CANDIDATES_PRESENT` | 3,999 |
| `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE` | 181 |
| `NEWSWIRE_RECALL_REVIEW_ENTITY_FEATURE_PENDING` | 447 |

These are blockers/unknowns, not negative evidence.

## L4 Details

| Metric | Value |
|---|---:|
| thesis bundles | 11,079 |
| evidence links | 17,276 |
| blockers | 52,311 |
| `DRAFT_MIXED` bundles | 11,076 |
| `DRAFT_BLOCKED` bundles | 3 |

L4 remains a diagnostic thesis packaging layer. It is not a final thesis engine and not a trading decision layer.

## Safety

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Trading authority opened: `0`
- Paper/live/broker/order opened: `0`

## Remaining Work

| Priority | Item | Meaning |
|---:|---|---|
| P0 | Keep L0 backfills running | BusinessWire, PRNewswire, market/macro, 5m still need more coverage |
| P1 | Convert more newswire review rows into entity-level L2 features | Current L3 now exposes the pending rows, but does not solve entity mapping itself |
| P1 | Add contradiction relation scan | L4 still correctly blocks final thesis interpretation because contradiction scan is not implemented |
| P1 | Improve source-specific L3 relation families | `MACRO_SECTOR`, `SECTOR_THEME`, and richer entity relation families remain future work |
