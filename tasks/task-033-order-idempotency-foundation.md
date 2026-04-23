# Task 033: Order Idempotency Foundation

## Goal
- Block duplicate submissions for the same order intent.

## Scope
- Added deterministic `order_intent_key` contract.
- Added pre-submit duplicate block based on open/pending records.

## Main Files
- `src/state/store.py`
- `src/app/run_trade_once.py`
- `src/app/report_recent_runs.py`
- `tests/unit/test_structure.py`

## Status
- DONE
