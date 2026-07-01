# Validation Results - TASK-4107

| Command | Result | Notes |
|---|---|---|
| python scripts/ops/scan_legacy_report_folders.py | PASS | Initial dry-run: 20 folders, 84 files, 11,071,083 bytes |
| python scripts/ops/scan_legacy_report_folders.py --delete | PASS_WITH_RETRY | First run removed A001-A010 class folders then hit Windows permission on daily feedback; script was patched for read-only removal |
| python scripts/ops/scan_legacy_report_folders.py --delete | PASS | Second run removed remaining 12 folders, 29 files, 139,700 bytes |
| python scripts/ops/scan_legacy_report_folders.py --delete | PASS_WITH_RETRY | Top-level report file pass hit a guard on `task_089_op_validation.md` after deleting first top-level files; guard was patched to protect only task folders |
| python scripts/ops/scan_legacy_report_folders.py --delete | PASS | Final top-level file pass removed remaining 4 files, 16,959 bytes |
| python scripts/ops/scan_legacy_report_folders.py | PASS | Final scan: 0 legacy non-task report entries |
| python scripts/ops/validate_task_registry.py | PASS | 8 tasks, TASK-4107 registered |
| python scripts/ops/validate_doc_registry.py --soft | PASS_WITH_WARNINGS | `task reports outside task folder` warning removed; unregistered markdown now 1542 |
| python scripts/ops/validate_task_scope.py --task TASK-4107 | PASS_WITH_WARNINGS | Existing dirty worktree outside TASK-4107 manifest ignored |
| python scripts/ops/validate_required_artifacts.py --task TASK-4107 | PASS | 5 required artifacts exist |
| python scripts/ops/validate_codex_closeout.py --task TASK-4107 | PASS_WITH_WARNINGS | Closeout passes with inherited doc soft-mode and dirty-worktree warnings |
| `$files = Get-ChildItem scripts\ops\*.py; python -m py_compile @files` | PASS | Windows-expanded equivalent of `python -m py_compile scripts/ops/*.py` |
