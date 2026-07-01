# TASK-4109 Doc Registry Closure and Obsolete Doc Cleanup

## Goal

Close the remaining `docs/**/*.md` registry gap after TASK-4108 without
weakening project safety boundaries.

## Results

- Added `scripts/ops/scan_unregistered_docs.py`.
- Scanned remaining unregistered markdown documents.
- Deleted 3 machine conflict duplicate docs with canonical counterparts present.
- Added 251 retained documents to `ops/doc_registry.yaml`.
- Reduced doc registry validation from warning state to strict pass.

## Classification Summary

| Action | Count |
|---|---:|
| DELETE_CONFLICT_DUPLICATE | 3 |
| REGISTER_ACTIVE_DOC | 109 |
| REGISTER_ACTIVE_TASK_ARTIFACT | 3 |
| REGISTER_ARCHIVED | 1 |
| REGISTER_HISTORICAL_REFERENCE | 17 |
| REGISTER_HISTORICAL_TASK_REPORT | 97 |
| REGISTER_LOCAL_REFERENCE_DOC | 7 |
| REGISTER_REFERENCE_DOC | 17 |

## Deleted Obsolete Docs

- `docs/obsidian/README-DESKTOP-2R00TB4.md`
- `docs/operating_system/subagent_handoff_template-DESKTOP-2R00TB4.md`
- `docs/ownership/subagent_packet_standard-DESKTOP-2R00TB4.md`

Each deletion required a canonical counterpart to exist.

## Registry Policy

Retained documents were registered with limited Codex read scope:

- current operating or domain docs: `TASK_PROFILE_ONLY`
- historical task reports and audits: `ONLY_IF_REFERENCED`
- Obsidian cockpit notes: `ONLY_IF_REFERENCED`
- archive material: `NEVER`

## Hard Boundaries Preserved

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation was added.
- No live order path was added.
- No paper promotion was added.
- No trading logic, scheduler, DB schema, broker, or order code was changed.

## Known Limitations

- The repo still has a large unrelated dirty worktree from pre-existing work.
- TASK-4109 scope validation uses this task artifact manifest as the hard gate.
- Remaining cleanup outside markdown docs, especially large data artifacts, is not complete.

## Next Work

1. Classify and clean obsolete `data/artifacts` L0 outputs with a manifest-backed retention gate.
2. Add a strict stale-artifact scanner for L0 smoke/backfill outputs.
