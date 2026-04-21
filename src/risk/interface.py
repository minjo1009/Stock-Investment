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

        RiskDecision semantics:
        - ALLOW: 신호를 그대로 허용한다.
        - BLOCK: 해당 신호를 거래 금지한다.
        - REDUCE: 신호는 유효하지만 축소가 필요함을 표시한다.
        - RiskDecision은 주문 지시가 아니라 판단 결과 계약이다.
        - risk_flags는 canonical taxonomy 값만 사용한다.

        - signal + market snapshot + account/position을 함께 참조할 수 있다.
        - Risk 호출 전 평가 가능 여부를 점검한다(`is_risk_evaluable`).
        - account=None은 foundation/paper 단계에서만 허용한다.
        - position=None은 flat 상태로 간주해 허용한다.
        - market_snapshot.data_fresh=False(stale)이면 Risk 평가를 금지한다.
        - signal symbol의 필수 feature key 누락 또는 값(None) 존재 시 Risk 평가를 금지한다.
        - 주문 실행 금지, 신규 신호 생성 금지.
        """
        ...
