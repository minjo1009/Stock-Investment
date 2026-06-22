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
| Primary read path | `REQUIRED_POST_SCAFFOLD_HARDENING` |
| Storybook | `npm run storybook`; smoke validation via `npm run storybook:smoke` |
| Screenshot QA | `REQUIRED_POST_SCAFFOLD_HARDENING` |
| Safety validator | `npm run validate:safety` |
| NativeWind | `DEFERRED_WITH_REASON_TASK3805` |

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
| Styling | NativeWind |
| Component base | React Native Reusables where practical |
| Story isolation | Storybook |
| Mobile flow QA | Maestro if selected by scaffold task |
| NativeWind | Deferred until Task3806 or later because stable/current install paths add Tailwind/Metro/Babel surface area before components use `className` |

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
| Typecheck | `npm run typecheck` | validated in Task3804 |
| Lint | `npm run lint` | scaffold boundary lint validated in Task3805 |
| Unit/component tests | `npm test` | Storybook story export smoke plus safety validator validated in Task3805 |
| Screenshot QA | `REQUIRED_POST_SCAFFOLD_HARDENING` | `npm run qa:screenshot` currently blocks intentionally |
| Maestro | `REQUIRED_POST_SCAFFOLD_HARDENING` | not installed in Task3804 |
| Frontend safety validator | `npm run validate:safety` | hardened and validated in Task3805 |

Do not document a command as runnable until a task proves it.

## Read Model Fixture Paths

Future Storybook and component fixtures must derive from `docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md`.

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

Fixture source path must be one of:

- generated JSON catalog from the backend
- read-only runtime API response
- read-only SQLite export transformed into this contract

The exact source must be selected before fixture payload files are created. Task3804 created only the fixture directory placeholder.

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
