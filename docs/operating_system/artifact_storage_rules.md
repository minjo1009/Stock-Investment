# Artifact Storage Rules

## Target Structure

```text
docs/
  architecture/
  operating_system/
  phases/
    PHASE_00/
      phase.md
      tasks/
        TASK_000.md
        TASK_001.md
      reports/
      decisions/
  graphify/
    raw/
    clean/
    reports/
    context_packs/
experiments/
  task_runs/
  backtest_research/
archive/
  external_references/
  obsolete_tasks/
  old_reports/
```

## Rules

- Every task report must live under its owning phase after migration: `docs/phases/{phase_id}/reports/{task_id}/`.
- Every task spec must live under `docs/phases/{phase_id}/tasks/{task_id}.md`.
- Every Graphify run must have raw graph, clean graph, report, and exclusion config.
- Every experiment must have a README explaining whether it is promoted, rejected, or archived.
- No one-off task script may remain in production app directories unless promoted by an explicit architecture decision.
- Existing `docs/reports/task_*` remains readable during migration; moves require compatibility review.
- External references belong under `archive/external_references/` and are excluded from production Graphify by default.

## Naming

- Task: `TASK_000`
- Phase: `PHASE_00`
- Report markdown: `report.md` or `{task_id}_{slug}.md`
- Report JSON: `{task_id}_{slug}.json`
- Decision: `DECISION_YYYYMMDD_{slug}.md`
- Graphify exclusion config: `graphify_exclude.yml`

## Promotion Rule
A task script or experiment becomes production only when a decision document records owner layer, tests, public interface, rollback plan, and Graphify impact.

