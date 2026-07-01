# Validation Results - TASK-4109

| Command | Result | Notes |
|---|---|---|
| python scripts/ops/scan_unregistered_docs.py | PASS | initial dry-run found 254 unregistered markdown docs; 3 delete candidates |
| python scripts/ops/scan_unregistered_docs.py --apply | PASS | deleted 3 conflict duplicates; added 251 registry entries |
| python scripts/ops/validate_doc_registry.py --soft | PASS | document registry warning cleared |
| python scripts/ops/validate_doc_registry.py --strict | PASS | 312 registered documents; no duplicate paths |
| python scripts/ops/render_ops_dashboard.py | PASS | refreshed static dashboard and summary |
| python -m compileall -q scripts/ops | PASS | PowerShell wildcard py_compile form was invalid; compileall used instead |
| python scripts/ops/validate_task_registry.py | PASS | 10 tasks; profiles resolved |
| python scripts/ops/validate_task_scope.py --task TASK-4109 | PASS_WITH_WARNINGS | task manifest scope clean; unrelated dirty worktree remains |
| python scripts/ops/validate_required_artifacts.py --task TASK-4109 | PASS | required report, manifest, validation files exist |
| python scripts/ops/validate_codex_closeout.py --task TASK-4109 | PASS_WITH_WARNINGS | closeout fields true; warning only from dirty worktree scope gate |
| python scripts/ops/scan_unregistered_docs.py --inventory docs/reports/task_4109_doc_registry_closure_and_obsolete_doc_cleanup/post_apply_unregistered_docs_inventory.csv | PASS | post-apply scan found 0 unregistered markdown docs |
| Remove scripts/ops/__pycache__ | PASS | validation bytecode cache removed |
