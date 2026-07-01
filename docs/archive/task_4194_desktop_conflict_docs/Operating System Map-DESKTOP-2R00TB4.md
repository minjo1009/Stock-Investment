---
tags:
  - ops
  - research-governance
---

# Operating System Map

## Current Status Pointer

- Operating state: [Project Operating State](../../operating_system/project_operating_state.md)
- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

This map is a rule/navigation layer. It is not strategy acceptance, deployment readiness, or broker truth.

## Governing Rules

- [Project Operating State](../../operating_system/project_operating_state.md)
- [Goal Operating Cycle](../../operating_system/goal_operating_cycle.md)
- [Task Report Standard](../../report_standard.md)
- [Team Charter](../../ownership/team_charter.md)
- [Module Ownership Map](../../ownership/module_ownership_map.md)
- [Subagent Packet Standard](../../ownership/subagent_packet_standard.md)

## Registries

- [Task Registry](../../../tasks/task_registry.csv)
- [Archive Candidate Registry](../../../tasks/archive_candidate_registry.csv)

## Required Decision Checks

- Objective, target metrics, forbidden actions, available raw sources, missing raw sources.
- Owner team and reviewer team.
- Artifact locations and validation commands.
- Completion and failure criteria.

## Non-Negotiable Quant Rules

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback.
- Missing labels are never negatives.
- Missing raw sources are reported, not approximated.
- Labels and outcomes are evaluation-only and must not enter assignment logic.
- Deployment claims require live-source readiness.

## Validation Commands

```powershell
python scripts/task_registry_validate.py
python scripts/codeowners_coverage_validate.py
python scripts/governance_completion_audit.py
```

Validation success does not modify strategy acceptance status.

## DB Management Program

- Report: `docs/reports/task_3601_3640_db_management_program/task_3601_3640_db_management_program.md`
- Contracts: `docs/db/DB_TOPOLOGY.md`, `docs/db/SCHEDULER_SEMANTICS.md`
- Current conclusion: DB management tooling exists; source freshness and scheduler recurrence remain blockers.

## DB Loop Contract Schema

- Report: `docs/reports/task_3641_3660_db_loop_contract_schema/task_3641_3660_db_loop_contract_schema.md`
- Status: loop contracts installed in DB; actual source loops still need receipt/lineage implementation.

