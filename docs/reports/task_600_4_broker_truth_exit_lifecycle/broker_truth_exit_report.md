## Decision Summary

- Verdict: FAIL (FAIL_BROKER_TRUTH_SELL_FILLS_ZERO)
- Strategy acceptance status: NOT_ACCEPTED
- Deployment readiness status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- Key metrics: runtime_exit_count=23, broker_truth_sell_fills=0, exit_fill_linkage_coverage=0.0%, closed_positions_with_fill=0.0%
- What changed: exit broker truth lineage mapper and reconciliation now write only broker_fill_id, broker_fill_timestamp, and broker_fill_price onto exact-matched lifecycle rows.
- Next action: Ingest actual broker/order-status SELL fills, then rerun T600-4 reconciliation.

## Runtime Exit Count

- 23

## Broker Exit Count

- 0

## Missing Broker Exit Count

- 23

## Exit Mapping Coverage

- mapped_broker_truth_exits=0
- exit_fill_linkage_coverage=0.0%
- closed_positions_with_fill=0.0%

## Current Status

- FAIL_BROKER_TRUTH_SELL_FILLS_ZERO

## Coverage %

- 0.0%

## Remaining Gaps

- No broker truth SELL fills are present in the current DB; runtime synthetic SELL fills were not counted as broker truth.
- Exit fill linkage coverage is below the >95% acceptance threshold.
- Closed positions with broker fill coverage is below the >95% acceptance threshold.

## Acceptance Impact

- FAIL: broker_truth_sell_fills == 0. No synthetic/runtime paper fill was promoted to broker truth.

## Quant Expert Report

- Data source and source readiness: broker truth SELL fills are accepted only from order status or broker execution-report style sources; runtime synthetic, shadow, simulated, backtest, and position-delta fallback sources are excluded.
- Exact join keys: exit_fill_id to broker_fill_id, exit_order_id to broker_order_id, or exact broker event lifecycle ID. Symbol/date/price/time proximity matching is not used.
- Leakage audit: labels/outcomes do not enter assignment logic; this task only links exit fill lineage.
- Split/OOS metrics: not applicable to execution lineage integration.
- Failure decomposition: missing or non-unique exact broker truth links remain unmapped and are reported.
- Cost/slippage stress where PnL changed: not applicable; T600-4 does not alter realized PnL or exit prices.
- Remaining blockers: broker truth SELL source availability if broker_truth_sell_fills is zero.

## No-Background Decision-Maker Report

- What happened: runtime paper exits exist, but the system now separately checks whether real broker/order-status SELL fill evidence is attached.
- Why it matters: paper runtime exits cannot be treated as broker truth.
- Whether this changes capital/deployment readiness: no; deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY and Real Capital remains FORBIDDEN.
- Plain-language next step: Ingest actual broker/order-status SELL fills, then rerun T600-4 reconciliation.

## Artifact Manifest

- broker_truth_exit_sources.csv
- broker_truth_exit_mapping.csv
- broker_truth_exit_summary.csv
- task_600_4_decision.csv
- artifact_manifest.csv
