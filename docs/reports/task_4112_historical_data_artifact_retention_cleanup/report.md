# TASK-4112 Historical Data Artifact Retention Cleanup

## Goal

Delete unreferenced historical task artifacts under `data/artifacts` while
preserving artifacts referenced by current operating documents.

## Results

- Added `scripts/ops/scan_historical_data_artifacts.py`.
- Scanned current operating docs for protected `data/artifacts/...` paths and
  referenced task numbers.
- Deleted 167 unreferenced historical task artifact directories.
- Deleted 1,830 files.
- Removed 6,390,455,155 bytes.
- Post-delete scan found zero remaining delete candidates under the same rule.

## Retention Model

Protected artifacts were retained when:

- the artifact directory was explicitly referenced by current operating docs
- the task number was referenced by current operating docs
- the directory belonged to current governance cleanup task ranges

Deleted artifacts were task-scoped directories under `data/artifacts/task_*`
with no current operating document reference.

## Post-Delete State

| Action | Directories | Files | Bytes |
|---|---:|---:|---:|
| KEEP_REFERENCED_ARTIFACT | 17 | 191 | 524,279,236 |
| KEEP_REFERENCED_TASK_ARTIFACT | 114 | 1,871 | 3,566,532,310 |
| IGNORE_NON_TASK_ARTIFACT | 22 | 131 | 41,210,695 |
| DELETE_UNREFERENCED_HISTORICAL_TASK_ARTIFACT | 0 | 0 | 0 |

## Safety Boundary Check

- Broker mutation: none.
- Live order: none.
- Paper promotion: none.
- Real capital: none.
- DB schema: none.
- Scheduler code: none.
- Strategy acceptance: unchanged.

## Known Limitations

- Referenced historical artifacts remain even if large; deleting them requires a
  separate supersession or dependency migration.
- Non-task artifact directories remain outside this task scope.
- The repo still has unrelated dirty worktree state outside this task manifest.
