# Task 032: Execution Loop Foundation

## Goal
- Wrap one-shot execution with a safe repeat loop shell.

## Scope
- Added loop runner with kill switch, interval guard, single-process lock, and exception isolation.
- Added read-only position/open-order visibility per iteration.

## Main Files
- `src/app/run_trade_loop.py`
- `src/state/store.py`
- `tests/unit/test_structure.py`

## Status
- DONE
