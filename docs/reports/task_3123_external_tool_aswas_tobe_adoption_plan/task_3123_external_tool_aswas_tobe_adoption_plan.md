# Task3123 External Tool AS-WAS TO-BE Adoption Plan

## Decision Summary

- Verdict: `adopt_only_infrastructure_tools_that_reduce_current_bottlenecks`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: Task3122 candidates were judged against the actual project operating model, with AS-WAS, TO-BE, benefit, and first-use plans.
- What did not change: no install, source acquisition, replay, selector change, sizing change, paper order, live order, or deployment state changed.
- Key conclusion: tools are helpful only if they strengthen source extraction, validation, lineage, local query, or read-only monitoring. Most market-data MCPs are not helpful now.
- Next action: implement a small non-trading `edgartools` fixture comparison and a `Pandera` validator pilot before any new MCP connection.

## Quant Expert Report

### Adoption Gate

An external MCP or open-source tool should be adopted only if it passes all of these:

1. It reduces a current project bottleneck.
2. It improves speed, reliability, coverage, or auditability versus current scripts.
3. It preserves raw source identity, timestamp, hash, and provider terms.
4. It does not write buy, sell, rank, size, selector, paper order, or live order fields.
5. It can be validated with local task validators.

### AS-WAS / TO-BE Plan

| Area | AS-WAS | TO-BE | Advantage | Help? | First Use |
| --- | --- | --- | --- | --- | --- |
| SEC extraction | Custom SEC/Finnhub/FMP fallback scripts. SEC companyfacts and filing artifacts are already used, but extractor logic is repo-specific and grows per task. | Evaluate `edgartools` as a local deterministic SEC extraction adapter before any SEC MCP. Keep raw filing/accession/CIK/date paths in repo artifact discipline. | Less custom SEC parsing, better typed access to filings/XBRL/Form 4/13F, no new API quota layer, easier fixture comparison. | `YES_P0` | Compare `edgartools` output against one existing SEC financing/dilution fixture. |
| Panel validation | Many task-specific Python validators check each report/output separately. Rules can duplicate and drift. | Add `Pandera` schemas for recurring panel classes: source receipt, primitive facts, candidate bundles, MDD attribution, runtime catalog. | Reusable schema checks, stronger anti-leak checks, clearer missing-data rules, easier validator maintenance. | `YES_P0` | Add one Pandera schema around a non-trading artifact validator. |
| Large local joins | Many analyses read CSV/parquet with ad hoc pandas code. Large joins can become slow and memory-heavy. | Use DuckDB for artifact SQL joins and Polars for lazy dataframe transforms where panels are large. | Faster joins, lower memory, reproducible SQL snippets, easier MDD/bundle/source audits. | `YES_P0` | Benchmark one MDD attribution or source-bundle join against the existing pandas path. |
| External source loading | Each source acquisition task writes its own call log, raw path, normalized rows, and manifest shape. | Use `dlt` only if building `external_source_receipt` loader. It must emit raw payload path, hash, requested_at, received_at, provider, endpoint, and terms note. | Standardized API-to-local loading and retry metadata without changing strategy logic. | `CONDITIONAL_P0` | Build a loader skeleton with local fixture payloads, not live API calls. |
| Upstream repo/security monitoring | Manual search or one-off GitHub lookup when a question appears. | Use GitHub MCP read-only for scheduled/low-frequency monitoring of selected repos: `edgartools`, `Pandera`, `dlt`, DuckDB, Polars, OpenLineage, Dagster/Prefect, MCP servers. | Keeps dependency/security/API-change awareness without touching trading data. | `YES_P1` | Weekly read-only watch packet. |
| Lineage/audit graph | Artifact manifests and task reports describe lineage, but no standard lineage event model exists across all pipelines. | Consider OpenLineage for source->feature->policy->report lineage only if lineage becomes cross-pipeline and hard to audit manually. Marquez only if visualization is needed. | Standard lineage event model; easier impact audit when moving artifacts or replaying policies. | `CONDITIONAL_P1` | Design-only mapping from current artifact manifest to OpenLineage event fields. |
| Source/backfill orchestration | Task scripts and PowerShell runners handle acquisition and backfill. Task646 already has bounded workers and a shared request limiter. | Use Prefect or Dagster only if retries, asset dependencies, or observability exceed script maintainability. | Better retry state, asset graph, scheduled runs, and failure visibility. | `CONDITIONAL_P1` | Do not migrate yet. First write criteria for when scripts are insufficient. |
| Official feed watch | Official feeds are discovered per task; broad event/news sources can over-attach and create false relevance. | Use RSS MCP only for official low-frequency feeds and watchlists. Keep GDELT as context-only unless strict source-text relevance is proven. | Lightweight event discovery without inventing source truth. | `LIMITED_P1_P2` | Official-feed watchlist only; no assignment fields. |
| SEC MCP servers | Agent-facing SEC MCPs can query filings, but add MCP trust, license, and agent-boundary risk. | Prefer `edgartools` first. SEC MCP only for read-only exploratory lookup after license/scope review. | Convenient exploration, but weaker than local deterministic extraction for governed evidence. | `P1_NOT_FIRST` | Review license and tool outputs before any connection. |
| Market-data MCPs | Alpha Vantage/Financial Datasets/Yahoo/Maverick-style MCPs wrap provider APIs and often inherit quota/terms limits. | Keep out of the governed path unless paid limits, retention terms, PIT timestamp support, and raw payload capture beat existing source stack. | May help spot checks, but mostly not better than current source discipline. | `MOSTLY_NO` | No full-pool attachment. |
| Quant engines | Current blockers are source/as-of completeness, same-experiment governance, cost/risk, and auditability. | Keep vectorbt/NautilusTrader/Lean as later diagnostic mirrors only after canonical artifacts exist. | Independent result sanity check later; not a current bottleneck fix. | `DEFER` | No migration. |
| ML/RL frameworks | Current task is not lack of model complexity. | Keep Qlib/FinRL as reading/reference only. | Avoids complexity and leakage risk. | `NO_NOW` | No pilot. |

### Concrete Operating Design

#### P0-1: SEC extraction comparison with `edgartools`

AS-WAS:

- SEC evidence is already central.
- Current extractors are task-specific.
- Validation is done through task reports and scripts.

TO-BE:

- Wrap `edgartools` behind a local adapter:

```text
sec_source_adapter
-> raw filing/accession/CIK/date identity
-> primitive fact rows
-> existing validator
```

Advantages:

- Lower custom parser burden.
- Easier Form 4, 13F, XBRL extension.
- No new market-data quota.
- Better deterministic fixture testing than an SEC MCP.

Adoption condition:

- Adopt only if it reproduces or improves a small existing SEC fixture without losing raw source identity.

#### P0-2: Local validator hardening with `Pandera`

AS-WAS:

- Validators are mostly imperative Python.
- Similar checks repeat across tasks.

TO-BE:

- Define small schemas:

```text
SourceReceiptSchema
PrimitiveFactSchema
CandidateBundleSchema
ReplayInputSchema
RuntimeCatalogSchema
```

Advantages:

- Faster review of column/type/null constraints.
- Easier anti-leakage rules.
- Less duplicated validation code.

Adoption condition:

- Adopt if one pilot validator becomes shorter or catches one class of issue more explicitly.

#### P0-3: Local query acceleration with DuckDB/Polars

AS-WAS:

- Large local artifacts are queried through per-script pandas reads.

TO-BE:

- Use DuckDB for SQL over parquet/csv.
- Use Polars lazy execution for large transforms.

Advantages:

- Faster joins.
- Lower memory pressure.
- Easier reproducible audit queries.

Adoption condition:

- Adopt for large-panel audit scripts only when it reduces runtime or code complexity.

#### Conditional P0: `dlt` for `external_source_receipt`

AS-WAS:

- Each API/source task builds its own loading and manifest pattern.

TO-BE:

- Use `dlt` only for a governed loader if it emits:

```text
raw_payload_path
raw_payload_sha256
requested_at_utc
received_at_utc
source_published_at_utc
provider
endpoint
terms_note
```

Advantages:

- Cleaner retries and load metadata.
- More consistent external source receipts.

Adoption condition:

- Adopt only if it does not hide raw payloads or provider timing.

### Recommended Order

1. `edgartools` fixture comparison.
2. `Pandera` validator pilot.
3. DuckDB/Polars audit query benchmark.
4. `dlt` source-receipt loader skeleton.
5. GitHub MCP read-only watch packet.
6. OpenLineage mapping design only.
7. Dagster/Prefect only if scripts become operationally painful.

### Do Not Do

- Do not attach Alpha Vantage free tier to the full 3,100-symbol pool.
- Do not attach Yahoo/Maverick MCP to governed evidence.
- Do not let SEC MCP results become source truth before local raw identity checks.
- Do not migrate the backtest engine to NautilusTrader/vectorbt/Lean now.
- Do not add Qlib/FinRL model outputs to slot decisions.

## No-Background Decision-Maker Report

Conclusion first: yes, some tools will help. But not the obvious finance MCPs.

The most helpful path is:

1. `edgartools` for SEC extraction.
2. `Pandera` for validators.
3. DuckDB/Polars for local artifact joins.
4. `dlt` only if we build external source receipts.
5. GitHub MCP read-only for monitoring.

This improves the brain because it strengthens evidence, validation, and audit speed. It does not make trading decisions better by itself.

Do not replace the brain. Upgrade the plumbing around the brain.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `docs/operating_system/project_operating_state.md`
  - `docs/architecture/skill_md_subagent_canonicalization_map.md`
  - `docs/reports/task_3121_external_tool_necessity_cost_benefit_review/task_3121_external_tool_necessity_cost_benefit_review.md`
  - `docs/reports/task_3122_expanded_external_tool_scout/task_3122_expanded_external_tool_scout.md`
- Outputs:
  - `docs/reports/task_3123_external_tool_aswas_tobe_adoption_plan/task_3123_external_tool_aswas_tobe_adoption_plan.md`
- Rows:
  - AS-WAS / TO-BE rows: 12.
- Validation commands:
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Not applicable. No external raw datasets were acquired.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
