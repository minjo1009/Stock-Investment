# TASK-4118 L0 Stage 1 Official Core API Smoke Stabilization

## Goal

Implement and validate Stage 1 L0 official/core API smoke preflight according to
the six-stage source acquisition roadmap. The task stabilizes the smoke
contract without making API calls by default.

## Results

- Added `scripts/run_l0_stage1_core_api_smoke.py`.
- Added `scripts/validate_l0_stage1_core_api_smoke.py`.
- Generated governed Stage 1 CSV artifacts for scope, source-family plan,
  API/raw call ledger, raw response classification, normalized source packets,
  decision-asof coverage, feature gate, source gaps, and materialization audit.
- Updated the scheduler management plan with
  `PREFLIGHT_PASS_NETWORK_SMOKE_PENDING` for Stage 1.
- Updated the L0 roadmap and active status docs so Stage 2 remains blocked
  until explicit bounded network smoke evidence exists.

## Smoke Result

`stage1_smoke_summary.json` reports:

- `stage1_status`: `PREFLIGHT_PASS_NETWORK_SMOKE_PENDING`
- `network_calls_made`: `0`
- `fail_count`: `0`
- `blocked_count`: `0`
- `materialization_blocked_count`: `0`

This means the current repository can validate Stage 1 contracts, config
bounds, safety gates, materialization, and L1 normalization shape without
network calls. It does not mean real provider network collection has been
proven.

## Source Families

| Source family | Stage 1 state |
|---|---|
| `official_public_releases` | Registry and synthetic L1 diagnostic contract pass |
| `gdelt_news_events` | Bounded registry and discovery-only L1 contract pass |
| `marketaux_news_free` | Quota registry, token audit, and discovery-only L1 contract pass |
| `microstructure_quotes_trades` | Alpaca credential-presence preflight passed without secret logging |

## Decision

Stage 1 is not fully complete yet. It is preflight-stabilized and ready for
TASK-4119 bounded network smoke, subject to explicit operator network permission
and current local credentials.

Stage 2 real-time source budget optimization remains blocked.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
