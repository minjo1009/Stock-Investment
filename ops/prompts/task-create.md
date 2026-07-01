# Task Create Prompt

## Required Task View

Every task must start from this view:

```text
Task ID:
Layer:
Work Type:
Specific Work:
Title:
```

Use this title shape:

```text
TASK-#### [Layer] [Work Type] Specific Work - Outcome
```

Good examples:

- `TASK-4192 [GOV] [DOCS_GOVERNANCE] Knowledge Surface Canonicalization - Registry Enforced`
- `TASK-4183 [L0-L4] [REALTIME_HEALTH] Realtime Backfill Recovery Audit - Blockers Classified`
- `TASK-4101 [UI] [VALIDATOR] Storybook Context Bundle Gate - Required Inputs Enforced`

## Layer Taxonomy

- `L0`: raw source acquisition, provider fetch, raw/cache ledger, realtime collection, historical backfill, source freshness
- `L1`: normalization, source packet, ticker/entity mapping, source-time certification, L1 blocker burn-down
- `L2`: interpretation, feature admission, primitive facts, feature materialization, read-model handoff
- `L3`: relation graph, economic relationship, contradiction/coverage gap, graph quality
- `L4`: thesis bundle, evidence coverage, institutional quality, blocker taxonomy, scanner coverage
- `L5`: policy action, review-only hold/reduce/exit/rerisk, risk clamp, exit score
- `L6`: execution safety, broker truth, order lifecycle, kill switch, paper/live permission checks
- `UI`: frontend/read-only cockpit, Storybook, screenshot QA, UX surface work
- `GOV`: registry, docs governance, validators, context bundles, operating prompts

## Required Fields

- Task ID
- Layer
- Work Type
- Specific Work
- Purpose
- Background
- In Scope
- Out of Scope
- Inputs
- Outputs
- Target Files
- Dependencies
- Acceptance Criteria
- Tests / Validators
- Risks
- Safety Boundary

## Creation Rules

- Create a task when files, registries, validators, docs, prompts, or SSOTs will change.
- Do not create vague tasks named only cleanup, next, fix, or improve.
- Split tasks when layers, work types, acceptance criteria, or validators differ.
- Every task output must update `ops/task_registry.yaml`.
- New documents must update `ops/doc_registry.yaml`.

## Safety Boundary

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- Missing or stale data is `UNKNOWN_OR_BLOCKER`, never negative evidence.
