"""Intelligence/Reporting layer interfaces.

계약 요약:
- 분석/리포트/보고 책임.
- 매매 결정 금지.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class ReportingPort(Protocol):
    def publish(self, summary: Mapping[str, Any]) -> None:
        """리포트/로그/알림 발행 인터페이스."""
        ...

