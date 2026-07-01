# TASK-4120 L0 Stage 2 Realtime Source Budget Optimization

## Goal

Optimize real-time L0 source budgets after Stage 1 bounded network smoke passed,
without activating schedulers.

## Results

- Added `scripts/optimize_l0_stage2_realtime_budgets.py`.
- Added `scripts/validate_l0_stage2_realtime_budgets.py`.
- Updated Marketaux real-time cadence from unsafe 15-minute template posture to
  16 minutes.
- Budget result: `90` requests/day against a `95` requests/day guard,
  utilization `0.9474`.
- Updated scheduler management plan: Stage 2 is
  `COMPLETE_REALTIME_BUDGET_OPTIMIZED`; Stage 3 is now `NEXT`.
- Scheduler activation remains `0`.

## Budget Plan

| Source family | Budget decision |
|---|---|
| `official_public_releases` | Keep 15m bounded refresh, disabled by default. |
| `gdelt_news_events` | Keep one-symbol 15m cadence with 15m cooldown, discovery-only. |
| `marketaux_news_free` | Set 16m cadence, 90/day budget under 95/day cap. |

## Boundary

No scheduler recurrence was activated. No network calls were made by Stage 2.
No DB mutation, broker mutation, replay, paper promotion, live order, or
real-capital permission was added.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
