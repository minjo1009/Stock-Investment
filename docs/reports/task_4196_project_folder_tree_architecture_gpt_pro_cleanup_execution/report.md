# TASK-4196 Project Folder Tree Architecture GPT Pro Cleanup Execution

## Goal

Define a durable root/folder-tree architecture, consult GPT Pro, execute safe cleanup now, and leave validators/policies that prevent the same clutter from returning.

## Results

Completed, with GPT consult caveat recorded.

- Sent the local root inventory and cleanup problem statement to GPT Pro in the `Structure Cleanup Review` ChatGPT thread.
- Captured the stalled GPT response and an ASCII follow-up attempt as evidence instead of pretending the external review completed.
- Used the usable GPT decision plus local evidence: `frontend/` and `tasks/` are active legacy migration surfaces, not immediate whole-folder delete targets.
- Deleted five untracked generated dependency/build folders:
  - `apps/ios-trader-brain/node_modules`
  - `apps/ios-trader-brain/dist`
  - `apps/ios-trader-brain/.expo`
  - `frontend/trader-terminal/node_modules`
  - `frontend/trader-terminal/dist`
- Preserved `frontend/trader-terminal/public` because it contains catalog/public artifacts that need the frontend migration task, not blind deletion.
- Hardened `scripts/ops/validate_internal_cleanliness.py` so those generated folders fail closeout if they return.
- Updated `.gitignore`, `ops/project_structure_policy.yaml`, and `ops/project_knowledge_surfaces.yaml` to treat generated dependency/build output as non-source.

## Final Folder Tree Decision

Level 0 stays intentionally small:

- Source/runtime code: `src`, `scripts`, `tools/db`, `apps`
- Governance: `ops`, `schemas`, `docs`
- Protected evidence/artifacts: `data`
- Tests: `tests`
- Local-only state: `.codex`, `.dvc`, `.obsidian`, `logs`, local env/token files
- Legacy-active migration surfaces: `frontend`, `tasks`
- Owner-review blocked known debt: `trading.db`, `trading-DESKTOP-2R00TB4.db`

`frontend/` and `tasks/` are not cleaned by deletion in this pass because active references remain. The next cleanup has to be a migration task with shims/reference updates, then archive/delete.

## Hard State

Strategy: NOT_ACCEPTED

Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

Real Capital: FORBIDDEN

No broker mutation, no live order, no paper promotion.
