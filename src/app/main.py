"""Application entrypoint (foundation skeleton only)."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from app.pipeline import run_pipeline
from common.models import (
    apply_fill_event,
    BrokerOrder,
    FillEvent,
    MarketDataSnapshot,
    MarketSessionState,
    OrderIntent,
    QuantityInstruction,
    REQUIRED_STRATEGY_FEATURE_KEYS,
    RiskInputContext,
    RiskDecision,
    SignalEvent,
    SymbolFeatureSnapshot,
    transition_order_status,
)
from execution.interface import ExecutionPort
from market.interface import MarketDataPort
from reporting.interface import ReportingPort
from risk.interface import RiskPort
from strategy.interface import StrategyPort


MarketCode = Literal["KR", "US"]
RuntimeEnv = Literal["paper", "live"]


class DummyMarketPort(MarketDataPort):
    def load_market_snapshot(self, market: MarketCode, env: RuntimeEnv) -> MarketDataSnapshot:
        session = MarketSessionState(
            market=market,
            session_state="OPEN",
            timestamp="2026-01-01T00:00:00Z",
            is_trading_day=True,
        )
        symbols = (
            SymbolFeatureSnapshot(
                market=market,
                symbol="AAPL" if market == "US" else "005930",
                timestamp="2026-01-01T00:00:00Z",
                last_price=100.0,
                volume=1000.0,
                turnover=100000.0,
                spread_bps=2.5,
                feature_version="foundation-v1",
                features={
                    "turnover_rank": 12.0,
                    "volatility_20d": 0.18,
                    "gap_pct": -0.6,
                    "momentum_20d": 3.4,
                },
            ),
        )
        # 계약 정합성: 더미 snapshot도 최소 표준 feature key를 포함한다.
        assert all(key in symbols[0].features for key in REQUIRED_STRATEGY_FEATURE_KEYS)
        return MarketDataSnapshot(
            market=market,
            env=env,
            timestamp="2026-01-01T00:00:00Z",
            session=session,
            symbols=symbols,
            universe_size=len(symbols),
            data_fresh=True,
            snapshot_version="foundation-v1",
        )


class DummyStrategyPort(StrategyPort):
    # Strategy는 broker 호출 금지.
    def generate_signal(self, feature_snapshot: MarketDataSnapshot) -> SignalEvent | None:
        return None


class DummyRiskPort(RiskPort):
    # Risk는 주문 실행 금지.
    def evaluate(self, context: RiskInputContext) -> RiskDecision | None:
        return RiskDecision(
            decision_id="risk-decision-dummy",
            event_id=context.signal.event_id,
            decision="ALLOW",
            reason="dummy",
            risk_snapshot_id="risk-snapshot-dummy",
            risk_flags=(),
            reduce_factor=None,
        )


class DummyExecutionPort(ExecutionPort):
    def __init__(self) -> None:
        self._orders: dict[str, BrokerOrder] = {}

    # Execution은 signal 생성 금지.
    def build_intent(self, decision: RiskDecision | None) -> OrderIntent | None:
        return None

    def submit(self, intent: OrderIntent) -> BrokerOrder:
        if intent.quantity is None:
            raise ValueError("intent.quantity is required for submit")
        order = BrokerOrder(
            order_id=f"order-{intent.source_decision_id}",
            intent_id=intent.source_decision_id,
            symbol=intent.symbol,
            side=intent.side,
            quantity=intent.quantity,
            filled_quantity=0.0,
            status="NEW",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        submitted = transition_order_status(
            order,
            "SUBMITTED",
            updated_at="2026-01-01T00:00:01Z",
        )
        self._orders[submitted.order_id] = submitted
        # Dummy fill simulation: single full-fill event (no pricing/sizing logic).
        fill = FillEvent(
            fill_id=f"fill-{submitted.order_id}",
            order_id=submitted.order_id,
            symbol=submitted.symbol,
            side=submitted.side,
            fill_quantity=submitted.quantity,
            fill_price=100.0,
            timestamp="2026-01-01T00:00:02Z",
            is_final=True,
        )
        updated = self.on_fill(fill)
        return updated

    def cancel(self, order_id: str) -> BrokerOrder:
        order = self._orders[order_id]
        cancelled = transition_order_status(
            order,
            "CANCELLED",
            updated_at="2026-01-01T00:00:02Z",
        )
        self._orders[order_id] = cancelled
        return cancelled

    def get_status(self, order_id: str) -> BrokerOrder:
        return self._orders[order_id]

    def on_fill(self, fill: FillEvent) -> BrokerOrder:
        order = self._orders.get(fill.order_id)
        if order is None:
            raise ValueError("unknown order_id for fill")
        updated = apply_fill_event(order, fill)
        self._orders[updated.order_id] = updated
        return updated


class DummyReportingPort(ReportingPort):
    # Intelligence/Reporting은 매매 결정 금지.
    def publish(self, summary: Mapping[str, Any]) -> None:
        print(f"[foundation] summary={summary}")


def main() -> None:
    quantity_instruction = QuantityInstruction(
        symbol="005930",
        side="BUY",
        final_quantity=1.0,
        instruction_version="foundation-v1",
        source="foundation-dummy",
    )
    summary = run_pipeline(
        market_port=DummyMarketPort(),
        strategy_port=DummyStrategyPort(),
        risk_port=DummyRiskPort(),
        execution_port=DummyExecutionPort(),
        reporting_port=DummyReportingPort(),
        market="KR",
        env="paper",
        quantity_instruction=quantity_instruction,
    )
    print(f"[foundation] pipeline completed: {summary}")


if __name__ == "__main__":
    main()
