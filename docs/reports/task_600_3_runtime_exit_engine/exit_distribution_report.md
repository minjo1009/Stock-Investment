## Problem

- Exit acceptance cannot inspect distribution until runtime paper exits have explicit exit_reason values.

## Evidence

- TIMEOUT: count=23, avg_realized_pnl=3.477452, total_realized_pnl=79.9814

## Root Cause

- Prior closed-trade distribution was diagnostic-only and not written as runtime paper SELL fills.

## Fix Candidate

- Summarize runtime paper closed rows by exact exit_reason without symbol/date/price/time lifecycle fallback matching.

## Acceptance Impact

- exit_reason_populated=23
- Distribution evidence is paper/runtime scoped and does not claim broker-truth or real-capital readiness.
