"""Pipeline skeleton for market -> strategy -> risk -> execution -> reporting.

주의:
- 이 파일은 흐름 구조만 제공한다.
- 실제 매매/리스크/API 로직은 구현하지 않는다.
"""

from __future__ import annotations

from typing import Any, Literal

from common.models import (
    AccountSnapshot,
    build_order_intent_from_handoff,
    PositionSnapshot,
    QuantityInstruction,
    RISK_INPUT_CONTEXT_VERSION,
    RiskDecision,
    RiskInputContext,
    is_risk_evaluable,
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
    quantity_instruction: QuantityInstruction | None = None,
) -> dict[str, Any]:
    """레이어 호출 순서만 표현하는 최소 파이프라인."""
    market_snapshot = market_port.load_market_snapshot(market, env)
    signal = strategy_port.generate_signal(market_snapshot)

    # 계좌/포지션 동기화 로직은 Phase 01 범위를 벗어나므로 placeholder만 둔다.
    account: AccountSnapshot | None = None
    position: PositionSnapshot | None = None
    decision: RiskDecision | None = None
    if signal is not None:
        risk_input = RiskInputContext(
            signal=signal,
            market_snapshot=market_snapshot,
            account=account,
            position=position,
            context_version=RISK_INPUT_CONTEXT_VERSION,
        )
        if is_risk_evaluable(risk_input):
            decision = risk_port.evaluate(risk_input)

    broker_order = None
    if decision is not None:
        intent = None
        if signal is not None:
            intent = build_order_intent_from_handoff(signal, decision, quantity_instruction)

        # BLOCK은 intent 생성 금지.
        if decision.decision in ("ALLOW", "REDUCE"):
            # Execution 구현체가 별도 intent 구성을 제공하면 우선 사용한다.
            built_intent = execution_port.build_intent(decision)
            if built_intent is not None:
                intent = built_intent

        if intent is not None:
            broker_order = execution_port.submit(intent)
            broker_order = execution_port.get_status(broker_order.order_id)

    summary = {
        "market": market,
        "env": env,
        "snapshot_version": market_snapshot.snapshot_version,
        "universe_size": market_snapshot.universe_size,
        "data_fresh": market_snapshot.data_fresh,
        "has_signal": signal is not None,
        "has_decision": decision is not None,
        "has_order": broker_order is not None,
        "has_fill": broker_order is not None and broker_order.status == "FILLED",
    }
    reporting_port.publish(summary)
    return summary
