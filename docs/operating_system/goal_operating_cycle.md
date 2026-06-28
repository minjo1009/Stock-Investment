# Goal Operating Cycle

## Purpose

This document fixes the continuity layer for the project. A user goal is not handled as a one-off chat instruction. It is handled as a governed research operating cycle with team ownership, exact data rules, artifact discipline, validation, and investor-grade reporting.

For current paper-trading governance, first read `docs/ownership/current_operating_model.md`. It names the current standing operating board, named leads, readiness status, and latest blockers.

Every non-trivial work item must close with `docs/operating_system/work_closeout_protocol.md`.

## Trigger

Use this cycle whenever the user provides:

- `/goal`
- `Goal:`
- `goal :`
- a long-running project objective
- a request to continue developing until a measurable target is reached

## Step 1. Goal Intake Contract

Before implementation, record the working contract in the task report or task notes:

| Field | Requirement |
|---|---|
| Objective | One concrete sentence |
| Target Metrics | Count, avg net, win rate, false positive, drawdown, OOS, or data-readiness targets |
| Forbidden Actions | No inferred matching, no fake source, no label leakage, no deployment claim unless live-ready |
| Available Data | Raw sources currently present |
| Missing Data | Raw sources required but absent |
| Owner Team | One primary team |
| Reviewer Team | At least one reviewer team |
| Output Directory | `docs/reports/<task_id>/` for reports and small tables |
| Large Artifact Directory | `data/artifacts/<task_id>/` for large panels |
| Validation | Unit tests, scripts, leakage audit, split/OOS audit |

If required raw data is missing, the next task is data acquisition or source audit, not strategy fitting.

If a Graphify context pack is older than the current task family, treat it as stale discovery context only. Current ownership and readiness must come from `docs/ownership/current_operating_model.md`, `tasks/task_registry.csv`, and the latest relevant task reports.

## Step 2. Team Routing

| Work Type | Owner Team | Reviewer Team |
|---|---|---|
| Raw source, quote, status, LULD, depth, receive timestamp | Data & Market Microstructure | Research Governance |
| Multi-day market/theme regime | Regime Research | Backtest & Simulation Infra |
| Intraday continuation archetypes | Intraday Continuation Research | Regime Research |
| Deterministic replay, grid backtest, exact lifecycle labels | Backtest & Simulation Infra | Research Governance |
| Cost, slippage, exposure, live-readiness | Execution & Risk | Data & Market Microstructure |
| Registry, report, artifact migration, standards | Research Governance | Relevant owner team |

Current named lead mapping is maintained in `docs/ownership/team_charter.md` and `docs/ownership/current_operating_model.md`. Do not infer a missing lead from team name alone.

## Step 3. Subagent Packet

Subagents must receive bounded packets using `docs/ownership/subagent_packet_standard.md`.

Required fields:

```text
Objective:
Owner Team:
Read Scope:
Write Scope:
Inputs:
Required Outputs:
Forbidden Actions:
Validation Command:
Report Requirement:
```

Parallel subagents must have disjoint write scopes. Explorers do not edit files. Workers report changed files and commands run.

## Step 4. Data Integrity Gate

No research result can proceed to strategy interpretation until the data gate is explicit:

- exact key used for joins
- lifecycle identity source
- available raw fields
- missing raw fields
- inferred matching flag
- label leakage audit
- source path and artifact lineage

Hard failures:

- symbol/date/price/time proximity lifecycle matching
- unlabeled rows converted to negatives
- missing quote/depth/status/LULD approximated as real microstructure
- full-day or future outcome fields used in entry assignment

## Step 5. Implementation Discipline

Default implementation order:

1. Source audit or feature contract
2. Deterministic panel build
3. Exact label join
4. Leakage audit
5. Split/OOS evaluation
6. Cost/slippage stress if PnL is claimed
7. Artifact manifest
8. Report

For quant strategy work, do not jump directly to a best filter. Build candidate sets or grids only after data labelability is known.

## Step 6. Artifact Discipline

| Artifact Type | Location |
|---|---|
| Markdown report | `docs/reports/<task_id>/` |
| Decision CSV | `docs/reports/<task_id>/` |
| Small audit table | `docs/reports/<task_id>/` |
| Large panel/grid/assignment log | `data/artifacts/<task_id>/` |
| Raw market data | `data/raw/<source>/` |
| Artifact manifest | `docs/reports/<task_id>/artifact_manifest.csv` |

Existing large artifacts may move only through a dependency-aware migration plan and migration result log.

## Step 7. Report Discipline

Every goal report must include:

1. `Decision Summary`
2. `Quant Expert Report`
3. `No-Background Decision-Maker Report`
4. `Artifact Manifest`

The report must explicitly state:

- whether inferred matching was used
- whether missing labels were treated as negatives
- whether missing raw sources were approximated
- whether the result is diagnostic-only or deployment-ready
- what the next blocker is

## Step 8. Registry Discipline

Update `tasks/task_registry.csv` when:

- a task becomes canonical
- a task becomes active
- a task is superseded
- strategy acceptance or data readiness changes
- a new key report/decision artifact becomes the current reference

Update `tasks/archive_candidate_registry.csv` and artifact manifests after large artifact migration or report storage changes.

## Step 9. Validation Discipline

Minimum validation for a goal:

```text
python scripts/task_registry_validate.py
python scripts/codeowners_coverage_validate.py
python validate_readiness_registry.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```

Add task-specific tests or scripts listed in the task report. If validation cannot run, the report must say why and mark the remaining risk.

## Step 10. Completion Output

The final response for a goal must include:

- what changed
- where the artifacts are
- what validation passed
- what remains blocked
- whether the target was achieved
- next recommended action

Do not claim completion because work was attempted. Claim completion only when the stated completion criteria are satisfied or the blocker is explicitly proven.
