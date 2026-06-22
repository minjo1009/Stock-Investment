# Task Frontend SSOT P0 Alignment

## Decision Summary

- Verdict: `FRONTEND_SSOT_P0_ALIGNMENT_DOCS_ONLY`
- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`

This task resolves the frontend SSOT conflict between the React/TypeScript web architecture note, the historical Expo Go 3052 cockpit, and the requested Expo Development Build iOS-first implementation target.

No source code, DB row, scheduler, broker API, order path, replay, paper run, live run, deployment command, or real-capital state was changed.

## Quant Expert Report

The active frontend target is now documented as an Expo Development Build, iOS-first read-only app.

The final app IA is fixed as `HOME / BRAIN / PORTFOLIO / ORDERS / SYSTEM`.

The universal detail frame is now V2:

1. `Decision Summary`
2. `Thesis / Logic`
3. `Validation / Readiness`
4. `Evidence`
5. `Risk`
6. `Next Action`

The frontend remains L7 display only. It must expose decisions, reasons, evidence, source freshness, blockers, provenance, and disabled action governance reasons. It must not infer execution permission from UI state, tests, paper-looking rows, or old cockpit artifacts.

## No-Background Decision-Maker Report

The frontend docs are now aligned enough to begin a future implementation task.

The next implementation task must still choose exact file paths, read-model endpoints, Storybook commands, screenshot QA commands, and no-live-order validators before adding app code.

This is not strategy acceptance. This is not deployment readiness. This is not paper/live permission.

## Artifact Manifest

See `artifact_manifest.csv`.

## Validation

- `python scripts/task_registry_validate.py`
- Manual read-only review of README, LLM wiki routing docs, operating-state entry, and frontend SSOT pack links.

