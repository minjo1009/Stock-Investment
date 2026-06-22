# Obsidian Operating Plan

## Decision Summary

Use this repository root as the Obsidian vault. Obsidian is a navigation and review layer over the existing operating system, not a replacement for `tasks/task_registry.csv`, `docs/reports/`, raw-source rules, or validation commands.

## Objective

Make the project easier to navigate, review, and continue by linking tasks, reports, graphify outputs, operating rules, and templates inside Obsidian while preserving the repository's governed artifact discipline.

Current paper-ops sessions must start from `docs/ownership/current_operating_model.md`; Graphify outputs are stale until regenerated.

## Scope

- Vault root: repository root.
- Primary Obsidian surface: `docs/obsidian/Vault Home.md`.
- Primary visual board: `docs/obsidian/boards/Research Cockpit.canvas`.
- Codex workflow guide: `docs/obsidian/Codex Obsidian Workflow.md`.
- Project maps: `docs/obsidian/mocs/`.
- Templates: `docs/obsidian/templates/`.
- Source of truth remains: `tasks/task_registry.csv`, task markdown files, report markdown files, decision CSVs, artifact manifests, and validation commands.

## Non-Goals

- Do not move existing reports, raw data, or derived artifacts for Obsidian convenience.
- Do not treat backlinks, tags, or graph proximity as quant evidence.
- Do not infer task lineage from similar names, nearby dates, or visual graph proximity.
- Do not use Obsidian notes to bypass required task reports or artifact manifests.

## Application Plan

1. Open the repository root as an Obsidian vault.
2. Start each session from `docs/obsidian/Vault Home.md`.
3. Open `docs/obsidian/boards/Research Cockpit.canvas` when you want a visual control-room view.
4. Use `docs/obsidian/Codex Obsidian Workflow.md` to understand how Codex should use Obsidian while working.
5. Use `docs/obsidian/mocs/Operating System Map.md` to check rules before goal or task work.
6. Use `docs/obsidian/mocs/Quant Research Map.md` to navigate current research lanes by team and blocker.
7. Use `docs/graphify/context_packs.json` and `graphify-out/GRAPH_REPORT.md` only as stale historical discovery aids until Graphify is regenerated; verify every finding against source files.
8. Use `docs/obsidian/templates/task-note-template.md` only for working notes that eventually point to standard reports.
9. Before any new frontend UI/design work, check `../../DESIGN.md` and `../llm_wiki/frontend_app_ssot_pack.md` as the baseline.

## Success Metrics

- A new session can find the current operating model, operating rules, registry, active/canonical task chain, graphify status, and report standard from one home note.
- A visual board can show the current lane, blocker themes, and Codex closeout loop without becoming evidence itself.
- Every Obsidian working note links back to a task, report, registry row, or explicit blocker.
- No Obsidian-only note becomes the sole source of a decision.
- Repo validation still runs without depending on Obsidian.

## Maintenance Rules

- Add links to the MOCs only when a document becomes an actual recurring navigation target.
- Keep tags broad and operational: `#ops`, `#research-governance`, `#data-readiness`, `#diagnostic-only`, `#execution-risk`.
- Prefer markdown links to real files over unresolved wiki links.
- Leave large files in `data/artifacts/`, `data/raw/`, and source-specific folders.
- Keep personal Obsidian workspace files untracked.

## Validation

Run after changes to governance/navigation files:

```powershell
python scripts/task_registry_validate.py
python scripts/codeowners_coverage_validate.py
python scripts/governance_completion_audit.py
```

For this Obsidian application task, the minimum validation is file existence plus markdown link review because no strategy logic or registry status changed.
