# Frontend Implementation Preconditions

## Purpose

This document is the gate before Storybook setup, foundation components, or screen implementation.

It fixes the implementation path, command placeholders, fixture paths, screenshot QA scope, and safety-validator requirements so future Codex work does not invent app roots, commands, fixtures, QA flows, or unsafe trading affordances.

This document does not authorize strategy acceptance, paper permission, live permission, broker mutation, deployment readiness, or real-capital action.

## Current Status

| Item | Status |
| --- | --- |
| Frontend target | Expo Development Build, iOS-first |
| App scaffold | `CREATED_TASK3804` |
| Actual app root | `apps/ios-trader-brain` |
| Package manager | `npm` |
| Primary app read path | `GENERATED_JSON_CATALOG_FIXTURE_SNAPSHOT_TASK3809_NOT_AUTHORITY` |
| Storybook/component fixture source | `STATIC_TYPED_FIXTURES_DERIVED_FROM_08_TASK3806_NOT_AUTHORITY` |
| Storybook | `npm run storybook`; smoke validation via `npm run storybook:smoke` |
| Storybook on-device | `DEFERRED_WITH_REASON_TASK3806` |
| Screenshot QA | `REQUIRED_POST_SCAFFOLD_HARDENING` |
| Safety validator | `npm run validate:safety` |
| NativeWind | `DEFERRED_WITH_REASON_TASK3806` |

## Actual App Root Path

Future app scaffold must use:

```text
apps/ios-trader-brain
```

Reason:

- `docs/frontend_app_ssot/10_IMPLEMENTATION_ARCHITECTURE.md` already names `apps/ios-trader-brain` as the preferred path.
- The repo currently has no tracked `apps/` scaffold.
- Using this reserved path prevents arbitrary future app roots such as `apps/tos-mobile` or `apps/trading-os-mobile`.

Task3804 created the app directory.

## Scaffold Baseline

The future scaffold must target:

| Concern | Required direction |
| --- | --- |
| Runtime | Expo Development Build |
| Platform priority | iOS first |
| Navigation | Expo Router |
| Language | TypeScript |
| Styling | Token and React Native style props now; NativeWind deferred |
| Component base | React Native Reusables where practical |
| Story isolation | Storybook |
| Mobile flow QA | Maestro if selected by scaffold task |
| NativeWind | Deferred until a component or design-system task proves the className/Tailwind path is needed and compatible with Storybook web-vite |

## Command Contract

Because the app scaffold does not exist yet, commands are not runnable now.
They must be finalized by the scaffold task and then reflected here.

| Purpose | Required current value | Future command slot |
| --- | --- | --- |
| Package manager | `npm` | selected by Task3804 scaffold |
| Install dependencies | `npm install` | executed by `create-expo-app` and `npx expo install` |
| Expo start | `npm run start` | runnable command, not a deployment claim |
| Expo iOS simulator start | `npm run ios` | defined by Expo scaffold; not validated on Windows/macOS-only simulator path |
| Expo Development Build | `REQUIRED_POST_SCAFFOLD_HARDENING` | `npm run ios:dev` currently blocks intentionally |
| Storybook | `npm run storybook` | starts Storybook web runtime on port 6006 |
| Storybook smoke | `npm run storybook:smoke` | validated in Task3805 |
| Storybook on-device | `DEFERRED_WITH_REASON_TASK3806` | deferred because on-device Storybook requires Expo Router/Metro entry wrapping and native runtime proof that is larger than foundation component hardening |
| Typecheck | `npm run typecheck` | validated in Task3804 |
| Lint | `npm run lint` | scaffold boundary lint validated in Task3805 |
| Unit/component tests | `npm test` | Storybook story export smoke plus safety validator validated in Task3805 |
| Screenshot QA | `REQUIRED_POST_SCAFFOLD_HARDENING` | `npm run qa:screenshot` currently blocks intentionally |
| Maestro | `REQUIRED_POST_SCAFFOLD_HARDENING` | not installed in Task3804 |
| Frontend safety validator | `npm run validate:safety` | hardened and validated in Task3805 |
| Read-model fixture validator | `npm run validate:fixtures` | validates Task3809 generated JSON catalog fixture snapshot |
| Pre-screen GPT loop validator | `npm run validate:pre-screen` | validates Task3811 10-loop gate before product screen work |

Do not document a command as runnable until a task proves it.

## Read Model Fixture Paths

Future Storybook and component fixtures must derive from `docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md`.

Task3806 selected the first Storybook/component fixture strategy:

- Option selected: static typed fixtures derived from `08_FRONTEND_READ_MODEL_CONTRACT.md`.
- Current fixture path: `apps/ios-trader-brain/src/mocks/fixtures/foundation-states.ts`.
- Scope: component-state fragments for Storybook only.
- Authority status: `NOT_AUTHORITY`; these fixtures are not backend truth, broker truth, source truth, trading permission, or app read-path authority.
- Full screen payload paths below remain reserved until a backend-generated JSON catalog, read-only runtime API snapshot, or read-only SQLite export transformer is selected.

Task3809 selected the first full app read-model fixture source strategy:

- Option selected: generated JSON catalog fixture snapshot.
- Current manifest path: `apps/ios-trader-brain/src/mocks/fixtures/catalog-manifest.json`.
- Current screen fixture paths: the reserved JSON files listed below.
- Scope: scaffold-only screen read-model payloads for Storybook/domain component contracts.
- Authority status: `NOT_AUTHORITY`; these fixtures are not backend truth, broker truth, source truth, trading permission, paper permission, deployment readiness, or real-capital permission.
- Frontend direct active `trading.db` access remains forbidden.
- Future production read path must replace this snapshot with a backend-generated JSON catalog, read-only runtime API response, or read-only SQLite export transformer selected by a later authority task.

Reserved fixture paths:

| Fixture | Reserved path | Source contract |
| --- | --- | --- |
| HOME | `apps/ios-trader-brain/src/mocks/fixtures/home.json` | `HomeReadModel` |
| BRAIN | `apps/ios-trader-brain/src/mocks/fixtures/brain.json` | `BrainReadModel` |
| Candidate detail | `apps/ios-trader-brain/src/mocks/fixtures/candidate-detail.json` | `CandidateDetailReadModel` |
| Chain detail | `apps/ios-trader-brain/src/mocks/fixtures/chain-detail.json` | `ChainDetailReadModel` |
| Portfolio | `apps/ios-trader-brain/src/mocks/fixtures/portfolio.json` | `PortfolioReadModel` |
| Position detail | `apps/ios-trader-brain/src/mocks/fixtures/position-detail.json` | `PositionDetailReadModel` |
| Orders | `apps/ios-trader-brain/src/mocks/fixtures/orders.json` | `OrdersReadModel` |
| Order detail | `apps/ios-trader-brain/src/mocks/fixtures/order-detail.json` | `OrderDetailReadModel` |
| System health | `apps/ios-trader-brain/src/mocks/fixtures/system-health.json` | `SystemReadModel` |

Full screen fixture source path must be one of:

- generated JSON catalog from the backend
- read-only runtime API response
- read-only SQLite export transformed into this contract

The exact full screen source must be selected before screen payload files are created. Task3804 created only the fixture directory placeholder. Task3806 created only typed foundation-state fixture fragments for Storybook. Task3809 created the first full screen scaffold fixture snapshot under these paths and added `npm run validate:fixtures`.

## Required P0 Components Before Screens

Foundation/domain components must exist before top-level screens.
Each component must receive props from the read-model contract, not ad hoc mock fields.

| Component | Required source |
| --- | --- |
| `DecisionHeader` | `AppShellReadModel`, `CandidateDetailReadModel.sections.decisionSummary` |
| `SourceFreshnessBadge` | `SourceState` |
| `BlockerList` | `BlockerState[]` |
| `EvidenceList` | `EvidenceItem[]` |
| `ValidationReadinessPanel` | `validationReadiness` section |
| `RiskGate` | `BlockerState[]`, `SourceState[]`, `ChartSourceState[]` |
| `DisabledActionBar` | `DisabledAction[]` |
| `ChartWithSourceState` | `ChartSourceState` |
| `SystemHealth` | `SystemReadModel` |
| `OrderStateSummary` | `OrdersReadModel`, `OrderDetailReadModel` |

Screen implementation must not start until these component contracts are represented in Storybook or an equivalent scaffold-approved component isolation layer. Task3804 added only `AppText`, `Badge`, and `CardContainer`.

Task3806 hardened the foundation/layout/generic layer with:

- `AppText`
- `Badge`
- `CardContainer`
- `ScreenContainer`
- `SectionContainer`
- `MetricCard`
- `StatusRow`
- `SourceFreshnessBadge`
- `BlockerList`

These components are props-only, read-only, and Storybook-covered for default/read-only/blocked/stale/missing/unknown/disabled-action states. They do not replace the future domain components listed above.

## Storybook Preconditions

Storybook must include P0 stories for:

- `DecisionHeader`
- `SourceFreshnessBadge`
- `BlockerList`
- `EvidenceList`
- `ValidationReadinessPanel`
- `RiskGate`
- `DisabledActionBar`
- `ChartWithSourceState`
- `SystemHealth`
- `OrderStateSummary`

Required story states:

- fresh source
- stale source
- missing source
- unknown source
- blocked state
- disabled action state
- chart missing
- source not attached

Story args must come from the reserved fixture paths or typed fixture builders generated from them after a future task selects the read-model fixture source. Task3805 provides runnable foundation Storybook stories, but not source-derived read-model payload fixtures.

Task3806 adds typed fixture fragments in `src/mocks/fixtures/foundation-states.ts` for the foundation/layout/generic Storybook stories. They are scaffold-only and must not be used as backend/source authority.

## Screenshot QA Preconditions

Required screenshot QA device preset:

| Setting | Required value |
| --- | --- |
| Device | iPhone 15 Pro |
| Theme | Light |
| Scale | 100% |
| Orientation | Portrait |

Required screenshot screens:

1. Home
2. Brain Overview
3. Candidate Detail
4. Portfolio Overview
5. Position Detail
6. Orders Overview
7. Order Detail
8. System Overview
9. Stale Source State
10. Disabled Action State

Screenshot QA must fail if stale/missing/source-not-attached states are hidden.

## Frontend Safety Validator Preconditions

A frontend safety validator exists as `npm run validate:safety`. Task3805 hardened it for disabled/blocked visible action context, handler detection, broker/API import detection, and top-level tab boundary checks.

The validator must check:

- no broker mutation handlers
- no live-order handlers
- no real-capital affordances
- no active approve/reject/cancel/execute/submit controls
- backtest, paper, and live are not top-level tabs
- source freshness and blockers are visible in required screens
- chart-required components do not use synthetic source-free fallback data

Forbidden visible action language unless explicitly disabled or blocked:

- `BUY`
- `SELL`
- `EXECUTE`
- `LIVE`
- `LIVE DEPLOY`
- `REAL CAPITAL`
- `BROKER SUBMIT`
- `PLACE ORDER`

Allowed read-only language:

- `Review`
- `Inspect`
- `Validate`
- `Open Evidence`
- `Open Source`
- `View Risk`
- `View Order Detail`
- `Disabled`
- `Blocked`
- `Requires Governance Change`

If forbidden language appears in code, story args, fixtures, or screenshots, the validator must prove it is disabled/blocked and tied to governance reasons.

## Blocked/Disabled Action Display Rules

Disabled action surfaces must show:

- `actionState = disabled`
- `disabledReason`
- `requiredGovernanceChange`
- current project status boundary
- source or control-state blocker when applicable

No disabled action component may have a hidden broker submit, DB write, paper promote, live promote, or real-capital handler.

## Implementation Start Gate

Foundation component implementation may continue only after a future task confirms:

1. Expo Development Build command is runnable or explicitly blocked with evidence.
2. read-model fixture source is selected.
3. source-derived fixture payloads are created from `08_FRONTEND_READ_MODEL_CONTRACT.md`.
4. screenshot QA command and device preset are runnable or explicitly blocked with evidence.
5. NativeWind is either installed with typecheck evidence or remains deferred with current reason.
6. no strategy/deployment/paper/live/broker/real-capital permission has changed.

Until then, frontend work remains scaffold/foundation hardening only.

Task3806 decisions:

- Storybook path: keep web-vite Storybook for now. On-device Storybook is deferred until a native-device QA task needs it and can own Expo Router/Metro entry wrapping.
- NativeWind: `DEFERRED_WITH_REASON_TASK3806`. Official install paths add Metro/Babel/CSS configuration and Expo web Metro assumptions; the current scaffold is stable with tokens/style props and Storybook web-vite.
- Fixture source: static typed fixtures derived from `08_FRONTEND_READ_MODEL_CONTRACT.md` for Storybook foundation states only. Full app read path remains unselected.

Task3809 decisions:

- Full app read-model fixture source: generated JSON catalog fixture snapshot, scaffold-only, `NOT_AUTHORITY`.
- Fixture validator: `npm run validate:fixtures`.
- P0 domain component contracts represented in Storybook: `DecisionHeader`, `EvidenceList`, `ValidationReadinessPanel`, `RiskGate`, `DisabledActionBar`, `ChartWithSourceState`, `SystemHealth`, and `OrderStateSummary`.
- Product screen implementation remains blocked until a future task selects an authoritative backend/read-only source and screenshot QA is configured.

Task3811 decisions:

- GPT relay was used in autonomous override mode for a 10-loop pre-screen hardening pass.
- `npm run validate:pre-screen` is the local 10-loop gate.
- `npm test` now includes Storybook smoke, safety validation, fixture validation, and pre-screen validation.
- Product screen implementation remains blocked until screenshot QA and authoritative read source decisions are made.
