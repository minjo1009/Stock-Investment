# Task3908 Portfolio Backtest Positions Display

## Summary

Task3908 extended the selected diagnostic backtest frontend snapshot beyond the
summary card so the Portfolio holdings table and selected-detail card display
symbol-level diagnostic trade summaries.

## What Changed

- The frontend backtest snapshot builder now reads the selected Task3903 trade
  CSV and aggregates diagnostic position summaries by symbol.
- The generated JSON snapshot and TypeScript fixture now include
  `diagnosticPositions`.
- The Portfolio tab maps `diagnosticPositions` into the holdings table before
  falling back to placeholder rows.
- Validators now require diagnostic position summaries and the Portfolio route
  binding.

## Safety Boundary

- The displayed rows are diagnostic backtest summaries, not broker/account
  positions.
- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation, paper permission, and live permission remain forbidden.
- No active DB, runtime API, broker, KIS, Alpaca, order, or real-capital system
  is connected from the frontend.

## Validation

- `python -m py_compile scripts/build_frontend_backtest_snapshot.py scripts/validate_frontend_backtest_snapshot.py`
- `python scripts/build_frontend_backtest_snapshot.py`
- `python scripts/validate_frontend_backtest_snapshot.py`
- `cd apps/ios-trader-brain && npm run validate:backtest-snapshot`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run lint`
