from __future__ import annotations

from typing import Protocol


RISK_POLICIES = {
    "BASELINE": {"break_even": False, "giveback": False, "time_stop": False},
    "BREAK_EVEN_STOP": {"break_even": True, "giveback": False, "time_stop": False},
    "MFE_GIVEBACK_50": {"break_even": False, "giveback": True, "time_stop": False},
    "TIME_STOP": {"break_even": False, "giveback": False, "time_stop": True},
    "HYBRID": {"break_even": True, "giveback": True, "time_stop": True},
}

RISK_MFE_TRIGGER = 0.03
RISK_GIVEBACK_FRACTION = 0.50
RISK_TIME_STOP_BARS = 10
RISK_TIME_STOP_MIN_RETURN = 0.01


class PositionRiskView(Protocol):
    stop_price: float
    entry_fill_price: float
    entry_index: int
    max_high_since_entry: float


def get_risk_policy(name: str) -> dict[str, bool]:
    key = str(name or "BASELINE").strip().upper()
    if key == "TIME_STOP_ONLY":
        key = "TIME_STOP"
    if key not in RISK_POLICIES:
        raise ValueError(f"unknown risk_policy={name}")
    return RISK_POLICIES[key]


def position_mfe(position: PositionRiskView) -> float:
    if position.entry_fill_price <= 0:
        return 0.0
    return (position.max_high_since_entry - position.entry_fill_price) / position.entry_fill_price


def evaluate_risk_exit(
    *,
    i: int,
    close: float,
    low: float,
    position: PositionRiskView,
    risk_policy: dict[str, bool],
) -> dict[str, float | str] | None:
    mfe = position_mfe(position)

    if risk_policy["break_even"] and mfe >= RISK_MFE_TRIGGER:
        break_even_stop = max(position.stop_price, position.entry_fill_price)
        if low <= break_even_stop:
            return {"kind": "stop", "stop_price": break_even_stop}

    if risk_policy["giveback"] and mfe >= RISK_MFE_TRIGGER:
        giveback_price = position.entry_fill_price * (1.0 + mfe * RISK_GIVEBACK_FRACTION)
        if low <= giveback_price:
            return {"kind": "exit", "price": giveback_price, "rule": "RISK_MFE_GIVEBACK_50"}

    holding_bars = i - position.entry_index + 1
    if risk_policy["time_stop"] and holding_bars >= RISK_TIME_STOP_BARS:
        current_return = (close - position.entry_fill_price) / position.entry_fill_price
        if current_return < RISK_TIME_STOP_MIN_RETURN:
            return {"kind": "exit", "price": close, "rule": "RISK_TIME_STOP"}

    return None
