# Task588 - KIS Paper Market Hours Runtime Loop

## Decision Summary

- decision_status=PAPER_RUNTIME_LOOP_RUNNING_OK
- iterations=1
- orders_submitted_total=0
- TRADING_MAX_OPEN_ORDERS defaults to 1 to prevent repeated paper orders.
- Task615 intelligence sidecar may collect sources during the loop, but sidecar_trade_signal_used_flag stays 0.

## Quant Expert Report

The loop runs Task583 signal refresh, Task584 runtime decision, Task585 KIS paper execution, Task587 Slack report, and catalog rebuild in sequence.
Task615 can run as a data-collection sidecar before the trading sequence; its output is not passed into Task584 or Task585.
Order execution is guarded by Task585 active-order checks; an existing pending/submitted/partial order blocks duplicate submission.
Frontend updates are driven by catalog rebuilds rather than raw CSV reads.

## No-Background Decision-Maker Report

미장 개장 중 모의투자 흐름을 반복 실행하는 운영 루프입니다.
이미 미체결 주문이 있으면 새 주문을 막아 과매수를 방지합니다.
프론트엔드에서는 최신 데이터, 전략 판단, 주문 상태, Slack 상태를 계속 확인할 수 있습니다.

## Artifact Manifest

See `artifact_manifest.csv`.
