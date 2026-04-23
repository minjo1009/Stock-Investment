"""Backtest/Execution shared data contracts for strategy evaluation.

Task 020 scope:
- Define model skeletons only.
- No execution logic, DB logic, or strategy logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


SignalSide = Literal["BUY", "SELL"]
SignalType = Literal["ENTER", "EXIT", "HOLD", "SKIP"]
ExecutionStatus = Literal["SUBMITTED", "FILLED", "CANCELLED", "FAILED"]


@dataclass(frozen=True)
class SignalEvent:
    """Strategy output signal contract."""

    strategy_id: str
    symbol: str
    side: SignalSide
    signal_type: SignalType
    signal_time: datetime
    reference_price: float
    breakout_level: float
    stop_price: float
    reason: str


@dataclass(frozen=True)
class ExecutionIntent:
    """Execution submission intent built from a signal."""

    intent_id: str
    strategy_id: str
    symbol: str
    side: SignalSide
    intended_price: float
    quantity: float
    created_at: datetime


@dataclass(frozen=True)
class ExecutionResult:
    """Actual broker-side order/fill outcome snapshot."""

    order_id: str
    intent_id: str
    symbol: str
    side: SignalSide
    order_price: float
    fill_price: float | None
    filled_quantity: float
    status: ExecutionStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PositionSnapshot:
    """Current position snapshot for a symbol."""

    symbol: str
    quantity: float
    avg_price: float
    updated_at: datetime


@dataclass(frozen=True)
class TradeResult:
    """Unified trade result contract shared by execution and backtest."""

    trade_id: str
    strategy_id: str
    symbol: str
    entry_time: datetime
    entry_price: float
    entry_fill_price: float | None
    exit_time: datetime | None
    exit_price: float | None
    exit_fill_price: float | None
    quantity: float
    expected_pnl: float
    actual_pnl: float | None
    slippage: float | None
    holding_time: float | None


@dataclass(frozen=True)
class BacktestTrade:
    """Backtest-only trade extension metrics."""

    trade_id: str
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    pnl: float
    max_drawdown: float | None
    max_runup: float | None

