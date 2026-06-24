# Task3886 — HOME Full Production Spec Alignment

## Summary

Task3886 applied the remaining HOME production specification supplied by the user after Task3885 only covered the first subset.

The HOME screen now follows the larger vertical structure: portfolio hero, performance timeline chart, portfolio holdings empty state, investment journal empty state, attention items, and secondary source/governance status. The screen remains read-only, fixture-backed, and `NOT_AUTHORITY`.

## Implemented

- Replaced the prior account-summary-first HOME with a production-spec section stack.
- Added a 220px-class portfolio hero card with evaluation amount, principal, total P/L, return rate, win rate, and MDD.
- Kept missing KPI values compact as `-` to prevent narrow mobile wrapping.
- Reworked the chart card into a `Performance` timeline card for evaluation vs principal.
- Added static timeframe controls: `1M`, `3M`, `6M`, `1Y`, `ALL`.
- Preserved chart fail-closed behavior: `SOURCE_NOT_ATTACHED`, zero chart points, no synthetic lines.
- Added Portfolio Holdings empty state: `보유 중인 포트폴리오가 없습니다.`
- Added Investment Journal month rail and empty trade-history state: `해당 월의 거래내역이 없습니다.`
- Moved source/governance status to secondary lower content so system state does not dominate above the fold.
- Updated HOME and product IA validators for the full production spec structure.

## Deferred

- Real chart lines, crosshair, pan, zoom, haptics, and long-press locking remain deferred until authoritative chart data and interaction policy are attached.
- Holding-card navigation and trade-card expansion remain deferred because current frontend safety validators preserve handler-free scaffold surfaces.
- Pull-to-refresh remains deferred because there is no authoritative runtime API or refresh contract attached.
- Dark mode remains a later theme task.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:home-design-alignment`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:evidence-visibility`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm test`
- `git diff --check`

## Visual Evidence

- `data/artifacts/task_3886_home_full_production_spec/home_full_production_spec_390x844.png`

Scope: local LAN web-preview screenshot only. This is not native iOS device evidence, TestFlight evidence, deployment evidence, broker evidence, paper/live permission, strategy acceptance, or real-capital permission.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
