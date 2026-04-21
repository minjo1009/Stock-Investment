"""Canonical domain objects from context/architecture/domain-model.md."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
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

RiskFlag = Literal[
    "MAX_POSITION_EXCEEDED",
    "MAX_EXPOSURE_EXCEEDED",
    "MAX_DAILY_LOSS_REACHED",
    "SPREAD_TOO_WIDE",
    "LOW_LIQUIDITY",
    "HIGH_VOLATILITY",
    "STALE_DATA",
    "MISSING_FEATURE",
]
RISK_FLAG_VALUES: tuple[RiskFlag, ...] = (
    "MAX_POSITION_EXCEEDED",
    "MAX_EXPOSURE_EXCEEDED",
    "MAX_DAILY_LOSS_REACHED",
    "SPREAD_TOO_WIDE",
    "LOW_LIQUIDITY",
    "HIGH_VOLATILITY",
    "STALE_DATA",
    "MISSING_FEATURE",
)
QUANTITY_INSTRUCTION_VERSION = "foundation-v1"
ExecutionStatus = Literal[
    "NEW",
    "SUBMITTED",
    "PARTIAL_FILLED",
    "FILLED",
    "CANCELLED",
    "REJECTED",
]
EXECUTION_STATUS_VALUES: tuple[ExecutionStatus, ...] = (
    "NEW",
    "SUBMITTED",
    "PARTIAL_FILLED",
    "FILLED",
    "CANCELLED",
    "REJECTED",
)
LateFillReconciliationStatus = Literal["REVIEW_REQUIRED", "REJECTED"]


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
    """Execution이 해석할 Risk 판단 결과 계약.

    Legacy fields removed. decision is the single source of truth.

    Semantics:
    - ALLOW: 신호를 그대로 허용한다(축소 없음).
    - BLOCK: 거래를 금지한다(축소 없음).
    - REDUCE: 신호는 유효하지만 축소가 필요하다.

    규칙:
    - ALLOW/BLOCK이면 reduce_factor는 반드시 None.
    - REDUCE이면 reduce_factor는 None 또는 양수 값이 될 수 있다(계산 로직은 별도).
    """

    decision_id: str
    event_id: str
    decision: Literal["ALLOW", "BLOCK", "REDUCE"]
    reason: str
    risk_snapshot_id: str
    risk_flags: tuple[RiskFlag, ...] = ()
    reduce_factor: float | None = None

    def __post_init__(self) -> None:
        if self.decision in ("ALLOW", "BLOCK") and self.reduce_factor is not None:
            raise ValueError("reduce_factor must be None for ALLOW/BLOCK")
        if self.decision == "REDUCE" and self.reduce_factor is not None and self.reduce_factor <= 0:
            raise ValueError("reduce_factor must be positive when provided for REDUCE")
        for flag in self.risk_flags:
            if flag not in RISK_FLAG_VALUES:
                raise ValueError(f"invalid risk flag: {flag}")


@dataclass(frozen=True)
class OrderIntent:
    """Execution이 해석하는 canonical 주문 입력 계약.

    정의:
    - quantity는 최종 주문 수량이다(Execution 계산 금지).
    - reduce_factor는 (0, 1] 범위에서 축소 비율을 표현한다.
    - reduce_factor=None은 축소 미적용을 의미한다.
    - price_type은 LIMIT/MARKET 중 하나다.
    """

    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float | None
    price_type: Literal["LIMIT", "MARKET"]
    reduce_factor: float | None
    source_decision_id: str

    def __post_init__(self) -> None:
        if self.quantity is not None and self.quantity <= 0:
            raise ValueError("quantity must be positive when provided")
        if self.reduce_factor is not None and not (0 < self.reduce_factor <= 1):
            raise ValueError("reduce_factor must be in (0, 1]")


@dataclass(frozen=True)
class QuantityInstruction:
    """OrderIntent.quantity 공급을 위한 canonical handoff 계약.

    - final_quantity는 최종 주문 수량이며 이미 계산 완료된 값이다.
    - Risk/Execution은 final_quantity를 계산하지 않는다.
    """

    symbol: str
    side: Literal["BUY", "SELL"]
    final_quantity: float
    instruction_version: str = QUANTITY_INSTRUCTION_VERSION
    source: str | None = None

    def __post_init__(self) -> None:
        if self.final_quantity <= 0:
            raise ValueError("final_quantity must be positive")


@dataclass(frozen=True)
class BrokerOrder:
    order_id: str
    intent_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
    filled_quantity: float
    status: ExecutionStatus
    created_at: str
    updated_at: str


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def is_valid_transition(from_status: ExecutionStatus, to_status: ExecutionStatus) -> bool:
    allowed: dict[ExecutionStatus, tuple[ExecutionStatus, ...]] = {
        "NEW": ("SUBMITTED",),
        "SUBMITTED": ("PARTIAL_FILLED", "FILLED", "CANCELLED", "REJECTED"),
        "PARTIAL_FILLED": ("FILLED", "CANCELLED"),
        "FILLED": (),
        "CANCELLED": (),
        "REJECTED": (),
    }
    return to_status in allowed[from_status]


def transition_order_status(
    order: BrokerOrder,
    new_status: ExecutionStatus,
    *,
    updated_at: str | None = None,
) -> BrokerOrder:
    if not is_valid_transition(order.status, new_status):
        raise ValueError(f"invalid transition: {order.status} -> {new_status}")
    return replace(order, status=new_status, updated_at=updated_at or _utc_now_iso())


@dataclass(frozen=True)
class FillEvent:
    fill_id: str
    order_id: str
    symbol: str
    side: Literal["BUY", "SELL"]
    fill_quantity: float
    fill_price: float
    timestamp: str
    is_final: bool = False

    def __post_init__(self) -> None:
        if self.fill_quantity <= 0:
            raise ValueError("fill_quantity must be positive")
        if not self.timestamp:
            raise ValueError("timestamp is required")


@dataclass(frozen=True)
class LateFillReconciliationResult:
    """Late fill is not auto-applied; it is only classified for reconciliation review."""

    order_id: str
    fill_id: str
    accepted_for_review: bool
    reason: str
    reconciliation_status: LateFillReconciliationStatus
    original_order_status: ExecutionStatus


def apply_fill_event(order: BrokerOrder, fill: FillEvent) -> BrokerOrder:
    """FillEvent를 적용해 BrokerOrder를 이벤트 기반으로 갱신한다."""
    if order.status not in ("SUBMITTED", "PARTIAL_FILLED"):
        raise ValueError(f"fill not accepted for order status: {order.status}")
    if order.order_id != fill.order_id:
        raise ValueError("fill.order_id does not match order.order_id")
    if order.symbol != fill.symbol or order.side != fill.side:
        raise ValueError("fill symbol/side does not match order")
    if fill.fill_quantity > order.quantity:
        raise ValueError("fill_quantity cannot exceed order.quantity")

    cumulative_filled = order.filled_quantity + fill.fill_quantity
    if cumulative_filled > order.quantity:
        raise ValueError("cumulative filled quantity cannot exceed order.quantity")

    next_status: ExecutionStatus = "FILLED" if cumulative_filled == order.quantity else "PARTIAL_FILLED"
    transitioned = transition_order_status(order, next_status, updated_at=fill.timestamp)
    return replace(transitioned, filled_quantity=cumulative_filled)


def reconcile_late_fill(order: BrokerOrder, fill: FillEvent) -> LateFillReconciliationResult:
    """Classify late fills for review without mutating BrokerOrder state."""
    if order.status in ("NEW", "REJECTED"):
        raise ValueError(f"late fill reconciliation not allowed for order status: {order.status}")
    if order.status in ("SUBMITTED", "PARTIAL_FILLED"):
        raise ValueError(f"order status is on normal fill path, not late reconciliation: {order.status}")
    if order.status not in ("CANCELLED", "FILLED"):
        raise ValueError(f"unsupported reconciliation status: {order.status}")

    if order.order_id != fill.order_id:
        raise ValueError("fill.order_id does not match order.order_id")
    if order.symbol != fill.symbol:
        raise ValueError("fill symbol does not match order symbol")
    if order.side != fill.side:
        raise ValueError("fill side does not match order side")

    return LateFillReconciliationResult(
        order_id=order.order_id,
        fill_id=fill.fill_id,
        accepted_for_review=True,
        reason=f"late fill requires reconciliation review for {order.status} order",
        reconciliation_status="REVIEW_REQUIRED",
        original_order_status=order.status,
    )


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


def is_risk_evaluable(context: RiskInputContext) -> bool:
    """Risk 평가 가능 여부를 최소 정책으로 판정한다(계산 로직 없음).

    정책:
    - signal이 없으면 Risk 호출 금지(호출 전제).
    - snapshot이 stale(data_fresh=False)면 Risk 평가 금지.
    - account=None은 paper/foundation 단계에서만 허용.
    - position=None은 flat 상태로 간주해 허용.
    - signal 대상 symbol의 필수 feature key가 누락되거나 값이 None이면 평가 금지.
    """
    snapshot = context.market_snapshot

    if not snapshot.data_fresh:
        return False

    # account nullability policy: foundation/paper only.
    if context.account is None and snapshot.env != "paper":
        return False

    signal_symbol_snapshot = next(
        (item for item in snapshot.symbols if item.symbol == context.signal.symbol),
        None,
    )
    if signal_symbol_snapshot is None:
        return False

    for key in REQUIRED_STRATEGY_FEATURE_KEYS:
        if key not in signal_symbol_snapshot.features:
            return False
        if signal_symbol_snapshot.features[key] is None:
            return False

    return True


def map_risk_decision_to_order_intent(
    decision: RiskDecision,
    signal: SignalEvent,
    quantity: float | None = None,
) -> OrderIntent | None:
    """RiskDecision을 Execution handoff용 OrderIntent로 변환한다.

    매핑 규칙:
    - BLOCK: OrderIntent를 생성하지 않는다.
    - quantity가 없으면 Execution 계산 없이 실행 불가이므로 생성하지 않는다.
    - ALLOW: reduce_factor=None으로 전달한다.
    - REDUCE: decision.reduce_factor를 전달한다(축소 계산은 수행하지 않음).
    """
    if decision.decision == "BLOCK":
        return None

    if signal.side not in ("BUY", "SELL"):
        return None
    if quantity is None:
        return None

    reduce_factor = decision.reduce_factor if decision.decision == "REDUCE" else None
    return OrderIntent(
        symbol=signal.symbol,
        side=signal.side,
        quantity=quantity,
        price_type="MARKET",
        reduce_factor=reduce_factor,
        source_decision_id=decision.decision_id,
    )


def build_order_intent_from_handoff(
    signal: SignalEvent,
    decision: RiskDecision,
    quantity_instruction: QuantityInstruction | None,
) -> OrderIntent | None:
    """RiskDecision + QuantityInstruction -> OrderIntent 조립 계약.

    규칙:
    - BLOCK이면 quantity_instruction이 있어도 intent를 생성하지 않는다.
    - quantity_instruction이 없으면 intent를 생성하지 않는다.
    - 계산 없이 전달값을 조립한다.
    """
    if decision.decision == "BLOCK":
        return None
    if quantity_instruction is None:
        return None
    if signal.symbol != quantity_instruction.symbol:
        return None
    if signal.side not in ("BUY", "SELL"):
        return None
    if signal.side != quantity_instruction.side:
        return None

    return OrderIntent(
        symbol=signal.symbol,
        side=signal.side,
        quantity=quantity_instruction.final_quantity,
        price_type="MARKET",
        reduce_factor=decision.reduce_factor if decision.decision == "REDUCE" else None,
        source_decision_id=decision.decision_id,
    )


# Canonical snake_case aliases for contract naming parity.
signal_event = SignalEvent
risk_decision = RiskDecision
order_intent = OrderIntent
quantity_instruction = QuantityInstruction
broker_order = BrokerOrder
fill_event = FillEvent
late_fill_reconciliation_result = LateFillReconciliationResult
position_snapshot = PositionSnapshot
account_snapshot = AccountSnapshot
market_session_state = MarketSessionState
symbol_feature_snapshot = SymbolFeatureSnapshot
market_data_snapshot = MarketDataSnapshot
risk_input_context = RiskInputContext
