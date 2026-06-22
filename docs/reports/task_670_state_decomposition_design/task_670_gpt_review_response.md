# Task670 GPT Review Response

- captured_via: Chrome ChatGPT
- tab: 1. 코딩/투자
- source_type: external_model_interpretation
- use_rule: Review only. Local artifacts decide acceptance.

## Summary

GPT judged the six layers as a useful skeleton but not firm-grade state decomposition.

The main problem is not only the playbook labels. The problem is compressing different risk, liquidity, sector, catalyst, flow, and portfolio states into one action-style name.

## Required Separate Axes

These axes should not be compressed:

- source integrity
- market and macro context
- liquidity and credit condition
- factor exposure
- sector/theme leadership
- intra-theme leadership
- company catalyst quality
- price/flow acceptance
- risk/crowding
- execution/microstructure
- portfolio/capacity context

## Minimum Viable Decomposition

Implementable core axes with current entry-time data:

1. source_integrity_state
2. market_macro_state
3. liquidity_credit_state
4. theme_leadership_state
5. rotation_participation_state
6. company_catalyst_quality_state
7. price_acceptance_state
8. portfolio_capacity_state

Diagnostic-only axes:

9. factor_exposure_state
10. microstructure_state
11. crowding_risk_state

## Required Task670 Artifacts

- `task670_state_axis_panel.csv`
- `task670_state_purity_report.csv`
- `task670_state_cross_tab_matrix.csv`
- `task670_sparse_cell_report.csv`
- `task670_mdd_axis_exposure_report.csv`
- `task670_capacity_context_report.csv`
- `task670_axis_definition.md`

## Forbidden

- Do not create trading actions in Task670.
- Do not define states from MDD interval outcomes.
- Do not use realized returns to name or rank states.
- Do not compress back into action names such as `confirmation_required`.
- Do not treat source gaps or microstructure missing values as bearish signals.
- Do not promote sparse cells.

## PM Judgment

Task670 should be a state decomposition design and data-structure task, not a strategy promotion task.

