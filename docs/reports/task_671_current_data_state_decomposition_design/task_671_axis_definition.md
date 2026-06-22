# Task671 Current-Data State Axis Definition

## Decision

Task671 uses currently available entry-time data only.

Quote/trade/NBBO/microstructure data is excluded because the source is still being collected.

## Implementable Axes

### 1. source_integrity_state

Purpose: separate valid current data from source/as-of gaps.

Allowed inputs:

- `asof_valid_flag`
- `used_for_assignment_flag`
- `return_used_in_assignment_flag`
- `label_used_in_assignment_flag_task661`
- `macro_release_timestamp_repaired_flag`
- `macro_asof_provisional_for_diagnostic_flag`

Forbidden:

- Missing source as bearish.
- Missing label as negative.

### 2. macro_market_state

Purpose: broad market and macro backdrop.

Allowed inputs:

- `macro_overall_state`
- `macro_pressure_score`
- `macro_support_score`
- `broad_market_score`
- `broad_market_stress`
- `breadth_20d`
- `market_ret_20d`

### 3. rates_dollar_credit_liquidity_state

Purpose: decompose macro pressure into rates, dollar, credit, and liquidity drivers.

Allowed inputs:

- `macro_rates_state`
- `macro_dollar_state`
- `macro_credit_state`
- `macro_liquidity_state`
- `liquidity_ratio`
- `rates_exposure`
- `dollar_exposure`
- `credit_exposure`
- `liquidity_exposure`

### 4. theme_leadership_state

Purpose: identify whether a theme is leading, fading, participating, or narrow.

Allowed inputs:

- `theme_id`
- `theme_ret20_prev`
- `theme_breadth20_prev`
- `theme_volume_ratio_prev`
- `theme_regime_state_v4`
- `theme_rank_prev`

### 5. company_catalyst_state

Purpose: separate real catalyst quality from simple information presence.

Allowed inputs:

- `catalyst_quality_tier`
- `catalyst_quality_score`
- `positive_contract_customer_count`
- `positive_backlog_order_count`
- `positive_guidance_up_count`
- `positive_margin_supply_combo_count`
- `content_supply_demand_count`
- `content_guidance_margin_count`

### 6. price_chart_acceptance_state

Purpose: determine whether price and chart behavior support the catalyst.

Allowed inputs:

- `price_acceptance_state`
- `price_acceptance_score`
- `range_pos`
- `intraday_ret_from_open`
- `volume_ratio_prev`
- `near_high60_prev`
- `trend_stack_prev`

Forbidden:

- Calling this microstructure.

### 7. relation_transmission_state

Purpose: preserve whether macro/theme/company/price forces reinforce or conflict.

Allowed inputs:

- `mechanism_relation_state`
- `mechanism_support_count`
- `mechanism_pressure_count`
- `theme_macro_relation_state`
- `conflict_count`
- `support_count`
- `transmission_reason_code`

### 8. portfolio_capacity_state

Purpose: describe max5 slot pressure and concentration using pre-entry candidate context.

Allowed inputs:

- same timestamp candidate count
- same timestamp theme count
- same timestamp relation count
- active slot count in deterministic replay
- active theme concentration
- active relation concentration

Forbidden:

- Realized PnL.
- Forced liquidation.
- Outcome-based displacement labels.

## Diagnostic-Only Auxiliary Axis

### proxy_risk_context

Purpose: record available risk proxies without pretending they are firm-grade crowding or microstructure.

Allowed inputs:

- `vol20_prev`
- `range_pos`
- `theme_rank_prev`
- `volume_ratio_prev`
- `broad_market_stress`

Status:

- diagnostic only
- not a hard gate
- not promotion eligible by itself

## Source Pending

### microstructure_state

Value:

- `SOURCE_PENDING_NOT_USED`

Required flag:

- `microstructure_used_in_assignment = 0`

Forbidden:

- quote/trade/NBBO proxy creation
- treating source pending as bearish
- using chart fields as fake microstructure

## Non-Negotiable

Task671 creates decomposition artifacts only. It does not create new trading actions, priorities, caps, sizing, or backtest promotion candidates.

