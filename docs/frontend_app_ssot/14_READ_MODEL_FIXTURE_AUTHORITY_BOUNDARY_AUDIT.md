# Read Model Fixture Authority Boundary Audit

## Purpose

Fix the boundary for current read-model fixtures before product screen implementation.

## Current Status

Current full-app fixture source is `GENERATED_JSON_CATALOG_FIXTURE_SNAPSHOT_TASK3809_NOT_AUTHORITY`.

Current JSON fixtures are scaffold-only read-model contract fixtures. They are `NOT_AUTHORITY`.

## Non-Authorization Rule

Fixtures do not authorize product screens, backend read-path authority, broker actions, paper/live operation, deployment readiness, or real-capital use.

## Fixture Inventory

- `apps/ios-trader-brain/src/mocks/fixtures/catalog-manifest.json`
- `apps/ios-trader-brain/src/mocks/fixtures/home.json`
- `apps/ios-trader-brain/src/mocks/fixtures/brain.json`
- `apps/ios-trader-brain/src/mocks/fixtures/candidate-detail.json`
- `apps/ios-trader-brain/src/mocks/fixtures/chain-detail.json`
- `apps/ios-trader-brain/src/mocks/fixtures/portfolio.json`
- `apps/ios-trader-brain/src/mocks/fixtures/position-detail.json`
- `apps/ios-trader-brain/src/mocks/fixtures/orders.json`
- `apps/ios-trader-brain/src/mocks/fixtures/order-detail.json`
- `apps/ios-trader-brain/src/mocks/fixtures/system-health.json`

## Authority Boundary

Current fixtures are not:

- backend truth
- broker truth
- source truth
- active DB truth
- trading permission
- paper/live permission
- deployment readiness
- real-capital permission
- production read-path authority

## What Fixtures Can Prove

1. Read-model shape can be represented.
2. Storybook/domain component props can be exercised.
3. Stale/missing/unknown/blocked states can be visually represented.
4. Disabled action display can be scaffold-tested.
5. Fixture validator can check schema/shape consistency.

## What Fixtures Cannot Prove

Fixtures cannot prove real backend data correctness, source freshness truth, broker truth, order validity, strategy validity, paper/live readiness, deployment readiness, real-capital readiness, production API readiness, active `trading.db` authority, economic interpretation correctness, candidate lifecycle truth, or execution permission.

## Future Authoritative Read Source Requirements

A future authoritative read source must be selected separately from these options:

1. backend-generated JSON catalog
2. read-only runtime API response
3. read-only SQLite export transformer

Minimum proof:

- read-only path only
- no direct active `trading.db` frontend access
- source lineage attached
- source freshness explicit
- missing/stale/unknown preserved as `UNKNOWN/BLOCKER`
- no broker mutation
- no paper/live promotion
- no real-capital path
- deterministic artifact generation
- payload maps to `08_FRONTEND_READ_MODEL_CONTRACT.md`

## Screen Implementation Gate

Product screen implementation remains blocked until fixture authority is acknowledged, screenshot QA preflight exists, Maestro preflight exists, domain story gap audit is complete, the selected screen receives explicit loop authorization, scope remains read-only, and production authority is not inferred from scaffold fixtures.

## Acceptance Criteria

This audit passes only if fixtures are explicitly marked `NOT_AUTHORITY`, inventory is listed, fixture capabilities and limits are separated, future read-source requirements are defined, active `trading.db` frontend access remains forbidden, and no fixture payload, validator, or package script is changed.

## Failure Criteria

The audit fails if fixtures are treated as source/backend/broker truth, used to infer trading readiness or paper/live permission, used to authorize product screens, or if missing/stale/unknown is treated as negative evidence.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, DB/runtime connection, package change, fixture edit, or validator edit is authorized.
