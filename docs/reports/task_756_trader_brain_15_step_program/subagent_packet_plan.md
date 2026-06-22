# Task756 Subagent Packet Plan

Use bounded packets from `docs/ownership/subagent_packet_standard.md`.

## Packet 1

Objective: Task757 brain dependency DAG and supersession audit.
Owner Team: Research Governance.
Reviewer Team: Backtest & Simulation Infra.
Read Scope: Task727-742 source files, reports, tests, registry rows.
Write Scope: `docs/reports/task_757_brain_dependency_dag_supersession/`.
Forbidden Actions: no code edits, no task file deletion, no strategy/deployment claim.
Validation Command: `python scripts/trader_brain_program_validate.py`.
Validation Authority: Research-only governance validation.

## Packet 2

Objective: Task758 L1 evidence contract and context retention.
Owner Team: Data & Market Microstructure.
Reviewer Team: Research Governance.
Read Scope: Task722, Task731, Task735 reports and source router code.
Write Scope: `docs/reports/task_758_l1_evidence_contract/`.
Forbidden Actions: no source family blanket block, no source-to-trade jump.
Validation Command: `python -m unittest tests.test_task731_source_information_router`.
Validation Authority: Research-only source routing validation.

## Packet 3

Objective: Task761 Task742-to-Task729 adapter contract.
Owner Team: Backtest & Simulation Infra.
Reviewer Team: Research Governance + Regime Research.
Read Scope: Task742 packets, Task728 contract, Task729 interaction engine reports/code.
Write Scope: `docs/reports/task_761_task742_to_task729_adapter_contract/`.
Forbidden Actions: no assignment output, no outcome fields, no backtest eligibility.
Validation Command: `python -m unittest tests.test_task728_five_layer_interaction_logic_contract tests.test_task729_five_layer_interaction_engine_application`.
Validation Authority: Research-only interaction validation.
