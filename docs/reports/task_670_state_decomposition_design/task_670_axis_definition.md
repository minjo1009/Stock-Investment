# Task670 State Axis Definition

## Decision

The original six layers are not enough for firm-grade state decomposition.

Task670 must preserve separate axes before any playbook action or backtest wrapper is created.

## Core Axes

### 1. source_integrity_state

Purpose: separate usable evidence from source gaps.

Allowed inputs:

- as-of validity flags
- source availability flags
- assignment-use flags

Forbidden:

- Treating missing data as bearish.
- Treating source gaps as negative labels.

### 2. market_macro_state

Purpose: broad risk appetite and macro pressure.

Allowed inputs:

- macro_overall_state
- macro_pressure_score
- macro_support_score
- broad_market_score
- broad_market_stress
- breadth_20d
- market_ret_20d

### 3. liquidity_credit_state

Purpose: funding, credit, dollar, rates, and liquidity pressure.

Allowed inputs:

- macro_rates_state
- macro_dollar_state
- macro_credit_state
- macro_liquidity_state
- liquidity_ratio
- rates_exposure
- dollar_exposure
- credit_exposure
- liquidity_exposure

### 4. theme_leadership_state

Purpose: identify theme leadership, fading, narrow leadership, and participation.

Allowed inputs:

- theme_id
- theme_ret20_prev
- theme_breadth20_prev
- theme_volume_ratio_prev
- theme_regime_state_v4
- theme_rank_prev

### 5. rotation_participation_state

Purpose: distinguish broad risk-on, broad risk-off, healthy rotation, defensive rotation, and narrow leadership.

Allowed inputs:

- market_macro_state
- theme_leadership_state
- theme breadth
- theme volume
- broad market breadth

Forbidden:

- Defining rotation from realized strategy returns.

### 6. company_catalyst_quality_state

Purpose: separate real catalyst quality from simple content presence.

Allowed inputs:

- catalyst_quality_tier
- catalyst_quality_score
- positive_contract_customer_count
- positive_backlog_order_count
- positive_guidance_up_count
- positive_margin_supply_combo_count
- content_supply_demand_count
- content_guidance_margin_count

### 7. price_acceptance_state

Purpose: determine whether price and flow accepted the catalyst.

Allowed inputs:

- price_acceptance_state
- price_acceptance_score
- range_pos
- intraday_ret_from_open
- volume_ratio_prev
- near_high60_prev
- trend_stack_prev

### 8. portfolio_capacity_state

Purpose: capture max5 slot pressure, same-theme concentration, same-relation concentration, and displacement risk.

Allowed inputs:

- entry timestamp candidate set
- active relation concentration
- active theme concentration
- slot availability
- accepted/rejected allocation audit

Forbidden:

- Forced early liquidation in Task670.
- Using realized PnL to decide capacity state.

## Diagnostic-Only Axes

### 9. factor_exposure_state

Purpose: separate duration, high beta, quality, cyclical, and funding-sensitive exposures.

Status: diagnostic until factor exposure definitions are validated.

### 10. microstructure_state

Purpose: execution quality and fragile tape detection.

Status: diagnostic because current microstructure columns have weak variation and historical coverage limitations.

### 11. crowding_risk_state

Purpose: detect crowding, overextension, and fragile winners.

Status: diagnostic unless based on pre-entry features only.

Forbidden:

- Defining crowding from later drawdown.
- Defining crowding from losing trades.

## Non-Negotiable Rule

Task670 must not map these axes to trading actions. It only builds the decomposition structure and audits state quality.

