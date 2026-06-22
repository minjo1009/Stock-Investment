# Task3124 External Tool Operations Plan

## Decision Summary

- Verdict: `external_tools_operate_as_governed_infrastructure_not_trading_brain`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: a concrete apply/manage/operate plan was defined for selected open-source and MCP tools.
- What did not change: no install, source acquisition, replay, selector change, sizing change, paper order, live order, or deployment state changed.
- Key metrics:
  - P0 tools: 3 families.
  - Conditional tools: 4 families.
  - Forbidden/blocked uses: 5.
  - First implementation lane: fixture-only, non-trading.
- Next action: start `Phase 0` dependency/security review, then run only the `edgartools` and `Pandera` fixture pilots.

## Quant Expert Report

### Operating Principle

External tools must be operated as infrastructure around the Trader Brain.

They may improve:

- source extraction,
- panel validation,
- local query speed,
- source receipt loading,
- lineage/audit memory,
- upstream dependency monitoring.

They may not produce:

- buy/sell,
- rank,
- sizing,
- selector input,
- paper order,
- live order,
- acceptance or deployment claims.

### Target Operating Model

| Lane | AS-WAS | TO-BE | Managed By | Validation Authority | Promotion Rule |
| --- | --- | --- | --- | --- | --- |
| SEC extraction | Task-specific SEC scripts and fallback logic. | `edgartools` adapter is tested against fixed existing SEC fixtures. | Source/Research Governance | `DATA_HEALTH` plus governance report | Promote only if fixture parity passes and raw filing identity is preserved. |
| Data validation | Imperative task validators with repeated schema checks. | `Pandera` schemas wrap recurring panels and validators. | Research Governance | `GOVERNANCE_HEALTH` / task-specific validator | Promote only if one validator becomes clearer or catches a documented issue. |
| Local artifact query | Pandas-heavy script joins over CSV/parquet. | DuckDB for SQL joins, Polars for lazy transforms in large artifact audits. | Backtest/Data Infra | `RESEARCH_ONLY` for audits, not acceptance | Promote only where runtime or code complexity improves. |
| Source loading | Each source task owns call log and manifest shape. | Optional `dlt` loader emits `external_source_receipt` rows. | Source Acquisition | `DATA_HEALTH` | Promote only if raw payload path/hash/timestamps are not hidden. |
| Dependency monitoring | Manual GitHub/web checks. | GitHub MCP read-only produces weekly upstream watch packets. | Governance | `GOVERNANCE_HEALTH` | Keep read-only; no repo writes or trading data access. |
| Lineage | Task reports and artifact manifests. | OpenLineage mapping only if lineage becomes cross-pipeline. | Governance/Data Infra | `GOVERNANCE_HEALTH` | Design first; no Marquez service until needed. |
| Orchestration | Scripts and PowerShell runners. | Prefect/Dagster only if retry/observability burden exceeds scripts. | Data Infra | `DATA_HEALTH` | No migration until current scripts are operationally insufficient. |

### Phase Plan

#### Phase 0: Intake And Safety Review

Scope:

- No code installation unless explicitly approved in a later implementation task.
- Review license, dependency footprint, network behavior, and raw-output controllability.

Artifacts:

- `tool_intake_matrix.csv`
- `tool_risk_register.csv`

Required fields:

```text
tool_name
version_or_commit
license
network_required
secret_required
raw_payload_access
timestamp_access
hashable_output
allowed_layers
forbidden_layers
promotion_status
```

Pass means:

- Tool is eligible for fixture-only pilot.

Pass does not mean:

- Tool is installed in production.
- Tool output is accepted as source truth.
- Strategy acceptance changes.

#### Phase 1: Fixture-Only Pilots

P1A `edgartools` SEC fixture comparison:

- Input: one existing SEC financing/dilution fixture.
- Output: comparison report.
- Join keys: CIK, accession number, filing date, document path, extracted fact key.
- Pass rule: raw identity preserved and extracted primitive facts match or explain differences.
- Stop rule: if accession/date/raw document identity is lost.

P1B `Pandera` validator pilot:

- Input: one non-trading artifact panel.
- Output: schema file plus validator diff report.
- Required rules:
  - no missing-as-negative,
  - timestamp fields present,
  - no outcome columns in assignment inputs,
  - row count stable.
- Stop rule: if schema creates brittle checks that block valid historical artifacts.

P1C DuckDB/Polars audit benchmark:

- Input: one existing MDD or candidate-bundle join.
- Output: runtime/code-size comparison.
- Pass rule: faster or simpler without changing rows.
- Stop rule: if row order, join keys, or null handling changes silently.

#### Phase 2: Opt-In Infrastructure Wrappers

Only after Phase 1 passes:

- Add wrappers under a narrow infrastructure namespace.
- Keep all outputs in reports/artifacts.
- Do not connect to selector, sizing, replay, or paper runtime.

Wrapper contracts:

```text
sec_extractor_adapter -> primitive fact fixture rows
panel_schema_validator -> validation report
artifact_query_helper -> reviewed query result
source_receipt_loader -> external_source_receipt rows
upstream_watch_packet -> dependency/security notes
```

#### Phase 3: Operating Cadence

Daily:

- None by default.
- No market-data MCP polling.

Weekly:

- GitHub MCP read-only watch packet for selected repos.
- Dependency/security drift notes only.

Per source-acquisition task:

- Use `edgartools` only if the task touches SEC extraction.
- Use `Pandera` if the output panel matches an existing schema.
- Use DuckDB/Polars if the artifact join is large enough to benefit.

Per quarterly cleanup or broad audit:

- Consider OpenLineage mapping if lineage questions repeat.
- Consider Prefect/Dagster only if failures/retries become hard to operate with scripts.

### Management Rules

#### Ownership

| Tool Family | Owner | Reviewer | Write Scope |
| --- | --- | --- | --- |
| `edgartools` | Source Acquisition | Research Governance | fixture reports and adapter prototypes only |
| `Pandera` | Research Governance | Data Infra | validator schemas and reports only |
| DuckDB/Polars | Data Infra | Backtest/Research Governance | audit helpers and benchmark reports only |
| `dlt` | Source Acquisition | Governance | source receipt loader skeleton only |
| GitHub MCP read-only | Governance | User/Lead review | watch packets only |
| OpenLineage | Governance/Data Infra | Research Governance | mapping docs only |
| Dagster/Prefect | Data Infra | Governance | design docs only until approved |

#### Environment Policy

- Pin versions or commits before pilot execution.
- Do not store secrets in reports, manifests, or source files.
- Network access must be explicit in task report.
- Raw payloads stay in `data/raw/<source>/`.
- Large derived panels stay in `data/artifacts/<task_id>/`.
- Small reports stay in `docs/reports/<task_id>/`.

#### Status Policy

Tool pass can update:

- docs,
- validators,
- artifact manifests,
- source-readiness notes.

Tool pass cannot update:

- strategy acceptance,
- deployment readiness,
- real-capital permission,
- broker truth,
- PnL validity,
- slot decision,
- sizing.

### Stop Rules

Stop adoption if any tool:

- hides raw payload identity,
- cannot expose source timestamps,
- requires secrets in command strings,
- changes row counts silently,
- infers lifecycle matches,
- treats missing data as negative,
- produces recommendation/rank/action text that cannot be separated from source facts,
- requires a long-running service before a simple script is proven insufficient.

### Concrete First Work Packet

Task name:

```text
External Tool Phase 1 Fixture Pilot
```

Read scope:

- Task3123 plan.
- Existing SEC financing/dilution fixture/report.
- One existing non-trading validator.
- One existing MDD or candidate-bundle join script/report.

Write scope:

- `docs/reports/<new_task_id>/`
- optional fixture-only prototype under `scripts/` only if implementation is explicitly authorized.

Validation:

- `python scripts/task_registry_validate.py`
- plus task-specific pilot validator if code is added.

Success:

- One of `edgartools`, `Pandera`, or DuckDB/Polars proves a measurable benefit without touching trading logic.

Failure:

- No tool proves a benefit. Keep current scripts.

## No-Background Decision-Maker Report

Conclusion first: apply these tools slowly and only around the brain.

First, review tool safety.  
Second, test with fixed fixtures only.  
Third, promote only wrappers that improve extraction, validation, or audit speed.  
Fourth, keep everything away from selector, sizing, replay, and orders.

The first real pilot should be:

1. `edgartools` SEC fixture comparison.
2. `Pandera` validator pilot.
3. DuckDB/Polars audit join benchmark.

Do not start with MCP market data. Do not start with a new backtest engine. Do not start with ML.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `docs/operating_system/project_operating_state.md`
  - `docs/architecture/test_validation_canonicalization_map.md`
  - `docs/reports/task_3123_external_tool_aswas_tobe_adoption_plan/task_3123_external_tool_aswas_tobe_adoption_plan.md`
- Outputs:
  - `docs/reports/task_3124_external_tool_operations_plan/task_3124_external_tool_operations_plan.md`
- Row counts:
  - Operating lanes: 7.
  - Tool owner rows: 7.
  - Phase count: 4.
- Validation commands:
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Not applicable. No external raw datasets were acquired.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
