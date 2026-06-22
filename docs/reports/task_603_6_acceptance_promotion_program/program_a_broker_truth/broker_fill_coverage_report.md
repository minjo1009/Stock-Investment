## Problem

Broker fill coverage must be measured from broker/order-status SELL evidence only. Symbol, date, price, or time proximity is not accepted as linkage.

## Evidence

- broker_truth_sell_fills: 0
- broker_fill_linked_rows: 0
- missing_broker_fill_count: 23
- broker_fill_linkage: 0.0%
- inferred_matching_used_flag: 0
- proximity_fallback_used_flag: 0
- non_broker_truth_link_count: 0

## Root Cause

The current DB has no accepted broker truth SELL fills. Existing runtime paper SELL fills are synthetic and were left out of broker truth linkage.

## Fix Candidate

Ingest actual broker/order-status SELL fills with exact broker_order_id, broker_fill_id, or broker event lifecycle_id, then rerun T603-6 reconciliation.

## Acceptance Impact

- FAIL: broker_truth_sell_fills == 0. Synthetic runtime paper SELL fills were not promoted to broker truth.
- Strategy acceptance remains NOT_ACCEPTED; deployment remains diagnostic-only until broker truth SELL fills are available and linked.
