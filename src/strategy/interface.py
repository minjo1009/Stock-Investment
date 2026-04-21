"""Strategy layer interfaces.

계약 요약:
- 입력은 MarketDataSnapshot으로 고정한다.
- 100% 룰 기반 판단 영역.
- broker 호출 금지.
"""

from __future__ import annotations

from typing import Protocol

from common.models import MarketDataSnapshot, SignalEvent


class StrategyPort(Protocol):
    def generate_signal(self, feature_snapshot: MarketDataSnapshot) -> SignalEvent | None:
        """MarketDataSnapshot 입력 계약 기반으로 signal_event를 생성한다.

        - SymbolFeatureSnapshot의 top-level(raw-ish) + features(파생/정규화)를 함께 참조할 수 있다.
        - 최소 표준 feature key가 없는 symbol은 평가 제외(SKIP)할 수 있다.
        - Strategy는 broker 호출이 금지된다.
        """
        ...
