# Task3904 — Mobile Center Column Fix

## Summary

Task3904 repaired the mobile web layout width calculation that made tab contents appear stuck to one side or overflow the phone viewport.

- `ScreenContainer` now renders a centered inner column inside the scroll view.
- Main tab screen styles no longer override the centered column with `width: "100%"`.
- `AppText` now shrinks within parent containers and stretches to the parent width, reducing long-copy overflow.
- HOME, PORTFOLIO, and BRAIN screenshots were recaptured after the fix.

## Visual Evidence

Final 390x844 captures:

- `data/artifacts/task_3904_mobile_center_column_fix/screenshots/home_final_390x844.png`
- `data/artifacts/task_3904_mobile_center_column_fix/screenshots/portfolio_final_390x844.png`
- `data/artifacts/task_3904_mobile_center_column_fix/screenshots/brain_final_390x844.png`

## DOM Position Evidence

Chrome-headless DOM measurement after the fix:

- HOME primary cards: `x=20`, `right=370`, `width=350`, document scroll width `390`.
- PORTFOLIO primary cards: `x=20`, `right=370`, `width=350`, document scroll width `390`.
- BRAIN primary cards: `x=20`, `right=370`, `width=350`, document scroll width `390`.

This confirms the visible phone viewport has 20px side margins and no page-level horizontal overflow.

## Validation

Executed from `apps/ios-trader-brain`:

- `npm run typecheck` — PASS
- `npm run validate:safety` — PASS
- `npm run validate:mobile-product-v1` — PASS
- `npm run validate:product-ia-reorder` — PASS

## Safety State

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No DB, broker, runtime API, paper/live order, deployment, or real-capital integration was added.
