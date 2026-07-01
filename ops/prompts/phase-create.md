# Phase Create Prompt

## Required Phase View

Every phase must start from this view:

```text
Phase ID:
Layer Scope:
Phase Type:
Primary Workstream:
Title:
```

Use this title shape:

```text
PHASE-## [Layer Scope] [Phase Type] Primary Workstream - Exit State
```

Good examples:

- `PHASE-13 [GOV] [DOCS_GOVERNANCE] Knowledge Surfaces - Canonical Registry Enforced`
- `PHASE-12 [L0-L4] [REALTIME_RECOVERY] Collector Backfill Recovery - Currentness Audited`
- `PHASE-14 [L1-L2] [L1_L2_HANDOFF] Newswire Packets To Features - Diagnostic Handoff Ready`

## Phase vs Task

- A phase is a sequencing and handoff plan.
- A task is the implementation and validation unit.
- A phase should define task order, exit criteria, blockers, and handoff.
- A task should define target files, acceptance criteria, validators, and closeout artifacts.

## Required Fields

- Phase ID
- Layer Scope
- Phase Type
- Primary Workstream
- Objective
- Why This Phase Exists
- Entry Conditions
- Scope
- Out of Scope
- Deliverables
- Task Inventory
- Execution Order
- Exit Criteria
- Risks
- Handoff
- Safety Boundary

## Creation Rules

- Create a phase when several tasks need ordered execution or handoff.
- Do not create a phase for a single file edit that fits one task.
- Do not create phases with vague exit states such as cleanup done or system improved.
- Every task in the phase inventory must have a layer, work type, expected output, and validator.

## Safety Boundary

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- Missing or stale data is `UNKNOWN_OR_BLOCKER`, never negative evidence.
