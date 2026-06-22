# Task828-Task839 Subagent Packet Plan

Objective: Implement a controlled dry adapter path from research-only candidate bundles to validated adapter input rows without executing a backtest.

Owner Team: Research Governance

Reviewer Team: Backtest and Simulation Infra + Data and Market Microstructure + Execution and Risk

Read Scope:

- `docs/operating_system/project_operating_state.md`
- `docs/reports/task_823_candidate_bundle_adapter_contract/`
- `docs/reports/task_826_backtest_adapter_readiness_checklist/`
- `docs/reports/task_827_go_no_go_closeout/`
- `docs/reports/task_813_golden_graph_fixture_pack/`
- `docs/reports/task_821_graph_fixture_corpus_expansion/`
- `docs/architecture/test_validation_canonicalization_map.md`

Write Scope:

- Task828 worker: `docs/reports/task_828_controlled_adapter_program/`
- Task829 worker: `docs/reports/task_829_controlled_adapter_design_contract/`
- Task830 worker: `docs/reports/task_830_adapter_input_schema_contract/`
- Task831 worker: `docs/reports/task_831_source_time_namespace_contract/`
- Task832 worker: `docs/reports/task_832_leakage_guard_validator_design/`
- Task833 worker: `docs/reports/task_833_candidate_bundle_expansion_pack/`
- Task834 worker: `docs/reports/task_834_negative_adapter_fixture_pack/`
- Task835 worker: `docs/reports/task_835_adapter_eligibility_validator/` and `scripts/trader_brain_adapter_eligibility_validate.py`
- Task836 worker: `docs/reports/task_836_controlled_adapter_input_builder/` and `scripts/trader_brain_adapter_input_builder.py`
- Task837 worker: `docs/reports/task_837_adapter_output_audit_report/`
- Task838 worker: `docs/reports/task_838_adapter_dry_run_governance_gate/` and `scripts/trader_brain_adapter_dry_run_gate.py`
- Task839 worker: `docs/reports/task_839_controlled_backtest_go_no_go/`, `scripts/trader_brain_828_839_program_validate.py`, registry and operating-state updates.

Required Outputs:

- Controlled adapter design.
- Adapter input schema.
- Source-time namespace.
- Leakage guard catalog.
- Expanded candidate bundle pack.
- Negative adapter fixtures.
- Eligibility validator.
- Dry adapter input builder.
- Audit report.
- Dry-run governance gate.
- Go/no-go closeout.

Forbidden Actions:

- No buy/sell output.
- No rank or global top list.
- No score or hidden alpha total.
- No actual sizing or allocation.
- No backtest execution.
- No backtest eligibility assignment.
- No runtime or broker integration.
- No symbol/date/price/time fallback matching.
- No missing-to-negative conversion.
- No strategy acceptance claim from test success.

Validation Command:

`python scripts/trader_brain_828_839_program_validate.py`

Validation Authority:

GOVERNANCE_HEALTH and RESEARCH_ONLY only. PASS does not mean strategy acceptance, deployment readiness, broker truth completion, source completeness, backtest validity, or real-capital permission.
