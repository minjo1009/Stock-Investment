# Task 088 - Evidence Aggregation & Decision Engine

- final_status: WARNING
- total_runs: 32
- trading_days_observed: 1

## Aggregate Metrics
- trading_days_observed: 1
- total_runs: 32
- order_attempts: 0
- submitted_orders: 0
- filled_orders: 0
- cancelled_orders: 0
- partial_fills: 0
- late_fills: 0
- timeout_events: 0
- unknown_events: 0
- reconciliation_checks: 26
- reconciliation_critical_count: 0
- fill_rate: 0.0
- cancel_success_rate: 0.0
- timeout_rate: 0.0
- average_slippage: 0.0
- max_slippage: 0.0
- realized_pnl: 0.0
- paper_pf: 0.0
- paper_mdd: 0.0
- evidence_completeness: 1.0
- eod_reviews_completed: 28
- unresolved_late_fill: 0
- market_order_path_count: 0
- risk_guard_breach_count: 0
- live_env_count: 0
- slippage_drift_flag: False
- data_fresh_ratio: 0.9375
- missing_bar_ratio: 1.0
- signal_generated_runs: 28

## Minimum Sample Criteria
- minimum_trading_days: 5
- minimum_order_attempts: 10
- minimum_filled_orders: 5
- minimum_cancel_events: 1
- minimum_eod_reviews: 5
- minimum_reconciliation_checks: 5

## Decision
- status: WARNING
- warning: HIGH_MISSING_BAR_RATIO
- warning: MINIMUM_SAMPLE_NOT_MET
- warning: NO_CANCEL_SAMPLE
- warning: NO_ORDER_SAMPLE

## Notes
- Current status remains WARNING because minimum sample criteria are not met.
- Critical rule applied: before minimum sample is met, PASS is not allowed.
