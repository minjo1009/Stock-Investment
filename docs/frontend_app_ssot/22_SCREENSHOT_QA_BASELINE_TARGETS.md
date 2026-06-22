# Screenshot QA Baseline Targets

## Status

Task3834 installs screenshot QA target validation only.

Task3834 did not perform screenshot capture. No screenshot artifact should be treated as product readiness, source truth, broker truth, deployment readiness, paper/live permission, or real-capital permission.

Task3836 later captured Chrome-headless web-preflight screenshots under `data/artifacts/task_3836_frontend_actual_screenshot_capture/`. Those screenshots remain `NOT_AUTHORITY` QA artifacts and do not grant visual approval, product readiness, deployment readiness, paper/live permission, or real-capital permission.

## Target Manifest

Canonical scaffold target manifest:

- `apps/ios-trader-brain/src/qa/screenshot-targets.json`

Validator:

- `cd apps/ios-trader-brain && npm run validate:screenshot-qa`
- `cd apps/ios-trader-brain && npm run qa:screenshot`

Both commands validate target readiness and explicitly report that screenshot capture was not run.

## Required Surfaces

The baseline target set includes:

1. `HOME`
2. `BRAIN`
3. `PORTFOLIO`
4. `ORDERS`
5. `SYSTEM`
6. `Candidate Detail`
7. `Position Detail`
8. `Order Detail`
9. `Chain Detail`

## Required Device Presets

The initial manifest records two web-preflight widths:

- `iphone-se-width`: 375 x 667
- `iphone-15-width`: 393 x 852

These are preflight dimensions only. Native iOS simulator evidence remains a future task.

## Boundaries

Screenshot QA may inspect visibility of:

- read-only state
- `NOT_AUTHORITY`
- blockers
- source freshness
- disabled actions
- route coverage
- small-width overflow risk

Screenshot QA must not claim:

- strategy acceptance
- deployment readiness
- paper/live permission
- broker mutation permission
- real-capital permission
- source/backend/broker truth
