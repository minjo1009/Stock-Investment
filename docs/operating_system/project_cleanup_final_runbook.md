# Project Cleanup Final Runbook

## Purpose

This runbook closes the five-pass cleanup loop.

It tells future Codex sessions:

```text
Where to start.
What is official.
What can be changed.
What must not be overclaimed.
What development can resume next.
```

## Standing Status

| Area | Status |
| --- | --- |
| Strategy | `NOT_ACCEPTED` |
| Deployment | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |
| Real capital | `FORBIDDEN` |
| GPT/Chrome | Review-only |
| Test success | Does not change acceptance |
| Inventory complete | Classification only |
| Governance complete | Does not mean research complete |

## Required Read Order

Use low-token context loading by default.

Minimum start:

1. `docs/operating_system/project_operating_state.md`
2. Latest relevant task report or file being edited

Open detailed maps only when the task touches that domain.

Full read order for broad governance, handoff, or ambiguous cross-domain work:

1. `docs/operating_system/project_context_bootstrap.md`
2. `docs/operating_system/project_operating_state.md`
3. `docs/architecture/project_status_authority_matrix.md`
4. `docs/ownership/current_operating_model.md`
5. `docs/architecture/canonical_workstream_map.md`
6. `docs/architecture/brain_layer_map.md`
7. `docs/architecture/workstream_surface_inventory.md`
8. `docs/architecture/src_canonicalization_map.md`
9. `docs/architecture/test_validation_canonicalization_map.md`
10. `docs/architecture/skill_md_subagent_canonicalization_map.md`
11. `docs/ownership/subagent_roster_and_routing.md`
12. `tasks/task_registry.csv`
13. Latest relevant task report

## Domain-Triggered Context

| Task Touches | Open This |
| --- | --- |
| `src/` | `docs/architecture/src_canonicalization_map.md` |
| `tests/`, validation, CI, PASS wording | `docs/architecture/test_validation_canonicalization_map.md` |
| skills, MD, GPT, subagents | `docs/architecture/skill_md_subagent_canonicalization_map.md` |
| acceptance, deployment, real capital | `docs/architecture/project_status_authority_matrix.md` |
| multi-domain governance | full read order above |

## Five-Pass Cleanup Results

| Pass | Task | Output | What It Means | What It Does Not Mean |
| --- | --- | --- | --- | --- |
| 1/5 | Task745 | Project surface inventory | Formal repo surface is mapped | Validation complete |
| 2/5 | Task746 | Source-code canonicalization map | `src/` code is classified | Package code is production-ready |
| 3/5 | Task747 | Test validation authority map | Test PASS meanings are separated | Strategy accepted |
| 4/5 | Task748 | Skill/MD/subagent canonicalization | Operating docs and GPT/subagent rules are aligned | Research brain complete |
| 5/5 | Task749 | Final runbook and closeout | Future work has a starting path | Deployment ready |

## Authority Rules

```text
PASS != Acceptance
Inventory != Validation
Governance != Deployment
Research != Execution
Active != Canonical
Canonical candidate != Approved
Canonical candidate != Production-ready
GPT review != Source-of-truth
Governance completion != Research completion
```

## Architecture Snapshot

The intended research brain remains:

```text
L1 Source evidence
-> L2 Primitive fact and economic meaning
-> L3 Relation edge
-> L4 Candidate bundle
-> L5 Slot or execution decision
-> Backtest/deployment gate
```

Current active brain work is Task727-742 family.

Important:

```text
Current active != approved architecture
Task727-742 active != strategy accepted
```

## Change Control

Before changing code, tests, skills, or reports:

1. Identify owner team and reviewer team.
2. Identify read scope and write scope.
3. Check whether touched code is:
   - `canonical_package_candidate`
   - `owner_review_package_candidate`
   - `active_task_code_review`
   - `supporting_task_code_review`
   - `historical_task_code_review`
4. Check validation authority:
   - `PACKAGE_HEALTH`
   - `GOVERNANCE_HEALTH`
   - `RESEARCH_ONLY`
   - `EVIDENCE_ONLY`
   - `EXECUTION_HEALTH`
   - `ACCEPTANCE_EVIDENCE_REVIEW`
   - `DATA_HEALTH`
   - `REPORTING_HEALTH`
5. State what PASS means.
6. State what PASS does not mean.
7. Update report, manifest, and registry when the task changes active state.

## Locked Development Resume Order

Do not resume with new alpha factors, ranking models, selection models, or execution models.

Resume in this order:

1. Canonical Package Extraction
   - Review the 33 Task746 package candidates.
   - Map exact package-health tests.
   - Decide which modules become stable package code.
2. Historical Isolation
   - Keep 346 historical task-code files from being imported as current engines.
   - Add supersession notes before reuse.
3. Brain Stabilization
   - Stabilize Task727-742 boundaries.
   - Lock L1/L2/L3 contracts before L4/L5 trading decisions.
4. Governance Consistency Audit
   - Confirm skills, subagents, registry, tests, and maps say the same thing.
5. Acceptance Blocker Work
   - Return to Task599/T600 acceptance blockers only after steps 1-4.

New alpha work comes after the above.

## Subagent Rule

Every subagent packet must include:

```text
Objective:
Owner Team:
Reviewer Team:
Read Scope:
Write Scope:
Inputs:
Required Outputs:
Forbidden Actions:
Validation Command:
Validation Authority:
Report Requirement:
```

Workers must have disjoint write scopes.

Explorers are read-only.

GPT/Chrome is review-only.

## GPT/Chrome Rule

GPT/Chrome may review:

- overclaims
- missing evidence
- unclear architecture
- weak decomposition
- validation wording

GPT/Chrome may not decide:

- strategy acceptance
- deployment readiness
- broker truth
- raw source correctness
- PnL validity
- buy/sell/sizing

Every GPT finding must become repo-native work:

```text
finding -> owner -> artifact -> validation -> authority -> registry/report
```

## Required Closeout Footer

Every future validation or closeout should include:

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```

## Current Safe Next Task

The safe next task after Task749 is:

```text
Task750 Canonical Package Extraction Plan
```

Forbidden as immediate next task:

- new alpha search
- new ranking model
- new selection model
- new execution model
- strategy acceptance promotion
- deployment readiness promotion
