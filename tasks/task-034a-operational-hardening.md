# Task 034-A: Operational Hardening

## Goal
- Reduce false positives while keeping strict safety behavior for critical mismatches.

## Scope
- Added reconciliation severity model (`INFO/WARN/CRITICAL`).
- Hardened broker-status mapping and stale-lock behavior.
- Added recon alert trigger path and summary output improvements.

## Main Files
- `src/app/reconciliation.py`
- `src/app/run_trade_loop.py`
- `src/app/report_recent_runs.py`
- `README.md`
- `tests/unit/test_structure.py`

## Status
- DONE
