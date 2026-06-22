# Task3834 Frontend Screenshot QA Baseline

## Decision Summary

Task3834 completed the requested next 10-loop frontend pass by installing a screenshot QA baseline and route/boundary validators for the scaffold-only app.

This task makes screenshot QA target selection runnable. It does not capture screenshots and does not grant product readiness.

Strategy remains `NOT_ACCEPTED`, deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and real capital remains `FORBIDDEN`.

## Quant Expert Report

### Scope

The 10 loops executed under this task were:

1. GPT expert repo review and next-loop ranking.
2. Screenshot target manifest.
3. Screenshot target validator.
4. `qa:screenshot` runnable target-validation command.
5. Route/deep-link scaffold validator.
6. Screen read-only boundary validator.
7. Test script consolidation.
8. Screenshot QA SSOT target note.
9. Task report, artifact manifest, and loop evidence.
10. Registry, wiki, operating-state, and validation closeout.

### What Changed

- Added `apps/ios-trader-brain/src/qa/screenshot-targets.json`.
- Added `apps/ios-trader-brain/src/qa/screenshot-qa-validator.mjs`.
- Added `apps/ios-trader-brain/src/qa/route-link-validator.mjs`.
- Added `apps/ios-trader-brain/src/qa/scaffold-screen-boundary-validator.mjs`.
- Updated `apps/ios-trader-brain/package.json` so `npm test` includes route, boundary, and screenshot target validation.
- Replaced `qa:screenshot` hardening placeholder with a runnable target validator that explicitly does not claim screenshot capture.
- Added `docs/frontend_app_ssot/22_SCREENSHOT_QA_BASELINE_TARGETS.md`.

### GPT Expert Result

The GPT expert reviewer read repo/Git state and selected screenshot QA tooling as the first next loop because Task3831 identified screenshot QA as the immediate bottleneck and visual repair without capture evidence would be speculative.

The expert also recommended route/deep-link guardrails and small-width stress checks after screenshot target tooling.

### Safety Boundary

No package install, DB/runtime/KIS/Alpaca/broker connection, active `trading.db` access, broker mutation, order submit/cancel/execute handler, paper/live path, EAS deployment, screenshot capture, source acquisition, replay, selector change, sizing change, strategy acceptance, deployment readiness, or real-capital permission was added.

The screenshot target manifest authority is `NOT_AUTHORITY` and capture status is `TARGETS_READY_CAPTURE_NOT_RUN`.

## No-Background Decision-Maker Report

The frontend now has runnable QA checks for the scaffold route set.

This means the app can verify which screens must be captured later, whether scaffold links resolve locally, and whether each route still shows read-only and `NOT_AUTHORITY` boundaries.

It does not mean screenshots were captured or the UI is visually approved.

## Artifact Manifest

See `artifact_manifest.csv`.

## Validation

Validation evidence:

- `cd apps/ios-trader-brain && npm run validate:routes`: PASS
- `cd apps/ios-trader-brain && npm run validate:screen-boundary`: PASS
- `cd apps/ios-trader-brain && npm run validate:screenshot-qa`: PASS
- `cd apps/ios-trader-brain && npm run qa:screenshot`: PASS, target validation only; capture not run
- `cd apps/ios-trader-brain && npm run typecheck`: PASS
- `cd apps/ios-trader-brain && npm run lint`: PASS
- `cd apps/ios-trader-brain && npm test`: PASS
- `cd apps/ios-trader-brain && npm run storybook:smoke`: PASS with non-blocking Vite tsconfig-paths warning
- `cd apps/ios-trader-brain && npm run validate:safety`: PASS
- `cd apps/ios-trader-brain && npm run validate:fixtures`: PASS
- `python scripts/task_registry_validate.py`: PASS
- `git diff --check`: PASS
- `git diff --cached --check`: PASS

## Next

Recommended next work:

1. Run actual screenshot capture through a controlled web or simulator path.
2. Record screenshot artifacts under `data/artifacts/task_3834_frontend_screenshot_qa_baseline/` or a successor task-specific directory.
3. Perform P0 visual repair only from captured evidence.
4. Keep authoritative read-source integration blocked.
