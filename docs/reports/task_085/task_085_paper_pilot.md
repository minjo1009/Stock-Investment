# Task 085 - Paper Pilot Execution Plan & Operational Validation

## 1. Execution Summary
- strategy: D_PORTFOLIO_SECTOR_FILTER
- db_path: trading.db
- total_runs: 29
- total_orders: 0
- filled_orders: 0
- cancelled_orders: 0

## 2. Operational Metrics
- fill_rate_pct: 0.0
- cancel_rate_pct: 0.0
- timeout_rate_pct: 0.0
- unknown_rate_pct: 0.0
- partial_fill_rate_pct: 0.0
- late_fill_count: 0
- reconciliation_mismatch_rate_pct: 0.0
- reconciliation_critical_count: 0
- retry_count: 0

## 3. Failure Cases
- cancel_failure: 0
- partial_fill_then_cancel: 0
- timeout_events: 0
- timeout_after_late_fill: 0
- api_error_or_failed: 0
- unknown_status: 0

## 4. Slippage Analysis
- sample_count: 0
- avg_slippage: None
- median_slippage: None
- max_slippage: None
- note: requested_price is not persistently stored in schema; slippage samples may be sparse.

## 5. Backtest vs Reality Gap
- backtest_pf_s4: 1.698872
- paper_real_pf_reference: None
- backtest_fill_rate_s4: 50.649351
- paper_fill_rate: 0.0
- fill_rate_gap_pctp: -50.649351
- backtest_sharpe_s4: 1.140162

## 6. Stability Analysis
- system_runs_without_crash: True
- cancel_reconcile_loop_health: ok
- unknown_free_operation: True
- db_state_alignment: True

## 7. Final Decision
- status: WARNING
- critical_answer_q1: WARNING
- critical_answer_q2: WARNING
- reason: Operational path works but drift/mismatch risk remains.

## Guard Validation
- daily_loss_limit_configured: False
- max_exposure_cap_configured: False
- symbol_cap_configured: False
- unknown_order_halt_enabled: True
- kill_switch_enabled: True
