# Task3839 Loop 3 Screenshot Regression Baseline

## Decision Summary

Loop 3 installs a baseline presence validator for existing Task3836 screenshot evidence.

This validator does not capture screenshots, compare pixels, approve visuals, or grant product/deployment readiness.

## Scope

- Verify Task3836 before and after2 screenshot manifests exist.
- Verify before and after2 contact sheets exist.
- Verify all 9 route IDs remain covered in both manifests.
- Verify manifest and capture authority remain `NOT_AUTHORITY`.

## Baseline Files Checked

- `data/artifacts/task_3836_frontend_actual_screenshot_capture/screenshot_capture_manifest.json`
- `data/artifacts/task_3836_frontend_actual_screenshot_capture/contact_sheet_iphone15_width.png`
- `data/artifacts/task_3836_frontend_actual_screenshot_capture/after2/screenshot_capture_manifest_after2.json`
- `data/artifacts/task_3836_frontend_actual_screenshot_capture/after2/contact_sheet_iphone15_width_after2.png`

## Validation

Run from `apps/ios-trader-brain`:

```bash
npm run validate:screenshot-baseline
```

Expected output:

```text
[SCREENSHOT_BASELINE_OK]
```

## Safety Boundary

Screenshots remain `NOT_AUTHORITY`.

No broker mutation, live order, paper promotion, DB/runtime connection, deployment readiness, strategy acceptance, or real-capital permission was added.
