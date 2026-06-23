# Task3885 — HOME Screen V1 Production Spec Alignment

## Summary

Task3885 revised the read-only mobile HOME screen around the user-provided `HOME_SCREEN_V1_PRODUCTION_SPEC`.

The first screen now leads with a Korean portfolio operating dashboard: account value, invested cash, cash, return status, win-rate status, MDD, and a QQQ-relative return/MDD chart area. Governance and permission notices remain visible but are demoted to secondary context.

## Implemented

- Rebuilt HOME around a mobile-first portfolio operating dashboard.
- Removed duplicate account snapshot, operating restriction, disabled-action, and internal fixture-path primary presentation from HOME.
- Repaired broken Korean copy in HOME fixture text and the QQQ/MDD chart card.
- Kept QQQ-relative return and MDD as source-attached-only: no fake chart series, no synthetic OHLC, no random data.
- Kept trading safety visible as secondary context: read-only, `NOT_AUTHORITY`, no broker mutation, no paper/live permission, no real-capital permission.
- Updated HOME validators to enforce product-first Korean IA, no mojibake, no internal path exposure, no fake chart data, and source-status visibility as a secondary layer.
- Captured a 390x844 local web-preview screenshot for visual QA.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:home-design-alignment`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm test`
- `git diff --check`

## Visual Evidence

- `data/artifacts/task_3885_home_screen_v1_production_spec/home_screen_v1_production_390x844.png`

Scope: local web-preview screenshot only. This is not native iOS evidence, TestFlight evidence, deployment evidence, broker evidence, paper/live permission, strategy acceptance, or real-capital permission.

## Remaining Limits

- Values remain fixture-backed `UNKNOWN` until authoritative read models are attached.
- QQQ/MDD chart remains `SOURCE_NOT_ATTACHED`; no chart points are rendered.
- Native iOS device evidence remains operator-gated.
- This task does not grant product readiness, paper/live readiness, deployment readiness, strategy acceptance, broker mutation, or real-capital permission.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
