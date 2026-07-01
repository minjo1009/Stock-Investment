# TASK-4100 Codex Governance / Task Operating System Bootstrap

## Goal

Create a repo-level operating layer that limits Codex sprawl, reduces irrelevant context loading, enforces task profiles, and exposes a read-only local dashboard for current Codex work.

## Implemented Files

- `AGENTS.md`
- `ops/*.yaml`
- `.codex/skills/*/SKILL.md`
- `scripts/ops/*.py`
- `docs/generated_context/README.md`
- `ops/dashboard/index.html`
- `docs/reports/task_4100_codex_governance_bootstrap/*`

## Governance Model

TASK-4100 introduces task and document registries, durable operating state, task profiles, context bundle configuration, validators, and a static dashboard. The model keeps trading safety boundaries explicit and makes task closeout depend on registries, artifacts, validators, and scope checks.

## Task Registry Summary

`ops/task_registry.yaml` defines `TASK-4100`, status enums, priority enums, allowed paths, forbidden paths, required artifacts, required validators, and closeout fields.

## Doc Registry Summary

`ops/doc_registry.yaml` registers the new governance documents, task artifacts, and Codex skill documents. Historical repository markdown is intentionally not migrated in this bootstrap and is reported through soft-mode warnings.

## Task Profiles Summary

`ops/task_profiles.yaml` defines `DOCS_GOVERNANCE`, L0-L6 profiles, `UI_STORYBOOK_VISION`, and `TASK_CLOSEOUT`, including required principles, forbidden intents, and checks.

## Context Bundle Summary

`ops/context_bundles.yaml` defines `TASK_4100` plus starter bundles for UI, L4, and L5 work. `build_context_bundle.py` creates deterministic markdown and CSV outputs under `docs/generated_context/`.

## Dashboard Summary

`scripts/ops/render_ops_dashboard.py` generates a read-only static dashboard at `ops/dashboard/index.html` with operating state, task status, validators, artifacts, document status, context token usage, validation reports, and hard boundaries.

## Validators

Validators cover task registry integrity, document registry integrity, context bundles, task scope, required artifacts, and closeout.

## Hard Boundaries Preserved

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains `FORBIDDEN`.
- Live order remains `FORBIDDEN`.
- Paper promotion remains `FORBIDDEN_UNLESS_EXPLICITLY_ACCEPTED`.
- Missing or stale data remains `UNKNOWN_OR_BLOCKER`.

## What This Does Not Do

This task does not implement trading logic, UI screens, broker integration, order execution, DB schema changes, scheduler registration, strategy acceptance, paper promotion, or live trading behavior.

## Known Limitations

- Historical markdown files are not fully registered; `validate_doc_registry.py --soft` reports them as warnings.
- Context token counting falls back to an approximate count when `tiktoken` is not installed.
- Scope validation uses the task artifact manifest as the hard gate when the repo already has unrelated dirty files.

## Next Recommended Tasks

1. TASK-4101 Context Bundle hardening for UI work
2. TASK-4102 L4 profile validator hardening
3. TASK-4103 L5 policy action validator hardening
4. TASK-4104 Mission Control Dashboard v1
