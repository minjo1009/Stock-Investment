# Task773 Implementation Handoff Packet

Objective: Implement or validate the Task773 attention budget contract without expanding input scope.

Owner Team: Backtest & Simulation Infra

Reviewer Team: Research Governance + Data & Market Microstructure

Read Scope:

- `docs/reports/task_773_attention_budget_contract/`
- `docs/reports/task_783_institutional_trader_panel_contract/`
- `docs/reports/task_784_macro_politics_filter_contract/`
- `docs/reports/task_785_economic_cycle_liquidity_contract/`
- `docs/reports/task_786_semiconductor_ai_infra_contract/`
- `docs/reports/task_787_space_defense_industrial_contract/`
- `docs/reports/task_788_backend_data_budget_contract/`
- `docs/reports/task_789_source_sufficiency_state_contract/`
- `docs/reports/task_790_cross_expert_conflict_arbitration/`

Write Scope:

- Future task-specific validator or contract implementation files only.

Required Outputs:

- attention packet schema validator
- sufficiency state validator
- forbidden-output audit
- source-gap preservation check
- validation report

Forbidden Actions:

- No buy/sell output.
- No rank or global top list.
- No score or hidden alpha total.
- No actual sizing or allocation.
- No backtest execution.
- No backtest eligibility assignment.
- No outcome label assignment.
- No symbol/date/price/time fallback matching.
- No missing-to-negative conversion.

Validation Authority:

GOVERNANCE_HEALTH and RESEARCH_ONLY only. PASS does not mean strategy acceptance, deployment readiness, source completeness, broker truth, or real-capital permission.

Next Safe Work:

Create Task792-Task801 relationship graph contracts before controlled Task773 validator implementation. Do not connect the validator to strategy selection or execution.
