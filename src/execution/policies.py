from __future__ import annotations

from typing import Protocol


ENTRY_POLICIES = {
    "BASELINE": {"limit_mult": 1.001, "wait_bars": 3, "chase_bps": 0.0, "market_like": False},
    "STRICT_LIMIT": {"limit_mult": 1.000, "wait_bars": 3, "chase_bps": 0.0, "market_like": False},
    "AGGRESSIVE_LIMIT": {"limit_mult": 1.002, "wait_bars": 3, "chase_bps": 0.0, "market_like": False},
    "EXTENDED_WAIT": {"limit_mult": 1.001, "wait_bars": 5, "chase_bps": 0.0, "market_like": False},
    "LIMITED_CHASE": {"limit_mult": 1.000, "wait_bars": 3, "chase_bps": 0.003, "market_like": False},
    "MARKET_LIKE": {"limit_mult": 1.000, "wait_bars": 0, "chase_bps": 0.0, "market_like": True},
}


class PendingEntryView(Protocol):
    limit_price: float
    chase_bps: float
    market_like: bool


def get_entry_policy(name: str) -> dict[str, float | bool]:
    key = str(name or "BASELINE").strip().upper()
    if key not in ENTRY_POLICIES:
        raise ValueError(f"unknown entry_policy={name}")
    return ENTRY_POLICIES[key]


def resolve_entry_fill_price(
    *,
    low: float,
    high: float,
    open_px: float,
    pending: PendingEntryView,
) -> tuple[bool, float | None]:
    if pending.market_like:
        return True, float(open_px)
    if low <= pending.limit_price <= high:
        return True, float(pending.limit_price)
    if pending.chase_bps > 0 and high >= pending.limit_price:
        chase_limit = pending.limit_price * (1.0 + pending.chase_bps)
        if low <= chase_limit:
            return True, float(min(chase_limit, max(open_px, pending.limit_price)))
    return False, None


def estimate_missed_trade_potential(
    *,
    highs: list[float],
    breakout_level: float,
    quantity: float,
    signal_index: int,
    horizon_bars: int,
) -> tuple[float, float]:
    start = signal_index + 1
    end = min(len(highs) - 1, signal_index + horizon_bars)
    if end < start:
        return 0.0, 0.0
    max_high_after_signal = max(highs[start : end + 1])
    max_future_return = (max_high_after_signal - breakout_level) / breakout_level
    missed_profit = max_future_return * breakout_level * quantity
    return float(max_future_return), float(missed_profit)
