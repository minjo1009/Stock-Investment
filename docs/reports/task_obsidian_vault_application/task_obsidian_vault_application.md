# Task Obsidian Vault Application

## Decision Summary

- Verdict: Obsidian is applied as a repository navigation and review layer.
- Strategy acceptance status: not applicable; this is Research Governance documentation, not a strategy claim.
- Key metrics: one vault home, one named-lead visual research cockpit board, one Codex workflow guide, two MOCs, one working-note template, minimal Obsidian settings, and one artifact manifest created.
- What changed: added a governed Obsidian entrypoint without moving existing reports, tasks, raw sources, or derived artifacts.
- Next action: use `docs/obsidian/Vault Home.md` as the default start page and add links only when a document becomes a recurring navigation target.

## Quant Expert Report

### Data Source and Source Readiness

No market data, labels, lifecycle joins, or strategy panels were created or modified. Existing source-of-truth locations remain unchanged:

- `tasks/task_registry.csv`
- `docs/reports/`
- `data/raw/`
- `data/artifacts/`
- `docs/graphify/`
- `graphify-out/`

### Exact Join Keys

Not applicable. No research panel, lifecycle label, or trading decision join was performed.

### Leakage Audit

Not applicable. The Obsidian layer is navigation-only and must not enter assignment logic, feature logic, backtest logic, or deployment decisions.

### Split/OOS Metrics

Not applicable. No strategy evaluation was run.

### Failure Decomposition

The main failure mode is governance drift: an Obsidian note could become an informal decision source. The mitigation is explicit in `docs/obsidian/README.md`: Obsidian notes must link back to registry rows, reports, decision CSVs, manifests, or blockers.

### Cost/Slippage Stress

Not applicable. No PnL or deployment claim changed.

### Remaining Blockers

- Obsidian cannot automatically prove task lineage; registry and manifests remain mandatory.
- Graphify outputs include inferred edges, so graph discoveries require source-file verification.
- Personal Obsidian workspace layout is intentionally untracked.

### Validation Commands

Passed:

```powershell
python scripts\task_registry_validate.py
python scripts\codeowners_coverage_validate.py
python scripts\governance_completion_audit.py
```

Additional checks passed:

- Obsidian JSON settings parse successfully.
- Research Cockpit canvas JSON parses successfully and every file node points to an existing repository path.
- Research Cockpit includes named leads and current active runtime lane anchors.
- Core Obsidian entrypoint, MOCs, template, report, and manifest paths exist.
- Manifest-listed artifact paths exist.

## No-Background Decision-Maker Report

Obsidian is now set up as a control room for the repo. Open the repository root as a vault, start from `docs/obsidian/Vault Home.md`, open `docs/obsidian/boards/Research Cockpit.canvas` for the visual board, and use the maps to jump to operating rules, task registry, reports, and graphify discovery outputs.

This does not change trading readiness, capital readiness, or strategy acceptance. It only improves navigation and review continuity.

## Artifact Manifest

See `artifact_manifest.csv` in this directory.
