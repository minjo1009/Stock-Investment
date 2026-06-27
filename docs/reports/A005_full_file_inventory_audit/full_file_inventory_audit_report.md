# A005 Full File Inventory Audit Report

## 1. Decision Summary

- Verdict: the project management system is clear enough to operate, but the repository still contains large evidence-bearing artifacts that must not be blindly deleted or moved.
- Scope: full repository file scan excluding only `.git`.
- Total files inventoried: 14958.
- DELETE_SAFE candidates: 853 generated cache files, about 9.2 MB.
- NEEDS_REVIEW candidates: 1262 files, dominated by derived/runtime data, possible duplicate frontend catalogs, local downloads, logs, temporary/checkpoint material, and unknown top-level reference context.
- ARCHIVE_REVIEW candidates: 2147 files, dominated by large report artifacts and historical reports.
- Protected KEEP files: 10696 files, including raw sources, DB authority files, governance files, validators, manifests, active docs, frontend public catalog files, project source/config, and canonical reports.
- What changed: A005 added a reusable full-file inventory classifier and generated auditable CSV manifests plus this report.
- What did not change: no files were deleted or moved in A005.
- Current status boundaries remain unchanged:
  - Strategy acceptance: `NOT_ACCEPTED`
  - Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
  - Real capital: `FORBIDDEN`
- Next action: run A006 for DELETE_SAFE generated cache deletion, then A007/A008 for dependency-aware archive planning and owner review.

## Goal Intake Contract

| Field | A005 Contract |
|---|---|
| Objective | Audit every project file so cleanup and future project management decisions are based on a complete manifest rather than partial guesses. |
| Target Metrics | Inventory CSV exists; class summary exists; delete-safe needs-review archive-review and protected-keep manifests exist; active registry records A005; validators pass. |
| Forbidden Actions | No trading/deployment/broker mutation; no order-generation changes; no backtest changes; no raw/DB/validator/canonical evidence deletion; no unapproved physical moves or deletes. |
| Available Raw Sources | Repository filesystem metadata and existing governance reports/manifests. |
| Missing Raw Sources | No external GPT or CodeRabbit review completed for A005; A004 already records CodeRabbit authentication as blocked. |
| Owner Team | Research Governance. |
| Reviewer Team | Governance Reviewer. |
| Output Directory | `docs/reports/A005_full_file_inventory_audit/` |
| Artifact Locations | A005 report, full inventory CSV, class summaries, candidate manifests, cleanup action plan, artifact manifest, inventory script. |
| Validation Commands | `python scripts/project_file_inventory_audit.py` plus active registry and governance closeout validators. |
| Completion Criteria | Full inventory and summaries generated; no destructive action taken; active docs/registry updated; validators pass. |
| Failure Criteria | Incomplete scan scope; unlogged deletion/move; status-boundary drift; missing report/manifest; validator failure. |

## 2. Inventory Method

The audit uses `scripts/project_file_inventory_audit.py`.

Rules:

- Exclude `.git` internals only.
- Preserve raw sources, DB authority files, secrets/local auth, validators, registries, artifact manifests, active governance docs, and canonical governance by default.
- Treat Python caches and pytest caches as `DELETE_SAFE`.
- Treat derived/runtime data, large unknown files, downloads, logs, temporary files, local tool state, and unknown context files as `NEEDS_REVIEW`.
- Treat large report artifacts, stale Graphify output, Obsidian navigation, and historical reports as archive-review material unless already active/canonical.
- Do not infer that a file is safe to delete merely because it is old, large, duplicated-looking, or outside default read scope.

## 3. Classification Summary

Largest classes by byte size:

| Class | Files | Bytes | Decision |
|---|---:|---:|---|
| `LARGE_REPORT_ARTIFACT` | 17 | 3259173733 | `ARCHIVE_REVIEW` |
| `DERIVED_OR_RUNTIME_DATA` | 46 | 2733685162 | `NEEDS_REVIEW` |
| `PROTECTED_RAW_SOURCE` | 822 | 2553725948 | `KEEP` |
| `PROJECT_SOURCE_OR_CONFIG` | 9476 | 243775014 | `KEEP` |
| `PROTECTED_DB_AUTHORITY` | 11 | 207851520 | `KEEP` |
| `HISTORICAL_REPORT` | 2119 | 195720421 | `KEEP_OR_ARCHIVE_REVIEW` |
| `UNKNOWN_NEEDS_REVIEW` | 1180 | 187054024 | `NEEDS_REVIEW` |
| `FRONTEND_PUBLIC_CATALOG` | 5 | 121163150 | `KEEP` |
| `POSSIBLE_DUPLICATE_GENERATED_CATALOG` | 5 | 121163150 | `NEEDS_REVIEW` |
| `GENERATED_CACHE` | 853 | 9238650 | `DELETE_SAFE` |

Top-level storage concentration:

| Top-level path | Files | Bytes | Decision |
|---|---:|---:|---|
| `data` | 886 | 5386834678 | Preserve raw; owner-review derived artifacts. |
| `docs` | 2428 | See `top_dir_summary.csv` | Preserve active/canonical reports; plan archive migration for large historical evidence. |
| `frontend` | 8784 | 357946041 | Keep source/config and frontend public catalog. |
| `참고 Context` | 1204 | 187535294 | Owner review before deletion or archive. |
| `frontend_data` | 5 | 121163150 | Review against frontend public catalog consumers. |
| `downloads` | 1 | 36501504 | Owner review before deletion. |

The exact current totals are in `classification_summary.csv` and `top_dir_summary.csv`.

## 4. Cleanup Diagnosis

A005 confirms that the previous cleanup posture was correct: the biggest storage opportunities are not safe blind deletes.

Safe cleanup:

- `GENERATED_CACHE`: 853 files. These are the best A006 deletion candidates.

Potential archive cleanup:

- `LARGE_REPORT_ARTIFACT`: 17 very large historical report artifacts.
- `HISTORICAL_REPORT`: 2119 historical evidence files.
- `STALE_DISCOVERY_OUTPUT`: 4 Graphify output files.
- `NAVIGATION_LAYER`: 7 Obsidian navigation files.

Potential owner-review cleanup:

- `DERIVED_OR_RUNTIME_DATA`: large data artifacts that may be reproducible but still need provenance and consumer checks.
- `POSSIBLE_DUPLICATE_GENERATED_CATALOG`: `frontend_data/catalog` appears to mirror frontend public catalog content but must be checked against consumers.
- `LOCAL_INSTALLER_OR_DOWNLOAD`: one local installer under `downloads`.
- `RUN_LOG`, `TMP_OR_CHECKPOINT`, `UNKNOWN_NEEDS_REVIEW`, and local tool state.

Do not delete:

- Raw source data.
- DB authority files.
- Secrets/local auth material.
- Validators and governance controls.
- Artifact manifests.
- Active docs and canonical governance.
- Frontend public catalog outputs used by the app.

## 5. Future Operating Control

Future cleanup and project-management work should use the A005 CSVs as the starting point:

- Deletion work starts from `delete_safe_candidates.csv`.
- Archive planning starts from `archive_review_candidates.csv`.
- Owner review starts from `needs_review_candidates.csv`.
- Protected material is checked against `protected_keep_files.csv`.

The active task registry should continue to carry one row per loop. A005 recommends:

- A006: safe generated-cache delete pass.
- A007: dependency-aware archive migration plan for large report/stale discovery/historical evidence.
- A008: owner review matrix for data artifacts, duplicate catalogs, downloads, logs, tmp, and unknown context files.
- A009: frontend catalog consumer dependency review.

## 6. Quant Expert Report

A005 made no strategy claim.

- Inferred lifecycle matching used: no.
- Symbol/date/price/time proximity fallback used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- Labels/outcomes entered assignment logic: no.
- Split/OOS or cost/slippage claim made: no.
- Deployment-ready claim made: no.

The result remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`; strategy remains `NOT_ACCEPTED`; real capital remains `FORBIDDEN`.

## 7. No-Background Decision-Maker Report

The project now has a full file inventory. The main finding is simple: there are small disposable cache files, but most of the large files are evidence, data artifacts, or frontend/runtime outputs that require owner review before cleanup.

This means the management system should not be judged by how aggressively it deletes files. It should be judged by whether each file class has a clear owner, decision rule, and validation trail. A005 creates that trail.

The next safe operational step is to delete generated caches only, then separately plan archive migration for large historical reports and review high-risk data/catalog files.

## 8. Validation

Commands run:

| Command | Result |
|---|---|
| `python scripts/project_file_inventory_audit.py` | `[FILE_INVENTORY_AUDIT] files=14958 out_dir=docs\reports\A005_full_file_inventory_audit` |
| `python scripts/active_task_registry_validate.py` | `[ACTIVE_REGISTRY_OK] tasks\active_task_registry.csv` |
| `python scripts/task_registry_validate.py` | `[REGISTRY_OK] tasks\task_registry.csv` |
| `python scripts/operating_closeout_validate.py` | `[OPERATING_CLOSEOUT_OK]` |
| `python scripts/governance_completion_audit.py` | `[GOVERNANCE_COMPLETE]` |
| `python scripts/codeowners_coverage_validate.py` | `[CODEOWNERS_OK] .github\CODEOWNERS` |
| `python validate_readiness_registry.py` | `[READINESS_REGISTRY_OK] docs\ownership\readiness_registry.yaml` |

CSV parse checks:

| File | Parsed rows |
|---|---:|
| `file_inventory.csv` | 14958 |
| `classification_summary.csv` | 25 |
| `top_dir_summary.csv` | 35 |
| `delete_safe_candidates.csv` | 853 |
| `needs_review_candidates.csv` | 1262 |
| `archive_review_candidates.csv` | 2147 |
| `protected_keep_files.csv` | 10696 |
| `cleanup_action_plan.csv` | 4 |
| `artifact_manifest.csv` | 15 |
| `tasks/active_task_registry.csv` | 5 |

## 9. Artifact Manifest

See `docs/reports/A005_full_file_inventory_audit/artifact_manifest.csv`.
