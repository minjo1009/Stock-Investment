# Frontend App SSOT Pack

This page summarizes the current frontend SSOT direction and points to the canonical pack in `docs/frontend_app_ssot/`.

Historical input came from the 2026-06-22 DOCX SSOT pack received from Downloads:

- `C:/Users/minjo/Downloads/00_PROJECT_SSOT.md.docx`
- `C:/Users/minjo/Downloads/01_DETAIL_ARCHITECTURE.md.docx`
- `C:/Users/minjo/Downloads/02_DESIGN_SYSTEM.md.docx`
- `C:/Users/minjo/Downloads/03_IMPLEMENTATION_ARCHITECTURE.md.docx`

This page is a routing memory for future frontend/app work. It does not supersede operating state, registry rows, reports, artifact manifests, validator output, or the canonical pack in `docs/frontend_app_ssot/`.

## Fixed Product Contract

- Product mission: support quantitative strategy development and execution through evidence-driven research, validation, paper/shadow review, and deployment gating.
- Core chain: every decision must show `decision -> reason/thesis -> evidence -> source`.
- Fixed top-level IA: `HOME`, `BRAIN`, `PORTFOLIO`, `ORDERS`, `SYSTEM`.
- Backtest, paper, and live are lifecycle states, not top-level navigation tabs.
- Strategy is an execution of a candidate in a validation or deployment context, not the parent object of the candidate.

## Universal Detail Frame V2

Every detail workspace should use:

1. `Decision Summary`
2. `Thesis / Logic`
3. `Validation / Readiness`
4. `Evidence`
5. `Risk`
6. `Next Action`

This applies to Candidate, Position, Chain, Risk, and Order workspaces.

## Detail Workspaces

| Workspace | Primary question | Required links |
| --- | --- | --- |
| Candidate Detail | Should this candidate progress in lifecycle? | Position, Risk, Order |
| Position Detail | Is the holding thesis still valid and sized correctly? | Candidate, Risk, Order |
| Chain Detail | What sequence led from signal to validation/order? | Candidate, Position, Risk, Order |
| Risk Detail | Which exposures, limits, and blockers matter now? | Candidate, Position, Order |
| Order Detail | Is the order purpose, status, and execution quality justified? | Candidate or Position, Risk |

## Design System Memory

- Use centralized tokens for color, typography, spacing, and elevation.
- Keep spacing on a 4 px grid.
- Use concise lifecycle/status badges for candidate states and trading modes.
- Cards are containers for Summary, Evidence, Risk, and Action, but should not obscure source/provenance.
- Charts, tables, and gauges must carry source references when they support a decision.
- Destructive actions require confirm/undo patterns. In this repo, execution actions remain blocked unless a future status document explicitly changes permissions.

## Implementation Direction

The active implementation direction is Expo Development Build, iOS-first mobile app:

- Expo Router for navigation.
- React Native plus TypeScript for app code.
- NativeWind for styling.
- React Native Reusables where practical.
- Skia for micro charts.
- TradingView Lightweight Charts through WebView when required for main charts.
- Storybook and screenshot QA for component/state verification.

The prior React plus TypeScript web structure is retained as design input only. For this repository, adapt frontend work carefully because the current backend is Python/DB-heavy. Do not create execution authority in the frontend.

## Current Repo Boundary

- Latest backend/runtime line remains Task3761-3800.
- Latest L7 bridge line remains Task3391-3400: read-only frontend models from runtime decisions.
- Latest mobile/cockpit history remains useful for display and migration patterns, not for route or stack authority.
- Canonical frontend pack: `docs/frontend_app_ssot/`.
- Current app scaffold: `apps/ios-trader-brain` from Task3804. It contains placeholder tabs only, not product screens.
- Current Storybook/QA baseline: Task3805 adds runnable Storybook web runtime, scaffold lint/test, and hardened frontend safety validator.
- Any frontend must display blockers, stale source state, and provenance rather than hiding them behind polished UI.

## Next Build Shape

1. Confirm the read-model endpoint/catalog source before fixtures are created.
2. Create source-derived fixture payloads for foundation/domain Storybook states.
3. Map current DB/runtime catalog fields into the five IA tabs.
4. Implement read-only domain components before product screens.
5. Add trading actions only as disabled/blocked affordances until governance allows otherwise.
6. Validate with frontend continuity, source freshness, no-live-order, no-broker-mutation, and screenshot QA checks.

Standing status:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
