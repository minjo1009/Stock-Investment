# Task3836 Frontend Screenshot Capture Loop

## Decision Summary

Task3836 executed the requested 5-loop GPT-Codex frontend pass.

The task converted Task3834's screenshot target validation into actual Chrome-headless web-preflight screenshot evidence, then performed one bounded P1 scaffold visual repair for screenshot-evidenced status badge clipping.

This task does not grant product readiness, visual approval beyond the narrow P1 repair, backend/source integration, paper/live permission, deployment readiness, broker mutation permission, or real-capital permission.

Strategy remains `NOT_ACCEPTED`, deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and real capital remains `FORBIDDEN`.

## Loop Summary

1. GPT expert repo/screenshot planning selected screenshot capture as the next evidence-first task.
2. Codex captured 18 PNG screenshots for 9 scaffold routes across 2 mobile viewport presets.
3. GPT reviewed capture evidence and classified right-edge clipped governance/status badges as P1, not P0.
4. Codex applied a bounded P1 repair in `Badge` and `StatusRow`, then recaptured after2 screenshots.
5. GPT reviewed after2 evidence as PASS and recommended report-only closeout with remaining density concerns deferred as P2.

## What Changed

- Added actual screenshot evidence under `data/artifacts/task_3836_frontend_actual_screenshot_capture/`.
- Added before, after, and final after2 capture manifests/contact sheets.
- Updated `apps/ios-trader-brain/src/components/foundation/badge.tsx` with max-width and flex-shrink safety.
- Updated `apps/ios-trader-brain/src/components/generic/status-row.tsx` so status badges stack below labels and long status/source tokens gain invisible break opportunities.

## Screenshot Evidence

Before evidence:

- `data/artifacts/task_3836_frontend_actual_screenshot_capture/screenshot_capture_manifest.json`
- `data/artifacts/task_3836_frontend_actual_screenshot_capture/contact_sheet_iphone15_width.png`

Intermediate after evidence:

- `data/artifacts/task_3836_frontend_actual_screenshot_capture/after/screenshot_capture_manifest_after.json`
- `data/artifacts/task_3836_frontend_actual_screenshot_capture/after/contact_sheet_iphone15_width_after.png`
- The first repair attempt did not fully remove right-edge clipping, so this evidence is retained as non-authoritative audit context.

Final after2 evidence:

- `data/artifacts/task_3836_frontend_actual_screenshot_capture/after2/screenshot_capture_manifest_after2.json`
- `data/artifacts/task_3836_frontend_actual_screenshot_capture/after2/contact_sheet_iphone15_width_after2.png`

Result:

- 18 before PNG captures were produced.
- 18 final after2 PNG captures were produced.
- The repeated right-edge clipped red governance/status badges visible before repair are no longer visible in the final after2 contact sheet.
- Status badges remain visible.
- Long source/reference text wraps better but remains vertically dense; this is P2 and deferred.

## GPT Expert Result

GPT Loop 1 selected actual screenshot capture before visual repair.

GPT Loop 3 reviewed the capture evidence summary and classified the clipped status badges as P1.

GPT Loop 4 reviewed after2 evidence and returned PASS for scaffold-only closeout, with no remaining P0/P1 visual blockers from the after2 contact sheet.

GPT did not become source of truth. Repo files, screenshot artifacts, and validator outputs remain the project evidence.

## Safety Boundary

No DB/runtime/KIS/Alpaca/broker connection was added.

No active `trading.db` access was added.

No broker mutation, order submit/cancel/approve/reject handler, paper/live path, EAS deployment, source acquisition, replay, selector change, sizing change, strategy acceptance, deployment readiness, or real-capital permission was added.

Screenshots are `NOT_AUTHORITY` QA artifacts.

## Validation

Validation evidence:

- `cd apps/ios-trader-brain && npm run typecheck`: PASS
- `cd apps/ios-trader-brain && npm run lint`: PASS
- `cd apps/ios-trader-brain && npm test`: PASS
- `cd apps/ios-trader-brain && npm run validate:screen-boundary`: PASS
- `python scripts/task_registry_validate.py`: PASS
- `git diff --check`: PASS
- `git diff --cached --check`: PASS

## Residuals

- P2: long source/reference tokens still consume vertical space after wrapping.
- P2: bottom tab label size should be checked from individual original PNGs before any typography repair.
- Screenshot capture was performed through Chrome headless web-preflight, not iOS simulator or native device.

## Next

Recommended next work:

1. Run a focused P2 visual density review only if the user wants compact source/reference presentation.
2. Add simulator/device screenshot QA later if iOS-native evidence is required.
3. Keep authoritative read-source integration blocked until operating documents explicitly select it.
