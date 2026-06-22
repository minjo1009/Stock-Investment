# Stock Investment Trader Brain

This repository is the working system for a United States equity quant trading project. The project is not a single alpha formula. It is a trader-brain style decision system that keeps a verifiable chain from raw source information to economic meaning, relationship graph, candidate thesis, validation, paper/shadow review, and eventual deployment gates.

## Current Status

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Latest canonical closeout: Task3804 Expo app scaffold and Storybook foundation setup.
- Current frontend direction: Expo Development Build iOS-first read-only app surfaces must expose decisions, reasons, evidence, source freshness, blockers, and provenance. They must not create broker mutations or imply paper/live permission.

Validation results never grant acceptance by themselves. Promotion requires split/OOS evidence, leakage review, cost/slippage review, artifact audit, live-source readiness, and explicit status change in the project operating documents.

## Read First

- `AGENTS.md`
- `docs/operating_system/project_operating_state.md`
- `docs/llm_wiki/README.md`
- `docs/llm_wiki/task_artifact_index.md`
- `docs/obsidian/Vault Home.md`
- `tasks/task_registry.csv`

Use Obsidian and LLM Wiki as navigation layers only. Current truth belongs in operating state, task registry rows, task reports, artifact manifests, and validator outputs.

## Latest Architecture Direction

The backend/runtime layer now has DB governance, DB loop contracts, registered diagnostic loop runners, cached/provider source acquisition, operator source scheduler scripts, source receipts, reference hashes, lineage rows, and freshness/gate validators.

The frontend/app layer should follow the current frontend SSOT pack in `docs/frontend_app_ssot/`:

- Fixed top-level IA: `HOME`, `BRAIN`, `PORTFOLIO`, `ORDERS`, `SYSTEM`.
- Universal detail frame V2: `Decision Summary`, `Thesis / Logic`, `Validation / Readiness`, `Evidence`, `Risk`, `Next Action`.
- Detail workspaces: Candidate, Position, Chain, Risk, and Order.
- Core philosophy: every screen should preserve the decision-reason-evidence-source chain.
- Active implementation target: Expo Development Build iOS-first mobile app with read-only backend/read-model integration, design tokens, reusable components, Storybook coverage, screenshot QA, and disabled trading action controls.

The prior React plus TypeScript web pack and Expo Go 3052 DOM cockpit are retained as design/migration evidence only. New frontend work should start from the fixed IA and read-only SSOT pack above.

## Repository Map

- `src/`: Python backend, runtime, brain, backtest, execution, integration, risk, state, and UI code.
- `tools/db/`: DB authority, healthcheck, snapshot, restore, source acquisition, and registered loop tooling.
- `scripts/`: validators, task runners, scheduler scripts, and research/build helpers.
- `docs/reports/`: task reports and decision artifacts.
- `docs/llm_wiki/`: short routing memory for future LLM sessions.
- `docs/obsidian/`: human navigation cockpit.
- `docs/db/`: DB topology, scheduler, retention, restore, and authority contracts.
- `data/artifacts/`: task outputs and derived panels.
- `data/raw/`: raw source families when applicable.
- `tasks/task_registry.csv`: canonical task registry.

## Safety Rules

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback.
- Missing labels are never negatives.
- Missing raw sources are reported, not approximated.
- Labels and outcomes are evaluation-only and must not enter assignment logic.
- GPT/Chrome and external tools are review-only unless an explicit connector/task contract says otherwise.
- Real capital remains forbidden until the project status documents explicitly change.

## Common Validation

```powershell
python scripts/task_registry_validate.py
```

Run task-specific validators from the relevant report or registry row. For DB/runtime work, prefer the validator named in the current task report before adding broader checks.

## GitHub Update Notes

Before publishing a fresh GitHub update, check:

1. `git status --short --branch`
2. The intended staged file list.
3. The latest operating state and registry tail.
4. That no local secrets, private env files, raw credentials, or generated caches are staged.
5. That any changed task report includes validation commands and status boundaries.

This repository currently contains many untracked generated or historical files. Do not bulk-stage everything without a scope review.
