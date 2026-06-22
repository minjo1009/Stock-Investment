# Task Frontend Foundation Hardening

## Decision Summary

- Verdict: `FOUNDATION_COMPONENTS_HARDENED_WITH_STATIC_TYPED_FIXTURES`
- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`

Task3806 hardens the frontend foundation/layout/generic component layer for Storybook-driven implementation.

No product screen, Candidate Detail screen, DB connection, runtime API connection, broker/API call, KIS/Alpaca integration, paper/live order path, chart implementation, strategy acceptance, deployment readiness, paper/live permission, broker mutation permission, or real-capital permission was added.

## Done

- Hardened foundation tokens and `Badge` tones for fresh/stale/missing/unknown/blocked/read-only/disabled display states.
- Added read-model common TypeScript types derived from `docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md`.
- Added scaffold-only static typed fixture fragments:
  - `apps/ios-trader-brain/src/mocks/fixtures/foundation-states.ts`
- Added foundation/layout/generic components:
  - `AppText`
  - `Badge`
  - `CardContainer`
  - `ScreenContainer`
  - `SectionContainer`
  - `MetricCard`
  - `StatusRow`
  - `SourceFreshnessBadge`
  - `BlockerList`
- Added Storybook stories for all components with:
  - default
  - read-only
  - blocked
  - stale
  - missing
  - unknown
  - disabled action
- Updated scaffold lint and Storybook smoke scripts to require the new component/story baseline.
- Selected the first fixture strategy for Storybook/component work:
  - `STATIC_TYPED_FIXTURES_DERIVED_FROM_08_TASK3806_NOT_AUTHORITY`
- Kept Storybook on the current web-vite runtime.
- Deferred on-device Storybook with explicit reason.
- Deferred NativeWind with explicit Task3806 reason.

## Fixture Source Decision

Selected option: static typed fixtures derived from `08_FRONTEND_READ_MODEL_CONTRACT.md`.

Current fixture path:

```text
apps/ios-trader-brain/src/mocks/fixtures/foundation-states.ts
```

Policy:

- The fixture file is a Storybook/component scaffold fixture only.
- It is not backend authority.
- It is not broker truth.
- It is not source truth.
- It is not trading permission.
- It is not the final app read path.
- Full screen JSON payload paths remain reserved until a generated JSON catalog, read-only runtime API fixture snapshot, or read-only SQLite export transformer is selected.

## NativeWind Decision

NativeWind remains `DEFERRED_WITH_REASON_TASK3806`.

Reason:

- Current components are stable with tokenized React Native style props.
- Current Storybook runtime uses `@storybook/react-native-web-vite`.
- Current NativeWind/Expo install paths add Metro/Babel/CSS configuration and Expo web Metro assumptions before any component needs `className`.
- Installing it now would increase scaffold surface area without solving a Task3806 requirement.

## Storybook On-Device Decision

On-device Storybook remains `DEFERRED_WITH_REASON_TASK3806`.

Reason:

- Current Storybook web-vite runtime is runnable and smoke-tested.
- On-device Storybook requires Expo Router/Metro entry wrapping and native runtime QA.
- That belongs to a future native-device QA task, not foundation component hardening.

## Quant Expert Report

### Data Source And Source Readiness

- No trading data source was read or mutated.
- No DB source, broker source, KIS source, Alpaca source, or runtime API was connected.
- Static typed fixtures are derived from the frontend read-model contract and marked `NOT_AUTHORITY`.

### Exact Join Keys

Not applicable. No joins were performed.

### Leakage Audit

No label, outcome, future return, candidate score, candidate rank, confidence score, symbol/date/price/time proximity matching, or lifecycle inference logic was added.

### Split/OOS Metrics

Not applicable. No backtest, replay, or strategy validation was performed.

### Failure Decomposition

Not applicable. This was a frontend foundation scaffold task.

### Cost/Slippage Stress

Not applicable. No PnL, trade, order, or execution calculation changed.

### Remaining Blockers

- Full app read path remains unselected.
- Full screen source-derived fixture payloads remain uncreated.
- Screenshot QA remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- Maestro remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- iOS development build remains unvalidated in this Windows environment.
- NativeWind remains deferred.
- npm audit findings and react-native-worklets peer warnings from Task3805 remain open.

## No-Background Decision-Maker Report

The app still has only placeholder tabs. Task3806 makes the shared component shelf safer before real screens start.

The important change is that source freshness, blockers, missing states, unknown states, and disabled action states now have reusable Storybook-covered components.

This does not change trading readiness. The system remains diagnostic-only, not accepted, and forbidden for real capital.

Next step: create the first read-only domain component contracts or add screenshot/native-device QA without connecting to DB, broker, or runtime mutation paths.

## Validation

Required validation commands:

```powershell
cd apps/ios-trader-brain && npm run typecheck
cd apps/ios-trader-brain && npm run lint
cd apps/ios-trader-brain && npm test
cd apps/ios-trader-brain && npm run storybook:smoke
cd apps/ios-trader-brain && npm run validate:safety
python scripts/task_registry_validate.py
git diff --check
git diff --cached --check
```

Validation results must not be interpreted as strategy acceptance, deployment readiness, paper/live permission, broker mutation permission, or real-capital permission.

## Artifact Manifest

See `artifact_manifest.csv`.
