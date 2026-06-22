# Project Context Bootstrap

## Purpose

This is the first file Codex should read before non-trivial work in this repository.

It answers:

- what the project is
- what is currently trusted
- where canonical state lives
- how to route work
- what must not be done

## Project In One Sentence

This repository is a governed US-equity quant/event trading research and paper-trading platform.

The project combines:

- raw market and intelligence source collection
- source-certified event interpretation
- multi-layer trading brain research
- deterministic backtest and replay
- paper/live execution readiness
- frontend/Slack reporting
- governance and artifact control

## Current Truth Hierarchy

Use this order when sources conflict:

1. `docs/operating_system/project_context_bootstrap.md`
2. `docs/ownership/current_operating_model.md`
3. `tasks/task_registry.csv`
4. latest relevant `docs/reports/<task_id>/` decision/report
5. `docs/architecture/canonical_workstream_map.md`
6. `docs/architecture/brain_layer_map.md`
7. source code and tests
8. stale Graphify or old task reports
9. chat memory

Chat memory is never the highest authority.

## Current Project Reality

| Area | Current State |
| --- | --- |
| Strategy acceptance | `NOT_ACCEPTED` unless a newer registry row proves otherwise |
| Deployment readiness | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` unless readiness registry proves otherwise |
| Real capital | `FORBIDDEN` until deployment gates pass |
| Paper trading | Controlled paper work exists, but strategy acceptance and broker-truth gates remain separate |
| Brain layer | Task742 is the current practical economic meaning candidate; it is review-only |
| Repository hygiene | Cleanup/canonicalization is required before broad new feature development |

## Work Routing

| Request Type | Start Here | Owner |
| --- | --- | --- |
| Project cleanup, canonical maps, registry, reports | `docs/architecture/canonical_workstream_map.md` | Research Governance |
| Source, timestamp, raw data, market microstructure | `docs/ownership/current_operating_model.md` and latest data task | Data & Market Microstructure |
| Strategy/regime/content/relation brain | `docs/architecture/brain_layer_map.md` | Regime Research plus relevant research team |
| Backtest, replay, OOS, cost, capacity | latest backtest task report and validation command | Backtest & Simulation Infra |
| Execution, broker truth, paper/live orders | current operating model and readiness registry | Execution & Risk |
| Frontend or Slack | frontend data contract, Slack reports, catalog scripts | Frontend/UI or Research Governance |
| GPT/Chrome review | `skills/gpt-chrome-review-subagent/SKILL.md` | Research Governance reviewer |

## Cleanup Authority Maps

| Map | Purpose |
| --- | --- |
| `docs/operating_system/project_operating_state.md` | One-page current standing state |
| `docs/architecture/project_status_authority_matrix.md` | What can and cannot change acceptance/deployment/real-capital status |
| `docs/operating_system/project_cleanup_final_runbook.md` | Final five-pass cleanup runbook and locked resume order |
| `docs/architecture/workstream_surface_inventory.md` | Project-wide formal surface inventory |
| `docs/architecture/src_canonicalization_map.md` | Source-code classification and reuse boundary |
| `docs/architecture/test_validation_canonicalization_map.md` | Test lane authority and PASS meaning |
| `docs/architecture/skill_md_subagent_canonicalization_map.md` | Skill, MD, GPT, and subagent routing boundary |

## Mandatory Guardrails

- No inferred lifecycle matching.
- No missing labels as negatives.
- No missing raw source approximation.
- No outcome/PnL/label in assignment logic.
- No deployment claim without live-source readiness.
- No strategy claim without split/OOS, leakage, cost/slippage, and artifact audit.
- No large raw/artifact data committed directly to Git.
- No GPT/Chrome output treated as source-of-truth.

## Brain Layer Quick Map

The active intended brain structure is:

```text
Source evidence
-> Primitive fact extraction
-> Economic meaning
-> Relation edge
-> Candidate bundle
-> Slot decision
-> Backtest/deployment gate
```

Important current interpretation:

- Task741 is useful as a denominator audit but too blocker-heavy for active practical interpretation.
- Task742 is the current practical economic meaning candidate.
- Task742 still emits review-only objects, not buy/sell/score/backtest permission.

## Artifact Storage Rule

Small, human-readable, commit-eligible:

- contracts
- architecture maps
- reports
- decision CSVs
- pass/fail CSVs
- artifact manifests

Local or external artifact storage:

- raw data
- full panels
- large CSV/JSONL/PARQUET outputs
- runtime databases
- broker/account archives

## Closeout Rule

Every meaningful work item must say:

- what changed
- where artifacts are
- which validation passed
- what remains blocked
- whether registry/current operating model updates were needed
- next action
