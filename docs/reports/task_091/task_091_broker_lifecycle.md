# Task 091 - Paper Broker Lifecycle Evidence Gate

## 1. Execution Summary
- total_runs: 11
- runs_with_orders: 0
- runs_with_fills: 0
- runs_with_cancels: 0

## 2. Lifecycle Trace
- submitted_orders: 0
- filled_orders: 0
- cancelled_orders: 0
- unknown_orders: 0
- latest_order_id: None
- latest_order_symbol: None
- latest_order_status: None
- latest_submitted_at: None

## 3. Broker vs Local State Comparison
- reconciliation_total: 7
- reconciliation_success_count: 7
- reconciliation_critical_count: 0
- local_unknown_orders: 0
- broker_local_aligned: True

## 4. Anomalies
- partial_fill_observed: False
- cancel_race_fill_observed: False
- late_fill_count: 0
- market_order_path_count: 0
- loop_non_zero: False

## 5. Fixture List
- written: tests\fixtures\kis\real\order_submit_response.json
- written: tests\fixtures\kis\real\order_status_pending.json
- written: tests\fixtures\kis\real\order_status_filled.json
- written: tests\fixtures\kis\real\order_status_cancelled.json
- written: tests\fixtures\kis\real\fills_response.json

## 6. Decision
- status: WARNING
- answer: NO
- reason: NO_ORDER_SAMPLE
