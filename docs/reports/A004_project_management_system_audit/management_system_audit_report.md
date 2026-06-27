# A004 Project Management System Audit Report

## 1. Decision Summary

- Verdict: the project management system is mostly clear and now has machine-checkable active-task governance.
- What was fixed during this audit:
  - `docs/active/PROJECT_STATUS.md` no longer says cleanup is still pre-A002/A003.
  - `docs/active/CURRENT_TASKS.md` no longer lists completed A002/A003 work as future recommendations.
  - `scripts/active_task_registry_validate.py` now validates the lightweight active task registry.
  - `scripts/governance_completion_audit.py` now checks active docs and the active registry validator.
- What remains incomplete:
  - CodeRabbit review did not complete. WSL CLI installation succeeded, but `coderabbit review --agent` timed out waiting for browser authentication.
  - A002 archive moves remain blocked by reference migration requirements.
  - Seven `NEEDS_REVIEW` delete candidates still require owner decisions.
- Current status boundaries remain unchanged:
  - Strategy acceptance: `NOT_ACCEPTED`
  - Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
  - Real capital: `FORBIDDEN`

## Goal Intake Contract

| Field | A004 Contract |
|---|---|
| Objective | Verify whether the project management system is clear, cleanup was conservative, and future work can be managed through the new active operating layer. |
| Target Metrics | Active docs exist; active registry validates; cleanup logs prove deletes/skips; stale task recommendations removed; governance validators pass. |
| Forbidden Actions | No trading/deployment/broker mutation; no order-generation changes; no backtest changes; no raw/DB/validator/canonical evidence deletion. |
| Available Raw Sources | Not applicable; audit used repository governance files and cleanup logs. |
| Missing Raw Sources | Not applicable; existing readiness blockers remain unchanged. |
| Owner Team | Research Governance. |
| Reviewer Team | Governance Reviewer. |
| Output Directory | `docs/reports/A004_project_management_system_audit/` |
| Artifact Locations | A004 report, audit matrix, CodeRabbit status, artifact manifest, validator changes. |
| Validation Commands | Active registry validator plus governance closeout validators. |
| Completion Criteria | Requirement matrix exists; CodeRabbit status recorded; stale active docs fixed; validators pass. |
| Failure Criteria | Active registry not validated; stale next-task state remains; cleanup evidence missing; status-boundary drift. |

## 2. Audit Findings

### Major: CodeRabbit Review Is Blocked By Authentication

`@coderabbit` was requested. Windows PowerShell lacked `git`, `coderabbit`, and `sh`; WSL had `git`, and the CodeRabbit CLI was installed manually from the official Linux x64 zip. Review commands reached the agent authentication flow but timed out waiting for browser login.

Evidence:

- `.git` directory exists.
- Windows `git` command is not available in PATH.
- Windows `coderabbit` command is not available in PATH.
- WSL `git` is available.
- WSL CodeRabbit CLI is installed at `/home/minjo1009/.local/bin/coderabbit`.
- `coderabbit review --agent` returned `authentication_failed` after browser login timeout.

Impact: this report is not a CodeRabbit review. It is a repository-local governance audit. See `coderabbit_status.md`.

Suggested fix: authenticate the WSL CLI with `/home/minjo1009/.local/bin/coderabbit auth login --agent`, then rerun the scoped review commands.

### Major: Active Registry Was Not Machine-Validated

Before this audit, `tasks/active_task_registry.csv` existed but was not checked by a dedicated validator or the governance audit.

Impact: future active-task rows could drift from required fields, unsupported statuses, or broken report links without failing closeout.

Fix applied:

- Added `scripts/active_task_registry_validate.py`.
- Updated `scripts/governance_completion_audit.py` to require active docs and validate `tasks/active_task_registry.csv`.

### Minor: Active Status Docs Had Stale A002/A003 Wording

`PROJECT_STATUS.md` still described cleanup as pre-delete approval, and `CURRENT_TASKS.md` still listed A002/A003 as next recommendations after A003 had completed.

Impact: future Codex runs could misread the state and repeat completed cleanup work.

Fix applied:

- Updated cleanup status in `docs/active/PROJECT_STATUS.md`.
- Updated next recommendations in `docs/active/CURRENT_TASKS.md`.

## 3. Requirement Evidence

See `management_system_audit_matrix.csv`.

Summary:

- Proven requirements: 13.
- Not proven requirements: 1.

Not proven:

- CodeRabbit review completion.

CodeRabbit is blocked by browser authentication, not by repository governance design. Git status was available through WSL and showed a very large pre-existing dirty worktree outside the A001-A004 scope.

## 4. Cleanup Audit

The A002/A003 cleanup was conservative.

Deleted:

- `.pytest_cache`
- `__pycache__`
- `graphify-out/needs_update`

Preserved:

- Seven `NEEDS_REVIEW` delete candidates.
- Ten archive candidates with live references.
- Raw data, DB files, validators, canonical reports, registry files, and status-boundary evidence.

Conclusion: excessive generated cache was removed, but evidence-bearing or reference-bearing files were preserved.

## 5. Future Operating Control

Future work now has these controls:

- Codex starts from `docs/active/`.
- Current tasks are tracked in `tasks/active_task_registry.csv`.
- Active registry rows are validated by `python scripts/active_task_registry_validate.py`.
- Full governance closeout now includes active-layer files and active registry validation.
- A002 remains visibly blocked until a dependency-aware archive migration plan exists.

## 6. Quant Expert Report

A004 made no strategy claim.

- Inferred lifecycle matching used: no.
- Symbol/date/price/time proximity fallback used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Labels/outcomes entered assignment logic: no.
- Split/OOS or cost/slippage claim made: no.
- Deployment-ready claim made: no.

The result remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`; strategy remains `NOT_ACCEPTED`; real capital remains `FORBIDDEN`.

## 7. No-Background Decision-Maker Report

The operating system is now understandable enough to use: start from `docs/active/`, check `PROJECT_STATUS`, follow `CODEX_READ_SCOPE`, and update `tasks/active_task_registry.csv` plus the task report/manifest before closing work.

The cleanup did remove disposable generated files, but it did not remove historical evidence that still has references. That is the right tradeoff for this project.

The main remaining work is not more blind deletion. It is dependency-aware archive migration and owner review of the seven `NEEDS_REVIEW` delete candidates.

## 8. Validation

Commands run:

| Command | Result |
|---|---|
| `python scripts/active_task_registry_validate.py` | `[ACTIVE_REGISTRY_OK] tasks\active_task_registry.csv` |
| `python scripts/task_registry_validate.py` | `[REGISTRY_OK] tasks\task_registry.csv` |
| `python scripts/operating_closeout_validate.py` | `[OPERATING_CLOSEOUT_OK]` |
| `python scripts/governance_completion_audit.py` | `[GOVERNANCE_COMPLETE]` |
| `python scripts/codeowners_coverage_validate.py` | `[CODEOWNERS_OK] .github\CODEOWNERS` |
| `python validate_readiness_registry.py` | `[READINESS_REGISTRY_OK] docs\ownership\readiness_registry.yaml` |

CSV parse checks:

| File | Parsed rows |
|---|---:|
| `management_system_audit_matrix.csv` | 14 |
| `artifact_manifest.csv` | 10 |
| `tasks/active_task_registry.csv` | 4 |

CodeRabbit:

- CLI installed in WSL at `/home/minjo1009/.local/bin/coderabbit`.
- Review did not complete because agent browser authentication timed out.
- Therefore CodeRabbit raised no reviewable issues in this run because no authenticated review completed.

## 9. Next Task Recommendation

- A005: dependency-aware archive migration plan for the 10 `SKIPPED_REFERENCE_REQUIRED` archive candidates.
- A006: owner review of the seven `NEEDS_REVIEW` delete candidates.
- A007: active SSOT compression for frontend/backend/governance pointers.

## 10. Artifact Manifest

See `docs/reports/A004_project_management_system_audit/artifact_manifest.csv`.
