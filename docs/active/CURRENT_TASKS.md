# Current Tasks

## Active

| Active ID | Title | Status | Owner | Reviewer | Report |
|---|---|---|---|---|---|
| A002 | Safe Archive Pass | blocked_reference_required | Research Governance | Governance Reviewer | `docs/reports/A002_A003_safe_archive_delete_pass/safe_archive_delete_report.md` |

## Completed

| Active ID | Title | Status | Owner | Reviewer | Report |
|---|---|---|---|---|---|
| A001 | Project Management Reset | completed | Research Governance | Governance Reviewer | `docs/reports/A001_project_management_reset/project_management_reset_report.md` |
| A003 | Safe Delete Pass | completed | Research Governance | Governance Reviewer | `docs/reports/A002_A003_safe_archive_delete_pass/safe_archive_delete_report.md` |
| A004 | Project Management System Audit | completed | Research Governance | Governance Reviewer | `docs/reports/A004_project_management_system_audit/management_system_audit_report.md` |
| A005 | Full File Inventory Audit | completed | Research Governance | Governance Reviewer | `docs/reports/A005_full_file_inventory_audit/full_file_inventory_audit_report.md` |
| A006 | Generated Cache Delete Pass | completed | Research Governance | Governance Reviewer | `docs/reports/A006_generated_cache_delete_pass/generated_cache_delete_report.md` |
| A007 | DVC/LFS Artifact Management | completed | Research Governance | Data & Governance Reviewers | `docs/reports/A007_dvc_lfs_artifact_management/dvc_lfs_artifact_management_report.md` |
| A008 | Path-By-Path Owner Review | completed | Research Governance | Data/Frontend/Governance Reviewers | `docs/reports/A008_path_by_path_owner_review/path_by_path_owner_review_report.md` |
| A010 | Artifact Guardrails | completed | Research Governance | Governance Reviewer | `docs/reports/A010_artifact_guardrails/artifact_guardrails_report.md` |

## Next Recommended Tasks

| Task | Purpose | Required approval |
|---|---|---|
| A011 | Configure DVC remote and verify restore on a clean checkout | DVC remote location/credential decision |
| A012 | Recover or explicitly retire missing A005 `참고 Context/**` external reference paths | Owner decision only if those references are still needed |
| A013 | Optional Git LFS installation for future binary artifacts | Tooling decision if large binary artifacts become active |

## Current Blocker

Large payloads now have DVC metadata and artifact guardrails. The current blocker is DVC remote configuration; without a remote, another checkout cannot restore DVC-managed payloads from Git alone. A005's `참고 Context/**` paths were missing at A008 execution and are recorded as missing-source disclosures, not successful deletions.
