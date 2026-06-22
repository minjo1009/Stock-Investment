# Subagent Artifact Governance Skill

## Purpose
Keep all task outputs reproducible, searchable, and auditable by enforcing a strict artifact lifecycle.

## Mandatory Rules
1. Never write task outputs directly into `docs/` root.
2. Every output must be placed in one lifecycle bucket:
   - `docs/reports/` for task outputs and experiment results
   - `docs/contracts/` for operating contracts and canonical state definitions
   - `docs/audits/` for architecture/execution/process audits
   - `docs/tmp/` for checkpoints and transient intermediate files
   - `docs/logs/` for run logs
   - `docs/specs/` for strategy/specification documents
3. Each task keeps one directory:
   - `docs/reports/<task-id>/...`
4. File naming standard:
   - report markdown: `<task-id>_<slug>.md`
   - report json: `<task-id>_<slug>.json`
   - checkpoint: `<task-id>_<slug>.checkpoint.json`
   - run log: `<task-id>_<slug>.run.log`
5. Every new artifact-producing task must update:
   - `docs/INDEX.md`
   - `docs/reports/task_log_YYYY-MM-DD.md` (same day only)

## Required Output Block (every subagent handoff)
Use exactly this structure:

```
**changed files**
- ...

**artifacts**
- absolute path list

**classification**
- report / contract / audit / tmp / log / spec

**validation**
- command + result

**validation authority**
- authority tag from `docs/architecture/test_validation_canonicalization_map.md`
- what PASS does not mean

**next actions**
- ...
```

## Move Policy
When cleanup is requested:
1. Create destination folders first.
2. Move files by lifecycle.
3. Create/update `docs/INDEX.md`.
4. Record old->new mapping in `docs/audits/artifact_relocation_log.md`.

## Guardrails
- Do not delete evidence files unless explicitly requested.
- Checkpoint/log files are never promoted to `reports` without explicit approval.
- If a script hardcodes an old path, keep compatibility by updating script defaults in a dedicated follow-up task.
- Do not describe test success as strategy acceptance, deployment readiness, broker truth completion, or real-capital permission.
- Use `docs/architecture/src_canonicalization_map.md` before promoting task-scoped code into a package path.
- Use `docs/architecture/test_validation_canonicalization_map.md` before calling a validation result a quality gate.

## UI Data Source Freshness Policy (Subagent Mandatory)
When a task affects frontend/reporting, subagents must validate data freshness before UI binding.

1. DB source resolution priority:
   - `TRADING_DB_PATH` (if set)
   - latest modified existing DB among:
     - `./trading.db`
     - `./data/trading.db`
     - `./docs/logs/trading.db`
2. Backtest trades source resolution priority:
   - `BACKTEST_TRADES_PATH` (if set)
   - latest modified existing JSON among:
     - `./data/backtest/trades.json`
     - task-level trade exports under `docs/reports/**/trades.json` (if present)
3. UI must surface:
   - resolved source path
   - file existence
   - latest-updated timestamp
   - warning if selected source is not latest among candidates
4. If no valid source exists:
   - show explicit diagnostics in UI
   - do not silently fall back to stale/empty placeholders.

## Quick Classification Guide
- `task_*.md/json` -> `docs/reports/<task-id>/`
- `*_contract*.md` -> `docs/contracts/`
- `*_audit*.md` -> `docs/audits/`
- `tmp_*.json`, `*.checkpoint.json` -> `docs/tmp/`
- `*.run.log` -> `docs/logs/`
- `strategy_spec_*.md` -> `docs/specs/`
