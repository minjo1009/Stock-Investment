# Codex Read Scope

Default read scope for normal work:

1. docs/active/README_ACTIVE.md
2. docs/active/PROJECT_STATUS.md
3. docs/active/ACTIVE_SSOT_INDEX.md
4. docs/active/CURRENT_TASKS.md
5. The specific file or folder being edited

Do not read all docs/reports by default.
Do not read all docs/llm_wiki by default.
Do not read all Obsidian files by default.
Do not read archived reports unless explicitly needed.

## Domain-Specific Read Expansion

Frontend work:
- `docs/frontend_data_contract.md` or active SSOT pointer
- relevant frontend task report only if directly relevant
- `frontend/trader-terminal` only if editing app code

Backend brain work:
- active backend pointers
- relevant L0-L7 map
- specific module files

DB/scheduler work:
- active DB pointers
- relevant DB docs
- specific scripts/configs

Backtest work:
- backtest discipline doc
- relevant harness/report
- validator scripts

Cleanup work:
- retention policy
- delete candidate manifest
- archive candidate manifest
- latest full file inventory report when cleanup scope is repository-wide
- `tasks/active_task_registry.csv`
- `python scripts/active_task_registry_validate.py`
- `python scripts/project_file_inventory_audit.py`
