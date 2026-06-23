# Task3882 News Ops To Backtest Plan

## Summary

The user goal is:

```text
scheduler optimization
-> L0/L1 storage validation
-> L1-L6 consumption path validation
-> source-time audit
-> diagnostic backtest
```

GPT Agent Mode with GitHub context was consulted. The answer supported the sequence, but added one prerequisite: reconcile GitHub-visible state against local-only state before changing scheduler behavior or claiming implementation completeness.

This is a planning task only. It does not enable broker mutation, paper orders, live orders, deployment readiness, strategy acceptance, or real-capital use.

## GPT Consult Evidence

- Prompt: `docs/reports/task_3882_news_ops_to_backtest_plan/gpt_agent_mode_plan_prompt.md`
- Captured response summary: `docs/reports/task_3882_news_ops_to_backtest_plan/gpt_agent_mode_plan_response.md`
- Relay mode: `single_gpt_consult`
- GPT mode requested: Agent Mode with GitHub enabled for `minjo1009/Stock-Investment`
- Capture status: `CAPTURED_SUMMARY_FROM_VISIBLE_GPT_OUTPUT`
- Tab cleanup status: `closed_or_released_by_finalize`

The browser clipboard copy of the Korean response produced mojibake, so the response artifact is a clean capture summary based on visible GPT output rather than a verbatim transcript.

## Adopted End-To-End Order

```text
A. GitHub/local state reconciliation
B. Scheduler registry and cadence optimization
C. L0/L1 storage validation
D. L1-L6 consumption contract validation
E. Source-time audit
F. No-execution diagnostic backtest harness
G. Controlled diagnostic replay only if blockers clear
```

## Scope A - State Reconciliation

Objective: prove which news/source implementations are available in the current repo state before scheduler activation.

Tasks:

1. Inspect source-family registration for `official_public_releases`, `gdelt_news_events`, and `marketaux_news_free`.
2. Compare scheduler JSON, DB registry specs, tests, and reports.
3. Mark any mismatch as `LOCAL_ONLY_NOT_GITHUB_VISIBLE` or `REGISTRY_CONFIG_DRIFT`.
4. Produce a reconciliation report before changing cadences.

Validation candidates:

```text
python scripts/task_registry_validate.py
python scripts/trader_brain_3761_3800_db_source_scheduler_config_freshness_validate.py
```

## Scope B - Scheduler Optimization

Objective: collect each source at the fastest useful cadence that does not break provider policy, quotas, or local safety gates.

Initial cadence policy:

| Source family | Candidate cadence | Default posture |
| --- | --- | --- |
| `market_ticks_intraday` | 5m during US regular hours | enabled diagnostic |
| `market_bars_5m` | 5m to 10m during US regular hours | enabled diagnostic |
| `macro_rates` | 60m or release-window | conservative enabled |
| `sec_events` | 60m cooldown-aware | enabled only with declared identity and cooldown |
| `official_public_releases` | 30m to 60m | conservative or disabled until reconciliation |
| `gdelt_news_events` | 15m to 30m, one symbol per cycle, throttled | disabled or very conservative |
| `marketaux_news_free` | 60m to 240m | token-gated and conservative |

Tasks:

1. Add a scheduler-cadence consistency validator across JSON config and DB registry.
2. Keep Marketaux token-gated and masked.
3. Keep GDELT one-symbol and cooldown-aware.
4. Keep SEC live cooldown and declared identity guards.
5. Prevent source jobs from changing broker, paper, live, or real-capital permission state.

## Scope C - L0/L1 Storage Validation

Objective: prove every active source family writes source rows with evidence, not just table rows.

Required evidence chain:

```text
target table row
-> source_receipts
-> reference_hashes
-> data_lineage_edges
-> source_freshness
-> scheduler_run_ledger
```

Tasks:

1. Build a validator for row counts, receipt coverage, hash coverage, lineage coverage, freshness status, and scheduler ledger status.
2. Verify source timestamp basis per family.
3. Verify failure and skip records remain fail-closed.
4. Verify strict/proxy gates stay closed unless an explicit source authority task opens them.

Stop conditions:

```text
missing source timestamp
missing raw hash
missing lineage edge
source freshness not recorded
strict/proxy authority accidentally opened
```

## Scope D - L1-L6 Consumption Path Validation

Objective: prove source rows can be consumed diagnostically without becoming direct trading decisions.

Tasks:

1. Trace L1 source evidence into L2 primitive-fact candidates.
2. Trace L2/L3/L4 contracts only when as-of ids and evidence ids exist.
3. Require GDELT and Marketaux rows to carry discovery/enrichment status unless official confirmation exists.
4. Hard-fail if source rows create rank, score, order intent, replay eligibility, or position sizing directly.

Candidate validation:

```text
python -m unittest tests.test_brain_meaning_adapter tests.test_brain_relation_adapter tests.test_brain_policy_adapter tests.test_brain_runtime_contracts
```

## Scope E - Source-Time Audit

Objective: prove the downstream brain and diagnostic backtest cannot see future source or market data.

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

Required rule:

```text
source_ts <= capture_ts <= available_to_brain_ts <= bundle_asof_ts <= adapter_created_ts <= tradable_after_ts
```

Tasks:

1. Build a source-time blocker report.
2. Check missing timestamp fields.
3. Check future-source and future-market-data leaks.
4. Check GDELT/Marketaux authority classification.
5. Preserve missing/stale as `UNKNOWN/BLOCKER`.

## Scope F - Diagnostic Backtest Harness

Objective: create a no-execution diagnostic harness before any replay.

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

## First Three Implementation Tasks

1. Scheduler registry reconciliation plus cadence validator.
2. L0/L1 storage validator.
3. L1-L6 consumption contract validator.

## Safety Boundary Confirmation

```text
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
No broker mutation added
No live order path added
No paper promotion added
Missing/stale data remains UNKNOWN/BLOCKER
```

## Next Action

Start Scope A as the next implementation task. Do not begin diagnostic replay until Scope C, Scope D, and Scope E have produced blocker-free evidence for the specific replay input manifest.
