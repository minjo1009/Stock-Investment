# TASK-4200 L0 Public Newswire Backfill Progress Hardening

## Conclusion

The overnight public newswire backfill did run, but it was still structurally slow. The main reason was not that the launcher was dead. The launcher was alive, but large BusinessWire monthly shards and short worker runtime caused active work to be recycled before it could become completed-unit progress.

TASK-4200 changed the existing L0 files so the current runtime uses smaller BusinessWire day shards, longer source-specific runtime budgets, active-progress-aware recycle logic, and completed-unit stall telemetry.

This is real L0 runtime hardening, not a backfill completion claim. L0 public newswire remains incomplete and must continue to block downstream completeness claims.

## What Changed

| Area | Before | After |
|---|---|---|
| BusinessWire shard size | Monthly shard could be too large to complete before recycle. | Day shard mode is implemented and active in current launcher config. |
| Worker max runtime | 30-minute timeout could kill active work. | BusinessWire runtime is 14,400 seconds and PRNewswire runtime is 21,600 seconds in the guard-launched config. |
| Recycle logic | Max runtime was too close to a hard kill. | If progress is still active, max runtime is extended and stale recycle remains separate. |
| Supervisor health | Process alive check was stronger than completed-unit progress check. | Supervisor records completed-unit delta and a 30-minute stall threshold. |
| Runtime handoff | Old launcher could keep running stale config. | Guard restarts stale launcher config and starts the current day-shard config. |

## Current Runtime Evidence

| Item | Value |
|---|---|
| Active launcher PID | 28924 |
| Active launcher task owner | TASK-4195 guard runtime |
| BusinessWire shard granularity | day |
| Concurrency | 5 |
| Source lanes | businesswire=4, prnewswire=1 |
| BusinessWire max worker seconds | 14400 |
| PRNewswire max worker seconds | 21600 |
| Diagnostic only | true |
| Trade authority | false |
| Broker mutation permitted | false |
| Real capital permitted | false |

## Current Progress Snapshot

| Metric | Value |
|---|---:|
| Status | RUNNING |
| Progress | 59.2704% |
| Completed units | 2356 |
| Pending units | 1619 |
| Partial units | 15 |
| Failed units | 0 |
| Total units | 3975 |
| BusinessWire pending units | 1494 |
| PRNewswire pending units | 125 |

## Residual Blockers

| Blocker | Meaning | Required Follow-Up |
|---|---|---|
| L0_PUBLIC_NEWSWIRE_INCOMPLETE | Public newswire backfill is still not complete. | Let current runtime continue and monitor completed-unit deltas. |
| L0_STALE_WORKERS_PRESENT | Some prior worker state still appears stale in L0 status. | Keep validator and supervisor checks active; do not treat as completed until cleaned by runtime or explicit terminal status. |
| PRNewswire partial offsets | PRNewswire has active offsets across historical months. | Keep offset-aware progress; do not split PRNewswire ranges until row/offset telemetry proves it is needed. |

## Files Changed

| File | Purpose |
|---|---|
| ops/l0_operating_contract.yaml | Declares the current L0 public newswire operating mode. |
| tools/db/source_acquisition/public_newswire_shards.py | Adds BusinessWire day shard inventory and legacy monthly-state inheritance. |
| scripts/run_l0_public_newswire_sharded_backfill.py | Adds day granularity argument and active-progress runtime extension. |
| scripts/run_task4193_l0_overnight_backfill_supervisor.py | Starts current day-shard config and restarts stale launcher configs. |
| tests/test_l0_public_newswire_sharded_backfill.py | Adds day-shard inventory and inheritance tests. |

## Closeout Position

TASK-4200 is closed as runtime hardening with residual collection blockers. It does not close L0 public newswire backfill. The next outcome unit should be pending unit reduction in `data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json`.
