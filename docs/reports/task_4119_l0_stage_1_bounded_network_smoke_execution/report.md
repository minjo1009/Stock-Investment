# TASK-4119 L0 Stage 1 Bounded Network Smoke Execution

## Goal

Execute bounded Stage 1 network smoke for the official/core L0 source families
after TASK-4118 preflight passed.

## Results

- Added `scripts/run_l0_stage1_bounded_network_smoke.py`.
- Added `scripts/validate_l0_stage1_bounded_network_smoke.py`.
- Ran bounded network smoke for:
  - `official_public_releases`: Apple Newsroom RSS
  - `gdelt_news_events`: one AAPL GDELT request with `maxrecords=1`
  - `marketaux_news_free`: one AAPL Marketaux request with `limit=1`
  - `microstructure_quotes`: one AAPL Alpaca IEX one-minute quote window
  - `microstructure_trades`: one AAPL Alpaca IEX one-minute trade window
- Captured redacted raw summaries and bounded row samples under this task
  report folder only.
- Updated the L0 roadmap and scheduler management plan: Stage 1 is
  `COMPLETE_NETWORK_SMOKE_PASS`; Stage 2 is now `NEXT`.

## Smoke Evidence

`stage1_network_smoke_summary.json`:

- `network_calls_made`: `5`
- `captured_raw_summaries`: `5`
- `exported_or_empty_count`: `5`
- `blocked_count`: `0`
- `failed_retryable_count`: `0`
- `normalized_packet_count`: `4`
- `stage1_status`: `NETWORK_SMOKE_EXECUTED_OWNER_REVIEW_PENDING`

Provider outcomes:

| Source family | Status | Interpretation |
|---|---|---|
| `official_public_releases` | `EXPORTED` | Official RSS reachable and captured. |
| `gdelt_news_events` | `EMPTY_PROVIDER_RESPONSE` | GDELT reachable; no article in bounded 15-minute AAPL window. |
| `marketaux_news_free` | `EXPORTED` | Marketaux reachable with token redacted from artifacts. |
| `microstructure_quotes` | `EXPORTED` | Alpaca quote endpoint reachable for bounded one-minute window. |
| `microstructure_trades` | `EXPORTED` | Alpaca trade endpoint reachable for bounded one-minute window. |

## Decision

Stage 1 official/core API smoke is complete for the bounded diagnostic path.
Stage 2 real-time source budget optimization is the next active step. Scheduler
recurrence remains inactive and must wait until Stage 3.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
