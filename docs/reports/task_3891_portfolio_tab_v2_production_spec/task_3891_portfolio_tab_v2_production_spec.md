# Task3891 — Portfolio Tab V2 Production Spec

## Summary

Task3891 applies the user-provided `PORTFOLIO_TAB_V2_PRODUCTION_SPEC` to the read-only Portfolio tab.

The Portfolio tab now uses the requested two-card structure: a fixed-height holdings table card and a stock detail card. The holdings table supports local row selection and horizontal metric browsing. The stock detail card updates from the selected row and shows local indicator/range controls, a source-not-attached chart frame, a timeline slider shell, a metrics strip, buy-reasoning context, and latest-news context.

The frontend remains read-only, fixture-backed, and `NOT_AUTHORITY`.

## Implemented

- Replaced the V1 summary/allocation-first Portfolio layout with the V2 table-detail layout.
- Added a fixed-height holdings table card with title, count badge, info badge, sort chips, filter chips, sticky name column, horizontal metrics area, and three visible rows.
- Added local row selection with selected-row tint and accent stripe.
- Added table columns for evaluation P/L, quantity/sellable quantity, evaluation/purchase amount, holding period, and MDD.
- Added a stock detail card driven by the selected table row.
- Added local indicator toggles for VWAP, volume, moving average, and system line.
- Added local range controls for `1D`, `1M`, `3M`, `1Y`, and `ALL`.
- Added a source-not-attached chart frame with no synthetic candles or lines.
- Added a timeline slider shell with a right handle labelled as locked to now.
- Added a horizontal metrics strip, buy-reasoning section, and latest-news section.
- Kept data freshness and operating state as lower supporting content inside the detail card.
- Updated frontend validators to distinguish safe local UI interaction from broker/API/order mutation.

## Deferred

- Real holdings, broker truth, account values, price candles, VWAP, volume, news, and buy-reason data remain deferred until authoritative read-only sources are attached.
- True sticky first column behavior under native horizontal scroll remains a visual shell in this slice.
- Vertical virtualization, crosshair, pinch/drag, draggable slider handles, pull-to-refresh, haptics, collapsible sections, and persistence remain deferred.
- Buy/sell workflows remain absent. No broker mutation, order submit, paper/live permission, deployment readiness, or real-capital path was added.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:mobile-scan-list-v1`
- `cd apps/ios-trader-brain && npm run validate:screen-boundary`
- `cd apps/ios-trader-brain && npm run validate:safety`

## Visual Evidence

- `data/artifacts/task_3891_portfolio_tab_v2_production_spec/portfolio_tab_v2_final2_390x844.png`

Scope: local LAN web-preview screenshot only. This is not native iOS device evidence, TestFlight evidence, deployment evidence, broker evidence, paper/live permission, strategy acceptance, or real-capital permission.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
