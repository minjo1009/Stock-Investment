---
tags:
  - ops
  - research-governance
---

# Operating System Map

## Governing Rules

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
