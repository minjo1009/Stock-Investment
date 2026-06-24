# Backtest Snapshot Read Path

## Purpose

This document defines the first safe path for showing diagnostic backtest results
inside the read-only frontend app.

The app must not scan arbitrary backtest outputs, active databases, broker
records, paper accounts, or live runtime state to find the "latest" result. The
app may read only a selected, validated, provenance-attached snapshot prepared
for frontend display.

## Current Decision

- Frontend source mode: `READ_ONLY_SELECTED_BACKTEST_SNAPSHOT`.
- First selected source: Task3903 stage-1 SEC neutral-attach same-experiment replay.
- UI status: diagnostic-only backtest summary.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Broker mutation: forbidden.
- Paper/live permission: forbidden.

## Snapshot Rules

The frontend snapshot must include:

1. `contractVersion`
2. `snapshotType`
3. selected task id and report path
4. selected policy id
5. source artifact references
6. generated timestamp
7. hard governance state
8. summary metrics
9. explicit blocker state for missing equity-curve/chart source
10. statement that the snapshot is not account truth, broker truth, paper truth,
    deployment readiness, strategy acceptance, or real-capital permission

## Automatic Update Policy

Automatic update is allowed only for the selected snapshot pointer, not for raw
backtest discovery.

Allowed:

- A validator may confirm that the selected snapshot is internally consistent.
- A future builder may overwrite the frontend snapshot after a new backtest run
  is explicitly selected by task/report governance.
- The UI may refresh from that selected snapshot.

Forbidden:

- The app must not read `trading.db` directly.
- The app must not inspect raw `data/artifacts` folders to infer the latest run.
- The app must not choose the newest file by timestamp.
- The app must not treat a passing backtest as strategy acceptance.
- The app must not show simulated fills as broker truth.
- The app must not imply paper/live readiness.

## First Implementation Boundary

Task3905 installs the frontend-side contract fixture and validator only. It does
not connect to a backend API, active DB, broker, paper account, live runtime, or
order system.

The HOME, PORTFOLIO, and BRAIN product screens may later consume this snapshot
only through a typed read-model adapter that preserves provenance and shows it
as diagnostic-only.

## Task3906 Implementation

Task3906 adds the first automatic update path:

- `scripts/build_frontend_backtest_snapshot.py` reads the selected backtest
  outputs and writes `data/frontend_snapshots/current_backtest_snapshot.json`.
- The same builder regenerates the app-side typed fixture so the Expo frontend
  can display the selected diagnostic result without scanning raw folders.
- `scripts/run_task3903_stage1_sec_neutral_attach_same_experiment_replay.py`
  calls the builder after its normal backtest report, decision, registry, and
  operating-state outputs are written.
- HOME displays a diagnostic-only backtest summary card from that fixture.
- `scripts/validate_frontend_backtest_snapshot.py` and
  `npm run validate:backtest-snapshot` enforce the snapshot boundary.

This implementation still does not connect the frontend to active DB, broker,
paper, live, runtime API, KIS, Alpaca, or real-capital systems.
