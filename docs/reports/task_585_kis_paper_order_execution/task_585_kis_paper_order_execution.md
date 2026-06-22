# Task585 - KIS Paper Order Execution And Lineage

## Decision Summary

- decision_status=ORDER_SUBMITTED_OR_TERMINAL_RECORDED
- order_status=UNKNOWN
- Only PAPER_ORDER_CANDIDATE decisions can submit KIS paper orders.
- Unfilled orders are not shown as fills.

## Quant Expert Report

The execution gate is downstream of Task584 and preserves decision_id as the local client_order_id.
Broker truth fill is recorded only when KIS order status/fill data confirms filled quantity.
Canonical lifecycle events are emitted after order submission and again after broker-confirmed fill, if present.

## No-Background Decision-Maker Report

이번 단계는 실제 모의계좌 주문 실행과 주문 계보 기록입니다.
신호가 없으면 주문을 내지 않고, 주문이 나가도 체결 확인 전에는 체결로 표시하지 않습니다.
프론트엔드에서는 decision_id에서 주문, 체결, lifecycle까지 이어지는 흐름을 확인할 수 있습니다.

## Artifact Manifest

See `artifact_manifest.csv`.
