# Project Operating System Skill

## Purpose

This is the repository-level operating skill for Codex work in this project.

Goal:

```text
Keep the US-equity quant/event trading and paper-trading project understandable across Codex sessions.
```

## Required Read Order

Default to low-token context loading.

Before non-trivial work, read only the short operating state first, then open detailed maps only when the task touches that domain.

Minimum start:

1. `docs/operating_system/project_operating_state.md`
2. Latest relevant task report or file being edited

Open the full stack below only for broad governance, handoff, or ambiguous cross-domain work:

1. `docs/operating_system/project_context_bootstrap.md`
2. `docs/operating_system/project_operating_state.md`
3. `docs/architecture/project_status_authority_matrix.md`
4. `docs/operating_system/project_cleanup_final_runbook.md`
5. `docs/ownership/current_operating_model.md`
6. `docs/architecture/canonical_workstream_map.md`
7. `docs/architecture/brain_layer_map.md`
8. `docs/architecture/src_canonicalization_map.md`
9. `docs/architecture/test_validation_canonicalization_map.md`
10. `docs/architecture/skill_md_subagent_canonicalization_map.md`
11. `docs/ownership/subagent_roster_and_routing.md`
12. `tasks/task_registry.csv`
13. Latest relevant task report

Chat memory is not higher authority than repository artifacts.

## Low-Token Operating Rule

- Do not preload every governance document every turn.
- Open `src_canonicalization_map.md` only when touching `src/`.
- Open `test_validation_canonicalization_map.md` only when discussing or running tests.
- Open `skill_md_subagent_canonicalization_map.md` only when touching skills, MD files, GPT, or subagents.
- Open `project_status_authority_matrix.md` only when a task could affect acceptance, deployment, real capital, or validation wording.
- Prefer validator scripts over rereading long reports.
- Keep chat reports short; put expert detail in repo reports.

## Standing Status

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- GPT relay: `CODEX_GPT_EXPERT_RELAY_LOOP_ACTIVE`
- Tests: never change acceptance status by themselves

## Core Principles

- Prefer canonical maps, artifact boundaries, and validation over new features.
- Keep raw data, generated panels, runtime DBs, and broker archives separate from code.
- Strategy acceptance, deployment readiness, broker truth, replay validity, source readiness, and blocker status do not change from external-model output alone.
- Missing raw sources are reported, not approximated.
- Outcome, PnL, and labels are evaluation-only and must not enter assignment logic.

## Work Classification

Classify work before editing:

| Type | Meaning | Required Owner |
| --- | --- | --- |
| `governance` | registry, artifact policy, canonical maps, report standard | Research Governance |
| `data` | raw source, provenance, timestamp, quality, source readiness | Data & Market Microstructure |
| `research` | regime, intraday, content, relation, hypothesis | Relevant research team |
| `backtest` | deterministic replay, OOS, cost, portfolio simulation | Backtest & Simulation Infra |
| `execution` | paper/live order lifecycle, broker truth, risk | Execution & Risk |
| `frontend` | trader terminal, chart/report UI, catalog surface | Frontend/UI |
| `reporting` | Slack, EOD, PM/CIO report, delivery safety | Research Governance or Slack owner |

## Source Code Rule

Use `docs/architecture/src_canonicalization_map.md`.

- `canonical_package_candidate` means review target, not production-ready.
- `active_task_code_review` means current task code that needs supersession notes before reuse.
- `historical_task_code_review` means preserve as evidence, not current engine.
- Do not build new features on task-scoped code without owner review.

## Test Authority Rule

Use `docs/architecture/test_validation_canonicalization_map.md`.

Allowed fast local gate candidates:

- `PACKAGE_HEALTH`
- `GOVERNANCE_HEALTH`

Not fast local quality gates:

- `EVIDENCE_ONLY`
- `RESEARCH_ONLY`
- `SUPPORT_ONLY`
- `EXECUTION_HEALTH`
- `ACCEPTANCE_EVIDENCE_REVIEW`
- `DATA_HEALTH`
- `REPORTING_HEALTH`

Every test result must preserve this footer:

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```

## Standard Workflow

1. Clarify the objective.
2. Gather current repo context.
3. Assign owner team and reviewer team.
4. Decide artifact scope.
5. Make the smallest safe change.
6. Validate with the right authority lane.
7. Update registry/report/manifest when applicable.
8. Report `done / failed / next` plainly.

## Artifact Rule

Commit candidates:

- `src/**/*.py`
- `tests/**/*.py`
- small `docs/**/*.md`
- decision CSVs
- pass/fail CSVs
- artifact manifests

Local or manifest-only by default:

- `data/raw/**`
- `data/artifacts/**`
- large `docs/reports/**/*.csv`
- `docs/reports/**/*.jsonl`
- runtime databases
- broker/account archives

## Subagent Rule

Use `docs/ownership/subagent_packet_standard.md`.

Use `docs/ownership/subagent_roster_and_routing.md` to choose the owner lane.

Rules:

- A worker edits only its write scope.
- An explorer is read-only.
- Two workers must not share a write scope in parallel.
- Legacy GPT/Chrome packets are historical artifacts only.

Subagent handoff must include:

- changed files
- artifacts produced
- validation commands run
- commands not run
- authority lane
- next blocker

## Codex-GPT Expert Relay Rule

Use `skills/codex-gpt-expert-relay-loop/SKILL.md` for non-trivial tasks that
benefit from expert prompt design or review before implementation.

The previous GPT/Chrome review skill has been deleted. Do not route new work
through `skills/gpt-chrome-review-subagent/SKILL.md` or its packet generator.

Relay output and historical GPT/Chrome notes remain review-only evidence. They
may not:

- invent facts, prices, dates, filings, fills, or labels
- approve strategy
- approve deployment
- replace raw sources or validation
- create buy/sell/sizing decisions
- change the task registry or readiness state by conversation alone

## Stop Rules

Stop and report when:

- required raw source is missing and the task is source-backed
- lifecycle matching would require symbol/date/price/time fallback
- assignment logic would require outcome, PnL, or label leakage
- artifact movement would require deletion or relocation without a migration plan
- current canonical task is unclear and several tasks conflict

## Closeout Rule

Every non-trivial task must close with:

- report or explicit non-reportable note
- registry update when active/canonical state changes
- artifact manifest when files are produced
- validation command
- authority lane
- clear next action and blocker
