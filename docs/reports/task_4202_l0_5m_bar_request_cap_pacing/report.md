# TASK-4202 L0 5m Bar Request Cap Pacing

## Conclusion

5-minute bar collection was running, but it was not using the configured 120 requests/minute cap efficiently. The old loop slept for `60 / rpm` after every request, so actual request latency and sqlite write time were added on top of the throttle interval.

TASK-4202 changed the existing collector so the throttle is based on request-start interval. The collector now subtracts request/DB elapsed time from the throttle sleep and only keeps the longer 60-second cooldown for rate-limit responses.

This does not force 120 rpm when provider latency or sqlite upsert time is already slower than 0.5 seconds. It does make the collector run as close to the configured cap as the provider and local write path allow.

## Before And After

| Item | Before | After |
|---|---|---|
| Configured cap | 120 rpm | 120 rpm |
| Observed rpm before restart | about 36 rpm | no longer target state |
| Observed rpm after restart sample | n/a | 82.8796 rpm initial sample; 51.6003 rpm latest longer sample |
| Sleep behavior | Always slept 0.5s after request. | Sleeps only remaining interval after request elapsed time. |
| 429 handling | Slept at least 60s. | Still sleeps at least 60s. |
| Runtime PID | 2088 | 27424 |

## Current Snapshot

| Metric | Value |
|---|---:|
| progress_pct | 35.109 |
| rows_written | 95,087,702 |
| symbol_index | 4227 |
| block_index | 4 / 32 |
| remaining_request_units | 250,012 |
| observed_requests_per_minute_this_run | 51.6003 |
| eta_hours_at_observed_rate | 80.75 |
| eta_hours_at_configured_rpm | 34.72 |
| rate_limited_events | 0 |

## Files Changed

| File | Purpose |
|---|---|
| tools/db/source_acquisition/bar_full_backfill.py | Implements request-start interval pacing and exposes pacing metadata in progress. |
| scripts/start_l0_bar_full_backfill.ps1 | Records request pacing mode in the background process artifact. |
| scripts/run_task4193_l0_overnight_backfill_supervisor.py | Restarts old 5m processes that do not expose current pacing mode. |
| ops/l0_operating_contract.yaml | Records current 5m operating mode. |
| tests/test_l0_bar_full_backfill_rate_pacing.py | Verifies throttle sleep behavior. |

## Residual Limit

120 rpm is a cap, not a guaranteed throughput. If an Alpaca fetch plus sqlite upsert takes longer than 0.5 seconds, one serial worker cannot reach 120 rpm. Reaching closer to 120 consistently would require parallel 5m lanes or lower write latency, which is a separate change and should be guarded because it increases DB lock and provider-load risk.
