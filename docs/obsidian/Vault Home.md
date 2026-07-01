---
tags:
  - ops
  - research-governance
  - obsidian
---

# Vault Home

This is the starting point for using the repository in Obsidian.

## Start Here

- [Repository README](../../README.md)
- [Docs Index](../INDEX.md)
- [Current Operating Model](../ownership/current_operating_model.md)
- [Obsidian Operating Plan](README.md)
- [Goal Operating Cycle](../operating_system/goal_operating_cycle.md)
- [Work Closeout Protocol](../operating_system/work_closeout_protocol.md)
- [Task Report Standard](../report_standard.md)
- [Task Registry](../../tasks/task_registry.csv)

## Maps

- [Operating System Map](mocs/Operating System Map.md)
- [Quant Research Map](mocs/Quant Research Map.md)

## Visual Boards

- [Research Cockpit](boards/Research Cockpit.canvas)

## Codex Workflow

- [Codex Obsidian Workflow](Codex Obsidian Workflow.md)

## Current Source-of-Truth Files

- Current operating model: [docs/ownership/current_operating_model.md](../ownership/current_operating_model.md)
- Readiness registry: [docs/ownership/readiness_registry.yaml](../ownership/readiness_registry.yaml)
- Work closeout protocol: [docs/operating_system/work_closeout_protocol.md](../operating_system/work_closeout_protocol.md)
- Strategy acceptance program: [Task599](../reports/task_599_strategy_acceptance_program/task_599_strategy_acceptance_program.md)
- Current paper-week operating plan: [Task598](../reports/task_598_paper_week_feedback_operating_plan/task_598_paper_week_feedback_operating_plan.md)
- Registry: [tasks/task_registry.csv](../../tasks/task_registry.csv)
- Archive candidates: [tasks/archive_candidate_registry.csv](../../tasks/archive_candidate_registry.csv)
- Report directory: [docs/reports](../reports)

## Stale Discovery Aids

- Graphify report: [graphify-out/GRAPH_REPORT.md](../../graphify-out/GRAPH_REPORT.md)
- Graphify context packs: [docs/graphify/context_packs.json](../graphify/context_packs.json)

Graphify outputs were generated on 2026-04-25 and are stale for current paper-ops governance until regenerated.

## Review Searches

Use these in Obsidian search:

```text
path:docs/reports/ DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
path:docs/reports/ blocked-source
path:tasks/ canonical
path:docs/reports/ "Artifact Manifest"
path:docs/ "missing raw"
```

## Session Close Checklist

- Did the work update the relevant report or explicitly mark report update not applicable?
- Did any active/canonical state change require `tasks/task_registry.csv`?
- Did every new output have a manifest entry when required?
- Did validation run, or is the reason for not running it recorded?
- Is the Obsidian board still pointing to source-of-truth files rather than replacing them?
