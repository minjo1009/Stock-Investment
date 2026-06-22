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
- latest frontend planning authority is the canonical pack in `docs/frontend_app_ssot/`, summarized in [frontend_app_ssot_pack.md](frontend_app_ssot_pack.md): active target is Expo Development Build iOS-first, fixed IA is `HOME / BRAIN / PORTFOLIO / ORDERS / SYSTEM`, detail workspaces use `Decision Summary / Thesis-Logic / Validation-Readiness / Evidence / Risk / Next Action`, and frontend surfaces remain read-only until governance changes. React web and Expo Go 3052 cockpit materials are design/migration evidence only.
- latest frontend implementation gate is Task3802: [08_FRONTEND_READ_MODEL_CONTRACT.md](../frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md) defines screen-ready read models, source freshness, provenance, blockers, and disabled-action props before UI coding.
- latest frontend pre-scaffold gate is Task3803: [11_IMPLEMENTATION_PRECONDITIONS.md](../frontend_app_ssot/11_IMPLEMENTATION_PRECONDITIONS.md) fixes `apps/ios-trader-brain` as the app root and marks commands/fixtures/QA/safety validator as scaffold decisions until proved runnable.
- latest frontend scaffold line is Task3804: `apps/ios-trader-brain` now exists with Expo SDK 56, Expo Router placeholder tabs, foundation components, smoke story files, `npm run typecheck`, and `npm run validate:safety`; Storybook runtime, NativeWind, lint/test, screenshot QA, Maestro, and fixture source selection remain post-scaffold hardening.
- latest frontend QA baseline is Task3805: Storybook web runtime is runnable through `npm run storybook` and smoke-tested through `npm run storybook:smoke`; `npm run lint`, `npm test`, and hardened `npm run validate:safety` pass. NativeWind, screenshot QA, Maestro, iOS dev build, and source-derived fixture payloads remain blocked/deferred.
- latest frontend foundation baseline is Task3806: foundation/layout/generic components now cover source freshness, blockers, missing/unknown/stale/blocked states, and disabled-action display in Storybook. Static typed fixtures under `apps/ios-trader-brain/src/mocks/fixtures/foundation-states.ts` are scaffold-only and NOT authority. NativeWind and on-device Storybook remain deferred.
- latest frontend read-model fixture/domain-contract baseline is Task3809: generated JSON catalog fixture snapshot under `apps/ios-trader-brain/src/mocks/fixtures/` is scaffold-only and NOT authority; `npm run validate:fixtures` validates the contract-shaped payloads; P0 domain components are props-only and Storybook-covered. Product screens and authoritative backend/read-only source integration remain future work.
- latest GPT-Codex loop correction is Task3817-Task3824: loops 3-10 completed as docs/governance preflight work for screenshot QA, Maestro smoke-flow QA, fixture authority, domain story coverage, Candidate Detail readiness, HOME readiness, NativeWind deferral, and iOS dev build validation. Product screens remain blocked.
- latest frontend implementation boundary is Task3826: `docs/frontend_app_ssot/21_SCAFFOLD_ONLY_SCREEN_ASSEMBLY_BOUNDARY.md` allows only future selected scaffold-only fixture-backed screen assembly under visible read-only and `NOT_AUTHORITY` constraints. Product screen implementation, authoritative read source, screenshot QA readiness, broker mutation, paper/live, deployment readiness, and real-capital permission remain blocked.
- latest frontend visible implementation is Task3827: HOME now has a scaffold-only fixture-backed `HOME v0` under `apps/ios-trader-brain/app/(tabs)/index.tsx`, backed by `src/read-models/homeFixture.ts`. It is `NOT_AUTHORITY`, read-only, and does not change strategy/deployment/paper/live/broker/real-capital state.
- latest frontend detail implementation is Task3828: Candidate Detail now exists at `apps/ios-trader-brain/app/brain/candidate/[candidateId].tsx`, backed by `src/read-models/candidateDetailFixture.ts`. It is scaffold-only, `NOT_AUTHORITY`, read-only, and shows stale/missing/chart-source blockers rather than implying readiness.
- latest frontend scaffold implementation is Task3831: the 10-loop run added scaffold-only fixture-backed BRAIN, PORTFOLIO, ORDERS, SYSTEM, Position Detail, Order Detail, Chain Detail, read-only cross-links, and Storybook scaffold overview coverage. These are still `NOT_AUTHORITY`, read-only, and not product readiness.
- latest frontend QA baseline is Task3834: screenshot target validation, route link validation, and scaffold screen-boundary validation are runnable. Screenshot capture and visual approval have not occurred.

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

Latest frontend screenshot evidence:

- Task3836 captured Chrome-headless web-preflight screenshots for 9 scaffold routes across 2 mobile widths and applied a bounded P1 `Badge`/`StatusRow` repair for screenshot-evidenced governance/status badge clipping. Screenshots remain `NOT_AUTHORITY`; product readiness is not granted.
