# Scaffold-only Screen Assembly Boundary

## Purpose

This document defines the limited frontend implementation class that may start before product screen implementation is authorized.

It exists because the user asked to begin frontend real implementation, while `11_IMPLEMENTATION_PRECONDITIONS.md` still blocks product screen implementation until an authoritative read source and screenshot QA evidence are selected.

## Current Problem

`apps/ios-trader-brain` has an Expo Router scaffold, read-only placeholder tabs, P0 foundation/generic/domain components, and scaffold-only JSON fixtures.

The current fixtures are useful for screen assembly and Storybook smoke work, but they remain `NOT_AUTHORITY`. They do not prove backend truth, source truth, broker truth, product readiness, paper permission, live permission, deployment readiness, or real-capital permission.

## Non-Authorization Rule

Scaffold-only screen assembly is not strategy acceptance.

Scaffold-only screen assembly is not deployment readiness.

Scaffold-only screen assembly is not paper or live trading permission.

Scaffold-only screen assembly is not broker mutation permission.

Scaffold-only screen assembly is not real-capital permission.

The hard project state remains:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Definitions

### Scaffold-only Screen Assembly

Scaffold-only screen assembly means:

- screen UI may be assembled from existing read-model JSON fixtures
- fixtures remain `NOT_AUTHORITY`
- no source truth is inferred
- no backend truth is inferred
- no broker truth is inferred
- no production read path is inferred
- no trading permission is inferred
- no deployment readiness is inferred
- no paper/live permission is inferred
- no real-capital permission is inferred
- the screen visibly surfaces read-only, scaffold-only, and `NOT_AUTHORITY` boundaries

### Product Screen Implementation

Product screen implementation means a screen is being prepared as a product-quality operating surface that can rely on an authoritative read path, screenshot QA evidence, device-flow evidence, and production data-source governance.

Product screen implementation remains blocked.

## Allowed Scaffold-only Screen Assembly

After this boundary exists, a future selected loop may assemble scaffold-only screens from existing fixtures and existing read-only components.

Allowed future loop candidates:

- `HOME v0` scaffold-only fixture-backed assembly
- `Candidate Detail v0` scaffold-only fixture-backed assembly

Both candidates must remain read-only, fixture-backed, and `NOT_AUTHORITY`.

## Still-blocked Product Screen Implementation

The following remain blocked until future authoritative operating documents explicitly change them:

- authoritative backend read-source integration
- runtime API integration
- active DB integration
- broker API integration
- KIS or Alpaca integration
- paper/live operating promotion
- production screenshot QA claims
- iOS development build readiness claims
- deployment readiness claims
- real-capital readiness claims

## Allowed Data Sources

For future scaffold-only screen assembly, the only allowed initial data sources are existing scaffold fixtures:

- `apps/ios-trader-brain/src/mocks/fixtures/home.json`
- `apps/ios-trader-brain/src/mocks/fixtures/candidate-detail.json`
- other existing `apps/ios-trader-brain/src/mocks/fixtures/*.json` files only if explicitly selected by a future loop

These sources remain fixture evidence only and are not authority.

## Forbidden Data Sources

Scaffold-only screen assembly must not read from or connect to:

- active `trading.db`
- runtime API
- broker API
- KIS
- Alpaca
- paper/live execution services
- real-capital account sources
- any mutation-capable account, order, or broker surface

## Required Visual Boundaries

Each scaffold-only screen must visibly surface, directly or through existing components:

- read-only state
- fixture-backed state
- `NOT_AUTHORITY` status
- source freshness state when present
- blockers when present
- disabled trading action state when present
- current hard state when applicable: `NOT_ACCEPTED`, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, `FORBIDDEN`

Stale, missing, unknown, and blocked states must be visible. They must not be hidden behind healthy-looking portfolio, candidate, order, or system summaries.

## Required Component Sources

Scaffold-only screens should use existing P0 components first:

- `ScreenContainer`
- `SectionContainer`
- `AppText`
- `Badge`
- `CardContainer`
- `MetricCard`
- `StatusRow`
- `SourceFreshnessBadge`
- `BlockerList`
- `DecisionHeader`
- `EvidenceList`
- `ValidationReadinessPanel`
- `RiskGate`
- `DisabledActionBar`
- `ChartWithSourceState`
- `SystemHealth`
- `OrderStateSummary`

New components are allowed only when a future selected loop proves they are reusable, props-only, read-only, and not screen-specific business logic.

## Required Fixture Boundaries

Fixture-backed screens must state or encode that:

- fixture payloads are `NOT_AUTHORITY`
- fixture payloads are not live source evidence
- fixture payloads are not broker truth
- fixture payloads are not runtime permission
- fixture payloads are not strategy validation
- fixture payloads are not deployment evidence

No code may infer missing source fields as negative evidence. Missing, stale, unknown, and blocked remain explicit states.

## Required Safety Copy

Scaffold-only screens must avoid language that implies execution permission.

Allowed intent language:

- Review
- Inspect
- Validate
- Open Evidence
- Open Source
- View Risk
- View Order Detail
- Disabled
- Blocked
- Requires Governance Change

Any future disabled action affordance must expose:

- disabled state
- disabled reason
- required governance change
- no hidden mutation handler

## Allowed Loop 2 Candidate: HOME v0

`HOME v0` may be implemented in a future selected loop as a scaffold-only fixture-backed screen.

Required boundaries:

- read from `home.json` or an explicit typed wrapper around that fixture only
- show portfolio, brain, attention, freshness, and blocker summaries as fixture-backed
- show stale/missing/unknown/blocker states if present
- preserve fixed top-level IA: `HOME / BRAIN / PORTFOLIO / ORDERS / SYSTEM`
- add no DB, runtime, broker, paper/live, or real-capital connection

## Allowed Loop 3 Candidate: Candidate Detail v0

`Candidate Detail v0` may be implemented in a future selected loop as a scaffold-only fixture-backed screen.

Required boundaries:

- read from `candidate-detail.json` or an explicit typed wrapper around that fixture only
- render the six-section detail frame: Decision Summary, Thesis-Logic, Validation-Readiness, Evidence, Risk, Next Action
- show disabled action state and governance reason
- preserve evidence and source freshness visibility
- add no DB, runtime, broker, paper/live, or real-capital connection

## Acceptance Criteria

A scaffold-only screen assembly loop passes only if:

- the loop is explicitly selected in the loop ledger or task report
- source fixtures remain `NOT_AUTHORITY`
- read-only and fixture-backed boundaries are visible
- stale/missing/unknown/blocked states remain visible
- no mutation-capable handler or import is added
- no app code claims operational readiness
- `npm run typecheck`, `npm run lint`, `npm test`, `npm run validate:safety`, and `npm run validate:fixtures` pass when app code changes
- `python scripts/task_registry_validate.py` and `git diff --check` pass

## Failure Criteria

The loop fails if it:

- treats fixtures as authoritative
- hides stale/missing/unknown/blocker states
- connects to active DB, runtime API, broker API, KIS, Alpaca, paper/live services, or real-capital sources
- adds a mutation handler
- claims paper/live/deployment/real-capital readiness
- claims strategy acceptance
- removes the product screen implementation blocker
- bypasses screenshot QA or authoritative read-source requirements for product readiness

## Validation Checklist

Before closing any scaffold-only screen assembly loop:

1. Confirm changed files are limited to the selected loop scope.
2. Confirm fixture use is visible as `NOT_AUTHORITY`.
3. Confirm read-only state is visible.
4. Confirm disabled or blocked action states have governance reasons.
5. Confirm no DB/runtime/broker/KIS/Alpaca imports were added.
6. Confirm no package/config/tooling change occurred unless explicitly selected.
7. Run the required validators for the files changed.
8. Update the task report, artifact manifest, task registry, and loop ledger.

## Safety Boundaries

This document authorizes only narrow scaffold-only screen assembly in future selected loops.

It does not authorize product screen implementation, source authority, runtime integration, broker mutation, paper/live operation, deployment readiness, or real-capital use.
