# GPT Loop 1 Prompt

You are a senior reviewer for the GitHub repo https://github.com/minjo1009/Stock-Investment.

Please read the repo/main conceptually from GitHub and review this specific Scope E blocker burn-down plan. This is review-only; do not claim source-of-truth over local validation.

Project standing constraints:

- Strategy acceptance: NOT_ACCEPTED
- Deployment readiness: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real capital: FORBIDDEN
- Broker mutation/live order/paper promotion: FORBIDDEN

Goal:

Scope E must prove source-time order before any controlled diagnostic replay:

```text
source_ts <= capture_ts <= available_to_brain_ts <= node/edge/bundle/adapter/tradable_after
```

This prevents lookahead leakage. Scope G may only proceed as diagnostic/no-execution if Scope E has no active source-time blockers.

Current local evidence before repair:

- Scope E status: PASS_WITH_BLOCKERS
- blocker_errors: source_time_blockers:market_bars_5m:64
- Other source families pass: market_ticks_intraday, macro_rates, sec_events, official_public_releases, gdelt_news_events, marketaux_news_free.
- Example: source_ts=2026-06-23T19:59:59Z and capture_ts=2026-06-23T19:56:57.351648Z for receipt:market_bars_5m:2026-06-23T19:55:00Z.

Likely root cause:

- cached_market_bars_5m evidence uses MAX(bar_end_ts) from market_bars_5m.
- If the cached table contains an in-progress 5m bar, bar_end_ts can be later than captured_at.
- Current receipt then says the system captured a bar before its end, which is a replay/lookahead blocker.

Candidate safe fix:

1. For cached market_bars_5m evidence and derived indicators, use only closed bars where bar_end_ts <= captured_at/now.
2. Quarantine existing invalid partial-bar receipts instead of deleting them, so they remain auditable but are excluded from active replay-eligible source-time audit.
3. Re-run source-time audit; expected active blocker count becomes zero while freshness gates remain closed unless source freshness is genuinely current.
4. Scope G can proceed only as no-execution diagnostic replay check, not strategy acceptance, paper permission, deployment readiness, or real capital.

Please answer concisely:

A. Is this diagnosis coherent with the evidence?
B. Is the proposed fix safe, or should it be changed?
C. What validations should be mandatory before declaring Scope E resolved and Scope G diagnostic-only proceeded?
D. Any GitHub-visible files you would expect to inspect or update?
