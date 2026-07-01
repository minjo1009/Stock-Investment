# TASK-4134 L1 Data-Present Risk Burn-Down

## Result

TASK-4134 fixes L1 risks where source data already exists but L1 was not handling it cleanly. It does not attempt to solve missing-data/backfill-incomplete cases.

## Fixed

- Daily bar raw CSVs in `data/raw/us_daily_alpaca_full_universe` are now sampled into L1 packets.
- The false daily-bars gap from the previous L1 bootstrap is removed when daily raw CSVs exist.
- Legacy direct L0-to-L2 news ingest is blocked by default.
- Existing public newswire and DB-resident 5-minute bars remain bounded, diagnostic-only, and fail-closed.

## Summary

- source_packet_count: 5
- strict_gate_pass_count: 2
- gap_count: 0
- data_present_families_handled: 5
- legacy_l2_bypass_blocked_by_default: True
- trading_authority_opened: false
- l2_materialization_written: false
