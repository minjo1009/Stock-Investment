# TASK-4165 L0 Newswire Failed Recovery and Sharded Runtime Cutover

## Summary

TASK-4165 recovered the remaining public newswire hard failures and cut the active L0/L1/L2 path over to the sharded public newswire runtime.

The important result is simple:

- public newswire hard failed units are now `0`.
- GlobeNewswire historical units are complete: `126 / 126`.
- PRNewswire no longer fails on truncated gzip payloads; large PRNewswire sitemap handling now uses a higher sharded max-bytes budget.
- the legacy monolithic public newswire runtime is not restarted by the worker recovery script.
- L1/L2 wide handoff now reads sharded public newswire event ledgers and recall overlays.
- TASK-4146 L0-L2 validator now passes with the sharded newswire launcher as the canonical runtime proof.

All trading gates stayed closed:

- strategy: `NOT_ACCEPTED`
- deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- real capital: `FORBIDDEN`
- broker mutation: `0`
- live order: `0`
- paper promotion: `0`

## What Changed

| Area | Before | After |
|---|---|---|
| Failed newswire units | failed shards remained in aggregate | hard failed units reduced to `0` |
| GlobeNewswire failed shards | partial/failed historical months | recovered and completed |
| PRNewswire failed shard | 2016-10 gzip sitemap could fail due default 3MB payload read | sharded launcher and recovery support source-specific `max_bytes`, PRNewswire set to `50MB` |
| Empty/parse failure handling | truncated gzip parse could look like empty/no rows | collector marks retryable sitemap parse failure instead of treating it as a valid empty archive |
| L0 official runtime | old monolithic and new sharded paths could be confused | sharded launcher under `l0_public_newswire_backfill_shards` is canonical |
| Recovery supervisor | legacy monolithic public newswire could be restarted | public newswire removed from legacy recovery lanes |
| L1/L2 handoff | mostly read legacy event path and legacy PID evidence | reads sharded event ledgers, recall overlays, and sharded launcher PID evidence |
| Validator | TASK-4146 validator treated dead legacy newswire PID as critical | validator passes because handoff now reports the sharded launcher PID |

## Recovery Result

| Source | Shards Attempted | Completed | Partial/Pending | Failed |
|---|---:|---:|---:|---:|
| GlobeNewswire | 10 | 10 | 0 | 0 |
| PRNewswire | 1 | 0 | 1 | 0 |
| Total | 11 | 10 | 1 | 0 |

PRNewswire 2016-10 is not a hard failure now. It is pending/partial and is handled by the running sharded launcher with `prnewswire=50000000` source max bytes.

## Current Newswire Aggregate

Latest checked aggregate:

| Metric | Value |
|---|---:|
| status | RUNNING |
| progress_pct | 52.3287 |
| completed_units | 2146 / 4101 |
| pending_units | 1955 |
| failed_units | 0 |
| partial_units | 64 |
| row_count | 727672 |

By source:

| Source | Completed | Pending | Failed | Partial | Rows |
|---|---:|---:|---:|---:|---:|
| BusinessWire | 2004 / 3834 | 1830 | 0 | 53 | 44178 |
| GlobeNewswire | 126 / 126 | 0 | 0 | 0 | 640970 |
| PRNewswire | 16 / 141 | 125 | 0 | 11 | 42524 |

## L1/L2 Handoff Result

TASK-4146 wide handoff validator passes after this cutover.

| Metric | Value |
|---|---:|
| L0 batch rows | 10401 |
| L1 packet rows | 10401 |
| L1 ready packet rows | 5982 |
| L2 rows | 10401 |
| L2 admitted/review rows | 5982 |
| feature candidate materialization rows | 5982 |
| trading authority opened | 0 |
| paper/live/broker/order opened | 0 |

Public newswire handoff:

| Metric | Value |
|---|---:|
| L0 batch rows | 5718 |
| raw item rows reported | 727357 |
| L1 ready packet rows | 4616 |
| L2 admitted/review rows | 4616 |
| feature candidate materialization rows | 4616 |

## Notes

The 5-minute bar mismatch discussed during the task was not a data mismatch. The issue was that older status readers could inspect `background_process.json` instead of the official 5-minute status path `background_process_5m.json`. Current evidence shows the 5-minute lane is running with PID `34128`, progress `28.6283%`, and `79,836,057` rows written.

## Remaining Work

| Item | Status | Meaning |
|---|---|---|
| BusinessWire backfill | RUNNING | still the largest remaining L0 newswire backfill body |
| PRNewswire monthly backfill | RUNNING | partial months are being continued by sharded runtime |
| 5-minute bars | RUNNING | long-running L0 backfill, separate from newswire |
| Full L0 completion proof | NOT YET | requires remaining pending units to finish |

No L1/L2/L3/L4 signal or trading authority was opened in this task.
