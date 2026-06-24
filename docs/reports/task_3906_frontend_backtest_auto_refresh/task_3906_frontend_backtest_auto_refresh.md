# Task3906 Frontend Backtest Auto Refresh

## Summary

Task3906 implemented the first automatic refresh path from a selected diagnostic
backtest result into the read-only Expo frontend.

## What Changed

- Added `scripts/build_frontend_backtest_snapshot.py`.
- Generated `data/frontend_snapshots/current_backtest_snapshot.json`.
- Regenerated the app typed backtest fixture from the current snapshot.
- Hooked the Task3903 runner so a completed Task3903 replay refreshes the
  frontend snapshot automatically.
- Added a HOME diagnostic-only backtest summary card.
- Added `scripts/validate_frontend_backtest_snapshot.py`.
- Extended the Task3903 validator to confirm the frontend current snapshot
  matches the selected Task3903 result.

## Displayed Result

- Selected task: `Task3903`.
- Selected policy: `exit_chain_repaired_soft_boost_cap_top2_v1`.
- Final equity: `6537.58`.
- Total return: `553.758%`.
- CAGR: `0.4388`.
- MDD: `-0.282109`.
- Trade count: `124`.
- Equity curve points attached: `62`.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains forbidden.
- The frontend still does not read active DB, broker, paper, live, runtime API,
  KIS, Alpaca, or raw artifact folders directly.

## Validation

- `python -m py_compile scripts/build_frontend_backtest_snapshot.py scripts/validate_frontend_backtest_snapshot.py scripts/run_task3903_stage1_sec_neutral_attach_same_experiment_replay.py scripts/validate_task3903_stage1_sec_neutral_attach_same_experiment_replay.py`
- `python scripts/validate_frontend_backtest_snapshot.py`
- `python scripts/validate_task3903_stage1_sec_neutral_attach_same_experiment_replay.py`
- `cd apps/ios-trader-brain && npm run validate:backtest-snapshot`
- `cd apps/ios-trader-brain && npm run typecheck`
