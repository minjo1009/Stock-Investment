# Codex Working Rules

This repository favors clear scope, small changes, and verifiable results over fast guesses.

## Required Read Order

Default to low-token context loading.

Before non-trivial work, read only the short operating state first, then open detailed maps only when the task touches that domain.

Minimum start:

1. `docs/operating_system/project_operating_state.md`
2. Latest relevant task report or file being edited

Backtest-related start:

1. `docs/operating_system/project_operating_state.md`
2. `docs/operating_system/backtest_harness_operating_discipline.md`
3. Latest relevant task report or file being edited

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

Graphify, stale chat summaries, and older task reports are below current operating documents and registry state.

## Low-Token Operating Rule

- Do not preload every governance document every turn.
- Open `src_canonicalization_map.md` only when touching `src/`.
- Open `test_validation_canonicalization_map.md` only when discussing or running tests.
- Open `skill_md_subagent_canonicalization_map.md` only when touching skills, MD files, GPT, or subagents.
- Open `project_status_authority_matrix.md` only when a task could affect acceptance, deployment, real capital, or validation wording.
- Open `backtest_harness_operating_discipline.md` before any backtest, replay, harness, adapter-to-backtest, split/OOS, cost/slippage, or replay-governance work.
- Prefer validator scripts over rereading long reports.
- Keep chat reports short; put expert detail in repo reports.

## Standing Status

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- GPT/Chrome: review-only
- Test success: never acceptance by itself
- Inventory complete: classification only, not validation complete

## Think Before Coding

- Summarize objective, assumptions, and success criteria before implementation.
- Resolve discoverable questions through files, docs, tests, and registry first.
- If a request is ambiguous, state tradeoffs instead of guessing.
- If a smaller path is enough, say so and keep scope small.

## Simplicity First

- Prefer the minimum change that solves the requested problem.
- Do not add unrequested features, configuration, or abstractions.
- Do not over-generalize one-off logic.
- Do not add defensive code for impossible or unsupported paths.

## Surgical Changes

- Modify only files directly connected to the request.
- Do not perform unrelated refactors, formatting, or cleanup.
- Follow existing structure unless the task explicitly updates structure.
- Remove only unused imports/variables/functions created by this change.
- Do not delete unrelated historical code or artifacts.

## Non-Negotiable Quant Rules

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback.
- Missing labels are never negatives.
- Missing raw sources are reported, not approximated.
- Labels/outcomes are evaluation-only and must not enter assignment logic.
- Strategy claims require split/OOS, leakage, cost/slippage, and artifact audit.
- Deployment claims require live-source readiness.

## Artifact Discipline

- Small reports and decisions: `docs/reports/<task_id>/`
- Large derived panels: `data/artifacts/<task_id>/`
- Raw sources: `data/raw/<source>/`
- Every canonical or active task needs a registry row and artifact manifest.
- Moving existing artifacts requires dependency-aware migration planning.

## Report Discipline

Every task report should follow `docs/report_standard.md`:

- Decision Summary
- Quant Expert Report
- No-Background Decision-Maker Report
- Artifact Manifest

## Subagent Discipline

When subagents are used, issue bounded packets following `docs/ownership/subagent_packet_standard.md`.

- Workers must have disjoint write scopes.
- Explorers must not edit files.
- GPT/Chrome is review-only and never source-of-truth.
- Every packet must include validation authority from `docs/architecture/test_validation_canonicalization_map.md`.

## User-Facing Report Style

Final/status reports to the user must:

- Say the conclusion first.
- Use short Korean sentences.
- Use numbers before explanation.
- Separate `done / failed / next`.
- Avoid long institutional wording in chat unless explicitly requested.
- Keep expert detail inside repo reports.
- Do not use the style nickname itself unless the user explicitly asks for that word.

## Completion Discipline

A task is not complete until these are updated or explicitly marked not applicable:

- task/report artifacts
- artifact manifest
- task registry when canonical/active state changes
- validation commands
- validation authority
- next action and blocker report
