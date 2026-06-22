# Task840-Task849 Subagent Packet Plan

Objective: Implement the no-execution backtest harness skeleton and operating discipline before any controlled replay run.

Owner Team: Research Governance

Reviewer Team: Backtest and Simulation Infra + Data and Market Microstructure + Execution and Risk

Read Scope:

- `docs/operating_system/project_operating_state.md`
- `docs/operating_system/backtest_harness_operating_discipline.md`
- `docs/reports/task_836_controlled_adapter_input_builder/adapter_inputs.csv`
- `docs/reports/task_839_controlled_backtest_go_no_go/`
- `docs/architecture/test_validation_canonicalization_map.md`
- `docs/architecture/project_status_authority_matrix.md`

Write Scope:

- Task840 worker: `docs/reports/task_840_backtest_harness_program/`
- Task841 worker: `docs/reports/task_841_backtest_input_manifest_schema/`
- Task842 worker: `docs/reports/task_842_tradable_after_timestamp_contract/`
- Task843 worker: `docs/reports/task_843_market_data_source_gate/`
- Task844 worker: `docs/reports/task_844_replay_config_contract/`
- Task845 worker: `docs/reports/task_845_no_execution_dry_replay_harness/` and `scripts/trader_brain_backtest_dry_replay_harness.py`
- Task846 worker: `docs/reports/task_846_split_oos_cost_slippage_plan/`
- Task847 worker: `docs/reports/task_847_failure_decomposition_schema/`
- Task848 worker: `docs/reports/task_848_harness_artifact_audit_validator/` and `scripts/trader_brain_backtest_harness_artifact_audit.py`
- Task849 worker: `docs/reports/task_849_first_controlled_backtest_go_no_go/`, `scripts/trader_brain_840_849_program_validate.py`, registry and operating-state updates.

Required Outputs:

- Backtest harness operating discipline.
- Backtest input manifest schema and fixture.
- Tradable-after timestamp contract.
- Market data source gate.
- Replay config contract.
- No-execution dry replay harness.
- Split/OOS cost/slippage plan.
- Failure decomposition schema.
- Artifact audit validator.
- Go/no-go closeout for first controlled replay.

Forbidden Actions:

- No price data lookup.
- No trade generation.
- No PnL, return, win rate, drawdown, Sharpe, or portfolio simulation.
- No backtest engine call.
- No runtime or broker integration.
- No buy/sell/rank/score/sizing output.
- No strategy acceptance, deployment readiness, or real-capital permission claim.

Validation Command:

`python scripts/trader_brain_840_849_program_validate.py`

Validation Authority:

GOVERNANCE_HEALTH and RESEARCH_ONLY only. PASS does not mean strategy acceptance, deployment readiness, broker truth completion, source completeness, backtest validity, or real-capital permission.
