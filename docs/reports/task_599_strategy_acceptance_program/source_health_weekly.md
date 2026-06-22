# Source Health Weekly

## Decision Summary

- Status: `BLOCKED_20_SESSION_LEDGER_INCOMPLETE`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Current evidence: `trading.db` has runtime `indicator_snapshots` and `market_ticks` for 13 UTC sessions through 2026-06-03, while `market_bars_5m` has broader historical bar coverage.
- What changed: current source availability was audited without treating historical bar presence as a full 20-session source-health ledger.
- Next action: create a session-level ledger with provider errors, quote age, fallback counts, freshness, and ATR coverage for 20 trading sessions.

## Quant Expert Report

The 20-session source-health gate is not complete. The current database has enough market-bar evidence to support the T600-5 ATR validation, but it does not yet provide the full source-health ledger required by Task599.

Required ledger columns remain:

- `session_id`
- `session_date`
- `provider`
- `universe_count`
- `fresh_count`
- `stale_count`
- `provider_error_count`
- `avg_quote_age_ms`
- `max_quote_age_ms`
- `exchange_fallback_count`
- `status`

Current gap:

- Runtime snapshots/ticks cover 13 UTC sessions, not 20 full source-health sessions.
- `indicator_snapshots` does not carry provider/source fields.
- Provider error count and quote age are not yet canonical session fields.
- Historical 5m bars cannot be promoted to full live-source readiness by themselves.

No inferred source, missing-source approximation, or provider-status guess was used.

## No-Background Decision-Maker Report

We have enough price evidence to fix the ATR blocker, but not enough structured source-health evidence to say the data pipeline is ready for acceptance. The source-health gate still needs a 20-session ledger with freshness, quote age, provider errors, and fallback counts.

## Artifact Manifest

See Task599 artifact manifest.
