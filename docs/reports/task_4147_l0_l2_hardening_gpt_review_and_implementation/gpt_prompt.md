# TASK-4147 GPT Pro Review Prompt

You are GPT Pro reviewing a local trading data pipeline implementation plan.

Important constraint:
- Do not use GitHub.
- Do not browse or inspect any repository.
- Assume the GitHub repository is stale and does not include the latest local work.
- Use only the context pasted below.
- Avoid overengineering. Do not recommend code for code's sake or guards for guards' sake.
- This is a diagnostic/data pipeline. Do not open signal, order, broker, live trading, or real-capital authority.

Please answer in Korean, using simple/direct wording.

## Project identity

This repository is a Trading Operating System for observing, verifying, monitoring, and controlling an automated US equity trading engine.

It is not a retail brokerage UI, stock recommendation app, or chart-first app.

Trading safety rules:
- No real capital.
- No live order.
- No broker mutation.
- No paper promotion unless explicitly accepted.
- Missing or stale data is UNKNOWN/BLOCKER, not negative evidence.

## Current L0-L2 state from local TASK-4146

TASK-4146 built a wide diagnostic handoff from Layer 0 through Layer 2.

Implemented files:
- `scripts/run_l0_l2_wide_handoff_4146.py`
- `scripts/validate_l0_l2_wide_handoff_4146.py`
- `scripts/run_l0_l2_wide_handoff_loop_4146.ps1`
- `scripts/start_l0_l2_wide_handoff_loop_4146.ps1`

Background 15-minute loop:
- pid: 32576
- status: RUNNING_PASS
- interval_seconds: 900
- last_run_exit: 0
- last_validation_exit: 0

Restarted L0 lanes:
- `public_newswire_backfill` pid 9276
- `public_market_macro_news_backfill` pid 21684

Current wide handoff counts:
- L0 batch rows: 1,754
- L0 raw item rows reported: 380,101
- L1 packet rows: 1,754
- L1 ready packet rows: 884
- L1 blocked packet rows: 870
- L2 rows: 1,754
- L2 admitted/review rows: 884
- Feature candidate materialization rows: 884
- Feature candidate count: 366,781
- Trading authority opened rows: 0
- Paper/live/broker/order opened rows: 0

Source rollup:
- `public_context_news_feeds`
  - L0 batch rows: 1,245
  - L0 raw item rows reported: 267,885
  - L1 ready rows: 411
  - L1 blocked rows: 834
  - L2 admitted/review rows: 411
  - feature candidate count: 267,885
- `public_market_macro_news_feeds`
  - L0 batch rows: 320
  - L0 raw item rows reported: 96,246
  - L1 ready rows: 307
  - L1 blocked rows: 13
  - L2 admitted/review rows: 307
  - feature candidate count: 96,246
- `public_newswire_feeds`
  - L0 batch rows: 189
  - L0 raw item rows reported: 15,970
  - L1 ready rows: 166
  - L1 blocked rows: 23
  - L2 admitted/review rows: 166
  - feature candidate count: 2,650

Current status:
- This is not a complete production feature pipeline.
- It is a working diagnostic pipeline v1.
- Main gap: L1/L2 currently consumes L0 too much at batch-level. It does not yet broadly eat raw row/article items as first-class packets.
- Feature candidates exist, but they remain diagnostic-only and are not yet promoted into the durable feature schema.
- Trading/order/signal authority remains closed by design.

## Work items the user wants

1. Expand L1 from batch-level packets to row/article-level packets.
2. Improve newswire ticker/entity mapping.
3. Separate an operating config that can safely enable L0 real-time collection.
4. Register a durable 15-minute L1/L2 loop in Windows Task Scheduler or the existing scheduler.
5. Keep raising backfill completion and produce completion proof.
6. Promote L2 diagnostic feature candidates into the actual feature schema, while keeping them completely separate from signal/order.

## Requested review

Please review how to implement/strengthen these six items.

I need:
1. A practical implementation sequence.
2. What to group together vs run as separate loops/subtasks.
3. Concrete output artifacts for each item.
4. Minimum useful validators.
5. What should be explicitly avoided as overengineering.
6. How to keep signal/order/broker authority closed while still making diagnostic features real schema rows.
7. A crisp done definition for TASK-4147.

Keep the answer direct. Use a table where helpful.
