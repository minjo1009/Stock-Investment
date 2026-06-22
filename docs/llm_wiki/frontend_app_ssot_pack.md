# Frontend App SSOT Pack

This page summarizes the 2026-06-22 DOCX SSOT pack received from Downloads:

- `C:/Users/minjo/Downloads/00_PROJECT_SSOT.md.docx`
- `C:/Users/minjo/Downloads/01_DETAIL_ARCHITECTURE.md.docx`
- `C:/Users/minjo/Downloads/02_DESIGN_SYSTEM.md.docx`
- `C:/Users/minjo/Downloads/03_IMPLEMENTATION_ARCHITECTURE.md.docx`

It is a routing memory for future frontend/app work. It does not supersede operating state, registry rows, reports, artifact manifests, or validator output.

## Fixed Product Contract

- Product mission: support quantitative strategy development and execution through evidence-driven research, validation, paper/shadow review, and deployment gating.
- Core chain: every decision must show `decision -> reason/thesis -> evidence -> source`.
- Fixed top-level IA: `HOME`, `BRAIN`, `PORTFOLIO`, `ORDERS`, `SYSTEM`.
- Backtest, paper, and live are lifecycle states, not top-level navigation tabs.
- Strategy is an execution of a candidate in a validation or deployment context, not the parent object of the candidate.

## Universal Detail Frame

Every detail workspace should use:

1. `Decision / Summary`
2. `Thesis / Logic`
3. `Evidence`
4. `Risk`
5. `Action`

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

The DOCX pack describes a React plus TypeScript web app architecture:

- `src/app`: providers, routing, theme, state setup.
- `src/features`: feature-owned components, hooks, services, and tests.
- `src/components`: shared cards, tables, charts, inputs, dialogs.
- `src/layouts`: dashboard and detail layouts.
- `src/services`: typed API clients and mappers.
- `src/state`: global stores or domain slices.
- `src/styles`: design tokens and global styles.
- Storybook is the isolation layer for UI component states.

For this repository, adapt this target carefully because the current backend is Python/DB-heavy. Do not create execution authority in the frontend.

## Current Repo Boundary

- Latest backend/runtime line remains Task3761-3800.
- Latest L7 bridge line remains Task3391-3400: read-only frontend models from runtime decisions.
- Latest mobile/cockpit history remains useful for display patterns, not for authority.
- Any frontend must display blockers, stale source state, and provenance rather than hiding them behind polished UI.

## Next Build Shape

1. Define a frontend read-model contract for the fixed IA.
2. Map current DB/runtime catalog fields into the five IA tabs.
3. Implement read-only screens first.
4. Add write actions only as disabled/blocked affordances until governance allows otherwise.
5. Validate with frontend continuity, source freshness, and no-live-order checks.

Standing status:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
