# GPT Pro Consult Prompt - TASK-4189 Project Structure Cleanup

You are an expert panel for the `minjo1009/Stock-Investment` project.

Required expert roles:
- Principal Project Architect
- Technical Program Manager for complex research systems
- Repository Governance Engineer
- Data/ML Platform Architect
- Trading-system Safety Reviewer

Required GPT mode:
- Agent Mode with GitHub enabled for `minjo1009/Stock-Investment`
- Inspect the repository before answering.
- Do not use Deep Research unless you need current external best practices; this is primarily repo-architecture work.

User goal:
The user says the project root and repository structure are disorganized. They want a durable system for file/folder management so Codex does not keep creating scattered scripts, skills, harnesses, reports, wiki notes, Graphify outputs, Obsidian notes, task logs, and duplicate root folders. They want safe deletion or trash/archive movement where appropriate, no duplicate root axes, clear layer/function separation, and persistent governance so this stays clean without repeated manual intervention.

Current local evidence from Codex TASK-4188/TASK-4189:
- `ops/project_hygiene_policy.yaml` classifies root entries and makes new unclassified root clutter fail validation.
- `scripts/ops/validate_project_hygiene.py` is wired into `scripts/ops/validate_codex_closeout.py`.
- TASK-4189 deleted only `.pytest_cache` as safe transient cache.
- Current duplicate axes needing expert review:
  - `config` vs `configs`: keep `configs` canonical until imports prove otherwise.
  - `apps` vs `frontend`: likely keep `apps` canonical for app surfaces; review `frontend`.
  - `.obsidian` vs `docs/obsidian`: `.obsidian` is local app state; `docs/obsidian` is repo cockpit.
  - `tasks` vs `ops/task_registry.yaml`: registry is canonical; legacy `tasks` needs archive or migration.
- Current docs surfaces marked REVIEW:
  - `docs/acceptance`
  - `docs/active`
  - `docs/audits`
  - `docs/candidate_funnel`
  - `docs/context`
  - `docs/contracts`
  - `docs/db`
  - `docs/execution`
  - `docs/frontend_ios`
  - `docs/frontend_web`
  - `docs/graphify`
  - `docs/harness`
  - `docs/logs`
  - `docs/specs`
- Canonical or keep surfaces:
  - `AGENTS.md`
  - `ops/**`
  - `docs/operating_system/**`
  - `docs/architecture/**`
  - `docs/ownership/**`
  - `docs/generated_context/**`
  - `docs/reports/task_*/**`
  - `docs/llm_wiki/**` as routing memory only
  - `docs/obsidian/**` as human cockpit only
  - `docs/frontend_app_ssot/**` for frontend SSOT

Hard project state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data is UNKNOWN/BLOCKER, never negative evidence
- GPT is advisory only; repo SSOT and validators remain source of truth.

What I need from you:
1. Propose a durable target repository tree for this project, grouped by layer and function.
2. Decide which root-level axes should be canonical and which should become archived, local-only, or deleted.
3. Give a concrete cleanup decision matrix for the duplicate axes and REVIEW docs surfaces above.
4. Define a safe trash/archive policy. Include when to delete, when to move to `docs/archive`, when to move to a local ignored folder, and when to block.
5. Define closeout validators or registry checks Codex should add so future tasks cannot recreate clutter.
6. Identify P0/P1 risks in deleting or moving the listed surfaces.
7. Give Codex a small next patch plan that is safe to implement now without touching broker, live trading, strategy logic, raw data, DB schema, or secrets.

Output format:
1. Architecture Diagnosis
2. Target Repository Tree
3. Canonical vs Archive/Delete Decisions
4. Cleanup Decision Matrix
5. Persistent Governance / Validators
6. P0/P1 Risks
7. Codex Patch Plan
8. Validation Checklist
