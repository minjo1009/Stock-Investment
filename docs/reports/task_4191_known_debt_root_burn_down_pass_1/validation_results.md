# Validation Results - TASK-4191

| Command | Result | Notes |
|---|---|---|
| `python scripts/ops/validate_project_structure_policy.py` | PASS | All root entries covered; duplicate axes declared; closeout validator wiring present. |
| `python scripts/ops/validate_project_hygiene.py` | PASS_WITH_WARNINGS | Optional `.pytest_cache` and `config/` absent; remaining known-debt warnings are `trading-DESKTOP-2R00TB4.db` and `trading.db`; sensitive local files are classified do-not-read. |
| `python scripts/ops/validate_task_registry.py` | PASS | 91 tasks; required fields and profiles resolved. |
| `python scripts/ops/validate_doc_registry.py --soft` | PASS | 879 documents; required fields present; no duplicate paths. |
| `python scripts/ops/validate_prime_task_contracts.py --task TASK-4191` | PASS | TASK-4191 prime contract valid. |
| `python scripts/ops/validate_task_scope.py --task TASK-4191` | PASS_WITH_WARNINGS | Forbidden paths clean; unrelated pre-existing dirty files ignored by scope gate. |
| `python scripts/ops/validate_required_artifacts.py --task TASK-4191` | PASS | 10 required artifacts exist; manifest rows match. |
| `python scripts/ops/validate_codex_closeout.py --task TASK-4191` | PASS_WITH_WARNINGS | Closeout gates passed; warnings are expected known-debt DB files, sensitive local files, and unrelated dirty worktree state. |
