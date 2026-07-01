# Validation Results - TASK-4188

| Command | Result | Notes |
|---|---|---|
| `python -m py_compile scripts/ops/validate_project_hygiene.py scripts/ops/validate_codex_closeout.py` | PASS | Syntax check passed. |
| `python scripts/ops/validate_project_hygiene.py` | PASS_WITH_WARNINGS | All 28 root entries classified. Warns on known debt and sensitive local root entries. |
| `python scripts/ops/validate_task_registry.py` | PASS | 88 tasks, required fields valid. |
| `python scripts/ops/validate_doc_registry.py --soft` | PASS | 841 registered documents, no duplicate paths. |
| `python scripts/ops/validate_context_bundle.py --task TASK-4188` | PASS | Token count 6329/22000, 8 included files. |
| `python scripts/ops/validate_prime_task_contracts.py --task TASK-4188` | PASS | Prime task contract valid. |
| `python scripts/ops/validate_task_scope.py --task TASK-4188` | PASS_WITH_WARNINGS | 13 manifest-scoped files checked; 783 unrelated dirty worktree files ignored by scope gate. |
| `python scripts/ops/validate_required_artifacts.py --task TASK-4188` | PASS | 11 required artifacts exist; manifest has 13 rows. |
| `python scripts/ops/validate_codex_closeout.py --task TASK-4188` | PASS_WITH_WARNINGS | Closeout passed; warnings are project hygiene known debt and unrelated dirty worktree. |

## Warning Baseline

- Known root debt: `.pytest_cache`, `config`, `frontend`, `tasks`, `trading-DESKTOP-2R00TB4.db`, `trading.db`.
- Sensitive local do-not-read entries: `.env`, `.kis_token_cache.json`.
- Existing unrelated dirty worktree files seen by git status: 783.
