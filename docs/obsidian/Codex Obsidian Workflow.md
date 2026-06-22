---
tags:
  - ops
  - obsidian
  - research-governance
---

# Codex Obsidian Workflow

## Purpose

This note defines how Codex should use Obsidian in this project to improve work speed, continuity, and review quality. Obsidian is a visual navigation layer. It does not replace source files, reports, registries, tests, or artifact manifests.

## What Changes When Obsidian Is Open

Obsidian helps the human side of the workflow more than the file-editing side. Codex can already read and edit the repository directly. The efficiency gain comes from shared navigation:

- You can watch the same report, board, or MOC that Codex is using.
- Codex can point to one stable home note instead of explaining the whole repository repeatedly.
- Backlinks, outgoing links, graph view, and canvas boards make task lineage easier to inspect.
- Review and handoff become faster because the current task, blocker, validation command, and source-of-truth files are visible together.

## Start Page

Always start from:

- [Vault Home](Vault Home.md)

The home note links to the current operating model, operating rules, registry, research maps, stale Graphify discovery outputs, and closeout checklist.

## Visual Board

Use this board for a high-level control-room view:

- [Research Cockpit](boards/Research Cockpit.canvas)

The board shows:

- source-of-truth files
- named project leads: 필수, 성원, 종찬, 중훈, 서연, 동승, 윤헌, 규승
- each lead's canonical team and ownership surface
- active runtime-source task flow, especially Task590-596
- research backbone and live-source blocker chain
- graphify discovery aids, stale until regenerated
- Codex work loop and validation gate

Canvas nodes are navigational aids only. If a canvas arrow suggests a relationship, verify it against `tasks/task_registry.csv`, `docs/ownership/team_charter.md`, `docs/ownership/module_ownership_map.md`, or the linked task report before making decisions.

## Codex Work Loop

### 1. Intake

Codex should first reduce the request to:

- objective
- assumptions
- success criteria
- owner team
- reviewer team
- expected artifacts
- validation command
- forbidden actions

For long-running goals, use [Goal Operating Cycle](../operating_system/goal_operating_cycle.md).

### 2. Navigate

Codex should use Obsidian-facing navigation in this order:

1. [Vault Home](Vault Home.md)
2. [Research Cockpit](boards/Research Cockpit.canvas) for team/lead orientation
3. [Task Registry](../../tasks/task_registry.csv)
4. [Team Charter](../ownership/team_charter.md) and [Module Ownership Map](../ownership/module_ownership_map.md) when ownership matters
5. relevant task report in `docs/reports/`
6. artifact manifest and decision CSV
7. code, tests, scripts, or raw-source files
8. graphify outputs only as stale discovery aids until regenerated

This prevents the common failure mode where a visually convenient note becomes more authoritative than the registry or report.

### 3. Scope

Before editing, Codex should identify the smallest write scope:

- navigation-only work: `docs/obsidian/`, `.obsidian/`, `docs/INDEX.md`
- governance/report work: `docs/reports/<task_id>/`, manifest, registry when applicable
- implementation work: direct source/test files tied to the task
- data work: raw sources in `data/raw/<source>/`, large derived panels in `data/artifacts/<task_id>/`

If a request can be solved by a small note, link, or board update, do not invent a new pipeline.

### 4. Execute

Codex should make the smallest change that satisfies the request. Obsidian is useful during execution for:

- keeping the current task report open
- keeping the relevant canvas visible
- using backlinks to find related reports
- using search to locate blockers such as `blocked-source`, `diagnostic-only`, `receive timestamp`, `broker truth`, and `full depth`

Obsidian should not be used to infer data joins, lifecycle identity, task parentage, or deployment readiness.

### 5. Verify

For navigation and governance changes, run:

```powershell
python scripts/task_registry_validate.py
python scripts/codeowners_coverage_validate.py
python scripts/governance_completion_audit.py
```

For task-specific work, run the command listed in `tasks/task_registry.csv` or the relevant report. If a command cannot run, Codex must record the reason and remaining risk.

### 6. Close

At closeout, Codex should leave the user with:

- what changed
- where the artifact is
- what validation passed
- what remains blocked
- what file or board to open next

If a task becomes canonical, active, superseded, or changes readiness status, update `tasks/task_registry.csv`. If no registry update is needed, say why.

## How You Should Use It While Asking Codex To Work

Keep Obsidian open when you want to review or steer work visually:

1. Open [Vault Home](Vault Home.md).
2. Open [Research Cockpit](boards/Research Cockpit.canvas) in another pane.
3. Ask Codex for the work.
4. When Codex mentions a report or task, click the linked node/file in Obsidian.
5. Use Backlinks and Outgoing Links to inspect related context.
6. Use the closeout checklist before accepting the result.

You do not need Obsidian open for Codex to edit code. It is most useful when the task is strategic, multi-step, or easy to lose in the project history.

## Search Recipes

Use Obsidian search:

```text
path:docs/reports/ blocked-source
path:docs/reports/ diagnostic-only
path:docs/reports/ "receive timestamp"
path:docs/reports/ "broker truth"
path:docs/reports/ "full depth"
path:tasks/ Task596
path:docs/reports/ "Validation Commands"
```

Use these searches to orient, not to prove.

## What Codex Should Update

Codex should update Obsidian files when:

- a new recurring navigation path appears
- a task chain becomes the current active lane
- a blocker theme becomes central to decisions
- a new visual board would reduce review friction
- a template can prevent repeated intake mistakes

Codex should not update Obsidian files when:

- the change is one-off and not worth preserving
- the note would duplicate a report without adding navigation value
- the update would hide a required registry or manifest update

## Status Language

Use exact project status language in reports, not casual Obsidian labels:

- `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- `PRIMARY_PASS`
- `SECONDARY_PASS`
- `NOT_ACCEPTED`
- `SUPERSEDED`

Canvas labels can be short, but reports must keep the exact status terms.

## Limits

Obsidian does not make research true. It makes the work easier to see.

The project rules still hold:

- no inferred lifecycle matching
- no proximity fallback
- missing labels are never negatives
- missing raw sources are reported, not approximated
- labels and outcomes stay out of assignment logic
- deployment claims require live-source readiness

When Obsidian and the registry disagree, the registry/report path wins.
