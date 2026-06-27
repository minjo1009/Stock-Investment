# A001 Project Management Reset Report

## 1. Decision Summary

- What changed: created a new `docs/active/` operating layer, a lightweight active task registry, cleanup policies, archive/delete candidate manifests, duplicate-doc review, and this A001 report.
- What did not change: no trading behavior, strategy acceptance, deployment readiness, broker mutation logic, order-generation logic, backtest result, raw data, DB file, validator, canonical report, or canonical registry file changed.
- Current status boundaries:
  - Strategy acceptance: `NOT_ACCEPTED`
  - Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
  - Real capital: `FORBIDDEN`
- Verdict: A001 is an operating-structure cleanup, not a trading or strategy task.
- Next action: user review of delete/archive manifests before any destructive A002/A003 work.

## Goal Intake Contract

| Field | A001 Contract |
|---|---|
| Objective | Create a clean active workspace and project table-of-contents system without changing trading behavior. |
| Target Metrics | Required files created; default Codex read scope reduced to active docs plus edited target; delete/archive manifests created; validation recorded. |
| Forbidden Actions | No trading/deployment/broker mutation; no order-generation changes; no backtest changes; no risky deletion without explicit approval. |
| Available Raw Sources | Not applicable. A001 did not use market raw sources. |
| Missing Raw Sources | Not applicable for cleanup. Existing readiness blockers remain unchanged. |
| Owner Team | Research Governance. |
| Reviewer Team | Governance Reviewer, with Execution & Risk and Data & Market Microstructure as status-boundary reviewers when needed. |
| Output Directory | `docs/reports/A001_project_management_reset/` |
| Artifact Locations | `docs/active/`, `docs/archive/`, `tasks/active_task_registry.csv` |
| Validation Commands | `python scripts/task_registry_validate.py`; `python scripts/operating_closeout_validate.py`; `python scripts/governance_completion_audit.py` |
| Completion Criteria | Active layer, candidate manifests, duplicate review, active registry, report, and validation record exist. |
| Failure Criteria | Any deletion without approval; status-boundary drift; missing report/manifest; unrecorded validation failure. |

## 2. Problem Diagnosis

The repository has strong governance artifacts, but the entry points overlap. `README.md`, `docs/INDEX.md`, Obsidian home, operating-system docs, current operating model, task registry, and report directories all point at different layers of truth.

Most confusing areas:

- `README.md` is older and broad.
- `docs/INDEX.md` is useful but wide.
- `docs/obsidian/` is a human navigation layer, not a Codex default context.
- `docs/reports/` contains many historical reports; several are superseded but still needed as evidence.
- Graphify output is stale for current paper-ops governance.
- The requested `docs/llm_wiki/`, `docs/frontend_app_ssot/`, `project_management_system.md`, and `project_operating_state.md` paths are not present in this checkout.

## 3. New Project Table of Contents

The new table of contents is in `docs/active/PROJECT_TABLE_OF_CONTENTS.md`.

It organizes the project as:

- PART 0. Active Operating Layer
- PART 1. Product / Frontend App
- PART 2. Trader Brain Backend
- PART 3. Data / DB / Scheduler
- PART 4. Backtest / Validation
- PART 5. Execution / Broker / Risk
- PART 6. Governance / Archive

Active/canonical/archive definitions are maintained in `docs/active/ACTIVE_SSOT_INDEX.md` and `docs/active/DOCUMENT_RETENTION_POLICY.md`.

## 4. Active Workspace Created

Created:

- `docs/active/README_ACTIVE.md`: default active entry point.
- `docs/active/PROJECT_STATUS.md`: condensed current status and boundaries.
- `docs/active/ACTIVE_SSOT_INDEX.md`: source-of-truth and classification index.
- `docs/active/CODEX_READ_SCOPE.md`: default Codex read scope and domain expansions.
- `docs/active/CURRENT_TASKS.md`: lightweight current task list.
- `docs/active/PROJECT_TABLE_OF_CONTENTS.md`: book-style project hierarchy.
- `docs/active/WORKSTREAM_MAP.md`: owner/reviewer routing.
- `docs/active/DOCUMENT_RETENTION_POLICY.md`: retention classes and never-delete rules.
- `docs/active/DELETE_CANDIDATE_POLICY.md`: deletion candidate guardrails.
- `tasks/active_task_registry.csv`: lightweight active queue seeded with A001.

## 5. Archive Candidate Summary

`archive_candidates.csv` contains 10 candidate rows.

Count by category:

- `diagnostic_backtests`: 4
- `superseded_reports`: 4
- `old_gpt_loops`: 1
- `duplicate_navigation_docs`: 1

Highest-impact archive candidates:

- `docs/reports/task_406_deterministic_decision_rebuild`
- `docs/reports/task_401_forward_live_canonical_multifactor_decision_layer`
- `docs/reports/task_407_raw_native_vectorized_rebuild`
- `graphify-out`

No files were moved.

## 6. Delete Candidate Summary

`delete_candidates.csv` contains 10 candidate rows.

Recommendation counts:

- `DELETE_SAFE`: 3
- `NEEDS_REVIEW`: 7
- `ARCHIVE_ONLY`: 0
- `KEEP`: 0

`DELETE_SAFE` candidates are limited to generated cache/marker files and still require user approval.

No files were deleted.

## 7. Duplicate Management Docs Review

`duplicate_docs_review.csv` reviews 15 rows, including all requested management-document paths and actual replacements where the requested path is missing.

Entry points:

- Default Codex entry: `docs/active/README_ACTIVE.md`
- Broad human/repository entry: `README.md`
- Broad docs navigation: `docs/INDEX.md`
- Obsidian human navigation: `docs/obsidian/Vault Home.md`

Canonical sources:

- `docs/ownership/current_operating_model.md`
- `docs/ownership/readiness_registry.yaml`
- `tasks/task_registry.csv`
- acceptance contracts

Superseded or missing layers:

- `docs/llm_wiki/`
- `docs/frontend_app_ssot/`
- missing older project management paths under `docs/operating_system/`

## 8. Codex Future Read Scope

Default read scope is now defined in `docs/active/CODEX_READ_SCOPE.md`.

Default normal work reads:

1. `docs/active/README_ACTIVE.md`
2. `docs/active/PROJECT_STATUS.md`
3. `docs/active/ACTIVE_SSOT_INDEX.md`
4. `docs/active/CURRENT_TASKS.md`
5. the specific file or folder being edited

Historical reports, Obsidian, Graphify, and old wiki-style layers are excluded unless directly needed.

## 9. Validation

Commands run:

| Command | Result |
|---|---|
| `python scripts/task_registry_validate.py` | `[REGISTRY_OK] tasks\task_registry.csv` |
| `python scripts/operating_closeout_validate.py` | `[OPERATING_CLOSEOUT_OK]` |
| `python scripts/governance_completion_audit.py` | `[GOVERNANCE_COMPLETE]` |
| `python scripts/codeowners_coverage_validate.py` | `[CODEOWNERS_OK] .github\CODEOWNERS` |
| `python validate_readiness_registry.py` | `[READINESS_REGISTRY_OK] docs\ownership\readiness_registry.yaml` |

CSV parse checks:

| File | Parsed rows |
|---|---:|
| `delete_candidates.csv` | 10 |
| `archive_candidates.csv` | 10 |
| `duplicate_docs_review.csv` | 15 |
| `tasks/active_task_registry.csv` | 1 |

Known limitations:

- Git status could not be checked because `git` was not available in the shell PATH.
- The initial requested first-read paths `docs/operating_system/project_management_system.md`, `docs/operating_system/project_operating_state.md`, `docs/llm_wiki/task_artifact_index.md`, and `docs/llm_wiki/README.md` were missing in this checkout.
- Graphify was read only as stale discovery evidence, not current state.

## 10. Clarifications Needed Before Destructive Cleanup

See `docs/reports/A001_project_management_reset/clarification_questions.md`.

Main blockers:

- Whether historical reports should be moved or only excluded from default read scope.
- Whether duplicate generated frontend catalogs have separate consumers.
- Whether old Graphify output should be archived before regeneration.
- Which old frontend/PWA evidence remains audit evidence.

## 11. Next Task Recommendation

- A002 safe archive move: move only approved `ARCHIVE_ONLY`/archive candidates and update references.
- A003 safe delete pass: delete only approved `DELETE_SAFE` candidates and produce a deletion log.
- A004 active SSOT compression: create condensed frontend/backend/governance pointers after owner review.

## 12. Quant Expert Report

A001 made no strategy claim.

- Inferred lifecycle matching used: no.
- Symbol/date/price/time proximity fallback used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Labels/outcomes entered assignment logic: no.
- Split/OOS or cost/slippage claim made: no.
- Deployment-ready claim made: no.

Current result remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`; strategy remains `NOT_ACCEPTED`; real capital remains `FORBIDDEN`.

## 13. No-Background Decision-Maker Report

The project now has a small front door: `docs/active/`.

Codex should start there instead of reading many old reports and overlapping navigation docs. Nothing was deleted, no trading logic changed, and the cleanup produced reviewable candidate manifests for the next archive/delete pass.

## 14. Artifact Manifest

The manifest is `docs/reports/A001_project_management_reset/artifact_manifest.csv`.

Outputs are small governance documents and CSV manifests. No large derived panel was created.
