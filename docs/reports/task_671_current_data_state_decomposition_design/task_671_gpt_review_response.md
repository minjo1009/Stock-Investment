# Task671 GPT Review Response

- captured_via: Chrome ChatGPT
- tab: 1. 코딩/투자
- source_type: external_model_interpretation
- use_rule: Review only. Local artifacts decide acceptance.

## Summary

GPT agreed with the correction. Task671 must use currently available data only.

Quote/trade/NBBO/microstructure data must be excluded from current state axes. It should only be recorded as `SOURCE_PENDING_NOT_USED`.

## Implementable Axes

1. `source_integrity_state`
2. `macro_market_state`
3. `rates_dollar_credit_liquidity_state`
4. `theme_leadership_state`
5. `company_catalyst_state`
6. `price_chart_acceptance_state`
7. `relation_transmission_state`
8. `portfolio_capacity_state`

## Diagnostic-Only

`proxy_risk_context` may be created from currently available proxy fields, but it must remain diagnostic-only.

Allowed proxy inputs:

- `vol20_prev`
- `range_pos`
- `theme_rank_prev`
- `volume_ratio_prev`
- `broad_market_stress`

It must not be called firm-grade crowding.

## Source Pending

The following are not used:

- quote/trade/NBBO microstructure
- spread
- order-book imbalance
- trade participation
- real-time liquidity depth
- execution slippage from quotes/trades

Required flags:

- `microstructure_state = SOURCE_PENDING_NOT_USED`
- `microstructure_used_in_assignment = 0`

## Required Artifacts

- `task671_state_axis_panel.csv`
- `task671_axis_definition.md`
- `task671_state_purity_report.csv`
- `task671_cross_axis_matrix.csv`
- `task671_sparse_cell_report.csv`
- `task671_forbidden_input_audit.csv`

## Forbidden

- Do not create microstructure proxies.
- Do not treat `SOURCE_PENDING_NOT_USED` as bearish.
- Do not rename states using realized returns.
- Do not create states from MDD outcomes.
- Do not use symbol/theme blacklists.
- Do not use proxy risk as a hard gate.
- Do not perform backtest action mapping in Task671.

