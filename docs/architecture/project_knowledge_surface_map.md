# Project Knowledge Surface Map

This is the current source-of-truth map for where project operating knowledge belongs.

The machine-readable registry is `ops/project_knowledge_surfaces.yaml`.

## Canonical Surfaces

| Surface | Canonical Location | Rule |
|---|---|---|
| Governance prompts | `ops/prompts/` | Do not recreate root `prompts/`. |
| Runnable project skills | `.codex/skills/<skill>/SKILL.md` | Keep flat for Codex discovery; classify by registry instead of nesting. |
| Governance harness | `scripts/ops/` | Closeout, registry, context, and project validators live here. |
| Layer harness | `scripts/run_l*`, `scripts/validate_l*` | Layer wrappers stay named by layer and work type. |
| L0/L1 source tools | `tools/db/` | Do not rename while `tools.db` imports are active. |
| Reusable code | `src/` | Library code lives here, not in scripts. |
| Apps | `apps/` | User-facing app surfaces live here. |
| Contracts | `schemas/` | Machine-readable contracts live here. |
| Human docs | `docs/` | Architecture, ownership, SSOTs, reports, generated context, Obsidian, and LLM wiki live here. |
| Artifacts | `data/` | Data/runtime artifacts are not cleanup targets without owner review. |

## Current Decision

- Root `prompts/` was removed as a legacy alias.
- `ops/prompts/task-create.md` and `ops/prompts/phase-create.md` are the canonical operating prompts.
- `.codex/skills` remains physically flat because Codex discovery and context bundles reference those paths.
- Skill grouping is enforced through `ops/project_knowledge_surfaces.yaml`, not by moving skill folders.
- `tools/db` remains in place because many active scripts import `tools.db.*`.

## Required Validator

Run:

```powershell
python scripts/ops/validate_knowledge_surfaces.py
```

The standard closeout gate also runs this validator.
