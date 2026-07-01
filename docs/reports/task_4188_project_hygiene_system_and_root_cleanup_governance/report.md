# TASK-4188 Project Hygiene System and Root Cleanup Governance

## Goal

Make project cleanup continuous instead of episodic. The task adds a root hygiene policy, a validator, and a closeout hook so future work cannot quietly add new unclassified files or folders to the repository root.

## What Changed

- Added `ops/project_hygiene_policy.yaml`.
- Added `scripts/ops/validate_project_hygiene.py`.
- Added the hygiene validator to `scripts/ops/validate_codex_closeout.py`.
- Added `TASK-4188` generated context with a small hygiene-focused bundle.
- Captured `root_hygiene_inventory.csv` for the current root classification baseline.

## Current Root Classification

The current root has 28 entries and all are classified by policy. The validator currently passes with warnings.

Known debt entries:

- `.pytest_cache`
- `config`
- `frontend`
- `tasks`
- `trading-DESKTOP-2R00TB4.db`
- `trading.db`

Sensitive local entries:

- `.env`
- `.kis_token_cache.json`

These were not moved, deleted, or read. They are now explicit cleanup targets rather than invisible clutter.

## Sustainability Mechanism

`validate_project_hygiene.py` is now part of the standard Codex closeout validator. That means future tasks can still proceed with the current known debt, but a new root-level file or folder must be classified in `ops/project_hygiene_policy.yaml` or the closeout gate fails.

## Not Done

No DB, token cache, source artifact, broker, scheduler, trading logic, paper order, live order, or data artifact was moved or deleted. The worktree already contains large unrelated changes, so physical cleanup should be done as a separate burn-down task with explicit path scope.

## Next Recommended Cleanup Task

Create a root-debt burn-down task using the baseline in `root_hygiene_inventory.csv`. The next task should reduce the six known debt entries or intentionally reclassify them after owner review, then run:

```powershell
python scripts/ops/validate_project_hygiene.py --strict-known-debt
```
