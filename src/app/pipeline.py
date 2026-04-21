"""Pipeline skeleton for market -> strategy -> risk -> execution -> reporting.

주의:
- 이 파일은 흐름 구조만 제공한다.
- 실제 매매/리스크/API 로직은 구현하지 않는다.
"""

from __future__ import annotations

from typing import Any, Literal

from common.models import (
    AccountSnapshot,
    PositionSnapshot,
    RISK_INPUT_CONTEXT_VERSION,
    RiskInputContext,
)
from execution.interface import ExecutionPort
from market.interface import MarketDataPort
from reporting.interface import ReportingPort
from risk.interface import RiskPort
from strategy.interface import StrategyPort


MarketCode = Literal["KR", "US"]
RuntimeEnv = Literal["paper", "live"]


def run_pipeline(
    market_port: MarketDataPort,
    strategy_port: StrategyPort,
    risk_port: RiskPort,
    execution_port: ExecutionPort,
    reporting_port: ReportingPort,
    market: MarketCode,
    env: RuntimeEnv,
) -> dict[str, Any]:
    """레이어 호출 순서만 표현하는 최소 파이프라인."""
    market_snapshot = market_port.load_market_snapshot(market, env)
    signal = strategy_port.generate_signal(market_snapshot)

    # 계좌/포지션 동기화 로직은 Phase 01 범위를 벗어나므로 placeholder만 둔다.
    account: AccountSnapshot | None = None
    position: PositionSnapshot | None = None
    decision = None
    if signal is not None:
        risk_input = RiskInputContext(
            signal=signal,
            market_snapshot=market_snapshot,
            account=account,
            position=position,
            context_version=RISK_INPUT_CONTEXT_VERSION,
        )
        decision = risk_port.evaluate(risk_input)

    broker_order = None
    fill = None
    if decision is not None:
        intent = execution_port.build_intent(decision)
        if intent is not None:
            broker_order = execution_port.submit(intent, env)
            if broker_order is not None:
                fill = execution_port.poll_fill(broker_order)

    summary = {
        "market": market,
        "env": env,
        "snapshot_version": market_snapshot.snapshot_version,
        "universe_size": market_snapshot.universe_size,
        "data_fresh": market_snapshot.data_fresh,
        "has_signal": signal is not None,
        "has_decision": decision is not None,
        "has_order": broker_order is not None,
        "has_fill": fill is not None,
    }
    reporting_port.publish(summary)
    return summary
