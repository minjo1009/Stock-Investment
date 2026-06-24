# Task3905 Backtest Snapshot Read Path

## Summary

Task3905 installed the first frontend-safe path for displaying diagnostic
backtest results without connecting the app to active DB, broker, paper account,
live runtime, or raw artifact discovery.

## What Changed

- Added the frontend SSOT contract for a selected backtest snapshot read path.
- Added a typed read-model fixture for the selected Task3903 diagnostic replay
  summary.
- Added a validator that preserves `NOT_AUTHORITY`, diagnostic-only display,
  strategy/deployment/real-capital hard state, and direct DB/API/broker import
  prohibitions.
- Added the validator to the frontend package scripts and test chain.

## GPT Consult

- Relay mode: `single_gpt_consult`.
- GPT mode intended: Agent Mode with GitHub enabled for `minjo1009/Stock-Investment`.
- Capture status: `BLOCKED_AUTOMATION_NO_GPT_CAPTURE`.
- Blocker: Chrome browser automation exposed an incompatible API surface for
  the required GPT relay methods in this session.
- Result: No GPT review is claimed. Codex proceeded from repository operating
  state, Task3903 report evidence, and frontend data contract evidence.

## Source Evidence

- `docs/operating_system/project_operating_state.md`: Task3903 current replay
  summary and hard-state preservation.
- `docs/reports/task_3903_stage1_sec_neutral_attach_same_experiment_replay/stage1_sec_neutral_attach_same_experiment_replay_report.md`:
  selected policy, full L5 rows, SEC attached rows, final equity, CAGR, MDD,
  trades, and hard-state preservation.
- `docs/frontend_data_contract.md`: UI provenance and prohibited mixing rules.

## Boundaries Preserved

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains forbidden.
- Missing chart/equity-curve source remains `SOURCE_NOT_ATTACHED`, not inferred
  or synthesized.

## What This Does Not Do

- Does not run a new backtest.
- Does not choose the latest backtest by file timestamp.
- Does not connect frontend to `trading.db`.
- Does not connect frontend to runtime API, KIS, Alpaca, broker, paper, or live
  account systems.
- Does not make HOME/PORTFOLIO/BRAIN show account truth.
- Does not grant paper, live, deployment, strategy, or real-capital readiness.

## Validation

- `cd apps/ios-trader-brain && npm run validate:backtest-snapshot`
- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `python scripts/task_registry_validate.py`
- `git diff --check`
