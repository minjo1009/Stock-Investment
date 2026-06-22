# Sub-Agent Handoff - TASK_001

- created_at: 2026-04-25T06:33:35.375133Z
- phase_id: PHASE_00
- phase_title: Governance and operating-system setup
- owner_agent: Architecture Orchestrator
- required_skill: subagent-artifact-governance
- safety_level: normal
- requires_user_execution: False

## Original Command

Normalize architecture harness storage rules and update orchestrator continuity docs

## Routing Rationale

- routing_scores: `{'PHASE_00': 2, 'PHASE_01': 2, 'PHASE_02': 0, 'PHASE_03': 0, 'PHASE_04': 1, 'PHASE_05': 0, 'PHASE_06': 0}`
- confidence: `2`

## Required Skill

Use `subagent-artifact-governance` and follow the storage rules in `docs/operating_system/harness_manifest.yml`.

## PowerShell Commands For User Execution

- None required at classification time.

## Stop Conditions

- Stop before broker/API execution, order submission/cancel/fill workflows, DB mutation, file move/delete migrations, or trading behavior changes unless explicitly approved.

## Required Handoff Output

- changed files:
- artifacts:
- validation:
- continuity facts:
- skill update proposals:
- unresolved risks:
