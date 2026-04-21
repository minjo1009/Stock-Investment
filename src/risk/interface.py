"""Risk layer interfaces.

계약 요약:
- 입력은 RiskInputContext로 고정한다.
- 주문 실행 금지.
"""

from __future__ import annotations

from typing import Protocol

from common.models import RiskDecision, RiskInputContext


class RiskPort(Protocol):
    def evaluate(self, context: RiskInputContext) -> RiskDecision | None:
        """RiskInputContext 기반 리스크 판단 결과를 반환한다.

        - signal + market snapshot + account/position을 함께 참조할 수 있다.
        - account/position은 None일 수 있다(초기 단계 허용).
        - 주문 실행 금지, 신규 신호 생성 금지.
        """
        ...
