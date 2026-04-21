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
        """리스크 판단 결과로 주문 의도를 구성한다."""
        ...

    def submit(self, intent: OrderIntent, env: str) -> BrokerOrder | None:
        """주문 제출 인터페이스(현재는 시그니처만 정의)."""
        ...

    def poll_fill(self, order: BrokerOrder) -> FillEvent | None:
        """체결 이벤트 수신 인터페이스(현재는 시그니처만 정의)."""
        ...

