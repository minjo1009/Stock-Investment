# TASK-4110 L0 Artifact Retention Cleanup

## Goal

Reduce L0 artifact clutter without deleting canonical collection, status,
source-acquisition, or microstructure evidence needed for diagnostic operation.

## Results

- Added `scripts/ops/scan_l0_artifact_retention.py`.
- Scanned `data/artifacts` directory-level retention state.
- Preserved 21 canonical L0 artifact directories.
- Deleted 127 obsolete L0 smoke/probe/L2-smoke/manual retry artifact directories.
- Removed 379 files and 22,812,348 bytes.
- Left 299 non-L0 artifact directories outside this task scope.

## Retention Rules

Deleted only L0 artifact directories under `data/artifacts` when the directory
name clearly indicated throwaway validation output:

- `_smoke`
- `smoke_`
- `_probe`
- `probe_`
- `capability_probe`
- `l2_smoke`
- `token_smoke`
- `sec_live_retry_manual`

Protected canonical L0 directories included current bar/news/status/source
artifacts, microstructure artifacts, and queue/checkpoint directories.

## Validation Summary

The post-delete scan found:

| Action | Directories | Files | Bytes |
|---|---:|---:|---:|
| KEEP_CANONICAL | 21 | 129 | 41,173,796 |
| IGNORE_NON_L0 | 299 | 3,894 | 10,481,302,418 |
| DELETE_OBSOLETE_L0_ARTIFACT | 0 | 0 | 0 |

## What This Did Not Touch

- No raw source directory outside `data/artifacts`.
- No DB schema.
- No scheduler code.
- No trading logic.
- No broker, order, paper, or live trading path.
- No strategy acceptance status.

## Known Limitations

- Large non-L0 artifact directories remain and need a separate retention task.
- Canonical L0 directories were kept even when large because deletion would
  require source-readiness review, not filename-based cleanup.
- `L0_DESKTOP_CODEX_HANDOFF.md` references a full handoff report path that is
  currently missing; this needs a recovery or supersession task before claiming
  the broader L0 operating documentation is fully repaired.
