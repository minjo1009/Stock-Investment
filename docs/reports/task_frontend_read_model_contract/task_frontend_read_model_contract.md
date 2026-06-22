# Task Frontend Read Model Contract

## Decision Summary

- Verdict: `FRONTEND_READ_MODEL_CONTRACT_EXPANDED_DOCS_ONLY`
- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`

This task expands the frontend SSOT read-model contract into a screen-ready implementation gate.

No source code, DB row, scheduler, broker API, order path, replay, paper run, live run, deployment command, or real-capital state was changed.

## Quant Expert Report

The next frontend bottleneck is data contract clarity, not UI layout.

`docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md` now defines:

- one primary read-path selection rule
- common governance, freshness, blocker, disabled-action, evidence, and chart-source types
- app-shell read model
- screen inventory for `HOME`, `BRAIN`, `PORTFOLIO`, `ORDERS`, `SYSTEM`, and detail routes
- screen-by-screen view-model schemas
- stale/missing/unknown/blocked empty-state semantics
- explicit ban on invented ranking/confidence fields without backend authority
- Storybook/screenshot/safety-validator dependency on the read-model contract

This keeps the frontend as a query/read surface and prevents action labels or UI affordances from becoming execution authority.

## No-Background Decision-Maker Report

The frontend can now start from a data contract instead of inventing props during UI implementation.

The next implementation task must still choose the exact read path: generated JSON catalog, read-only runtime API, or read-only SQLite export.

This is not strategy acceptance. This is not deployment readiness. This is not paper/live permission.

## Artifact Manifest

See `artifact_manifest.csv`.

## Validation

- `python scripts/task_registry_validate.py`
- Manual read-only review of frontend SSOT read-model contract and task pointers.

