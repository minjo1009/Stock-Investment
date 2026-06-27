# Document Retention Policy

## Purpose

Keep the repository usable without erasing evidence needed to prove current status boundaries.

## Retention Classes

| Class | Retention rule |
|---|---|
| `ACTIVE` | Keep in place and include in normal read scope. |
| `CANONICAL` | Keep in place unless a dependency-aware migration is approved. |
| `DIAGNOSTIC` | Keep if it proves a decision, blocker, or failed validation. Exclude from default read scope. |
| `SUPERSEDED` | Preserve until summarized and linked by a newer canonical artifact. |
| `ARCHIVE` | Preserve but exclude from default workflows. |
| `DELETE_CANDIDATE` | Delete only after explicit user approval and a deletion log. |
| `UNKNOWN_NEEDS_REVIEW` | Do not delete or move until an owner reviews it. |

## Never Delete Without Explicit Approval

- `tasks/task_registry.csv`
- `tasks/active_task_registry.csv`
- `AGENTS.md`
- `README.md`
- `docs/active/`
- `docs/ownership/current_operating_model.md`
- `docs/ownership/readiness_registry.yaml`
- strategy/deployment/acceptance contracts
- validators and validation scripts
- raw source data
- DB authority files
- artifact manifests
- canonical task reports
- files proving `NOT_ACCEPTED`, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, or `FORBIDDEN`

## Default Action

When unsure, classify as `UNKNOWN_NEEDS_REVIEW`.

