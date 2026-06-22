## Problem

T603-6 Program B needs an entry risk snapshot table for every exact `position_lifecycle.position_id` without changing strategy, entry, universe, alpha, or live capital behavior.
STOP and take-profit prices must come from real ATR14 source evidence only; missing OHLC evidence must remain null/source-blocked instead of approximated.

## Evidence

- snapshot_rows=24
- atr14_source_ok=24
- stop_price_populated=23
- take_profit_price_populated=23
- source_block_rows=24
- matching_policy=EXACT_POSITION_ID_FROM_POSITION_LIFECYCLE_ONLY
- real_capital_status=FORBIDDEN

## Root Cause

ATR14 is available only when `market_bars_5m` has at least 15 same-symbol OHLC bars at or before the entry timestamp.
VWAP, volume ratio, and market regime are not inferred from adjacent fields; if no explicit source column exists, those fields remain null/source-blocked.

## Fix Candidate

Maintain the new `entry_risk_snapshot` builder and add actual source columns or source tables for VWAP, volume ratio, and market regime when those feeds are approved.
For ATR or entry-price blockers, backfill real OHLC bars or exact entry-price source evidence before rerunning this task; do not use ATR approximations or symbol/date/price/time fallback.

## Acceptance Impact

- Required table columns: snapshot_id, position_id, symbol, entry_time, entry_price, atr14, stop_price, take_profit_price, vwap, volume_ratio, market_regime, created_at
- ATR blockers: none
- STOP/TP blockers: STOP_TP_SOURCE_BLOCK_ENTRY_PRICE_MISSING=1
- Optional source blockers: vwap_source_status:VWAP_SOURCE_BLOCK_COLUMN_MISSING=24; volume_ratio_source_status:VOLUME_RATIO_SOURCE_BLOCK_COLUMN_MISSING=24; market_regime_source_status:MARKET_REGIME_SOURCE_BLOCK_COLUMN_MISSING=24
Snapshot acceptance is decided by the validator metrics: snapshot_coverage, stop_price_populated, and take_profit_price_populated.
