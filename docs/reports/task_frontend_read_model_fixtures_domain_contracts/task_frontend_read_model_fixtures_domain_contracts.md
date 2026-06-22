# Task Frontend Read Model Fixtures Domain Contracts

## Decision Summary

- Verdict: `READ_MODEL_FIXTURE_SNAPSHOT_AND_DOMAIN_CONTRACTS_INSTALLED`
- Requested prompt label: `Task3807`
- Recorded registry task: `Task3809`
- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`

Task3809 selects the first full app read-model fixture strategy, creates contract-shaped scaffold JSON fixtures, adds a fixture validator, and installs props-only P0 domain component contracts with Storybook coverage.

No product screen, HOME real UI, Candidate Detail real UI, DB connection, active `trading.db` access, runtime API connection, broker/API call, KIS/Alpaca integration, paper/live order path, deployment command, real-capital action, strategy acceptance, deployment readiness, paper/live permission, broker mutation permission, or real-capital permission was added.

The prompt named this work `Task3807`, but the current task registry already uses `Task3807` and `Task3808` for governance-skill work. This closeout is therefore recorded as `Task3809` to preserve registry continuity.

## Done

- Selected full app read-model fixture source:
  - `GENERATED_JSON_CATALOG_FIXTURE_SNAPSHOT_TASK3809_NOT_AUTHORITY`
- Added catalog manifest:
  - `apps/ios-trader-brain/src/mocks/fixtures/catalog-manifest.json`
- Added screen read-model JSON fixtures:
  - `home.json`
  - `brain.json`
  - `candidate-detail.json`
  - `chain-detail.json`
  - `portfolio.json`
  - `position-detail.json`
  - `orders.json`
  - `order-detail.json`
  - `system-health.json`
- Added read-model TypeScript screen types derived from `08_FRONTEND_READ_MODEL_CONTRACT.md`.
- Added `npm run validate:fixtures`.
- Added props-only P0 domain components:
  - `DecisionHeader`
  - `EvidenceList`
  - `ValidationReadinessPanel`
  - `RiskGate`
  - `DisabledActionBar`
  - `ChartWithSourceState`
  - `SystemHealth`
  - `OrderStateSummary`
- Added Storybook coverage for P0 domain components:
  - fresh source
  - stale source
  - missing source
  - unknown source
  - blocked state
  - disabled action state
  - chart missing
  - source not attached
- Updated scaffold lint, Storybook smoke, and frontend safety validator scope.

## Fixture Source Decision

Selected option: generated JSON catalog fixture snapshot.

Current manifest path:

```text
apps/ios-trader-brain/src/mocks/fixtures/catalog-manifest.json
```

Authority policy:

- The generated JSON fixture snapshot is scaffold-only.
- It is `NOT_AUTHORITY`.
- It is not backend truth.
- It is not broker truth.
- It is not source truth.
- It is not trading permission.
- It is not paper/live permission.
- It is not deployment readiness.
- It is not real-capital permission.

The future production read path must still be selected from one of:

- backend-generated JSON catalog
- read-only runtime API response
- read-only SQLite export transformer

The frontend still must not open active `trading.db` directly.

## Quant Expert Report

### Data Source And Source Readiness

No trading source, broker source, active DB source, runtime API, KIS source, Alpaca source, or live provider was read or mutated.

The only data artifacts are source-contract-derived scaffold JSON fixtures under `apps/ios-trader-brain/src/mocks/fixtures/`.

### Exact Join Keys

Not applicable. No joins were performed.

### Leakage Audit

No label, outcome, future return, candidate score, candidate rank, confidence score, symbol/date/price/time proximity matching, lifecycle inference, trading authority calculation, or source-readiness inference logic was added.

### Split/OOS Metrics

Not applicable. No backtest, replay, strategy validation, split/OOS measurement, or performance claim was performed.

### Failure Decomposition

Not applicable. This was a frontend data-contract and component-contract scaffold task.

### Cost/Slippage Stress

Not applicable. No PnL, order, execution, cost, slippage, sizing, or broker calculation changed.

### Remaining Blockers

- Full authoritative app read path remains future work.
- Screenshot QA remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- Maestro remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- iOS development build remains unvalidated in this Windows environment.
- NativeWind remains `DEFERRED_WITH_REASON_TASK3806`.
- Domain components are props-only contracts, not product screens.

## No-Background Decision-Maker Report

The app still has placeholder tabs only. This task adds the data payloads and domain component contracts needed before real screens begin.

The important change is that future screen work now has contract-shaped fixtures and Storybook-covered domain components for decisions, evidence, validation readiness, risk, disabled actions, chart source state, system health, and order state.

This does not change trading readiness. Strategy remains not accepted, deployment remains diagnostic-only, and real capital remains forbidden.

Next step: configure screenshot QA or start read-only domain composition work without connecting to DB, broker, runtime API, paper/live order, or real-capital systems.

## Validation

Required validation commands:

```powershell
cd apps/ios-trader-brain && npm run typecheck
cd apps/ios-trader-brain && npm run lint
cd apps/ios-trader-brain && npm test
cd apps/ios-trader-brain && npm run storybook:smoke
cd apps/ios-trader-brain && npm run validate:safety
cd apps/ios-trader-brain && npm run validate:fixtures
python scripts/task_registry_validate.py
git diff --check
git diff --cached --check
```

Validation results must not be interpreted as strategy acceptance, deployment readiness, paper/live permission, broker mutation permission, or real-capital permission.

## Artifact Manifest

See `artifact_manifest.csv`.
