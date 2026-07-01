# TASK-4192 Project Knowledge Surface Canonicalization

## Goal

Make prompts, skills, harnesses, tools, and major project folders discoverable and enforceable for future Codex sessions.

## Results

- Created `ops/project_knowledge_surfaces.yaml` as the canonical registry for skills, prompts, harness groups, tools, apps, src, schemas, docs, and data.
- Added `scripts/ops/validate_knowledge_surfaces.py` and wired it into standard closeout.
- Moved the two governance prompts from root `prompts/` into `ops/prompts/`.
- Rewrote the corrupted prompt text into readable UTF-8 operating prompts.
- Removed the now-empty root `prompts/` alias.
- Removed Python cache folders under `tools/db`.
- Added `docs/architecture/project_knowledge_surface_map.md` as the human-readable map.
- Updated `docs/architecture/skill_md_subagent_canonicalization_map.md` to point to the new registry.

## Physical Movement

| From | To | Decision |
|---|---|---|
| `prompts/task-create.md` | `ops/prompts/task-create.md` | Moved and rewritten as readable governance prompt |
| `prompts/phase-create.md` | `ops/prompts/phase-create.md` | Moved and rewritten as readable governance prompt |
| `prompts/` | removed | Empty legacy root alias |
| `tools/db/**/__pycache__/` | removed | Transient Python caches |

## Kept Stable

- `.codex/skills` was not renamed or nested because Codex discovery, doc registry rows, and context bundles reference the flat skill paths.
- `tools/db` was not renamed because active code imports `tools.db.*`.
- `frontend` and `tasks` were not moved here; they remain separate migration-required surfaces from TASK-4191.

## Bottom Line

The project now has one validator-backed map for the operating knowledge surfaces. New prompts, skills, harness groups, or generic tool areas must be registered in `ops/project_knowledge_surfaces.yaml`, or closeout will fail.

## Safety

No broker mutation, live order, paper promotion, strategy acceptance, deployment readiness, source data mutation, or DB mutation occurred.
