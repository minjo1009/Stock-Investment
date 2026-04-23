# Task 030-A: Fill Idempotency / Dedupe and Recent Report CLI

## Goal
- Prevent duplicate fill inserts and provide an operator-friendly recent report CLI.

## Scope
- Deterministic fill dedupe key and unique constraint.
- Duplicate-safe insert policy (`INSERT OR IGNORE`).
- Added recent run/order/fill reporting command.

## Main Files
- `src/state/store.py`
- `src/app/report_recent_runs.py`
- `tests/unit/test_structure.py`

## Status
- DONE
