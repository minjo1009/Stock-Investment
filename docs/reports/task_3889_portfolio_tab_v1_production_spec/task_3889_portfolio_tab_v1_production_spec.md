# Task3889 — Portfolio Tab V1 Production Spec

## Summary

Task3889 applies the user-provided `PORTFOLIO_TAB_V1_PRODUCTION_SPEC` to the read-only Portfolio tab.

The Portfolio tab now follows a product-first vertical stack: header, portfolio summary, allocation chart section, holdings list header, holding row, and lower governance/source-state sections. Values remain `UNKNOWN` where authoritative broker/account data is not attached.

The frontend remains read-only, fixture-backed, and `NOT_AUTHORITY`.

## Implemented

- Replaced the previous scaffold-heavy Portfolio surface with a production V1 layout.
- Added a centered Portfolio header with lightweight search/filter icon placeholders.
- Added `PortfolioSummaryCard` with total evaluation, cost basis, total profit/loss, return, position count, win rate, MDD, timestamp, and `NOT_AUTHORITY` status.
- Added `PortfolioAllocationCard` with asset-type segmented labels, stacked allocation bar, category legend, and `SOURCE_NOT_ATTACHED` status.
- Added holdings list header with count and sort chips: evaluation, return, profit, and weight.
- Added a holding row structure with icon, name/ticker/quantity/weight, evaluation/cost, P/L/yield, and broker-truth state.
- Added disabled action chips for buy/sell/note/alert surfaces without handlers.
- Moved source freshness, broker truth, and operating restriction information into lower supporting sections.
- Updated product IA and mobile product V1 validators to require the Portfolio production structure.

## Deferred

- Real account values, broker truth, allocation percentages, and holding-level financial values remain deferred until authoritative data is attached.
- Sort/filter/search interactions remain visual-only until a non-mutating portfolio UI-state contract is defined.
- Row expansion, swipe actions, context menus, haptics, mini charts, pull-to-refresh, and persistence remain deferred.
- Buy/sell workflows remain blocked; no broker mutation, order submit, paper/live permission, or real-capital path was added.
- Dark mode and skeleton loading are not implemented in this slice.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run validate:frontend-governance`
- `cd apps/ios-trader-brain && npm run lint`

## Visual Evidence

- `data/artifacts/task_3889_portfolio_tab_v1_production_spec/portfolio_tab_v1_final_390x844.png`

Scope: local LAN web-preview screenshot only. This is not native iOS device evidence, TestFlight evidence, deployment evidence, broker evidence, paper/live permission, strategy acceptance, or real-capital permission.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
