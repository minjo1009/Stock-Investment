# Task744 Project Operating System Canonicalization

## Decision Summary

- Verdict: `PROJECT_OPERATING_SYSTEM_BASELINE_CREATED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed: project context bootstrap, canonical workstream map, subagent routing, project management system, and repaired project skill/AGENTS rules.
- Next action: classify untracked `src/` and `tests/` into canonical, experiment, archive, and local-only groups before further feature work.

## Quant Expert Report

### Data Source And Source Readiness

This task used repository-native governance inputs:

- `AGENTS.md`
- `skills/skill.md`
- `docs/operating_system/goal_operating_cycle.md`
- `docs/ownership/current_operating_model.md`
- `docs/ownership/module_ownership_map.md`
- `docs/ownership/subagent_packet_standard.md`
- `docs/architecture/brain_layer_map.md`
- `docs/contracts/task_registry_contract.md`
- `tasks/task_registry.csv`

No market data, labels, outcomes, PnL, broker data, or live source claims were used.

### Exact Join Keys

Not applicable. This is a project operating-system task.

### Leakage Audit

No strategy logic was changed.

No backtest or allocation output was produced.

No source interpretation or trading brain result was promoted.

### What Changed

| File | Purpose |
| --- | --- |
| `AGENTS.md` | Restored readable repo working rules and required read order. |
| `skills/skill.md` | Restored top-level project operating skill. |
| `docs/operating_system/project_context_bootstrap.md` | New first-read file for future Codex sessions. |
| `docs/operating_system/project_management_system.md` | New operating-system control document. |
| `docs/architecture/canonical_workstream_map.md` | New functional canonical map. |
| `docs/ownership/subagent_roster_and_routing.md` | New subagent/team/skill routing map. |
| `tasks/task_registry.csv` | Added Task744 registry row. |

### Brain Layer Review

The brain architecture remains:

```text
source evidence -> primitive fact -> economic meaning -> relation edge -> candidate bundle -> slot decision
```

Task742 remains the current practical economic meaning candidate, but it is review-only and not a trading signal.

The immediate risk is not the idea of the brain. The risk is unmanaged context:

- too many task variants
- untracked code and tests
- generated panels mixed into reports
- broken/unclear entry documents
- no single context bootstrap

Task744 addresses the management layer, not trading performance.

### Remaining Blockers

| Blocker | Why It Matters | Next Action |
| --- | --- | --- |
| `src/` has hundreds of untracked files | Unknown canonical code surface | Build canonical/experiment/archive classification table. |
| `tests/` has hundreds of untracked files | Test suite is not a controlled quality gate | Select canonical tests per workstream. |
| Several ownership docs contain mojibake in names | Readability and routing risk | Repair owner names only after a name/source decision. |
| Large historical artifacts remain local | Git and context overload risk | Manifest and classify before any move. |
| Brain task supersession is incomplete | Downstream could pick the wrong layer | Add supersession notes after selecting canonical subset. |

## No-Background Decision-Maker Report

The project was becoming hard to control because too much was added without one operating entry point.

This task creates that entry point.

Future work should start from:

1. `project_context_bootstrap.md`
2. `canonical_workstream_map.md`
3. `brain_layer_map.md`
4. `subagent_roster_and_routing.md`
5. `tasks/task_registry.csv`

This does not make the strategy accepted.

It makes future work less likely to lose context.

## Artifact Manifest

- `AGENTS.md`
- `skills/skill.md`
- `docs/operating_system/project_context_bootstrap.md`
- `docs/operating_system/project_management_system.md`
- `docs/architecture/canonical_workstream_map.md`
- `docs/ownership/subagent_roster_and_routing.md`
- `docs/reports/task_744_project_operating_system_canonicalization/task_744_project_operating_system_canonicalization.md`
- `docs/reports/task_744_project_operating_system_canonicalization/task_744_decision.csv`
- `docs/reports/task_744_project_operating_system_canonicalization/task_744_pass_fail_matrix.csv`

## Validation Commands

```powershell
python scripts\task_registry_validate.py
```
