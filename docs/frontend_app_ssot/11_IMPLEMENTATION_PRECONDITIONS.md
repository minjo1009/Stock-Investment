# Frontend Implementation Preconditions

## Purpose

This document is the gate before Storybook setup, foundation components, or screen implementation.

It fixes the implementation path, command placeholders, fixture paths, screenshot QA scope, and safety-validator requirements so future Codex work does not invent app roots, commands, fixtures, QA flows, or unsafe trading affordances.

This document does not authorize strategy acceptance, paper permission, live permission, broker mutation, deployment readiness, or real-capital action.

## Current Status

| Item | Status |
| --- | --- |
| Frontend target | Expo Development Build, iOS-first |
| App scaffold | `NOT_CREATED` |
| Actual app root | `apps/ios-trader-brain` |
| Package manager | `REQUIRED_PRE_SCAFFOLD_DECISION` |
| Primary read path | `REQUIRED_PRE_SCAFFOLD_DECISION` |
| Storybook | `REQUIRED_PRE_SCAFFOLD_DECISION` |
| Screenshot QA | `REQUIRED_PRE_SCAFFOLD_DECISION` |
| Safety validator | `REQUIRED_PRE_SCAFFOLD_DECISION` |

## Actual App Root Path

Future app scaffold must use:

```text
apps/ios-trader-brain
```

Reason:

- `docs/frontend_app_ssot/10_IMPLEMENTATION_ARCHITECTURE.md` already names `apps/ios-trader-brain` as the preferred path.
- The repo currently has no tracked `apps/` scaffold.
- Using this reserved path prevents arbitrary future app roots such as `apps/tos-mobile` or `apps/trading-os-mobile`.

No app directory is created by this task.

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

## Command Contract

Because the app scaffold does not exist yet, commands are not runnable now.
They must be finalized by the scaffold task and then reflected here.

| Purpose | Required current value | Future command slot |
| --- | --- | --- |
| Package manager | `REQUIRED_PRE_SCAFFOLD_DECISION` | `npm` or another documented manager |
| Install dependencies | `REQUIRED_PRE_SCAFFOLD_DECISION` | scaffold-owned command |
| Expo Development Build | `REQUIRED_PRE_SCAFFOLD_DECISION` | `npm run ios` or scaffold-owned equivalent |
| Storybook | `REQUIRED_PRE_SCAFFOLD_DECISION` | `npm run storybook` or RN Storybook equivalent |
| Typecheck | `REQUIRED_PRE_SCAFFOLD_DECISION` | `npm run typecheck` |
| Lint | `REQUIRED_PRE_SCAFFOLD_DECISION` | `npm run lint` |
| Unit/component tests | `REQUIRED_PRE_SCAFFOLD_DECISION` | `npm test` or scaffold-owned equivalent |
| Screenshot QA | `REQUIRED_PRE_SCAFFOLD_DECISION` | `npm run qa:screenshot` or Maestro-backed equivalent |
| Maestro | `REQUIRED_PRE_SCAFFOLD_DECISION` | `npx maestro test .maestro` if Maestro is installed |
| Frontend safety validator | `REQUIRED_PRE_SCAFFOLD_DECISION` | validator command must be created before screen implementation |

Do not document a command as runnable until the scaffold task proves it.

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

The exact source must be selected before the fixture files are created.

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

Screen implementation must not start until these component contracts are represented in Storybook or an equivalent scaffold-approved component isolation layer.

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

Story args must come from the reserved fixture paths or typed fixture builders generated from them.

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

A frontend safety validator must exist before screen implementation expands.

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

Storybook setup and foundation component implementation may start only after a future task confirms:

1. `apps/ios-trader-brain` scaffold exists.
2. package manager is selected and lockfile policy is documented.
3. Expo Development Build command is runnable or explicitly blocked with evidence.
4. Storybook command is runnable or explicitly blocked with evidence.
5. typecheck/lint/test commands are runnable or explicitly blocked with evidence.
6. screenshot QA command and device preset are documented.
7. frontend safety validator command exists.
8. read-model fixture source is selected.
9. P0 fixture paths are created from `08_FRONTEND_READ_MODEL_CONTRACT.md`.
10. no strategy/deployment/paper/live/broker/real-capital permission has changed.

Until then, frontend work remains documentation and scaffold planning only.

