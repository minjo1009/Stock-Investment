"""Market/Data layer interfaces.

계약 요약:
- 시장 데이터 수집/정제 책임.
- 주문 생성 및 포지션 변경 금지.
"""

from __future__ import annotations

from typing import Literal, Protocol

from common.models import MarketDataSnapshot


class MarketDataPort(Protocol):
    def load_market_snapshot(
        self,
        market: Literal["KR", "US"],
        env: Literal["paper", "live"],
    ) -> MarketDataSnapshot:
        """수집/정제된 시장 snapshot 계약 객체를 반환한다."""
        ...
