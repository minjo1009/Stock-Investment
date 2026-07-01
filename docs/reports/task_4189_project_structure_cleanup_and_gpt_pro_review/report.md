# TASK-4189 Project Structure Cleanup and GPT Pro Review

## Goal

Reduce root clutter safely and install a durable project structure policy so future Codex tasks cannot recreate unclassified folders, duplicate axes, or unmanaged docs surfaces.

## Results

Implemented:

- Added `ops/project_structure_policy.yaml`.
- Added `scripts/ops/validate_project_structure_policy.py`.
- Added `scripts/ops/run_task4189_project_structure_cleanup.py`.
- Added `scripts/ops/validate_task4189_project_structure_cleanup.py`.
- Wired `validate_project_structure_policy.py` into standard Codex closeout.
- Generated TASK-4189 context bundle.
- Deleted only `.pytest_cache` after resolved-path safety validation.
- Captured root, docs surface, duplicate-axis, cleanup, and GPT consult artifacts.

## Cleanup Executed

Only one physical cleanup action was executed:

| Path | Action | Status |
|---|---|---|
| `.pytest_cache` | delete transient cache | DELETED |

No DB, token cache, source data, broker, live, paper, strategy, runtime scheduler, or raw artifact path was moved or deleted.

## Current Structure Verdict

Root known debt reduced from six entries to five:

- `config`
- `frontend`
- `tasks`
- `trading-DESKTOP-2R00TB4.db`
- `trading.db`

Sensitive local do-not-read entries remain classified:

- `.env`
- `.kis_token_cache.json`

Duplicate axes requiring owner-reviewed follow-up:

- `config` vs `configs`
- `apps` vs `frontend`
- `.obsidian` vs `docs/obsidian`
- `tasks` vs `ops/task_registry.yaml`

## Durable Policy

`ops/project_structure_policy.yaml` now defines:

- target root keep/local-only/review lists
- layer/function tree for L0-L1, L2, L3-L4, UI, and OPS
- duplicate-axis decisions
- docs surface lifecycle policy
- delete/archive/local-trash rules
- closeout validators

The new structure validator confirms every current root entry and docs surface is classified.

## GPT Pro Consult

Relay mode: `single_gpt_consult`.

Prompt artifact:

- `docs/reports/task_4189_project_structure_cleanup_and_gpt_pro_review/gpt_pro_project_structure_prompt.md`

Capture status:

- `PENDING_RESPONSE`

The prompt was sent in ChatGPT Pro under the existing `Structure Cleanup Review` conversation. GPT Pro continued generating beyond the bounded wait window, so a partial body capture was saved to `gpt_pro_response_partial.txt` and the browser tab was left as handoff rather than closed.

## Not Done

No broad archive/delete pass was run. In the current dirty worktree, many files are already modified, deleted, or untracked outside this task. Physical movement of `config`, `frontend`, `tasks`, or DB files should be a separate task with explicit owner-reviewed references and rollback inventory.

## Next Cleanup Task

Target: reduce the five remaining known-debt root entries.

Recommended order:

1. Resolve `tasks` vs `ops/task_registry.yaml` by migrating any still-useful legacy task index into registered task reports, then archive/delete legacy `tasks`.
2. Resolve `config` vs `configs` by searching imports/references and making `configs` canonical.
3. Resolve `frontend` vs `apps` by cataloging whether `frontend/trader-terminal` is active or historical.
4. Decide whether local DB files should remain root-local, move to an ignored local store, or stay blocked.

Target validator for a full debt burn-down:

```powershell
python scripts/ops/validate_project_hygiene.py --strict-known-debt
```
