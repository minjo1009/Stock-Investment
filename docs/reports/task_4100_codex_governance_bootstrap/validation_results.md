# Validation Results - TASK-4100

| Command | Result | Notes |
|---|---|---|
| python scripts/ops/validate_task_registry.py | PASS | 1 task, TASK-4100 present, profile resolved |
| python scripts/ops/validate_doc_registry.py --soft | PASS_WITH_WARNINGS | 1579 historical docs and legacy report folders are unregistered in this bootstrap |
| python scripts/ops/build_context_bundle.py --task TASK-4100 | PASS | Generated 4908 approximate tokens; `tiktoken` not installed |
| python scripts/ops/validate_context_bundle.py --task TASK-4100 | PASS | 4908/22000 tokens, 7 included files |
| python scripts/ops/validate_task_scope.py --task TASK-4100 | PASS_WITH_WARNINGS | Existing dirty worktree outside TASK-4100 manifest ignored; 34 scoped files checked |
| python scripts/ops/validate_required_artifacts.py --task TASK-4100 | PASS | 3 required artifacts exist; manifest has 34 rows |
| python scripts/ops/render_ops_dashboard.py | PASS | Generated `ops/dashboard/index.html` |
| python scripts/ops/validate_codex_closeout.py --task TASK-4100 | PASS_WITH_WARNINGS | Closeout gates pass; warnings inherited from doc registry soft mode and dirty worktree scope handling |
| `$files = Get-ChildItem scripts\ops\*.py; python -m py_compile @files` | PASS | Windows-expanded equivalent of `python -m py_compile scripts/ops/*.py` |
