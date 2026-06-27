# Active SSOT Index

This index separates current source-of-truth files from navigation and historical material.

## Classification Taxonomy

| Class | Meaning |
|---|---|
| `ACTIVE` | Currently used for ongoing work. |
| `CANONICAL` | Source of truth for a domain. |
| `DIAGNOSTIC` | Research-only or validation-only. Not accepted. |
| `SUPERSEDED` | Replaced by a newer artifact, but useful for history. |
| `ARCHIVE` | Preserved but excluded from default Codex workflow. |
| `DELETE_CANDIDATE` | Likely safe to delete after explicit confirmation. |
| `UNKNOWN_NEEDS_REVIEW` | Do not delete. Requires owner review. |

## Current Active and Canonical Sources

| Path | Class | Purpose |
|---|---|---|
| `docs/active/README_ACTIVE.md` | `ACTIVE` | Default entry point. |
| `docs/active/PROJECT_STATUS.md` | `ACTIVE` | Condensed current status. |
| `docs/active/CODEX_READ_SCOPE.md` | `ACTIVE` | Default Codex context rules. |
| `docs/active/CURRENT_TASKS.md` | `ACTIVE` | Lightweight active queue. |
| `tasks/active_task_registry.csv` | `ACTIVE` | Lightweight active task registry. |
| `scripts/active_task_registry_validate.py` | `ACTIVE` | Validator for active task registry shape, statuses, and report links. |
| `scripts/project_file_inventory_audit.py` | `ACTIVE` | Full file inventory classifier for cleanup and retention decisions. |
| `docs/reports/A005_full_file_inventory_audit/` | `ACTIVE` | Current full-file inventory audit and cleanup candidate manifests. |
| `docs/ownership/current_operating_model.md` | `CANONICAL` | Paper-trading governance and acceptance-board truth. |
| `docs/ownership/readiness_registry.yaml` | `CANONICAL` | Machine-readable readiness and blocker state. |
| `tasks/task_registry.csv` | `CANONICAL` | Historical/canonical task registry evidence. |
| `docs/acceptance/strategy_acceptance_contract.md` | `CANONICAL` | Strategy acceptance contract. |
| `docs/acceptance/deployment_acceptance_contract.md` | `CANONICAL` | Deployment readiness contract. |
| `docs/reports/task_599_strategy_acceptance_program/` | `CANONICAL` | Current strategy acceptance program. |
| `docs/reports/task_598_paper_week_feedback_operating_plan/` | `CANONICAL` | Current paper-week diagnosis. |
| `docs/reports/task_597_frontend_backend_paper_ops_triage/` | `ACTIVE` | Supporting owner remediation board. |
| `docs/reports/task_600_4_broker_truth_exit_lifecycle/` | `ACTIVE` | P0 broker-truth blocker evidence. |
| `docs/reports/task_602_4_order_replay_recovery/` | `ACTIVE` | P0 replay blocker evidence. |
| `docs/reports/task_601_4_concentration_stability/` | `ACTIVE` | P0 candidate-funnel evidence. |

## Navigation-Only Sources

| Path | Class | Purpose |
|---|---|---|
| `README.md` | `NAVIGATION_ONLY` | Repository-level orientation, older than current active layer. |
| `docs/INDEX.md` | `NAVIGATION_ONLY` | Broad docs index. Superseded for default Codex startup by `docs/active/`. |
| `docs/obsidian/` | `NAVIGATION_ONLY` | Human Obsidian navigation and boards. |
| `graphify-out/` | `DIAGNOSTIC` | Stale 2026-04-25 discovery output; not current state. |

## Missing Historical Layers

| Path | Class | Note |
|---|---|---|
| `docs/llm_wiki/` | `SUPERSEDED` | Not present in this checkout; active layer replaces it for default startup. |
| `docs/frontend_app_ssot/` | `SUPERSEDED` | Not present in this checkout; use `docs/frontend_data_contract.md`, frontend task reports, and current active pointers. |
