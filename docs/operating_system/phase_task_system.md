# Phase / Task Operating System

## Purpose
Create one operating model for architecture, research, paper operations, and migration work. Every phase owns tasks, every task owns reports, and every output has an explicit location.

## Phase Contract
Each phase must define:

- `phase_id`
- `objective`
- `scope`
- `non_goals`
- `dependencies`
- `task_list`
- `entry_criteria`
- `exit_criteria`
- `acceptance_tests`
- `output_directory`

## Task Contract
Each task must define:

- `task_id`
- `phase_id`
- `owner_agent`
- `sub_agents`
- `required_skill`
- `input_artifacts`
- `expected_output_artifacts`
- `file_change_boundary`
- `acceptance_criteria`
- `validation_commands`
- `rollback_plan`
- `report_path`

## Canonical Phase Set

| phase | objective | output directory |
|---|---|---|
| PHASE_00 | Governance and operating-system setup | `docs/phases/PHASE_00/` |
| PHASE_01 | Repository classification and architecture normalization | `docs/phases/PHASE_01/` |
| PHASE_02 | Data, features, strategy, and backtest reliability | `docs/phases/PHASE_02/` |
| PHASE_03 | Execution, broker lifecycle, and safety contracts | `docs/phases/PHASE_03/` |
| PHASE_04 | Paper operations, evidence, UI, and monitoring | `docs/phases/PHASE_04/` |
| PHASE_05 | Live pilot readiness gates | `docs/phases/PHASE_05/` |
| PHASE_06 | Scaling, automation, and long-term maintenance | `docs/phases/PHASE_06/` |

## Operating Rules

- A task cannot start unless its phase entry criteria are met.
- A task cannot finish unless its report path exists and validation commands are recorded.
- Reports move under `docs/phases/{phase_id}/reports/{task_id}/` after migration approval.
- Any code-moving task requires a rollback plan before execution.
- Trading behavior changes require a dedicated task and cannot be hidden inside architecture cleanup.

