# TASK-4164 L0 Runtime Consistency and Recall Propagation Report

## Summary

This task checked whether the newly strengthened public newswire recall filter is actually applied to already collected raw data and future collection paths.

Main conclusion:

- Future sharded public newswire collection uses the updated collector path.
- Existing raw data needs derived overlay reclassification; raw files must not be mutated.
- The legacy monolithic public newswire backfill was still being restarted and could create mixed-version output. It has been stopped, and recovery no longer restarts it.
- The canonical historical newswire backfill path is now the sharded launcher under `l0_public_newswire_backfill_shards`.

## Actions

| Area | Result |
|---|---|
| Future newswire collection | `public_newswire_collector.py` already emits `newswire_recall_*` fields for new rows. |
| Legacy monolithic newswire collector | STOP file placed and live legacy/recovery PIDs stopped. |
| Recovery supervisor | `scripts/run_l0_backfill_worker_recovery_4148.py` no longer restarts legacy `public_newswire_backfill`. |
| Failed shard accounting | `COMPLETED_WITH_NONZERO_EXIT` is now recognized when collector state proves completion despite non-zero worker exit. |
| Worker debugging | Sharded launcher now appends worker stdout/stderr to the shard log path instead of discarding it. |
| Existing raw overlay | Event-ledger based overlay was generated and validated for BusinessWire and PRNewswire. |
| GlobeNewswire existing raw overlay | TASK-4163 latest-shard overlay remains valid. Full event-ledger GN overlay is still too heavy for this foreground run and remains a follow-up. |

## Current Evidence

Newswire sharded aggregate after refresh:

| Metric | Value |
|---|---:|
| status | RUNNING |
| progress_pct | 51.5972 |
| completed_units | 2116 |
| total_units | 4101 |
| pending_units | 1985 |
| failed_units | 11 |
| partial_units | 71 |
| row_count | 631752 |

Failed shard count changed from 12 to 11 because one shard had completed collector evidence but was previously counted failed only due to non-zero worker exit.

Remaining failed shards:

- `globenewswire:2017-04`
- `globenewswire:2017-06`
- `globenewswire:2017-11`
- `globenewswire:2020-07`
- `globenewswire:2021-09`
- `globenewswire:2022-09`
- `globenewswire:2023-04`
- `globenewswire:2024-06`
- `globenewswire:2024-11`
- `globenewswire:2025-12`
- `prnewswire:2016-10`

## Existing Raw Overlay Results

| Source | Discovery mode | Files | Recall rows | Status changed rows | Validator |
|---|---|---:|---:|---:|---|
| BusinessWire | event raw paths | 873 | 10726 | 9130 | PASS |
| PRNewswire | event raw paths | 95 | 3516 | 2595 | PASS |
| GlobeNewswire | latest shard overlay from TASK-4163 | 330 | 12040 | 10225 | PASS |

## 5-Minute Bars

The 5-minute bar collector is running. The previous mismatch came from reading an older background metadata file rather than `background_process_5m.json`.

Latest status:

| Metric | Value |
|---|---:|
| overall_progress_pct | 28.328 |
| five_min_symbol_index | 3410 / 12040 |
| five_min_rows_written | 78795108 |
| failed_events | 599 |
| observed_requests_per_minute_this_run | 33.267 |
| eta_hours_at_observed_rate | 138.34 |

## Remaining Work

| Priority | Work | Why |
|---:|---|---|
| P0 | Retry/repair 11 represented failed newswire shards | These are partial/monthly offset shards, not final data loss proof. |
| P0 | Build a chunked/background GN event-ledger overlay job | Foreground full GN overlay is too heavy; latest-shard overlay exists but full event raw coverage is still pending. |
| P0 | Ensure L1/L2 handoff reads sharded newswire events and recall overlays, not only legacy event paths | Otherwise L0 data is collected but not fully eaten by downstream layers. |
| P1 | Re-run aggregate and validator after failed-shard retries | Needed for coverage proof. |

Trading gates remain closed: no broker mutation, no live order, no paper promotion, no trade authority.
