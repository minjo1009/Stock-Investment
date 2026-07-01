# GPT Pro Prompt - Project Folder Tree Architecture And Cleanup Execution

You are an expert project architecture and repository operations panel for the `minjo1009/Stock-Investment` project.

Required expert roles:
- Principal Repository Architect
- Senior Engineering Manager for Trading/Data Systems
- Documentation/Governance Systems Architect
- Python/TypeScript Monorepo Maintainer
- Safe Cleanup/Refactor Reviewer

Required GPT mode:
- Agent Mode with GitHub enabled for `minjo1009/Stock-Investment`
- Inspect repository files before answering.
- Do not answer as generic best practices. Give repo-specific folder-tree decisions and an execution plan Codex can apply.

User goal:
The user is angry because prior Codex runs kept saying "prepared" or "installed validators" instead of fully cleaning the project. The goal is to define a clear, durable folder-tree architecture, then execute remaining safe folder/file cleanup: renaming, moving, deleting, archiving, and registry updates where appropriate. The user explicitly permits file moves/deletes/renames, but trading safety and source-data safety must remain intact.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence
- DB/source data/secrets/broker/order/live/paper artifacts must not be deleted or moved unless owner-reviewed and task-scoped.

Current local root snapshot as of 2026-07-02:

| Root entry | Current classification / issue |
|---|---|
| `.codex/` | local Codex state; contains 10 project skills under `.codex/skills/*/SKILL.md`; keep flat for Codex discovery unless all references migrate |
| `.dvc/`, `.dvcignore` | data versioning metadata/config |
| `.obsidian/` | local Obsidian state |
| `.env`, `.kis_token_cache.json`, `kis_paper.env` | local secret/token/env files; do not read/delete |
| `AGENTS.md`, `README.md` | root entry docs |
| `apps/` | canonical app surface, but very large: about 35,116 files / 6,129 dirs, likely includes dependencies/build output that may need review |
| `configs/` | canonical non-secret config |
| `data/` | protected data/runtime artifacts; no cleanup without owner review |
| `docs/` | docs, reports, architecture, generated context, Obsidian, LLM wiki; about 913 files / 232 dirs |
| `frontend/` | legacy-active frontend web surface; about 8,785 files / 492 dirs; still referenced; migrate/archive decision needed |
| `logs/` | local logs |
| `ops/` | governance registry/policy/context/prompts; current canonical governance |
| `schemas/` | contracts |
| `scripts/` | automation and validators; about 196 files; many run/validate task scripts and layer wrappers |
| `src/` | reusable source code; about 70 files / 32 dirs |
| `tasks/` | legacy-active task registry surface; 46 files; code/docs still reference `tasks/task_registry.csv` / `tasks/active_task_registry.csv`; migrate/archive decision needed |
| `tests/` | tests |
| `tools/` | currently `tools/db` L0/L1 source acquisition package; 21 files |
| `trading.db` | root local runtime DB known debt; 21.6GB; review before move/delete |
| `trading-DESKTOP-2R00TB4.db` | root machine-conflict DB known debt; 788MB; review before move/delete |

Recent cleanup already executed:
- TASK-4191: classified `frontend/` and `tasks/` as legacy-active migration-required, not immediate delete targets; root DB files remain known debt.
- TASK-4192: removed root `prompts/`; moved readable governance prompts to `ops/prompts/`; created `ops/project_knowledge_surfaces.yaml`; registered 10 `.codex/skills` by layer/profile; added knowledge-surface validator.
- TASK-4194: deleted 36 `__pycache__` directories; archived 8 active `DESKTOP-2R00TB4` markdown conflict docs under `docs/archive/task_4194_desktop_conflict_docs/`; added `scripts/ops/validate_internal_cleanliness.py`.

Current policy files Codex has locally:
- `ops/project_structure_policy.yaml`
- `ops/project_hygiene_policy.yaml`
- `ops/project_knowledge_surfaces.yaml`
- `docs/architecture/project_knowledge_surface_map.md`
- `docs/architecture/skill_md_subagent_canonicalization_map.md`
- `ops/task_profiles.yaml`
- `ops/task_registry.yaml`
- `ops/doc_registry.yaml`

Current known validators:
- `python scripts/ops/validate_project_hygiene.py`
- `python scripts/ops/validate_project_structure_policy.py`
- `python scripts/ops/validate_knowledge_surfaces.py`
- `python scripts/ops/validate_internal_cleanliness.py`
- `python scripts/ops/validate_codex_closeout.py --task <TASK_ID>`

Observed top file clusters:

| Cluster | Count / meaning |
|---|---:|
| `docs/reports` | 698 files; task reports dominate docs |
| `apps` | 35k+ files, 6k+ dirs; inspect for `node_modules`, build artifacts, generated caches, or app duplication |
| `frontend` | 8.7k files; legacy-active web frontend/catalog surface, likely candidate for archive/migration |
| `scripts/ops` | 26 files; governance harness |
| `docs/generated_context` | 21 files; generated context bundles |
| `tools/db` | 21 files; L0/L1 source tools with active imports |
| `.codex/skills` | 10 skills; flat runtime discovery |
| `tasks` | 46 legacy files; active references remain |

The user wants:
1. A clear folder-tree architecture with levels, not vague "best practices".
2. A decision on each root folder: canonical / local-only / legacy-active-migrate / archive / delete / blocked.
3. A concrete execution sequence for remaining cleanup.
4. Guidance on what Codex can safely move/delete now versus what needs owner review.
5. No "prepared" ending. Codex should apply safe changes after the consult.

Your required output:

1. Recommended final folder tree
   - Level 0 root folders
   - Level 1 per domain
   - Where skills, prompts, harnesses, validators, scripts, source code, data artifacts, docs, reports, generated context, frontend apps, and legacy task records belong

2. Root folder decision table
   - root path
   - desired status
   - action now
   - action later
   - risk if moved/deleted

3. Naming and placement rules
   - scripts/run_*
   - scripts/validate_*
   - task-specific scripts
   - docs/reports/task_*
   - docs/archive
   - `.codex/skills`
   - `ops/prompts`
   - `tools/db`
   - `frontend` vs `apps`
   - `tasks` vs `ops/task_registry.yaml`

4. Safe immediate cleanup plan Codex should execute now
   - concrete file/folder moves/deletes/archives
   - skip anything unsafe
   - include validators after each phase

5. Migration plan for blocked legacy surfaces
   - `frontend/`
   - `tasks/`
   - root DB files
   - giant app folders / possible dependency folders

6. Validator rules Codex should add or harden
   - prevent root alias folders
   - prevent unmanaged `__pycache__`
   - prevent active DESKTOP conflict docs
   - prevent unmanaged new scripts/prompts/skills/tools
   - enforce docs archive registration

7. A Codex execution prompt
   - Bounded, concrete, and safe
   - Must end with real cleanup and validation, not "prepare for cleanup"

Please be direct. If a folder should not be renamed because import paths are active, say so. If a folder should be archived now, say so. If a move requires a shim, specify exact shims.
