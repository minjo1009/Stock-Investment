# Task615 - Realtime Intelligence Sidecar Runtime Integration

## Decision Summary

- decision_status=INTELLIGENCE_SIDECAR_COLLECTION_OK
- event_store_rows=12186
- sidecar_trade_signal_used_flag=0
- strategy_acceptance_status=NOT_ACCEPTED
- real_capital_status=FORBIDDEN

## Quant Expert Report

Task615 runs the Task614 source collector as a runtime sidecar before or beside paper/autotrade execution.
The sidecar writes a persistent event store and status artifacts only; no source event is passed into order submission or position sizing.
Cadence is controlled by TRADING_INTELLIGENCE_SIDECAR_MIN_INTERVAL_SEC to avoid slowing the trading loop.

## No-Background Decision-Maker Report

The trading loop now has a separate intelligence collector.
It stores news/filing/policy style evidence for later backtests.
It does not make trades and does not approve the strategy.

## Artifact Manifest

See `artifact_manifest.csv`.
