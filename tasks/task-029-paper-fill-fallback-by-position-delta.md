# Task 029 - Paper Fill Fallback by Position Delta

## Goal
- Stabilize fill confirmation for KIS paper mode where fill query can be delayed or unavailable.

## Scope
- Added `get_position_quantity(symbol)` in `src/integration/kis_client.py`.
- Updated `src/app/run_trade_once.py` polling logic:
- Primary path: order status query
- Fallback path: position delta (`before_qty + ordered_qty`) confirms fill

## Fallback Rule
- If status is not `FILLED` but position quantity increased to expected level, treat as `FILLED`.

## Validation
- Integrated run path verified during live paper runs.
- Structure tests continue to pass.

## Notes
- This fallback is intentionally minimal for paper-account behavior differences.
- Production reconciliation remains a separate contract area.
