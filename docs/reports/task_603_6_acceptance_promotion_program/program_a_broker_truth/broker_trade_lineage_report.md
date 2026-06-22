## Problem

T603-6 Program A needs a broker_trade_lineage table that records runtime SELL trade lineage separately from broker truth. Runtime synthetic paper SELL fills must not be promoted to broker truth.

## Evidence

- task_id: T603-6
- current_status: FAIL_BROKER_TRUTH_SELL_FILLS_ZERO
- acceptance_status: FAIL
- runtime_sell_trade_count: 23
- lineage_rows: 23
- broker_truth_sell_fills: 0
- lineage_coverage: 100.0%
- broker_fill_linkage: 0.0%
- required_columns_present_flag: 1
- non_broker_truth_link_count: 0
- table_columns: lineage_id, position_id, signal_id, order_id, broker_order_id, fill_id, broker_fill_id, broker_status, broker_fill_price, broker_fill_timestamp, created_at

## Root Cause

The current DB has no accepted broker truth SELL fills. Existing runtime paper SELL fills are synthetic and were left out of broker truth linkage.

## Fix Candidate

Ingest actual broker/order-status SELL fills with exact broker_order_id, broker_fill_id, or broker event lifecycle_id, then rerun T603-6 reconciliation.

## Acceptance Impact

- FAIL: broker_truth_sell_fills == 0. Synthetic runtime paper SELL fills were not promoted to broker truth.
- Real Capital: FORBIDDEN
