# GPT Agent Mode Plan Response Capture

Capture status: `CAPTURED_SUMMARY_FROM_VISIBLE_GPT_OUTPUT`

Note: the browser clipboard copy produced mojibake for Korean text after capture. This file preserves the substantive GPT plan visible in Chrome, but it is a clean capture summary rather than a verbatim transcript.

## 3-Line Summary From GPT

1. The user's order is mostly correct, but GPT recommended adding a first state-reconciliation step before scheduler optimization.
2. GPT said the GitHub-visible state it could inspect looked centered on market, macro, and SEC scheduler/DB paths, while the latest news-provider implementation may be local-only until reconciled.
3. GPT ranked the first Codex tasks as scheduler registry expansion, L0/L1 storage validator, and L1-L6 contract validator.

## Corrected End-To-End Order

```text
A. State reconciliation
B. Scheduler registry / cadence optimization
C. L0/L1 storage validation
D. L1-L6 consumption contract validation
E. Source-time audit
F. No-execution diagnostic backtest harness
G. Controlled diagnostic replay only if source-time and input-manifest blockers clear
```

## Scope A - GitHub / Local State Reconciliation

Objective: separate what is GitHub-visible from what is local-only before changing scheduler behavior.

Concrete tasks:

1. Locate `official_public_releases`, `gdelt_news_events`, and `marketaux_news_free` in code, reports, tests, scheduler config, and DB registry.
2. If a source family exists only locally, report it as `LOCAL_ONLY_NOT_GITHUB_VISIBLE` instead of treating it as globally available.
3. Reconcile family maps and scheduler registry entries before enabling automatic loops.

Stop condition: do not claim a news implementation is generally available if it is not visible in the repo state under review.

## Scope B - Scheduler Optimization

Objective: make scheduler cadence consistent across JSON config, DB registry, and validators.

Concrete tasks:

1. Add or reconcile scheduler specs for `official_public_releases`, `gdelt_news_events`, and `marketaux_news_free`.
2. Keep conservative or disabled defaults when provider quota, authority, or local-only status is unresolved.
3. Preserve SEC user-agent, cooldown, and allow-network guards.
4. Preserve lease and fingerprint idempotency behavior.

Stop condition: stop if automatic live fetching becomes too aggressive or any token/secret can appear in logs or artifacts.

## Scope C - L0/L1 Storage Validation

Objective: prove each source family writes rows plus receipt/hash/lineage/freshness evidence.

Required evidence chain:

```text
target table row
-> source_receipts
-> reference_hashes
-> data_lineage_edges
-> source_freshness
-> scheduler_run_ledger
```

Minimum fields:

```text
provider
source_family
source_key
source_ts
capture_ts
available_to_brain_ts
raw_path
raw_sha256
source_time_basis
strict_gate_allowed=0
proxy_allowed=0
```

Stop condition: any row with missing source timestamp or raw hash blocks promotion.

## Scope D - L1-L6 Consumption Path Validation

Objective: ensure source rows do not bypass layer gates and cannot directly create ranking, sizing, replay eligibility, paper orders, or live orders.

Concrete tasks:

1. Trace L1 source evidence into primitive-fact candidates only.
2. Require GDELT and Marketaux to carry confirmation requirements.
3. Require source graph id, bundle id, and as-of timestamp before any L5/L6 use.
4. Hard-fail if L0/L1 rows create rank, score, order, or replay eligibility directly.

## Scope E - Source-Time Audit

Objective: block lookahead and leakage before any diagnostic replay.

Required timestamp chain:

```text
source_ts
capture_ts
available_to_brain_ts
node_asof_ts
edge_asof_ts
bundle_asof_ts
adapter_created_ts
tradable_after_ts
```

Required monotonic rule:

```text
source_ts <= capture_ts <= available_to_brain_ts <= bundle_asof_ts <= adapter_created_ts <= tradable_after_ts
```

Stop condition: missing timestamp, future source data, or market data after the decision time blocks replay.

## Scope F - Diagnostic Backtest Harness

Objective: build a no-execution harness manifest first; do not jump straight to PnL replay.

Required prerequisites:

```text
dry adapter input rows
source graph ids
candidate bundle ids
source/evidence ids
as-of timestamps
market data gate rows
split/OOS plan
cost/slippage config draft
```

Allowed first:

```text
input manifest
source-time blocker report
market data gate report
split/OOS plan
cost/slippage config draft
no-execution dry harness
```

Forbidden until blockers clear:

```text
PnL replay
trade generation
strategy acceptance comparison
paper promotion
live readiness
buy/sell/position-size recommendation
```

## Scheduler Cadence Matrix

| Source family | Safe cadence | Default posture | Notes |
| --- | --- | --- | --- |
| `market_ticks_intraday` | 5m during US regular hours | enabled diagnostic | Current config already pairs it with 5m bars. |
| `market_bars_5m` | 5-10m during US regular hours | enabled diagnostic | Existing policy mentions 10m cadence / 20m max lag. |
| `macro_rates` | 60m or release-window | conservative enabled | Macro data may tolerate larger lag than market data. |
| `sec_events` | 60m cooldown-aware | enabled only with declared identity and cooldown | Keep current SEC safety posture. |
| `official_public_releases` | 30-60m | conservative or disabled until reconciled | Authority-capable if source timestamps are official. |
| `gdelt_news_events` | 15-30m one-symbol throttled | disabled or very conservative | Discovery only, not authority. |
| `marketaux_news_free` | 60-240m | token-gated and disabled/conservative | Free-plan enrichment only unless confirmed. |

## First Three Codex Tasks

1. Scheduler registry reconciliation plus news family placeholders.
2. L0/L1 storage validator.
3. L1-L6 consumption contract validator.

## GPT Risk Notes

1. GitHub-visible state and local dirty state may differ; Codex must reconcile before implementation claims.
2. JSON scheduler config and DB scheduler registry can drift, so one validator should check consistency.
3. GDELT success does not make it authority evidence.
4. Marketaux token must remain gitignored and masked.
5. Any replay before source-time audit creates lookahead risk.

## Safety Boundary

```text
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
No broker mutation
No live order
No paper promotion
```
