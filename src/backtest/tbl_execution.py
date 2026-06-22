from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BarExecutionView:
    open: float
    high: float
    low: float
    close: float
    volume: float
    atr: float = 0.0


@dataclass(frozen=True)
class FillResult:
    filled: bool
    fill_price: float | None
    filled_quantity: float = 0.0
    fee: float = 0.0
    slippage: float = 0.0
    status: str = "MISSED"


def slippage_bps_for_bar(*, fixed_bps: float, atr: float, price: float, volatility_mult: float = 0.0) -> float:
    if price <= 0 or atr <= 0 or volatility_mult <= 0:
        return float(fixed_bps)
    return float(fixed_bps) + float(atr / price) * 10000.0 * float(volatility_mult)


def apply_slippage(price: float, *, side: str, bps: float) -> tuple[float, float]:
    sign = 1.0 if side.upper() == "BUY" else -1.0
    slip = float(price) * float(bps) / 10000.0
    return float(price) + sign * slip, slip


def volume_capped_quantity(*, requested_quantity: float, bar_volume: float, max_volume_participation: float) -> float:
    if requested_quantity <= 0 or bar_volume <= 0 or max_volume_participation <= 0:
        return 0.0
    return float(min(float(requested_quantity), float(bar_volume) * float(max_volume_participation)))


def resolve_limit_fill(
    *,
    side: str,
    limit_price: float,
    bar: BarExecutionView,
    requested_quantity: float,
    fee_rate: float,
    slippage_bps: float,
    max_volume_participation: float,
) -> FillResult:
    side_norm = side.upper()
    if side_norm == "BUY":
        fillable = float(bar.low) <= float(limit_price)
    elif side_norm == "SELL":
        fillable = float(bar.high) >= float(limit_price)
    else:
        raise ValueError(f"unsupported side={side}")
    if not fillable:
        return FillResult(False, None, 0.0, 0.0, 0.0, "MISSED")

    qty = volume_capped_quantity(
        requested_quantity=requested_quantity,
        bar_volume=bar.volume,
        max_volume_participation=max_volume_participation,
    )
    if qty <= 0:
        return FillResult(False, None, 0.0, 0.0, 0.0, "REJECTED_VOLUME")
    fill_price, slip = apply_slippage(float(limit_price), side=side_norm, bps=slippage_bps)
    fee = abs(fill_price * qty) * float(fee_rate)
    status = "FILLED" if qty >= float(requested_quantity) else "PARTIAL"
    return FillResult(True, fill_price, qty, fee, slip * qty, status)


def resolve_next_open_fill(
    *,
    side: str,
    bar: BarExecutionView,
    requested_quantity: float,
    fee_rate: float,
    slippage_bps: float,
    max_volume_participation: float,
) -> FillResult:
    qty = volume_capped_quantity(
        requested_quantity=requested_quantity,
        bar_volume=bar.volume,
        max_volume_participation=max_volume_participation,
    )
    if qty <= 0:
        return FillResult(False, None, 0.0, 0.0, 0.0, "REJECTED_VOLUME")
    fill_price, slip = apply_slippage(float(bar.open), side=side, bps=slippage_bps)
    fee = abs(fill_price * qty) * float(fee_rate)
    status = "FILLED" if qty >= float(requested_quantity) else "PARTIAL"
    return FillResult(True, fill_price, qty, fee, slip * qty, status)


def entry_bar_stop_first(*, fill_price: float, stop_price: float, bar: BarExecutionView) -> bool:
    _ = fill_price
    return float(bar.low) <= float(stop_price)
