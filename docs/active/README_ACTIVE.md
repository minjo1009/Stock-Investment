# Active Workspace

This directory is the default operating entry point for Codex and local development.

Use this layer to answer four questions before reading legacy material:

1. What is the current project status?
2. Which files are source-of-truth?
3. What should Codex read by default?
4. What tasks are active now?

## Read First

1. `docs/active/README_ACTIVE.md`
2. `docs/active/PROJECT_STATUS.md`
3. `docs/active/ACTIVE_SSOT_INDEX.md`
4. `docs/active/CODEX_READ_SCOPE.md`
5. `docs/active/CURRENT_TASKS.md`

## Standing Boundaries

| Boundary | Current status |
|---|---|
| Strategy acceptance | `NOT_ACCEPTED` |
| Deployment readiness | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |
| Real capital | `FORBIDDEN` |
| Paper operation | `READY_FOR_CONTROLLED_PAPER_RUN` |

These boundaries come from `docs/ownership/current_operating_model.md` and `docs/ownership/readiness_registry.yaml`. This A001 cleanup did not change trading behavior, strategy acceptance, broker logic, order generation, backtest results, or deployment readiness.

## Operating Rule

Default work should start here, then expand only to the specific file, folder, report, or contract needed for the task.

Do not preload all of `docs/reports/`, `docs/obsidian/`, Graphify outputs, or historical task reports unless the task explicitly needs them.

