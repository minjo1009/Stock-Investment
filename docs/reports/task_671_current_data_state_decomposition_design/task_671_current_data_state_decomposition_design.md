# Task671 Current-Data State Decomposition Design

## Decision Summary

- Verdict: `CURRENT_DATA_STATE_DECOMPOSITION_DESIGN_READY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

Task671 must use currently available entry-time data only. Microstructure is excluded because quote/trade/NBBO collection is still in progress.

## Quant Expert Report

Task670's broader decomposition included microstructure as diagnostic-only. The user corrected this. Current implementation must not include microstructure in state axes, even diagnostically, because the source is incomplete.

### Implementable Current-Data Axes

1. `source_integrity_state`
2. `macro_market_state`
3. `rates_dollar_credit_liquidity_state`
4. `theme_leadership_state`
5. `company_catalyst_state`
6. `price_chart_acceptance_state`
7. `relation_transmission_state`
8. `portfolio_capacity_state`

### Diagnostic-Only Auxiliary Axis

9. `proxy_risk_context`

This is not firm-grade crowding. It is a limited proxy from currently available fields.

### Excluded Source-Pending Axis

`microstructure_state = SOURCE_PENDING_NOT_USED`

`microstructure_used_in_assignment = 0`

### Required Implementation Artifacts

- `task671_state_axis_panel.csv`
- `task671_axis_definition.md`
- `task671_state_purity_report.csv`
- `task671_cross_axis_matrix.csv`
- `task671_sparse_cell_report.csv`
- `task671_forbidden_input_audit.csv`

## No-Background Decision-Maker Report

사장님 지적이 맞습니다.

호가/체결 데이터는 아직 모으는 중이므로 지금 상태 분해 축에 넣으면 안 됩니다.

지금은 현재 가진 macro, liquidity, theme, catalyst, price/chart, relation, portfolio capacity 데이터만으로 갑니다.

microstructure는 `SOURCE_PENDING_NOT_USED`로만 기록하고 매매 판단에 쓰지 않습니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| current_data_only_design | 1 | yes | no pending quote/trade/NBBO source used |
| implementable_axes_defined | 1 | 8 | current entry-time data axes |
| proxy_risk_context_diagnostic_only | 1 | diagnostic_only | no hard gate |
| microstructure_excluded | 1 | SOURCE_PENDING_NOT_USED | source pending not used |
| trading_action_allowed | 0 | design_only | no action mapping in Task671 |
| real_capital_allowed | 0 | forbidden | strategy remains not accepted |

## Artifact Manifest

- `task_671_gpt_review_packet.md`
- `task_671_gpt_review_response.md`
- `task_671_axis_definition.md`
- `task_671_current_data_state_decomposition_design.md`
- `task_671_decision.csv`
- `task_671_pass_fail_matrix.csv`

