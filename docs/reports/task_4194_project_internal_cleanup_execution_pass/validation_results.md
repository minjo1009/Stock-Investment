# Validation Results - TASK-4194

| Command | Result | Notes |
|---|---|---|
| `python scripts/ops/validate_internal_cleanliness.py` | PASS_WITH_WARNINGS | No caches, no root aliases, no active DESKTOP docs; root machine-conflict DB remains owner-review blocked. |
| `python scripts/ops/validate_project_structure_policy.py` | PASS | Internal cleanliness validator declared and wired into closeout. |
| `python scripts/ops/validate_knowledge_surfaces.py` | PASS | Knowledge-surface registry still valid. |
| `python scripts/ops/validate_project_hygiene.py` | PASS_WITH_WARNINGS | Remaining known-debt is root DB files; sensitive local files are do-not-read. |
| `python scripts/ops/validate_task_registry.py` | PASS | 95 tasks; profiles and required fields resolved. |
| `python scripts/ops/validate_doc_registry.py --soft` | PASS | 917 documents; required fields present; no duplicate paths. |
| `python scripts/ops/validate_prime_task_contracts.py --task TASK-4194` | PASS | Prime contract valid. |
| `python scripts/ops/validate_required_artifacts.py --task TASK-4194` | PASS | 17 required artifacts exist; manifest rows present. |
| `python scripts/ops/validate_task_scope.py --task TASK-4194` | PASS_WITH_WARNINGS | Forbidden paths clean; unrelated dirty worktree files ignored by scope gate. |
| `python scripts/ops/validate_codex_closeout.py --task TASK-4194` | PASS_WITH_WARNINGS | Closeout passed; warnings are root DB known-debt, owner-review DB blocker, and unrelated dirty worktree. |
| Final filesystem check | PASS | No `__pycache__` directories in managed roots; `prompts/`, `skills/`, `config/`, and `.pytest_cache` absent; DESKTOP docs only under archive plus blocked root DB. |
