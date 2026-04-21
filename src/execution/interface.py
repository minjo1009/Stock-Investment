"""Execution layer interfaces.

계약 요약:
- order_intent -> broker_order/fill_event 처리 책임.
- signal 생성 금지.
- 리스크 override 금지.
"""

from __future__ import annotations

from typing import Protocol

from common.models import BrokerOrder, FillEvent, OrderIntent, RiskDecision


class ExecutionPort(Protocol):
    def build_intent(self, decision: RiskDecision | None) -> OrderIntent | None:
        """리스크 판단 결과를 주문 의도로 해석한다.

        - ALLOW: signal을 그대로 전달하는 intent를 구성할 수 있다.
        - BLOCK: intent를 생성하지 않는다.
        - REDUCE: reduce_factor를 포함한 intent를 구성할 수 있다.
        - quantity는 최종 주문 수량이며 Execution은 계산하지 않는다.
        - 축소 수량 계산은 본 계약 범위에 포함하지 않는다.
        """
        ...

    def submit(self, intent: OrderIntent) -> BrokerOrder:
        """OrderIntent를 제출하고 BrokerOrder 상태를 반환한다."""
        ...

    def cancel(self, order_id: str) -> BrokerOrder:
        """주문 취소 요청 후 상태가 반영된 BrokerOrder를 반환한다."""
        ...

    def get_status(self, order_id: str) -> BrokerOrder:
        """주문 상태를 조회한다. quantity 계산은 수행하지 않는다."""
        ...

    def on_fill(self, fill: FillEvent) -> BrokerOrder:
        """FillEvent를 적용해 주문 상태를 갱신한다.

        허용 상태 정책은 common.models.apply_fill_event contract를 따른다.
        """
        ...
