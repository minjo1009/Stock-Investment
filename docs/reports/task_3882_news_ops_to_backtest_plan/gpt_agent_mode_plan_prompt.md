# GPT Agent Mode Planning Prompt

You are an expert panel for the `minjo1009/Stock-Investment` project.

## Required Expert Roles

- Data Platform Architect
- Scheduler / Pipeline Reliability Engineer
- Quant Data Infrastructure Reviewer
- Backtest Methodology Reviewer
- Source-Time / Leakage Audit Reviewer
- Trading Controls Reviewer

## User Goal

Build a concrete implementation plan for this sequence:

```text
scheduler optimization
-> L0/L1 storage validation
-> L1~L6 consumption path validation
-> source-time audit
-> diagnostic backtest
```

The user wants the plan to become the next operating GOAL. It must be concrete enough for Codex to implement in small scopes and tasks after your review.

## Required GPT Mode

Use Agent Mode with GitHub enabled for `minjo1009/Stock-Investment`.

Inspect the repository before answering. Base project-state claims on GitHub-visible files, current code, tests, reports, and SSOT docs. If GitHub cannot access a local-only artifact, say so plainly and reason from the visible repo state only.

## Current Local Context For Codex Reconciliation

Recent local state says:

1. Official news/source fetchers are implemented for company IR/newsroom, Federal Reserve, BLS, BEA, and Treasury.
2. Marketaux free-plan fetch is implemented with a gitignored local token file, local usage guard, and token masking.
3. GDELT DOC API fetch is implemented and was recovered by changing to one-symbol requests, `maxrecords=1`, `timespan=15m`, and at least 5.5 seconds before the request.
4. Latest GDELT diagnostic run succeeded with one L0 row. L1 remains blocked because GDELT is discovery metadata, not authority evidence.
5. News scheduler entries exist but official/GDELT/Marketaux automatic jobs may still be disabled or conservative pending schedule design.
6. Existing market/macro scheduler families include `market_ticks_intraday`, `market_bars_5m`, `daily_ohlcv`, `macro_rates`, and `sec_events`.
7. The active objective is not trading acceptance. It is diagnostic data operation and source-time-safe backtest preparation.

## Repository Files To Inspect First

Please inspect these files before producing the plan:

- `docs/operating_system/project_operating_state.md`
- `docs/operating_system/backtest_harness_operating_discipline.md`
- `docs/architecture/brain_layer_map.md`
- `docs/architecture/test_validation_canonicalization_map.md`
- `configs/db_source_acquisition_scheduler.json`
- `tools/db/run_source_acquisition_once.py`
- `tools/db/run_registered_loop_once.py`
- `tools/db/apply_management_schema.py`
- `tests/test_db_source_acquisition_runner.py`
- `tests/test_db_registered_loop_runner.py`
- `docs/reports/task_3875_news_source_ingestion_scope_plan/`
- `docs/reports/task_3876_openbb_funnlp_news_l0_l1_benchmark_plan/`
- `docs/reports/task_3878_news_l0_l1_source_implementation/`
- `docs/reports/task_3880_news_provider_live_fetch/`
- `docs/reports/task_3881_gdelt_429_recovery/`

If you find more relevant files for L1~L6 propagation, source-time audit, runtime catalogs, or diagnostic backtest, list them explicitly.

## Hard Project Boundaries

Preserve these exactly:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- No buy/sell/position-size recommendation
- Missing or stale data is `UNKNOWN/BLOCKER`, never negative evidence
- GDELT and Marketaux are discovery/enrichment unless independently confirmed by authority evidence
- Tests and a diagnostic backtest do not imply strategy acceptance or deployment readiness

## Questions To Answer

1. Is the user's proposed order correct?
   - scheduler optimization
   - L0/L1 storage validation
   - L1~L6 consumption path validation
   - source-time audit
   - diagnostic backtest

2. If the order is mostly correct, refine it into implementation scopes.

3. For each source family, propose the safest useful scheduler cadence:
   - `market_ticks_intraday`
   - `market_bars_5m`
   - `macro_rates`
   - `sec_events`
   - `official_public_releases`
   - `gdelt_news_events`
   - `marketaux_news_free`

4. Define how each source should prove L0/L1 storage:
   - DB table(s)
   - receipt/hash/lineage evidence
   - source timestamp basis
   - freshness status
   - failure and skip semantics

5. Define how news/event rows should be consumed from L1 through L6:
   - what code paths or contracts should be inspected or built
   - what must remain blocked until source-time proof exists
   - what evidence is enough for diagnostic-only propagation

6. Define the source-time audit:
   - required timestamp columns
   - as-of rules
   - leak/lookahead checks
   - blocker conditions
   - artifact outputs

7. Define the diagnostic backtest prerequisites:
   - what inputs must exist before any replay
   - which backtest remains forbidden until blockers clear
   - what a diagnostic run may and may not claim
   - required validation commands

8. Rank the first 3 Codex implementation tasks.

## Required Output Format

Return the answer in this structure:

1. Task Diagnosis
2. Corrected End-to-End Order
3. Scope Plan

For each scope, include:

- Scope name
- User-visible objective
- Code files likely touched
- DB tables / artifacts involved
- Concrete tasks
- Validation commands
- Stop conditions
- Safety notes

4. Scheduler Cadence Matrix
5. L0/L1 Storage Verification Plan
6. L1~L6 Consumption Verification Plan
7. Source-Time Audit Plan
8. Diagnostic Backtest Plan
9. First 3 Codex Tasks To Implement
10. Risks / Open Questions

Be concrete. Avoid generic advice. Do not claim completion or readiness.
