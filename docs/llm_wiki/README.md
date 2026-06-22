# LLM Wiki

This folder is a short routing memory for Codex/GPT sessions.

It is not a source of truth. Verify current state in:

- [Project Operating State](../operating_system/project_operating_state.md)
- [Task Registry](../../tasks/task_registry.csv)
- [Task Reports](../reports)
- artifact manifests and validator outputs

## Read Order

1. [status_boundaries.md](status_boundaries.md)
2. [task_artifact_index.md](task_artifact_index.md)
3. [anti_loop_checklist.md](anti_loop_checklist.md)
4. Domain-specific file:
   - sources: [source_truth_map.md](source_truth_map.md)
   - source design token file: [DESIGN.md](../../DESIGN.md)
   - frontend app SSOT pack: [frontend_app_ssot_pack.md](frontend_app_ssot_pack.md)
   - backtest/replay: [backtest_replay_contract.md](backtest_replay_contract.md)
   - subagents/GPT: [subagent_gpt_boundaries.md](subagent_gpt_boundaries.md)
   - brain/code operating loop: [brain_code_operating_loop.md](../operating_system/brain_code_operating_loop.md)
   - realtime L0-L6 trading operations: [realtime_trading_operations.md](realtime_trading_operations.md)

## Current Direction

The project is moving from repeated source/backtest loops toward governed paper/shadow trading:

- frozen main policy
- challenger policy separation
- daily paper decision journal
- MDD attribution
- read-only frontend app surface based on the fixed SSOT pack IA
- external tool helpers are split: Pandera remains validation-oriented, while Task3191-3195 promotes Polars and DuckDB into the core backend acceleration layer with pandas parity checks
- latest backend/runtime contract line is Task3351-3400: Task742 meaning -> relation edge -> thesis bundle -> review-only policy action -> L6 runtime decision -> L7 read-only model
- current repeatable brain/code operating loop is Task3181-3190
- current backend acceleration layer is Task3191-3195: Polars first, DuckDB second, pandas fallback, no trading semantics change
- first real accelerator migration is Task3196-3200: Task3141 strict-gate aggregate path now routes through `strict_gate_aggregate_accelerated()`
- current realtime operations recommendation is Task3401-3410: event-driven plus 10-minute changed-candidate brain heartbeat, with 5-minute safety heartbeat and 30-minute heavy-source refresh
- current realtime implementation guard is Task3411-3420: deterministic L0-L6 runtime state hash, idempotency key, duplicate-state skip, and 5-minute/10-minute cadence separation
- latest runtime operations implementation is Task3531-3560: operator dry-run scheduler config/scripts, KIS paper broker-truth reconciliation adapter, and full-evidence PAPER_ELIGIBLE path that stops at local paper intent creation
- latest operations cleanup line is Task3561-3570: generated caches were removed, logs/DBs/Graphify/external references were retained pending retention or migration policy, and P0 skill candidates were identified for scheduler operations and cleanup retention
- latest DB operations line is Task3601-3800: DB management tooling, DB-resident loop contracts, a generic registered loop runner, cached evidence adapters, provider/cache source acquisition, and operator source scheduler config are installed. Task3761-3800 adds `configs/db_source_acquisition_scheduler.json`, source scheduler run/install scripts, diagnostic `market_bars_5m -> indicator_snapshots -> runtime_strategy_decisions` loops, current broker-truth BLOCKED evidence, SEC live user-agent blocker artifact, and a gate-condition validator. Source gates remain closed; no strategy/deployment/real-capital status changes.
- latest frontend planning input is the 2026-06-22 SSOT DOCX pack summarized in [frontend_app_ssot_pack.md](frontend_app_ssot_pack.md): fixed IA is `HOME / BRAIN / PORTFOLIO / ORDERS / SYSTEM`, detail workspaces use `Decision / Thesis / Evidence / Risk / Action`, and frontend surfaces remain read-only until governance changes. Legacy mobile cockpit docs are removed from active routing.

Standing status:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`

Do not promote any result to strategy acceptance, deployment readiness, or real-capital permission.

## Brain / Skill Boundary

- L0-L6 judgment and runtime gate logic belongs in backend engine code.
- Skills are operating procedures for invoking, validating, reporting, and maintaining that backend work.
- Do not encode buy/sell/sizing judgment as skill prose.
- Do not let a skill become a hidden strategy engine.
- Frontend observation surfaces are explanation layers only. They must not become execution engines.

## Backend Operating Loop

Use this loop for sustainable repeat work:

1. Intake: define objective, owner, reviewer, read scope, write scope, forbidden actions, and success criteria.
2. Implement: keep changes scoped to the owning module, script, report, or artifact family.
3. Record: put decisions in `docs/reports/<task_id>/`, large outputs in `data/artifacts/<task_id>/`, and current pointers in `tasks/task_registry.csv`.
4. Validate: run the task validator plus `python scripts/task_registry_validate.py`; add broader governance checks only when the task changes operating state.
5. Close: update Obsidian/LLM wiki only as navigation, not as source-of-truth.

Git/GitHub rule:

- Use local Git for branch, diff, status, and commit discipline.
- Use GitHub MCP only for PR, issue, review, or repository monitoring workflows.
- Do not let GitHub issue text replace registry rows, reports, manifests, or validator output.
