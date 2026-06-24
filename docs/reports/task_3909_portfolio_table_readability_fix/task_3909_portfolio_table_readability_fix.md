# Task3909 Portfolio Table Readability Fix

## Summary

Task3909 fixed Portfolio tab table readability after diagnostic backtest
position summaries started rendering in the holdings table.

## What Changed

- Shortened Portfolio table column labels for mobile width.
- Replaced long secondary labels in metric cells with compact labels.
- Increased diagnostic metric column width from `104` to `132`.
- Reduced table amount formatting to whole-number display.
- Added validator coverage so narrow columns and long secondary labels do not
  regress.

## Safety Boundary

- Displayed rows remain diagnostic backtest summaries, not broker/account
  positions.
- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No active DB, runtime API, broker, paper/live, or real-capital system was
  connected.

## Validation

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:backtest-snapshot`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run lint`
- `python scripts/task_registry_validate.py`
- `git diff --check`
