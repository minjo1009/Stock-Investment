# TASK-4161 Dirty Worktree Triage

## Conclusion

The dirty worktree is not a single cleanup problem. It is a mix of recent active task outputs, historical deletion markers, DVC pointer deletions, and local runtime artifacts. This task performs classification only and does not delete or restore files automatically. It also updates `.gitignore` for local Codex state and runtime diagnostics so future status noise is lower.

## Summary

| Metric | Count |
|---|---:|
| Total dirty rows | 1051 |
| Git status ` D` | 298 |
| Git status ` M` | 29 |
| Git status `??` | 118 |
| Git status `A ` | 584 |
| Git status `AM` | 3 |
| Git status `M ` | 19 |

## Recommended handling

| Priority | Handling |
|---|---|
| P0 | Keep/register recent TASK-4100+ outputs and review deleted DVC/L2/L3 files before any restore/delete decision. |
| P1 | Review historical report/data artifact deletions against doc registry and retention policy. |
| P2 | Ignore or register local-only files such as `.codex/`, zip archives, and runtime diagnostics. |

## Files produced

- `dirty_worktree_inventory.csv`
- `dirty_worktree_p0_queue.csv`
- `dirty_worktree_review_required.csv`
- `dirty_worktree_keep_register.csv`
- `dirty_worktree_local_ignore_candidates.csv`
- `dirty_worktree_summary.csv`
- `dirty_worktree_summary.json`
