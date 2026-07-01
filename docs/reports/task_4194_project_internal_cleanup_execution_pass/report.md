# TASK-4194 Project Internal Cleanup Execution Pass

## Goal

Actually remove safe internal clutter from managed project folders and stop it from returning unnoticed.

## Executed Cleanup

- Deleted 36 `__pycache__` directories from managed roots.
- Archived 8 active `DESKTOP-2R00TB4` markdown conflict files into `docs/archive/task_4194_desktop_conflict_docs/`.
- Added `scripts/ops/validate_internal_cleanliness.py`.
- Updated standard closeout so Python child validators run with `PYTHONDONTWRITEBYTECODE=1`.
- Wired internal cleanliness validation into project structure policy and closeout.

## Archived Conflict Docs

The conflict docs were not identical to their canonical counterparts, so they were not deleted. They were moved out of active doc locations into the task archive.

## Still Blocked

- `trading-DESKTOP-2R00TB4.db` remains in root because DB files require runtime-owner review before move/delete.
- `trading.db` also remains root known-debt for the same reason.
- `frontend/` and `tasks/` remain legacy-active migration surfaces from TASK-4191, not safe delete targets.

## Safety

No broker mutation, live order, paper promotion, strategy acceptance, deployment readiness, source data mutation, or DB mutation occurred.
