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

## Next Recommended Tasks

| Task | Purpose | Required approval |
|---|---|---|
| A006 | Safe generated-cache delete pass from A005 `DELETE_SAFE` candidates | Approval of DELETE_SAFE-only deletion log |
| A007 | Dependency-aware archive migration plan for large reports and stale discovery output | Approval of reference update plan |
| A008 | Owner review matrix for data artifacts, duplicate catalogs, downloads, logs, tmp, and unknown context files | Owner approval for each class-level or path-level decision |
| A009 | Frontend catalog consumer dependency review | Frontend owner confirmation before deleting duplicate-looking catalog output |

## Current Blocker

Archive relocation is blocked until referenced candidates have a dependency-aware migration plan. A005 also found 1262 `NEEDS_REVIEW` files and 2147 archive-review files; only the 853 generated-cache files are suitable for a DELETE_SAFE pass.
