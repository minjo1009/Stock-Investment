# Task3887 — HOME QQQ Comparison and Journal Month Rail

## Summary

Task3887 updates the HOME screen production scaffold to match the user's latest HOME requirement.

The Performance card now represents the intended comparison as evaluation amount vs principal vs QQQ. The investment journal month rail now starts at January 2022 and grows through the current month in chronological left-to-right order.

The frontend remains read-only, fixture-backed, and `NOT_AUTHORITY`.

## Implemented

- Added QQQ as the third Performance comparison target.
- Updated chart copy, legend, blocker text, fixture source labels, and validators to require `평가금 vs 원금 vs QQQ`.
- Preserved fail-closed chart behavior: no synthetic lines, zero chart points, and `SOURCE_NOT_ATTACHED` while authoritative chart data is missing.
- Replaced the short hardcoded investment journal month list with a generated month sequence from 2022-01 through the current local month.
- January labels use a year-qualified format such as `22.01` and `23.01`.
- The current month also uses a year-qualified format so July 2026 will show `26.07` when the system date reaches July 2026.
- Months between January and the current month use compact Korean month labels such as `2월` through `12월`.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:home-design-alignment`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run validate:fixtures`
- `cd apps/ios-trader-brain && npm test`
- `git diff --check`

## Visual Evidence

- `data/artifacts/task_3887_home_qqq_journal_months/home_qqq_journal_months_390x844.png`

Scope: local LAN web-preview screenshot only. This is not native iOS device evidence, TestFlight evidence, deployment evidence, broker evidence, paper/live permission, strategy acceptance, or real-capital permission.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
