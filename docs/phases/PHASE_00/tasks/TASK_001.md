# TASK_001 - Orchestrated Task

## Metadata

- task_id: TASK_001
- phase_id: PHASE_00
- command_id: CMD_8CA69FBF0F57
- owner_agent: Architecture Orchestrator
- sub_agents: []
- required_skill: subagent-artifact-governance
- status: classified
- safety_level: normal
- requires_user_execution: false

## Original Command

Normalize architecture harness storage rules and update orchestrator continuity docs

## Output Locations

- handoff: `docs/phases/PHASE_00/reports/TASK_001/handoff.md`
- summary: `docs/phases/PHASE_00/reports/TASK_001/summary.md`
- validation: `docs/phases/PHASE_00/reports/TASK_001/validation.md`
- context_pack: `docs/phases/PHASE_00/reports/TASK_001/context_pack.md`
- decision: `docs/phases/PHASE_00/decisions/TASK_001_decision.md`

## File Change Boundary

- allowed roots: `docs/operating_system/`, `docs/phases/`, task-approved files only
- forbidden by default: broker/API calls, order workflows, DB mutation, strategy behavior changes, file moves/deletes

## Acceptance Criteria

- Task result is written to the phase report folder.
- Continuity facts are recorded through `complete-task`.
- External execution, if needed, is requested with PowerShell commands instead of auto-running.
