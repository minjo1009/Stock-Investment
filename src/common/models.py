"""Canonical domain objects from context/architecture/domain-model.md."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

# Strategy input refinement: top-level raw-ish fields와 분리된
# 전략용 파생/정규화 feature key의 최소 표준 계약.
StrategyFeatureKey = Literal[
    "turnover_rank",
    "volatility_20d",
    "gap_pct",
    "momentum_20d",
]
REQUIRED_STRATEGY_FEATURE_KEYS: tuple[StrategyFeatureKey, ...] = (
    "turnover_rank",
    "volatility_20d",
    "gap_pct",
    "momentum_20d",
)


@dataclass(frozen=True)
class SignalEvent:
    event_id: str
    timestamp: str
    market: Literal["KR", "US"]
    symbol: str
    strategy_id: str
    action: Literal["ENTER", "EXIT", "HOLD", "SKIP"]
    side: Literal["BUY", "SELL", "NONE"]
    reason: str
    score: float | None = None


@dataclass(frozen=True)
class RiskDecision:
    decision_id: str
    event_id: str
    status: Literal["ALLOW", "BLOCK", "REDUCE"]
    block_reason: str | None
    approved_size: float
    risk_snapshot_id: str


@dataclass(frozen=True)
class OrderIntent:
    intent_id: str
    market: Literal["KR", "US"]
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
    order_type: Literal["LIMIT", "MARKET"]
    limit_price: float | None
    stop_loss: float | None
    take_profit: float | None
    timestamp: str


@dataclass(frozen=True)
class BrokerOrder:
    broker_order_id: str
    intent_id: str
    env: Literal["paper", "live"]
    status: Literal["NEW", "PARTIAL", "FILLED", "CANCELED"]
    submitted_at: str


@dataclass(frozen=True)
class FillEvent:
    fill_id: str
    broker_order_id: str
    symbol: str
    price: float
    quantity: float
    timestamp: str


@dataclass(frozen=True)
class PositionSnapshot:
    symbol: str
    quantity: float
    avg_price: float
    unrealized_pnl: float
    realized_pnl: float


@dataclass(frozen=True)
class AccountSnapshot:
    env: Literal["paper", "live"]
    total_balance: float
    available_balance: float
    timestamp: str


# Market/Data -> Strategy canonical snapshot contracts.
# NOTE: feature key 목록, freshness 임계값 등은 후속 task에서 상세화한다.
@dataclass(frozen=True)
class MarketSessionState:
    market: Literal["KR", "US"]
    session_state: Literal["PREOPEN", "OPEN", "CLOSED", "HALTED"]
    timestamp: str
    is_trading_day: bool


@dataclass(frozen=True)
class SymbolFeatureSnapshot:
    market: Literal["KR", "US"]
    symbol: str
    timestamp: str
    last_price: float | None
    volume: float | None
    turnover: float | None
    spread_bps: float | None
    feature_version: str
    # features는 전략용 파생/정규화 값을 담는다.
    # raw-ish 핵심값(last_price/volume/turnover/spread_bps)은 top-level을 canonical로 사용한다.
    features: Mapping[str, float | int | bool | None]


@dataclass(frozen=True)
class MarketDataSnapshot:
    market: Literal["KR", "US"]
    env: Literal["paper", "live"]
    timestamp: str
    session: MarketSessionState
    symbols: tuple[SymbolFeatureSnapshot, ...]
    universe_size: int
    data_fresh: bool
    snapshot_version: str


def has_required_strategy_features(snapshot: SymbolFeatureSnapshot) -> bool:
    """최소 표준 feature key 존재 여부만 검사한다(계산 로직 없음)."""
    return all(key in snapshot.features for key in REQUIRED_STRATEGY_FEATURE_KEYS)


# Canonical risk input contract for Risk Layer.
# account/position은 foundation 단계/초기 상태/미보유 상태에서 None을 허용한다.
RISK_INPUT_CONTEXT_VERSION = "foundation-v1"


@dataclass(frozen=True)
class RiskInputContext:
    signal: SignalEvent
    market_snapshot: MarketDataSnapshot
    account: AccountSnapshot | None
    position: PositionSnapshot | None
    context_version: str = RISK_INPUT_CONTEXT_VERSION


# Canonical snake_case aliases for contract naming parity.
signal_event = SignalEvent
risk_decision = RiskDecision
order_intent = OrderIntent
broker_order = BrokerOrder
fill_event = FillEvent
position_snapshot = PositionSnapshot
account_snapshot = AccountSnapshot
market_session_state = MarketSessionState
symbol_feature_snapshot = SymbolFeatureSnapshot
market_data_snapshot = MarketDataSnapshot
risk_input_context = RiskInputContext
