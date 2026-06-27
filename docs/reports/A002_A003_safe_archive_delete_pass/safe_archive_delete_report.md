# A002-A003 Safe Archive and Delete Pass Report

## 1. Decision Summary

- A002 archive relocation moved 0 paths.
- A002 blocked 10 archive candidates because every A001 archive row had `reference_required=TRUE` and reference search found registry, artifact migration, script, or historical report references.
- A003 deleted only 3 `DELETE_SAFE` generated cache/marker candidate paths:
  - `.pytest_cache`
  - `__pycache__`
  - `graphify-out/needs_update`
- A003 skipped all 7 `NEEDS_REVIEW` delete candidates.
- Validation recreated root `__pycache__`; it was removed again and recorded as a fourth deletion operation.
- Current status boundaries remain unchanged:
  - Strategy acceptance: `NOT_ACCEPTED`
  - Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
  - Real capital: `FORBIDDEN`

No trading behavior, strategy acceptance, deployment readiness, broker mutation logic, order-generation logic, backtest result, raw source data, DB file, validator, canonical report, or canonical task registry file was changed.

## Goal Intake Contract

| Field | A002-A003 Contract |
|---|---|
| Objective | Execute A002 safe archive review and A003 safe delete pass from A001 manifests without breaking references or deleting evidence. |
| Target Metrics | Archive relocation log exists; deletion log exists; only `DELETE_SAFE` items removed; `NEEDS_REVIEW` items preserved; validators run. |
| Forbidden Actions | No trading/deployment/broker mutation; no order generation changes; no backtest changes; no raw/DB/validator/canonical report deletion; no blind archive moves. |
| Available Raw Sources | Not applicable. Cleanup used A001 manifests and repository references. |
| Missing Raw Sources | Not applicable. Existing readiness blockers remain unchanged. |
| Owner Team | Research Governance. |
| Reviewer Team | Governance Reviewer. |
| Output Directory | `docs/reports/A002_A003_safe_archive_delete_pass/` |
| Artifact Locations | A002/A003 report, archive relocation log, deletion log, skipped delete log, artifact manifest. |
| Validation Commands | Closeout validators and CSV parse checks. |
| Completion Criteria | Logs exist; safe deletes complete; unsafe moves/deletes skipped; validation recorded. |
| Failure Criteria | Any non-DELETE_SAFE deletion; broken status boundary; unlogged move/delete; skipped validation. |

## 2. A002 Archive Relocation

Archive candidates reviewed: 10.

Physical moves performed: 0.

Reason: all 10 A001 archive candidates were marked `reference_required=TRUE`. Reference search found direct references in one or more of:

- `tasks/archive_candidate_registry.csv`
- `docs/artifact_migration_plan.csv`
- `tasks/task_registry.csv`
- `docs/INDEX.md`
- `docs/reports/task_obsidian_vault_application/`
- daily feedback reports
- `scripts/operating_closeout_validate.py`
- historical reports

Moving these paths without a dependency-aware migration would create stale references and weaken auditability. The safe A002 output is therefore `archive_relocation_log.csv`, with every candidate marked `SKIPPED_REFERENCE_REQUIRED`.

## 3. A003 Safe Delete Pass

Deleted candidate paths: 3.

Deletion operations logged: 4.

| Path | Result |
|---|---|
| `.pytest_cache` | deleted |
| `__pycache__` | deleted |
| `graphify-out/needs_update` | deleted |
| `__pycache__` post-validation recreation | deleted again |

Skipped candidates: 7.

All skipped rows were `NEEDS_REVIEW` in A001 and remain in place.

## 4. Logs

- Archive relocation log: `docs/reports/A002_A003_safe_archive_delete_pass/archive_relocation_log.csv`
- Deletion log: `docs/reports/A002_A003_safe_archive_delete_pass/deletion_log.csv`
- Skipped delete candidates: `docs/reports/A002_A003_safe_archive_delete_pass/skipped_delete_candidates.csv`
- Artifact manifest: `docs/reports/A002_A003_safe_archive_delete_pass/artifact_manifest.csv`

## 5. Quant Expert Report

A002-A003 made no strategy claim.

- Inferred lifecycle matching used: no.
- Symbol/date/price/time proximity fallback used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Labels/outcomes entered assignment logic: no.
- Split/OOS or cost/slippage claim made: no.
- Deployment-ready claim made: no.

The result remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`; strategy remains `NOT_ACCEPTED`; real capital remains `FORBIDDEN`.

## 6. No-Background Decision-Maker Report

The cleanup advanced safely.

Generated cache files were removed. Historical reports and navigation folders were not moved because they still have live references in registries, migration plans, scripts, or reports. This means the project is cleaner, but not brittle: evidence and references still line up.

## 7. Validation

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
| `archive_relocation_log.csv` | 10 |
| `deletion_log.csv` | 4 |
| `skipped_delete_candidates.csv` | 7 |
| `artifact_manifest.csv` | 8 |
| `tasks/active_task_registry.csv` | 3 |

Deletion state checks:

| Path | Result |
|---|---|
| `.pytest_cache` | missing after delete |
| `__pycache__` | missing after delete |
| `graphify-out/needs_update` | missing after delete |
| 7 `NEEDS_REVIEW` candidates | still present |

## 8. Known Limitations

- `git` was not available in the shell PATH, so git status/diff could not be used.
- A002 did not physically move archive candidates because reference updates require a separate dependency-aware migration plan.
- A003 did not delete any `NEEDS_REVIEW` candidate.

## 9. Next Task Recommendation

- A004: dependency-aware archive migration plan for the 10 `SKIPPED_REFERENCE_REQUIRED` archive candidates.
- A005: owner review of the 7 skipped delete candidates.
- A006: optional Graphify regeneration after archive/reference policy is settled.

## 10. Artifact Manifest

See `docs/reports/A002_A003_safe_archive_delete_pass/artifact_manifest.csv`.
