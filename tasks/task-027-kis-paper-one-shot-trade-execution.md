# Task 027 - KIS Paper One-Shot Trade Execution

## Goal
- Add a runnable one-shot paper trade entrypoint.
- Keep existing architecture contracts intact.

## Scope
- Added `src/integration/kis_client.py` minimal US paper API calls:
- quote
- order submit
- order status check
- Added `src/integration/slack_client.py` webhook sender.
- Added `src/app/run_trade_once.py` end-to-end run flow.

## Flow
1. Load runtime guard (`control_state`) from `trading.db`.
2. Fetch current price for `AAPL`.
3. Send Slack order-decision report.
4. Submit paper order.
5. Poll status up to 10 times.
6. Send Slack fill result (or timeout).

## Validation
- `python -m unittest tests.unit.test_structure -v` passes.
- Runtime execution path validated via `python -m app.run_trade_once` with `PYTHONPATH=src`.

## Notes
- This task focuses on minimal executable pipeline, not full production orchestration.
