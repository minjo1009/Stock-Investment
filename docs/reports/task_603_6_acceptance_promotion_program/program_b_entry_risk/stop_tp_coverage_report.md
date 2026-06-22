## Problem

T603-6 Program B acceptance requires entry risk snapshots to cover exact runtime positions and populate STOP/TP thresholds from ATR14 without source approximation.
The validator must report snapshot_coverage, stop_price_populated, and take_profit_price_populated against `position_lifecycle.position_id` only.

## Evidence

- acceptance_status=FAIL
- decision_status=FAIL_STOP_TP_SOURCE_BLOCKED
- snapshot_coverage=1.0
- stop_price_populated=0.958333
- take_profit_price_populated=0.958333
- position_count=24
- exact_snapshot_count=24
- source_block_count=24
- atr_source_block_count=0
- stop_tp_source_block_count=1
- matching_policy=EXACT_POSITION_ID_FROM_POSITION_LIFECYCLE_ONLY
- real_capital_status=FORBIDDEN

## Root Cause

Coverage can fail only from missing exact position snapshots or from STOP/TP fields left null because ATR14 or entry-price source evidence is blocked.
The validator does not use symbol/date/price/time proximity fallback and does not convert missing labels into negatives.

## Fix Candidate

If STOP/TP coverage fails, add real OHLC bars and exact entry-price source evidence before each entry, then rebuild `entry_risk_snapshot`; do not approximate ATR.
If snapshot coverage fails, rebuild from `position_lifecycle` exact position IDs and inspect missing snapshot rows.

## Acceptance Impact

- Current trading DB status: FAIL (FAIL_STOP_TP_SOURCE_BLOCKED)
- Acceptance metrics: snapshot_coverage=1.0, stop_price_populated=0.958333, take_profit_price_populated=0.958333
- Blockers: STOP_TP_SOURCE_BLOCK_ENTRY_PRICE_MISSING=1
- Real Capital remains FORBIDDEN; this task does not submit orders or change strategy/entry/universe/alpha logic.
