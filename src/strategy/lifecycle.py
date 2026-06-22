from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class LifecycleState(StrEnum):
    INITIAL_ENTRY = "INITIAL_ENTRY"
    CONFIRMED_ADD = "CONFIRMED_ADD"
    PARTIAL_TAKE_PROFIT = "PARTIAL_TAKE_PROFIT"
    RUNNER = "RUNNER"
    EXITED = "EXITED"
    STOPPED = "STOPPED"


class LifecycleAction(StrEnum):
    HOLD = "HOLD"
    ADD = "ADD"
    PARTIAL_TAKE_PROFIT = "PARTIAL_TAKE_PROFIT"
    EXIT = "EXIT"
    STOP = "STOP"


@dataclass(frozen=True)
class LifecyclePosition:
    lifecycle_id: str
    symbol: str
    state: LifecycleState
    entry_index: int
    entry_price: float
    average_price: float
    stop_price: float
    initial_stop_price: float
    initial_r: float
    initial_quantity: float
    quantity: float
    target_quantity: float
    highest_close: float
    trailing_stop: float | None = None
    added: bool = False
    partial_taken: bool = False
    runner: bool = False
    realized_pnl: float = 0.0
    exit_reason: str | None = None


@dataclass(frozen=True)
class LifecycleDecision:
    action: LifecycleAction
    position: LifecyclePosition
    quantity: float = 0.0
    reason: str = ""


def initialize_lifecycle_position(
    *,
    lifecycle_id: str,
    symbol: str,
    entry_index: int,
    entry_price: float,
    initial_stop_price: float,
    initial_quantity: float,
    target_quantity: float,
) -> LifecyclePosition:
    initial_r = float(entry_price) - float(initial_stop_price)
    if initial_r <= 0:
        raise ValueError("initial_r must be positive")
    if initial_quantity <= 0:
        raise ValueError("initial_quantity must be positive")
    return LifecyclePosition(
        lifecycle_id=lifecycle_id,
        symbol=symbol,
        state=LifecycleState.INITIAL_ENTRY,
        entry_index=int(entry_index),
        entry_price=float(entry_price),
        average_price=float(entry_price),
        stop_price=float(initial_stop_price),
        initial_stop_price=float(initial_stop_price),
        initial_r=initial_r,
        initial_quantity=float(initial_quantity),
        quantity=float(initial_quantity),
        target_quantity=float(target_quantity),
        highest_close=float(entry_price),
    )


def position_r_multiple(position: LifecyclePosition, price: float) -> float:
    return (float(price) - position.entry_price) / position.initial_r


def should_add_position(position: LifecyclePosition, high_price: float) -> bool:
    if position.added or position.state in {LifecycleState.EXITED, LifecycleState.STOPPED}:
        return False
    return position_r_multiple(position, high_price) >= 1.0


def should_take_partial_profit(position: LifecyclePosition, high_price: float) -> bool:
    if position.partial_taken or position.state in {LifecycleState.EXITED, LifecycleState.STOPPED}:
        return False
    return position_r_multiple(position, high_price) >= 2.0


def apply_add(position: LifecyclePosition, *, add_price: float, add_quantity: float) -> LifecyclePosition:
    if position.added or add_quantity <= 0:
        return position
    new_qty = position.quantity + float(add_quantity)
    avg = ((position.average_price * position.quantity) + (float(add_price) * float(add_quantity))) / new_qty
    return replace(
        position,
        state=LifecycleState.CONFIRMED_ADD,
        average_price=avg,
        quantity=new_qty,
        added=True,
        stop_price=max(position.stop_price, position.entry_price),
    )


def apply_partial_take_profit(
    position: LifecyclePosition,
    *,
    exit_price: float,
    exit_quantity: float,
    fee: float = 0.0,
) -> LifecyclePosition:
    if position.partial_taken or exit_quantity <= 0:
        return position
    qty = min(float(exit_quantity), position.quantity)
    realized = (float(exit_price) - position.average_price) * qty - float(fee)
    remaining = max(position.quantity - qty, 0.0)
    return replace(
        position,
        state=LifecycleState.RUNNER,
        quantity=remaining,
        partial_taken=True,
        runner=True,
        realized_pnl=position.realized_pnl + realized,
    )


def update_trailing_stop(position: LifecyclePosition, *, close_price: float, atr: float, multiplier: float = 3.0) -> LifecyclePosition:
    highest_close = max(position.highest_close, float(close_price))
    if not position.runner:
        return replace(position, highest_close=highest_close)
    candidate = highest_close - float(atr) * float(multiplier)
    trailing = candidate if position.trailing_stop is None else max(position.trailing_stop, candidate)
    return replace(
        position,
        highest_close=highest_close,
        trailing_stop=trailing,
        stop_price=max(position.stop_price, trailing),
    )


def should_exit_position(position: LifecyclePosition, *, low_price: float, current_index: int, max_holding_bars: int = 20) -> tuple[bool, str]:
    if position.state in {LifecycleState.EXITED, LifecycleState.STOPPED}:
        return False, ""
    if float(low_price) <= position.stop_price:
        return True, "STOP" if not position.runner else "TRAILING_STOP"
    if int(current_index) - position.entry_index + 1 > int(max_holding_bars):
        return True, "TIME_EXIT"
    return False, ""


def close_position(
    position: LifecyclePosition,
    *,
    exit_price: float,
    fee: float = 0.0,
    reason: str,
) -> LifecyclePosition:
    realized = (float(exit_price) - position.average_price) * position.quantity - float(fee)
    final_state = LifecycleState.STOPPED if reason in {"STOP", "TRAILING_STOP"} else LifecycleState.EXITED
    return replace(
        position,
        state=final_state,
        quantity=0.0,
        realized_pnl=position.realized_pnl + realized,
        exit_reason=reason,
    )


def update_lifecycle_state(
    position: LifecyclePosition,
    *,
    high_price: float,
    low_price: float,
    close_price: float,
    atr: float,
    current_index: int,
) -> LifecycleDecision:
    updated = update_trailing_stop(position, close_price=close_price, atr=atr)
    should_exit, reason = should_exit_position(updated, low_price=low_price, current_index=current_index)
    if should_exit:
        return LifecycleDecision(action=LifecycleAction.STOP if "STOP" in reason else LifecycleAction.EXIT, position=updated, reason=reason)
    if should_take_partial_profit(updated, high_price):
        return LifecycleDecision(
            action=LifecycleAction.PARTIAL_TAKE_PROFIT,
            position=updated,
            quantity=updated.quantity * 0.5,
            reason="+2R_PARTIAL",
        )
    if should_add_position(updated, high_price):
        return LifecycleDecision(
            action=LifecycleAction.ADD,
            position=updated,
            quantity=max(updated.target_quantity - updated.quantity, 0.0),
            reason="+1R_ADD",
        )
    return LifecycleDecision(action=LifecycleAction.HOLD, position=updated)
