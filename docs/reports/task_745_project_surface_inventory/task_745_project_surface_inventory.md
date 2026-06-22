# Task745 Project Surface Inventory

## Decision Summary

- Verdict: `PROJECT_SURFACE_INVENTORY_CREATED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Inventory rows: 2,707
- Needs owner review: 1,066
- Summary commit candidates: 1,493
- Canonical candidates: 135
- Local-only: 13
- Next action: 2/5 cleanup pass should classify `src/` into canonical, task-scoped, experiment, archive, and local-only groups.

## Quant Expert Report

### Data Source And Source Readiness

This task uses repository-native metadata only:

- `git status --porcelain=v1 -z --untracked-files=all`
- `git ls-files -z`
- local file size, extension, path, and top-level directory

No market data, labels, PnL, broker data, or strategy outcomes are used.

### Exact Join Keys

Not applicable. This is a project surface inventory task.

### Leakage Audit

No strategy assignment logic was changed.

No backtest result, score, rank, buy/sell, sizing, or deployment output was created.

### Inventory Summary

| Suggested Class | Count | Meaning |
| --- | ---: | --- |
| `summary_commit_candidate` | 1,493 | Small reports, decisions, pass/fail files, manifests. |
| `needs_owner_review` | 1,066 | Needs canonical/experiment/archive/local classification. |
| `canonical_candidate` | 135 | Likely stable docs, contracts, skills, package code/tests. |
| `local_only` | 13 | Keep local or manifest-only. |

### Top-Level Surface

| Top Level | Count |
| --- | ---: |
| docs | 1,600 |
| src | 558 |
| tests | 378 |
| tasks | 58 |
| scripts | 35 |
| data | 16 |
| frontend | 16 |
| skills | 8 |

### Main Findings

1. `src/` is the largest code risk.
   It contains 558 visible files, with task-scoped backtest/research code mixed with package code.

2. `tests/` is not yet a clean quality gate.
   It contains 378 visible files, many task-scoped.

3. `docs/` is large but mostly summary commit candidates.
   The report policy should keep markdown/decision/manifests while full panels stay local.

4. `참고 Context/` was removed from formal inventory via `.gitignore`.
   It is local reference material, not the project control surface.

5. No deletion or movement was performed.
   Classification comes before migration.

## No-Background Decision-Maker Report

This pass made the project visible.

Before this, the project looked like a pile of files.

Now we know the first hard target:

```text
src first, then tests, then skills/MD/subagents, then final runbook.
```

The next pass should not touch trading logic.

It should classify `src/` so future Codex sessions know which code is real project code and which code is task-scoped research.

## Artifact Manifest

- `scripts/project_surface_inventory.py`
- `docs/architecture/workstream_surface_inventory.md`
- `docs/reports/task_745_project_surface_inventory/task745_project_surface_inventory.csv`
- `docs/reports/task_745_project_surface_inventory/task745_project_surface_inventory_summary.md`
- `docs/reports/task_745_project_surface_inventory/task_745_project_surface_inventory.md`
- `docs/reports/task_745_project_surface_inventory/task_745_decision.csv`
- `docs/reports/task_745_project_surface_inventory/task_745_pass_fail_matrix.csv`

## Validation Commands

```powershell
python scripts\project_surface_inventory.py
python -m py_compile scripts\project_surface_inventory.py
python scripts\task_registry_validate.py
```
