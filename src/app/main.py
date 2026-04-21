"""Application entrypoint (foundation skeleton only)."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from app.pipeline import run_pipeline
from common.models import (
    BrokerOrder,
    FillEvent,
    MarketDataSnapshot,
    MarketSessionState,
    OrderIntent,
    REQUIRED_STRATEGY_FEATURE_KEYS,
    RiskInputContext,
    RiskDecision,
    SignalEvent,
    SymbolFeatureSnapshot,
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
        return None


class DummyExecutionPort(ExecutionPort):
    # Execution은 signal 생성 금지.
    def build_intent(self, decision: RiskDecision | None) -> OrderIntent | None:
        return None

    def submit(self, intent: OrderIntent, env: str) -> BrokerOrder | None:
        return None

    def poll_fill(self, order: BrokerOrder) -> FillEvent | None:
        return None


class DummyReportingPort(ReportingPort):
    # Intelligence/Reporting은 매매 결정 금지.
    def publish(self, summary: Mapping[str, Any]) -> None:
        print(f"[foundation] summary={summary}")


def main() -> None:
    summary = run_pipeline(
        market_port=DummyMarketPort(),
        strategy_port=DummyStrategyPort(),
        risk_port=DummyRiskPort(),
        execution_port=DummyExecutionPort(),
        reporting_port=DummyReportingPort(),
        market="KR",
        env="paper",
    )
    print(f"[foundation] pipeline completed: {summary}")


if __name__ == "__main__":
    main()
