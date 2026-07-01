# Validation Results - TASK-4106

| Command | Result | Notes |
|---|---|---|
| python scripts/ops/scan_obsolete_materials.py | PASS | After safe deletion: 0 safe-delete candidates, 8 review-needed candidates |
| python scripts/ops/scan_obsolete_materials.py --delete-safe | PASS | Deleted 9 safe candidates, 1,767,606 bytes |
| python scripts/ops/scan_obsolete_materials.py --delete-review-needed | PASS | Deleted 8 OneDrive conflict DB/env/token candidates, 320,148,240 bytes |
| python scripts/ops/scan_obsolete_materials.py | PASS | Final scan: 0 safe-delete candidates, 0 review-needed candidates |
| python scripts/ops/validate_task_registry.py | PASS | 7 tasks, TASK-4106 registered |
| python scripts/ops/validate_doc_registry.py --soft | PASS_WITH_WARNINGS | Unregistered markdown reduced to 1578; historical docs still pending |
| python scripts/ops/validate_task_scope.py --task TASK-4106 | PASS_WITH_WARNINGS | Existing dirty worktree outside TASK-4106 manifest ignored |
| python scripts/ops/validate_required_artifacts.py --task TASK-4106 | PASS | 6 required artifacts exist |
| python scripts/ops/validate_codex_closeout.py --task TASK-4106 | PASS_WITH_WARNINGS | Closeout passes with inherited doc soft-mode and dirty-worktree warnings |
| `$files = Get-ChildItem scripts\ops\*.py; python -m py_compile @files` | PASS | Windows-expanded equivalent of `python -m py_compile scripts/ops/*.py` |
