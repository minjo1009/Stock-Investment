# L0 Collection Host Migration Handoff Supersession

## Purpose

This document supersedes the missing pointer target:

`docs/reports/task_l0_collection_host_migration_handoff/l0_collection_host_migration_handoff.md`

The original full handoff report is not present in the current worktree. This
file does not reconstruct unavailable evidence. It preserves the current
operator-facing handoff facts that remain available in `L0_DESKTOP_CODEX_HANDOFF.md`
and links the cleanup reports that changed the repository state afterward.

## Current Handoff Facts

- Notebook-side collection workers were stopped at `2026-06-28T22:59Z`.
- After cleanup, no `python*` collection process remained on the notebook.
- Desktop should confirm OneDrive sync before restarting collectors.
- Desktop should not run notebook and desktop collectors at the same time.

## Current L0 Restart Checklist

1. Confirm OneDrive sync is complete.
2. Run `python scripts/report_l0_collection_status.py`.
3. Start collectors on desktop only.
4. Keep all trading gates diagnostic-only.

## Canonical L0 Artifact Retention Result

TASK-4110 retained canonical L0 collection/status/source artifacts and deleted
only smoke/probe/L2-smoke/manual retry artifacts:

- deleted directories: 127
- deleted files: 379
- deleted bytes: 22,812,348
- post-delete delete candidates: 0

Source report:

`docs/reports/task_4110_l0_artifact_retention_cleanup/report.md`

## Safety Boundaries

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation.
- No live order.
- No paper promotion.
- Missing or stale data remains `UNKNOWN/BLOCKER`.

## Limitation

The missing historical handoff report was not restored. This document is the
current repo-local supersession and should be treated as the active pointer
target until a better source artifact is recovered.
