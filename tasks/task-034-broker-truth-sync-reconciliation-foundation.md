# Task 034: Broker Truth Sync / Reconciliation Foundation

## Goal
- Compare broker-authoritative state with local state before submit and block on mismatch/error.

## Scope
- Added reconciliation check before submit.
- Persisted reconciliation runs/events.
- Added CLI visibility for reconciliation status.

## Main Files
- `src/app/reconciliation.py`
- `src/app/run_trade_once.py`
- `src/state/store.py`
- `src/app/report_recent_runs.py`
- `tests/unit/test_structure.py`

## Status
- DONE
