# TASK-4183 L0-L4 Realtime and Backfill Recovery Audit

## Conclusion

- Overall verdict: BLOCKED_NOT_ALL_RUNNING
- Generated at: 2026-07-01T14:14:19.697341Z
- Scope: L0-L4 collection/backfill/read-model health audit only.
- Trading safety: diagnostic-only; no broker mutation, paper promotion, live order, or real-capital permission.

## Level Verdicts

| Level | Status | Reason |
|---|---|---|
| L0 | PARTIAL_RUNNING_WITH_BLOCKER | backfill/L0-L2 scheduled tasks are running or recently successful, but public newswire aggregate still records dead active worker PIDs |
| L1 | RECENT_ARTIFACT_PRESENT | latest L1 task artifacts are present; this does not prove a live parser loop |
| L2 | STALE_OR_NOT_REALTIME_DB | DB L2 runtime primitive latest asof is older than July 1; separate L0-L2 hardening artifacts are updating but DB runtime is stale |
| L3 | RECENT_ARTIFACT_PRESENT | relation-graph artifacts exist, but no live L3 scheduler/process was observed |
| L4 | RECENT_ARTIFACT_PRESENT | L4 scanner artifact exists, but no live L4 scheduler/process was observed |

## Key Evidence

- L0 public newswire aggregate status: RUNNING progress=55.6693 pending_units=1818
- L0 aggregate active workers: 3 recorded, dead PIDs=3
- Python collector processes observed: 5
- Scheduled backfill worker result: 267009
- Scheduled L0-L2 hardening result: 1
- L2 latest asof: 2026-06-28T06:00:00Z

## Safety Boundary

Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
