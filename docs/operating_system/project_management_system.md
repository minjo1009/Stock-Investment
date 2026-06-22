# Project Management System

## Purpose

This project is too large to run from chat memory.

All future work must be managed through a repository-native operating system:

```text
bootstrap -> workstream map -> owner routing -> task registry -> artifact policy -> validation -> closeout
```

## Management Objects

| Object | Location | Purpose |
| --- | --- | --- |
| Bootstrap | `docs/operating_system/project_context_bootstrap.md` | First read before meaningful work |
| Current operating model | `docs/ownership/current_operating_model.md` | Current paper/strategy/deployment state |
| Workstream map | `docs/architecture/canonical_workstream_map.md` | Functional canonical map |
| Brain map | `docs/architecture/brain_layer_map.md` | Trading brain layer map |
| Subagent routing | `docs/ownership/subagent_roster_and_routing.md` | Owner/reviewer/skill routing |
| Task registry | `tasks/task_registry.csv` | Task state and current references |
| Task report | `docs/reports/<task_id>/` | Decision and evidence |
| Large artifacts | `data/artifacts/<task_id>/` | Generated panels and heavy outputs |
| Raw sources | `data/raw/<source>/` | Raw input sources |

## Operating States

| State | Meaning |
| --- | --- |
| `canonical` | Current source of truth for a domain |
| `active` | Current working line |
| `diagnostic` | Research-only, not accepted |
| `superseded` | Replaced by a newer task |
| `archived` | Preserved but excluded from default workflows |

## Work Intake

Every non-trivial work item must define:

- objective
- owner team
- reviewer team
- read scope
- write scope
- forbidden actions
- output artifacts
- validation commands
- completion criteria

If these are unclear, the first task is not coding. The first task is clarification or canonicalization.

## Canonicalization Before Expansion

When a domain has too many task variants, do not add another feature.

First answer:

1. Which task is current?
2. Which tasks are diagnostic only?
3. Which task superseded which?
4. Which code path is reusable?
5. Which report is decision-grade?
6. Which artifacts are local-only?
7. Which validation command proves the current state?

## Artifact Policy

Use:

- `docs/reports/<task_id>/` for markdown reports, decisions, small audit tables, manifests.
- `data/artifacts/<task_id>/` for large generated panels.
- `data/raw/<source>/` for raw market/source data.

Do not put large CSV/JSONL/PARQUET panels into Git as normal docs.

Reports should link to large artifacts by path and manifest, not embed or duplicate them.

## Validation Policy

Minimum governance validation:

```powershell
python scripts\task_registry_validate.py
```

When available and relevant:

```powershell
python scripts\codeowners_coverage_validate.py
python validate_readiness_registry.py
python scripts\operating_closeout_validate.py
python scripts\governance_completion_audit.py
```

Task-specific tests must be listed in the task report.

## Brain Development Policy

The trading brain must stay layered:

```text
source evidence
-> primitive facts
-> economic meaning
-> relation edge
-> candidate bundle
-> slot decision
-> backtest/deployment gate
```

Forbidden shortcuts:

- source text directly to buy/sell
- content direction directly to rank/score
- missing data directly to bearish label
- report language directly to strategy acceptance
- GPT review directly to source truth

## Skill Policy

Use skills only when they improve discipline.

| Skill | When To Use |
| --- | --- |
| `skills/codex-gpt-expert-relay-loop/SKILL.md` | Non-trivial task classification, expert prompt routing, Chrome GPT relay, and post-implementation review prompt |
| `skills/subagent-artifact-governance/SKILL.md` | Artifact classification, report cleanup, migration planning |
| `skills/subagent-broker-lifecycle-ops/SKILL.md` | Broker truth, order lifecycle, paper/live execution gates |

Skills can define workflow, not final truth.

## Closeout

No non-trivial task is complete until it states:

- what changed
- what did not change
- validation result
- report path
- registry update status
- artifact manifest status
- next blocker

If a task only produces governance documents, it must say no strategy or deployment state changed.
