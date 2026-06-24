# Task3907 Portfolio Backtest Snapshot Display

## Summary

Task3907 connected the existing selected diagnostic backtest snapshot to the
Portfolio tab so `/portfolio` visibly reflects the current backtest read path.

## What Changed

- Portfolio now imports the generated read-only backtest snapshot fixture.
- Portfolio renders a compact diagnostic-only backtest summary card near the
  top of the tab.
- The mobile product validator now requires the Portfolio tab to keep the
  backtest diagnostic summary visible.
- The backtest snapshot validator now checks the Portfolio route binding.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains forbidden.
- No active DB, runtime API, broker, KIS, Alpaca, order, or real-capital system
  is connected from the frontend.

## Validation

- `cd apps/ios-trader-brain && npm run validate:backtest-snapshot`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run lint`
- `python scripts/task_registry_validate.py`
- `git diff --check`
