# Task3122 Expanded External Tool Scout

## Decision Summary

- Verdict: `expanded_external_tool_scout_completed_selective_adoption`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: broader external MCP/open-source scan beyond market-data MCPs and quant engines.
- What did not change: no MCP install, API call, source acquisition, replay, selector change, sizing change, paper order, live order, or deployment state changed.
- Key conclusion: yes, there are more useful tools. The best near-term candidates are not trading engines. They are SEC extraction, data quality validation, lineage/audit, local analytical query, and pipeline loading/orchestration tools.

## Quant Expert Report

### Expanded Candidate Map

| Category | Candidate | Fit To Our Brain | Need Now? | Decision |
| --- | --- | --- | --- | --- |
| SEC extraction | `dgunning/edgartools` | Raw source evidence / primitive fact extraction for SEC filings, XBRL, Form 4, 13F | High | `P0_EVALUATE_FIRST` |
| SEC MCP | `stefanoamorelli/sec-edgar-mcp` | MCP interface to SEC EDGAR for agent-side lookup | Medium | `P1_REVIEW_LICENSE_AND_SCOPE` |
| SEC MCP | `cyanheads/secedgar-mcp-server` | Small Apache-licensed SEC MCP | Low-medium | `P1_SMALL_PILOT_CANDIDATE` |
| Data quality | Great Expectations | Source/feature quality gates and data docs | Medium-high | `P0_OR_P1_FOR_BATCH_VALIDATION` |
| Data quality | Pandera | Lightweight dataframe schema/statistical checks | High | `P0_BEST_FIT_FOR_LOCAL_VALIDATORS` |
| Lineage | OpenLineage | Standardized lineage metadata collection | Medium | `P1_IF_LINEAGE_BECOMES_CROSS_PIPELINE` |
| Lineage UI | Marquez | Visualize lineage metadata | Low-medium | `P2_ONLY_IF_OPENLINEAGE_USED` |
| Orchestration | Dagster | Data asset orchestration and observation | Medium | `P1_FOR_SOURCE_ASSET_GRAPH` |
| Orchestration | Prefect | Resilient Python workflow orchestration | Medium | `P1_FOR_BACKFILL_RETRY_OPS` |
| Loading | dlt | Python data loading from APIs to local stores | High | `P0_FOR_EXTERNAL_SOURCE_RECEIPT_LOADER` |
| Query/storage | DuckDB | Local analytical SQL over parquet/csv/json | High | `P0_ALREADY_ALIGNED_WITH_ARTIFACTS` |
| Query/storage | Polars | Fast dataframe/lazy query engine | High | `P0_FOR_LARGE_PANEL_TRANSFORMS` |
| News/event | GDELT / `gdeltPyR` | Broad event/news context, weak source specificity | Low-medium | `P2_CONTEXT_ONLY` |
| RSS MCP | `veithly/rss-mcp` | Low-friction official feeds/watchlists | Medium | `P1_FOR_LOW_FREQUENCY_FEEDS` |
| DuckDB MCP | `dacort/mcplucker` | Agent query interface to DuckDB | Low | `P2_TOO_SMALL_FOR_GOVERNED_PATH` |

### Best New Candidates

#### 1. `edgartools`

Why it matters:

- It directly targets our current strongest source family: SEC EDGAR.
- It covers filings, XBRL financials, Form 3/4/5, 13F, and related SEC objects.
- It is local Python, MIT-licensed, and does not require MCP mediation.

Why it may beat an MCP:

- Lower operational risk than an agent-facing MCP.
- Easier to retain raw filing identity, accession number, CIK, filing date, document path, and extracted primitives.
- Better fit for deterministic extractors and repo-native validators.

Decision:

- Evaluate before SEC MCP servers.
- Target layer: `Raw source evidence` and `Primitive fact extraction`.
- First use: compare one existing SEC financing/dilution extractor output versus `edgartools` extraction on a tiny fixed fixture.

#### 2. Pandera

Why it matters:

- Our repo already has many CSV/parquet panels, feature gates, and task validators.
- Pandera can express dataframe schema and statistical checks closer to the panel itself.

Why it may beat Great Expectations:

- Lighter.
- Easier to embed in existing Python validators.
- Better for strict local checks like `missing_treated_as_negative_flag == 0`, timestamp columns present, and no outcome columns in assignment inputs.

Decision:

- Strong P0 for local validator hardening.
- Target layer: `Resolver and QA`, `Primitive fact extraction`, `Candidate bundle`.

#### 3. dlt

Why it matters:

- The next concrete object from Task3082 was `external_source_receipt`.
- dlt is a Python loading library; it can help standardize API-to-local-store ingestion without creating strategy logic.

Decision:

- P0 if we implement an external source receipt loader.
- Target layer: `Raw source evidence`.
- Use only if it preserves raw payload path/hash and does not hide provider timing.

#### 4. DuckDB + Polars

Why it matters:

- Our existing artifact shape is large local CSV/parquet panels.
- DuckDB is a strong local analytical SQL engine.
- Polars is a strong lazy dataframe engine for large transforms.

Decision:

- P0 as infrastructure, not new trading intelligence.
- Target layer: source panels, QA joins, MDD attribution, candidate bundle audits.
- This is likely more useful than most finance MCPs.

#### 5. OpenLineage / Marquez

Why it matters:

- Our core pain is not only missing data. It is proving which raw source produced which feature, policy, replay, and UI status.

Decision:

- P1.
- OpenLineage first, Marquez only if visualization becomes worth the operational overhead.
- Target layer: artifact manifest and lineage audit.

#### 6. Dagster / Prefect

Why it matters:

- Source acquisition and microstructure backfills are already multi-step jobs.
- These tools could make retries, observability, and asset dependencies cleaner.

Decision:

- P1, not P0.
- Use only if current scripts become too hard to operate.
- Do not migrate existing source tasks just for elegance.

#### 7. RSS MCP / GDELT

Why it matters:

- Useful for context watch, official feeds, and low-frequency event discovery.

Decision:

- P1 for RSS if feeds are official and low-frequency.
- P2 for GDELT because broad event presence has already been dangerous in this project unless strict relevance is certified.

### Revised Priority

The revised priority is different from Task3121:

1. `edgartools` for SEC extraction comparison.
2. `Pandera` for local panel/schema validators.
3. `dlt` for `external_source_receipt` loader if we build one.
4. `DuckDB/Polars` for large artifact query and panel transforms.
5. `GitHub MCP read-only` for upstream monitoring.
6. `OpenLineage` only if lineage becomes cross-pipeline.
7. `Dagster/Prefect` only if orchestration complexity exceeds scripts.
8. Finance MCPs only if provider limits and retention terms beat existing paths.

### What This Means

The earlier answer was too narrow because it mainly asked:

```text
Which MCP can fetch market data?
```

The better question is:

```text
Which open-source tools reduce our actual bottlenecks: source truth, timestamp discipline, validation, lineage, and local artifact querying?
```

Under that better question, the strongest candidates are not Alpha Vantage-style MCPs. They are SEC extraction and data-engineering tools.

## No-Background Decision-Maker Report

Conclusion first: yes, there are more. And some are better than the first list.

The most useful new candidate is `edgartools`, because our brain already depends heavily on SEC evidence. It may improve extraction and reduce custom SEC glue.

The second best is `Pandera`, because it can strengthen local dataframe validators without changing strategy logic.

The third best is `dlt`, if we build the `external_source_receipt` loader.

DuckDB and Polars are probably more useful than most finance MCPs because our data is already local, large, and artifact-heavy.

Do not chase every MCP. Most MCPs are just a new wrapper around the same API limits. The real upgrade is better extraction, validation, lineage, and local query speed.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `docs/operating_system/project_operating_state.md`
  - `docs/reports/task_3121_external_tool_necessity_cost_benefit_review/task_3121_external_tool_necessity_cost_benefit_review.md`
  - GitHub repository metadata for 16 external candidates.
- Outputs:
  - `docs/reports/task_3122_expanded_external_tool_scout/task_3122_expanded_external_tool_scout.md`
- Candidate rows reviewed:
  - 16.
- Validation commands:
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Not applicable. No external raw datasets were acquired.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
