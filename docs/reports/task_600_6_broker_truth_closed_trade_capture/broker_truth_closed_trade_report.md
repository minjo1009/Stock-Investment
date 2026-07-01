# T600-6 Broker Truth Closed-Trade Capture And SELL Lineage Certification

## Decision Summary

- Verdict: FAIL_BROKER_TRUTH_SELL_SOURCE_MISSING
- Strategy acceptance status: NOT_ACCEPTED
- Deployment readiness: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Runtime SELL trade count: 23
- Broker-truth SELL fills: 0
- Broker fill linkage: 0.0%
- Rejected SELL source rows: 46
- What changed: T600-6 now inventories broker/order-status SELL evidence and rejected synthetic/fallback SELL rows without changing strategy logic.
- Next action: Capture actual broker/order-status SELL fills from KIS status/fill polling, then rerun T600-6 and T600-4 exact reconciliation.

## Quant Expert Report

- Data source and source readiness: source DB `trading.db` has 48 accepted BUY order-status source rows but 0 accepted SELL broker-truth fills.
- Exact join keys: EXACT_POSITION_ORDER_FILL_OR_BROKER_EVENT_ID_ONLY. Accepted keys are exact broker fill ID, exact broker order ID, or exact broker event lifecycle ID.
- Leakage audit: labels/outcomes do not enter assignment logic; this task only audits runtime order/fill evidence.
- Split/OOS metrics: not applicable because this is execution evidence certification, not alpha validation.
- Failure decomposition: synthetic/runtime SELL rows and position-delta fallback rows are reported as rejected sources, not promoted to broker truth.
- Cost/slippage stress: not changed. No PnL, execution cost, or strategy claim was updated.
- Remaining blockers: broker_truth_sell_fills must be > 0 and exact linkage must exceed 95%; current status is FAIL_BROKER_TRUTH_SELL_SOURCE_MISSING.

## No-Background Decision-Maker Report

- What happened: we checked whether the system has real broker/order-status evidence for closed SELL trades.
- Why it matters: without broker-truth SELL fills, a profitable backtest or controlled paper closeout still cannot prove executable exits.
- Whether this changes capital/deployment readiness: no. Strategy remains `NOT_ACCEPTED`, deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and real capital remains `FORBIDDEN`.
- Plain-language next step: Capture actual broker/order-status SELL fills from KIS status/fill polling, then rerun T600-6 and T600-4 exact reconciliation.

## Artifact Manifest

- Inputs: source DB, `position_lifecycle`, `fills`, `orders`, `paper_order_execution_events`.
- Outputs: `broker_truth_closed_trade_summary.csv`, `broker_truth_closed_trade_sources.csv`, `broker_truth_closed_trade_mapping.csv`, `broker_truth_closed_trade_rejected_sources.csv`, `task_600_6_decision.csv`.
- Validation commands: `python -m unittest tests.test_task600_6_broker_truth_closed_trade_capture tests.test_task600_4_broker_truth_exit_lifecycle tests.test_task600_5_stop_tp_validation`.
