# Task3888 — HOME Performance Timeframe Interaction

## Summary

Task3888 implements the HOME Performance timeframe control as an actual read-only UI interaction.

The Performance card now exposes touchable timeframe chips for `1D`, `1M`, `3M`, `6M`, `1Y`, and `ALL`. Selecting a chip updates the visible selected period. Because authoritative evaluation, principal, and QQQ chart series are still not attached, the chart remains fail-closed and does not draw synthetic lines.

The frontend remains read-only, fixture-backed, and `NOT_AUTHORITY`.

## Implemented

- Replaced static timeframe chips with `Pressable` chips.
- Added local selected-timeframe state with `1M` as the default selected period.
- Added a `1D` period option so daily/day selection is represented before longer ranges.
- Added mobile accessibility metadata for selected state.
- Added pressed-state feedback while preserving 44pt-class touch targets.
- Added visible selected-period status below the chart frame.
- Preserved chart fail-closed behavior: no synthetic lines, zero chart points, and `SOURCE_NOT_ATTACHED` while authoritative chart data is missing.
- Updated HOME validators to require clickable timeframe controls.

## Deferred

- Period-specific chart filtering remains deferred until authoritative evaluation, principal, and QQQ time-series data are attached.
- `5M` or intraday resolution switching remains deferred until a frontend chart data contract maps UI periods to source-backed resolutions.
- Crosshair, pan, zoom, and haptic chart interactions remain deferred until chart data and interaction policy are attached.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:home-design-alignment`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run validate:fixtures`
- `cd apps/ios-trader-brain && npm run lint`

## Visual Evidence

- `data/artifacts/task_3888_home_performance_timeframe_interaction/home_performance_timeframe_interaction_390x844.png`

Scope: local LAN web-preview screenshot only. This is not native iOS device evidence, TestFlight evidence, deployment evidence, broker evidence, paper/live permission, strategy acceptance, or real-capital permission.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
