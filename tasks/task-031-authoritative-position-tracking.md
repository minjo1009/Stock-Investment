# Task 031: Authoritative Position Tracking

## Goal
- Build minimal authoritative position state from fills.

## Scope
- Added `positions` latest snapshot table and `position_events` append-only history table.
- Applied position update only when fill insert was accepted.

## Main Files
- `src/state/store.py`
- `src/app/run_trade_once.py`
- `src/app/report_recent_runs.py`
- `tests/unit/test_structure.py`

## Status
- DONE
