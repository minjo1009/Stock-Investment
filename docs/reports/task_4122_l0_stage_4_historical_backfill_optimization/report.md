# TASK-4122 L0 Stage 4 Historical Backfill Optimization

## Goal

Optimize historical backfill chunking, checkpointing, resume, retry, and
coverage audit posture before any Stage 5 background collection from 2016.

## Results

- Added Stage 4 optimization metadata to the three Stage 5 backfill candidates:
  `public_context_news_backfill`, `public_market_macro_news_backfill`, and
  `microstructure_backfill_batch`.
- Kept all backfill jobs disabled with `allow_network=false` and
  `scheduler_activation_permitted=0`.
- Repaired microstructure backfill chunking so `chunk_minutes` from config is
  actually used by the Python backfill runner.
- Produced a backfill optimization plan, blocker ledger, and coverage audit
  plan.
- Updated the six-stage management plan: Stage 4 is
  `COMPLETE_HISTORICAL_BACKFILL_OPTIMIZED_NOT_ACTIVATED`; Stage 5 is now
  `NEXT`.

## Backfill Direction

| Backfill job | Start | Optimized unit | Current status |
|---|---:|---|---|
| `public_context_news_backfill` | 2016-01-01 | source cursor/date window with state/event/progress/STOP controls | Optimized, not activated |
| `public_market_macro_news_backfill` | 2016-01-01 | source cursor/date window after collector materialization | Blocked by OneDrive local materialization |
| `microstructure_backfill_batch` | 2016-01-01 target program, bounded operator dates per run | 1 symbol x 1 date x 2 chunks x quotes/trades; 15-minute chunks | Optimized, not activated |

## Boundary

No background process was started. No provider network calls were made. No DB
mutation, broker mutation, replay, paper promotion, live order, or real-capital
permission was added.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
