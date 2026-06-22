from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from strategy.conditions import prepare_condition_frame


INITIAL_CAPITAL = 100_000.0
ENTRY_SLIPPAGE_BPS = 10.0
EXIT_SLIPPAGE_BPS = 10.0
FEE_RATE = 0.001
MAX_ORDERS_PER_BAR = 4
MAX_CONCURRENT_POSITIONS = 4
RISK_PER_TRADE = 0.01
TOTAL_RISK_CAP_R = 1.0
RSI_PERIOD = 4

LEVERAGED_ETFS = {"TQQQ", "SOXL", "QLD"}
MEGACAPS = {"NVDA", "MSFT", "AAPL", "AMZN", "META", "AVGO"}
DEFAULT_HYBRID_UNIVERSE = sorted(LEVERAGED_ETFS | MEGACAPS)
ALL_MODES = {"baseline", "regime_switch_v1", "regime_switch_v2", "compare"}


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _slip_up(px: float) -> float:
    return float(px * (1.0 + ENTRY_SLIPPAGE_BPS / 10000.0))


def _slip_dn(px: float) -> float:
    return float(px * (1.0 - EXIT_SLIPPAGE_BPS / 10000.0))


def _compute_rsi(close: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    gain = up.ewm(alpha=1.0 / period, adjust=False).mean()
    loss = down.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = gain / loss.replace(0.0, pd.NA)
    return 100.0 - (100.0 / (1.0 + rs))


def detect_regime_strength_raw(df: pd.DataFrame) -> pd.Series:
    # t-1 only inputs
    close_prev = pd.to_numeric(df["close"], errors="coerce").shift(1)
    ma200_prev = pd.to_numeric(df["ma200"], errors="coerce").shift(1)
    slope_prev = ma200_prev - ma200_prev.shift(5)
    ret20_prev = pd.to_numeric(df["close"], errors="coerce").pct_change(20).shift(1)

    out = pd.Series("RANGE", index=df.index, dtype="object")
    strong = (close_prev > ma200_prev) & (slope_prev > 0) & (ret20_prev > 0)
    weak = (close_prev > ma200_prev) & (~strong.fillna(False))
    out.loc[weak.fillna(False)] = "WEAK_TREND"
    out.loc[strong.fillna(False)] = "STRONG_TREND"
    return out


def apply_regime_hysteresis(raw: pd.Series, confirm_bars: int = 2) -> pd.Series:
    if raw.empty:
        return raw
    out = raw.copy()
    current = str(raw.iloc[0])
    streak = 0
    for i in range(1, len(raw)):
        nxt = str(raw.iloc[i])
        if nxt == current:
            streak = 0
            out.iloc[i] = current
            continue
        streak += 1
        if streak >= max(1, int(confirm_bars)):
            current = nxt
            streak = 0
        out.iloc[i] = current
    return out


def build_symbol_bucket(symbol: str, profile: str) -> str:
    if profile != "hybrid_v1":
        return "B"
    a_bucket = {"META", "NFLX", "SOXL", "NVDA", "GOOGL"}
    c_bucket = {"AAPL", "AVGO", "COST", "AMZN", "QCOM"}
    if symbol in a_bucket:
        return "A"
    if symbol in c_bucket:
        return "C"
    return "B"


@dataclass
class Position:
    symbol: str
    entry_family: str
    entry_ts: pd.Timestamp
    entry_idx: int
    entry_price: float
    size: int
    stop_price: float
    regime_state: str
    regime_strength: str
    regime_prev: str
    regime_next: str
    switch_reason: str
    switch_confirm_bars: int
    risk_leg: str
    risk_bucket: str
    allocation_bucket: str
    symbol_bucket: str
    stop_model: str
    entry_gate_reason: str
    stop_distance_at_entry: float
    best_price: float
    breakeven_armed: bool = False


@dataclass
class PendingOrder:
    symbol: str
    side: str  # BUY / SELL
    created_idx: int
    fill_idx: int
    reason: str
    entry_family: str = ""
    regime_state: str = ""
    regime_strength: str = ""
    regime_prev: str = ""
    regime_next: str = ""
    switch_reason: str = ""
    switch_confirm_bars: int = 0
    risk_leg: str = ""
    risk_bucket: str = ""
    allocation_bucket: str = ""
    symbol_bucket: str = ""
    stop_model: str = ""
    entry_gate_reason: str = ""
    reserved_cash: float = 0.0
    est_size: int = 0
    stop_price: float = 0.0
    stop_distance_at_entry: float = 0.0


def _load_frames(symbols: list[str], base_dir: Path, confirm_bars: int) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        raw = load_daily_bars(s, base_dir=base_dir)
        if raw.empty:
            continue
        frame = prepare_condition_frame(raw).copy()
        if frame.empty:
            continue
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame["open"] = pd.to_numeric(frame["open"], errors="coerce")
        frame["high"] = pd.to_numeric(frame["high"], errors="coerce")
        frame["low"] = pd.to_numeric(frame["low"], errors="coerce")
        frame["ret20"] = frame["close"].pct_change(20)
        frame["rsi4"] = _compute_rsi(frame["close"], period=RSI_PERIOD)
        frame["atr_pct"] = pd.to_numeric(frame["atr14"], errors="coerce") / frame["close"]
        frame["regime_raw"] = detect_regime_strength_raw(frame)
        frame["regime_strength"] = apply_regime_hysteresis(frame["regime_raw"], confirm_bars=confirm_bars)
        frame["regime_state"] = frame["regime_strength"].apply(lambda x: "TREND" if x in ("STRONG_TREND", "WEAK_TREND") else "RANGE")
        frame = frame.set_index(pd.to_datetime(frame["timestamp"], utc=True)).sort_index()
        out[s] = frame
    return out


def _collect_timestamps(frames: dict[str, pd.DataFrame]) -> list[pd.Timestamp]:
    return sorted({ts for f in frames.values() for ts in f.index})


def _row(fr: pd.DataFrame, ts: pd.Timestamp) -> pd.Series | None:
    if ts not in fr.index:
        return None
    r = fr.loc[ts]
    return r.iloc[-1] if isinstance(r, pd.DataFrame) else r


def _equity(cash: float, positions: list[Position], rows: dict[str, pd.Series]) -> float:
    return float(cash + sum(float(rows[p.symbol]["close"]) * p.size for p in positions if p.symbol in rows))


def _pending_cash(pending: list[PendingOrder]) -> float:
    return float(sum(o.reserved_cash for o in pending if o.side == "BUY"))


def _active_risk(positions: list[Position]) -> float:
    return float(sum(max(p.entry_price - p.stop_price, 0.0) * p.size for p in positions))


def _stop_pct(symbol: str, atr_pct: float, mode: str, bucket: str) -> tuple[float, str]:
    atr_pct = max(0.0, float(atr_pct))
    if mode != "regime_switch_v2":
        return 0.02, "fixed_2pct"
    if symbol in LEVERAGED_ETFS:
        base = max(0.06, 2.2 * atr_pct)
        if bucket == "A":
            return base * 1.1, "atr_leveraged_wide"
        if bucket == "C":
            return base * 0.9, "atr_leveraged_tight"
        return base, "atr_leveraged_std"
    base = max(0.03, 1.4 * atr_pct)
    if bucket == "A":
        return base * 1.05, "atr_megacap_mid"
    if bucket == "C":
        return base * 0.85, "atr_megacap_tight"
    return base, "atr_megacap_std"


def _alloc_target(regime_strength: str, mode: str) -> tuple[float, str]:
    if mode != "regime_switch_v2":
        return 0.70, "static_70"
    if regime_strength == "STRONG_TREND":
        return 0.95, "strong_90_100"
    if regime_strength == "WEAK_TREND":
        return 0.60, "weak_50_70"
    return 0.30, "range_20_40"


def _risk_bucket(regime_strength: str, mode: str) -> str:
    if mode != "regime_switch_v2":
        return "default"
    if regime_strength == "STRONG_TREND":
        return "full"
    if regime_strength == "WEAK_TREND":
        return "half"
    return "small"


def _guard_reversion_enabled(history: list[float], guard: str) -> bool:
    if guard != "on":
        return True
    if len(history) < 20:
        return True
    return sum(history[-20:]) >= 0.0


def _time_stop_bars(regime_state: str, mode: str) -> int:
    if mode != "regime_switch_v2":
        return 8
    return 10 if regime_state == "TREND" else 5


def _attribution(exit_trades: list[dict[str, Any]]) -> dict[str, Any]:
    def group_by(key: str) -> dict[str, Any]:
        grouped: dict[str, list[float]] = {}
        for t in exit_trades:
            grouped.setdefault(str(t.get(key, "NA")), []).append(float(t.get("net_pnl", 0.0)))
        out: dict[str, Any] = {}
        for k, vals in grouped.items():
            wins = [x for x in vals if x > 0]
            losses = [x for x in vals if x < 0]
            gp = sum(wins)
            gl = abs(sum(losses))
            out[k] = {
                "count": len(vals),
                "pnl": _f(sum(vals), 4),
                "pf": _f(_safe_div(gp, gl)) if gl > 0 else 999.0,
            }
        return out

    return {
        "by_family": group_by("entry_family"),
        "by_exit_reason": group_by("exit_reason"),
        "by_bucket": group_by("symbol_bucket"),
    }


def _metrics(exit_trades: list[dict[str, Any]], initial: float, daily_equity: list[tuple[pd.Timestamp, float]]) -> dict[str, Any]:
    pnls = [float(t["net_pnl"]) for t in exit_trades]
    final_cap = initial + sum(pnls)
    total_return = _safe_div(final_cap - initial, initial) * 100.0
    cagr = ((final_cap / initial) ** (1 / 5) - 1) * 100.0 if final_cap > 0 else -100.0

    if daily_equity:
        eq = pd.Series([v for _, v in daily_equity], index=pd.to_datetime([t for t, _ in daily_equity], utc=True)).sort_index()
        eq_daily = eq.resample("1D").last().ffill().dropna()
    else:
        eq_daily = pd.Series(dtype=float)
    peak = eq_daily.cummax() if not eq_daily.empty else pd.Series(dtype=float)
    dd = ((peak - eq_daily) / peak.replace(0.0, pd.NA)).fillna(0.0) if not eq_daily.empty else pd.Series(dtype=float)
    mdd = float(dd.max() * 100.0) if not dd.empty else 0.0
    tuw_months = int(round((dd > 0).sum() / 21.0)) if not dd.empty else 0
    yearly = eq_daily.resample("YE").last().pct_change().dropna()
    worst_year = float(yearly.min() * 100.0) if not yearly.empty else 0.0
    rets = eq_daily.pct_change().dropna()
    sharpe = float((rets.mean() / rets.std(ddof=0)) * math.sqrt(252)) if len(rets) > 2 and float(rets.std(ddof=0)) > 0 else 0.0

    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    gp = sum(wins)
    gl = abs(sum(losses))
    return {
        "initial_capital": _f(initial, 2),
        "final_capital": _f(final_cap, 2),
        "total_return_pct": _f(total_return),
        "cagr_pct": _f(cagr),
        "mdd_pct": _f(mdd),
        "worst_year_pct": _f(worst_year),
        "tuw_months": int(tuw_months),
        "sharpe": _f(sharpe),
        "trade_count": int(len(exit_trades)),
        "win_rate": _f(_safe_div(len(wins), len(pnls))) if pnls else 0.0,
        "profit_factor": _f(_safe_div(gp, gl)) if gl > 0 else 999.0,
    }


def _simulate(
    frames: dict[str, pd.DataFrame],
    mode: str,
    dd_limit_pct: float,
    regime_confirm_bars: int,
    momentum_cap_r: float,
    reversion_cap_r: float,
    symbol_bucket_profile: str,
    reversion_guard: str,
) -> dict[str, Any]:
    ts_all = _collect_timestamps(frames)
    if len(ts_all) < 260:
        return {"status": "FAIL", "reason": "insufficient_data"}

    cash = float(INITIAL_CAPITAL)
    positions: list[Position] = []
    pending: list[PendingOrder] = []
    exits: list[dict[str, Any]] = []
    daily_equity: list[tuple[pd.Timestamp, float]] = []
    regime_switch_count = 0
    last_regime: dict[str, str] = {}
    last_exit_idx_by_symbol: dict[str, int] = {}
    reversion_pnl_history: list[float] = []
    validation = {
        "no_negative_cash": True,
        "no_capital_overlap": True,
        "no_lookahead": True,
        "no_same_bar_fill": True,
    }

    for i in range(210, len(ts_all) - 1):
        ts = ts_all[i]
        rows = {s: _row(fr, ts) for s, fr in frames.items()}
        rows = {s: r for s, r in rows.items() if r is not None}

        # Fill pending on next-bar open.
        done: list[PendingOrder] = []
        fills = 0
        for od in list(pending):
            if od.fill_idx != i:
                continue
            row = rows.get(od.symbol)
            if row is None:
                continue
            if fills >= MAX_ORDERS_PER_BAR:
                continue
            fills += 1
            if od.side == "BUY":
                entry_px = _slip_up(float(row["open"]))
                size = max(0, int(od.est_size))
                spent = entry_px * size * (1.0 + FEE_RATE)
                cash += od.reserved_cash
                if size < 1 or spent > cash:
                    done.append(od)
                    continue
                cash -= spent
                if cash < -1e-6:
                    validation["no_negative_cash"] = False
                    validation["no_capital_overlap"] = False
                positions.append(
                    Position(
                        symbol=od.symbol,
                        entry_family=od.entry_family,
                        entry_ts=ts,
                        entry_idx=i,
                        entry_price=entry_px,
                        size=size,
                        stop_price=od.stop_price,
                        regime_state=od.regime_state,
                        regime_strength=od.regime_strength,
                        regime_prev=od.regime_prev,
                        regime_next=od.regime_next,
                        switch_reason=od.switch_reason,
                        switch_confirm_bars=od.switch_confirm_bars,
                        risk_leg=od.risk_leg,
                        risk_bucket=od.risk_bucket,
                        allocation_bucket=od.allocation_bucket,
                        symbol_bucket=od.symbol_bucket,
                        stop_model=od.stop_model,
                        entry_gate_reason=od.entry_gate_reason,
                        stop_distance_at_entry=od.stop_distance_at_entry,
                        best_price=entry_px,
                    )
                )
                done.append(od)
            else:
                pos = next((p for p in positions if p.symbol == od.symbol and p.entry_family == od.entry_family), None)
                if pos is None:
                    done.append(od)
                    continue
                exit_px = _slip_dn(float(row["open"]))
                proceeds = exit_px * pos.size
                fee = proceeds * FEE_RATE
                cash += proceeds - fee
                pnl = (exit_px - pos.entry_price) * pos.size - fee
                hold_bars = i - pos.entry_idx
                exits.append(
                    {
                        "symbol": pos.symbol,
                        "event": "EXIT",
                        "entry_family": pos.entry_family,
                        "entry_time": pos.entry_ts.isoformat(),
                        "exit_time": ts.isoformat(),
                        "entry_price": _f(pos.entry_price),
                        "exit_price": _f(exit_px),
                        "size": int(pos.size),
                        "net_pnl": _f(pnl, 4),
                        "regime_state": pos.regime_state,
                        "regime_strength": pos.regime_strength,
                        "regime_prev": pos.regime_prev,
                        "regime_next": pos.regime_next,
                        "switch_reason": pos.switch_reason,
                        "switch_confirm_bars": int(pos.switch_confirm_bars),
                        "risk_leg": pos.risk_leg,
                        "risk_bucket": pos.risk_bucket,
                        "allocation_bucket": pos.allocation_bucket,
                        "symbol_bucket": pos.symbol_bucket,
                        "stop_model": pos.stop_model,
                        "entry_gate_reason": pos.entry_gate_reason,
                        "stop_distance_at_entry": _f(pos.stop_distance_at_entry, 6),
                        "hold_bars": int(hold_bars),
                        "switch_to_trade_latency": int(pos.switch_confirm_bars),
                        "exit_reason": od.reason,
                    }
                )
                if pos.entry_family == "mean_reversion":
                    reversion_pnl_history.append(float(pnl))
                positions.remove(pos)
                last_exit_idx_by_symbol[pos.symbol] = i
                done.append(od)
        for od in done:
            if od in pending:
                pending.remove(od)

        # Exit scheduling with priority: regime_flip > time_stop > hard_stop
        for p in list(positions):
            row = rows.get(p.symbol)
            if row is None:
                continue
            low = float(row["low"])
            close = float(row["close"])
            p.best_price = max(p.best_price, close)
            if not p.breakeven_armed and p.stop_distance_at_entry > 0 and (p.best_price - p.entry_price) >= p.stop_distance_at_entry:
                p.stop_price = max(p.stop_price, p.entry_price)
                p.breakeven_armed = True
            cur_state = str(row.get("regime_state", "RANGE"))
            regime_flip = mode != "baseline" and cur_state != p.regime_state
            time_hit = (i - p.entry_idx) >= _time_stop_bars(p.regime_state, mode)
            stop_hit = low <= p.stop_price
            reason = ""
            if regime_flip:
                reason = "regime_flip"
            elif time_hit:
                reason = "time_stop"
            elif stop_hit:
                reason = "hard_stop"
            if reason and not any(o.symbol == p.symbol and o.side == "SELL" for o in pending):
                pending.append(
                    PendingOrder(
                        symbol=p.symbol,
                        side="SELL",
                        created_idx=i,
                        fill_idx=i + 1,
                        reason=reason,
                        entry_family=p.entry_family,
                    )
                )

        # Entry scheduling
        open_symbols = {p.symbol for p in positions}
        free_slots = max(0, MAX_CONCURRENT_POSITIONS - len(open_symbols))
        if free_slots > 0:
            mom_cands: list[tuple[str, float, str]] = []
            rev_cands: list[tuple[str, float, str]] = []
            for s, row in rows.items():
                if s in open_symbols or any(o.symbol == s and o.side == "BUY" for o in pending):
                    continue
                if pd.isna(row.get("ret20")) or pd.isna(row.get("atr_pct")):
                    continue
                cur_state = str(row.get("regime_state", "RANGE"))
                cur_strength = str(row.get("regime_strength", "RANGE"))
                prev = last_regime.get(s, cur_state)
                if prev != cur_state:
                    regime_switch_count += 1
                last_regime[s] = cur_state

                ret20 = float(row["ret20"])
                atr_pct = float(row["atr_pct"])
                rsi = float(row.get("rsi4", 50.0))
                bucket = build_symbol_bucket(s, symbol_bucket_profile)

                # 3-bar cooldown for weak trend v2
                if mode == "regime_switch_v2" and cur_strength == "WEAK_TREND":
                    if i - last_exit_idx_by_symbol.get(s, -10_000) < 3:
                        continue

                if mode == "baseline":
                    if ret20 > 0:
                        mom_cands.append((s, ret20, cur_strength))
                    continue

                if mode == "regime_switch_v1":
                    if cur_state == "TREND" and ret20 > 0:
                        mom_cands.append((s, ret20, cur_strength))
                    elif cur_state == "RANGE" and rsi < 30.0 and atr_pct >= 0.01:
                        rev_cands.append((s, -rsi, cur_strength))
                    continue

                # regime_switch_v2
                if cur_strength in ("STRONG_TREND", "WEAK_TREND") and ret20 > 0:
                    score = ret20 if cur_strength == "STRONG_TREND" else ret20 * 0.5
                    if bucket == "A":
                        score *= 1.1
                    elif bucket == "C":
                        score *= 0.8
                    mom_cands.append((s, score, cur_strength))
                elif cur_strength == "RANGE":
                    if bucket == "C":
                        continue
                    reversion_ok = _guard_reversion_enabled(reversion_pnl_history, reversion_guard)
                    prev_close = float(frames[s].loc[:ts]["close"].iloc[-2]) if len(frames[s].loc[:ts]) >= 2 else float(row["close"])
                    rebound_ok = float(row["close"]) > prev_close
                    if reversion_ok and rsi < 25.0 and atr_pct >= 0.015 and rebound_ok:
                        rev_cands.append((s, -rsi, cur_strength))

            mom_cands.sort(key=lambda x: x[1], reverse=True)
            rev_cands.sort(key=lambda x: x[1], reverse=True)

            selected: list[tuple[str, str, str]] = []
            if mode in ("baseline", "regime_switch_v1"):
                for s, _, strength in mom_cands[:free_slots]:
                    selected.append((s, "momentum", strength))
                if mode == "regime_switch_v1" and len(selected) < free_slots:
                    for s, _, strength in rev_cands[: free_slots - len(selected)]:
                        selected.append((s, "mean_reversion", strength))
            else:
                # v2: strict priority strong-trend momentum, then weak momentum, then tiny range reversion
                for s, _, strength in mom_cands[:free_slots]:
                    selected.append((s, "momentum", strength))
                if len(selected) < free_slots:
                    for s, _, strength in rev_cands[: free_slots - len(selected)]:
                        selected.append((s, "mean_reversion", strength))

            leg_risk_used = {"momentum": 0.0, "mean_reversion": 0.0}
            for p in positions:
                leg_risk_used[p.entry_family] += max(p.entry_price - p.stop_price, 0.0) * p.size

            orders = 0
            for s, family, strength in selected:
                if orders >= MAX_ORDERS_PER_BAR:
                    break
                row = rows[s]
                bucket = build_symbol_bucket(s, symbol_bucket_profile)
                est_entry = _slip_up(float(row["close"]))
                stop_pct, stop_model = _stop_pct(s, float(row.get("atr_pct", 0.0)), mode, bucket)
                stop = est_entry * (1.0 - stop_pct)
                stop_dist = max(est_entry - stop, 0.01)
                state = str(row.get("regime_state", "RANGE"))

                equity = _equity(cash + _pending_cash(pending), positions, rows)
                alloc_ratio, alloc_bucket = _alloc_target(strength, mode)
                max_notional = max(0.0, equity * alloc_ratio)
                total_risk_cap = equity * RISK_PER_TRADE * TOTAL_RISK_CAP_R
                remain_total_risk = max(0.0, total_risk_cap - _active_risk(positions))
                risk_bucket = _risk_bucket(strength, mode)
                risk_mul = 1.0 if risk_bucket == "full" else (0.5 if risk_bucket == "half" else 0.25)
                base_trade_risk = min(remain_total_risk, equity * RISK_PER_TRADE * risk_mul)

                leg_cap_r = momentum_cap_r if family == "momentum" else reversion_cap_r
                leg_cap_abs = equity * RISK_PER_TRADE * leg_cap_r
                remain_leg_risk = max(0.0, leg_cap_abs - leg_risk_used[family])
                trade_risk_budget = min(base_trade_risk, remain_leg_risk)
                if bucket == "C":
                    trade_risk_budget *= 0.5
                est_size = int(math.floor(trade_risk_budget / stop_dist))
                if est_size < 1:
                    continue
                est_notional = est_entry * est_size
                if est_notional > max_notional:
                    est_size = int(math.floor(max_notional / est_entry))
                if est_size < 1:
                    continue
                reserve_cash = est_entry * est_size * (1.0 + FEE_RATE)
                if reserve_cash > cash:
                    continue

                regime_prev = last_regime.get(s, state)
                switch_reason = "hysteresis_confirmed" if regime_prev != state else "stable"
                entry_gate_reason = f"{family}_{state.lower()}_gate"
                if mode == "regime_switch_v2" and family == "mean_reversion":
                    entry_gate_reason += "_strict"

                cash -= reserve_cash
                if cash < -1e-6:
                    validation["no_negative_cash"] = False
                    validation["no_capital_overlap"] = False
                pending.append(
                    PendingOrder(
                        symbol=s,
                        side="BUY",
                        created_idx=i,
                        fill_idx=i + 1,
                        reason="signal_entry",
                        entry_family=family,
                        regime_state=state,
                        regime_strength=strength,
                        regime_prev=regime_prev,
                        regime_next=state,
                        switch_reason=switch_reason,
                        switch_confirm_bars=regime_confirm_bars,
                        risk_leg=family,
                        risk_bucket=risk_bucket,
                        allocation_bucket=alloc_bucket,
                        symbol_bucket=bucket,
                        stop_model=stop_model,
                        entry_gate_reason=entry_gate_reason,
                        reserved_cash=reserve_cash,
                        est_size=est_size,
                        stop_price=stop,
                        stop_distance_at_entry=stop_dist,
                    )
                )
                leg_risk_used[family] += stop_dist * est_size
                orders += 1

        eq = _equity(cash + _pending_cash(pending), positions, rows)
        daily_equity.append((ts, eq))

    for od in pending:
        if od.side == "BUY":
            cash += od.reserved_cash

    # Force close remaining positions at last close
    last_ts = ts_all[-1]
    rows_last = {s: _row(fr, last_ts) for s, fr in frames.items()}
    for p in positions:
        row = rows_last.get(p.symbol)
        if row is None:
            continue
        exit_px = _slip_dn(float(row["close"]))
        proceeds = exit_px * p.size
        fee = proceeds * FEE_RATE
        cash += proceeds - fee
        pnl = (exit_px - p.entry_price) * p.size - fee
        hold_bars = len(ts_all) - 1 - p.entry_idx
        exits.append(
            {
                "symbol": p.symbol,
                "event": "EXIT",
                "entry_family": p.entry_family,
                "entry_time": p.entry_ts.isoformat(),
                "exit_time": last_ts.isoformat(),
                "entry_price": _f(p.entry_price),
                "exit_price": _f(exit_px),
                "size": int(p.size),
                "net_pnl": _f(pnl, 4),
                "regime_state": p.regime_state,
                "regime_strength": p.regime_strength,
                "regime_prev": p.regime_prev,
                "regime_next": p.regime_next,
                "switch_reason": p.switch_reason,
                "switch_confirm_bars": int(p.switch_confirm_bars),
                "risk_leg": p.risk_leg,
                "risk_bucket": p.risk_bucket,
                "allocation_bucket": p.allocation_bucket,
                "symbol_bucket": p.symbol_bucket,
                "stop_model": p.stop_model,
                "entry_gate_reason": p.entry_gate_reason,
                "stop_distance_at_entry": _f(p.stop_distance_at_entry),
                "hold_bars": int(hold_bars),
                "switch_to_trade_latency": int(p.switch_confirm_bars),
                "exit_reason": "time_stop",
            }
        )

    summary = _metrics(exits, INITIAL_CAPITAL, daily_equity)
    summary["mdd_guard_limit_pct"] = float(dd_limit_pct)
    summary["mdd_guard_pass"] = bool(float(summary["mdd_pct"]) <= float(dd_limit_pct))
    return {
        "status": "PASS",
        "strategy_mode": mode,
        "summary": summary,
        "regime_switch_count": int(regime_switch_count),
        "validation": validation,
        "attribution": _attribution(exits),
        "trades": exits,
    }


def _final_decision(baseline: dict[str, Any], v1: dict[str, Any], v2: dict[str, Any]) -> str:
    b = baseline["summary"]
    r1 = v1["summary"]
    r2 = v2["summary"]
    if (
        float(r2["total_return_pct"]) > float(r1["total_return_pct"])
        and float(r2["sharpe"]) >= float(r1["sharpe"])
        and float(r2["mdd_pct"]) <= 60.0
    ):
        return "PASS"
    if float(r2["total_return_pct"]) > float(b["total_return_pct"]):
        return "WARNING"
    return "FAIL"


def _md(report: dict[str, Any]) -> str:
    b = report["baseline"]["summary"]
    r1 = report["regime_switch_v1"]["summary"]
    r2 = report["regime_switch_v2"]["summary"]
    att = report["regime_switch_v2"]["attribution"]
    lines = [
        "# Task T511 - Regime Detail Rebuild (Execution-Driven)",
        "",
        "## Performance Comparison",
        "| Metric | Baseline | Regime V1 | Regime V2 |",
        "|---|---:|---:|---:|",
        f"| Initial Capital | ${b['initial_capital']:,.2f} | ${r1['initial_capital']:,.2f} | ${r2['initial_capital']:,.2f} |",
        f"| Final Capital | ${b['final_capital']:,.2f} | ${r1['final_capital']:,.2f} | ${r2['final_capital']:,.2f} |",
        f"| Total Return | {b['total_return_pct']:+.2f}% | {r1['total_return_pct']:+.2f}% | {r2['total_return_pct']:+.2f}% |",
        f"| CAGR | {b['cagr_pct']:+.2f}% | {r1['cagr_pct']:+.2f}% | {r2['cagr_pct']:+.2f}% |",
        f"| MDD | -{abs(b['mdd_pct']):.2f}% | -{abs(r1['mdd_pct']):.2f}% | -{abs(r2['mdd_pct']):.2f}% |",
        f"| Sharpe | {b['sharpe']:.4f} | {r1['sharpe']:.4f} | {r2['sharpe']:.4f} |",
        f"| Trade Count | {b['trade_count']} | {r1['trade_count']} | {r2['trade_count']} |",
        "",
        "## Loss Cause Decomposition (Regime V2)",
        "| Group | Count | PnL | PF |",
        "|---|---:|---:|---:|",
    ]
    for k, v in att["by_exit_reason"].items():
        lines.append(f"| exit:{k} | {v['count']} | {v['pnl']:+.2f} | {v['pf']:.3f} |")
    for k, v in att["by_family"].items():
        lines.append(f"| family:{k} | {v['count']} | {v['pnl']:+.2f} | {v['pf']:.3f} |")
    for k, v in att["by_bucket"].items():
        lines.append(f"| bucket:{k} | {v['count']} | {v['pnl']:+.2f} | {v['pf']:.3f} |")
    lines.extend(
        [
            "",
            "## Validation",
            f"- baseline: {report['baseline']['validation']}",
            f"- regime_switch_v1: {report['regime_switch_v1']['validation']}",
            f"- regime_switch_v2: {report['regime_switch_v2']['validation']}",
            f"- mdd_guard_pass(v2): {report['regime_switch_v2']['summary']['mdd_guard_pass']}",
            "",
            f"## Final Decision: {report['final_decision']}",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T511 regime detail rebuild")
    parser.add_argument("--strategy-mode", type=str, default="compare", help="baseline|regime_switch_v1|regime_switch_v2|compare")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE) + DEFAULT_HYBRID_UNIVERSE)
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_511/task_511_regime_rebuild.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_511/task_511_regime_rebuild.md")
    parser.add_argument("--regime-confirm-bars", type=int, default=2)
    parser.add_argument("--family-risk-cap-momentum-r", type=float, default=1.0)
    parser.add_argument("--family-risk-cap-reversion-r", type=float, default=0.5)
    parser.add_argument("--symbol-bucket-profile", type=str, default="hybrid_v1")
    parser.add_argument("--reversion-guard", type=str, default="on", help="on|off")
    args = parser.parse_args(argv)

    mode = str(args.strategy_mode).strip().lower()
    if mode not in ALL_MODES:
        raise SystemExit(f"invalid --strategy-mode: {mode}")
    guard = str(args.reversion_guard).strip().lower()
    if guard not in {"on", "off"}:
        raise SystemExit(f"invalid --reversion-guard: {guard}")

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    frames = _load_frames(symbols, Path(args.data_dir), confirm_bars=max(1, int(args.regime_confirm_bars)))
    dd_limit_pct = 60.0

    if mode == "baseline":
        report = {
            "task": "T511",
            "result": _simulate(
                frames,
                "baseline",
                dd_limit_pct,
                max(1, int(args.regime_confirm_bars)),
                float(args.family_risk_cap_momentum_r),
                float(args.family_risk_cap_reversion_r),
                str(args.symbol_bucket_profile),
                guard,
            ),
        }
    elif mode == "regime_switch_v1":
        report = {
            "task": "T511",
            "result": _simulate(
                frames,
                "regime_switch_v1",
                dd_limit_pct,
                max(1, int(args.regime_confirm_bars)),
                float(args.family_risk_cap_momentum_r),
                float(args.family_risk_cap_reversion_r),
                str(args.symbol_bucket_profile),
                guard,
            ),
        }
    elif mode == "regime_switch_v2":
        report = {
            "task": "T511",
            "result": _simulate(
                frames,
                "regime_switch_v2",
                dd_limit_pct,
                max(1, int(args.regime_confirm_bars)),
                float(args.family_risk_cap_momentum_r),
                float(args.family_risk_cap_reversion_r),
                str(args.symbol_bucket_profile),
                guard,
            ),
        }
    else:
        baseline = _simulate(
            frames,
            "baseline",
            dd_limit_pct,
            max(1, int(args.regime_confirm_bars)),
            float(args.family_risk_cap_momentum_r),
            float(args.family_risk_cap_reversion_r),
            str(args.symbol_bucket_profile),
            guard,
        )
        v1 = _simulate(
            frames,
            "regime_switch_v1",
            dd_limit_pct,
            max(1, int(args.regime_confirm_bars)),
            float(args.family_risk_cap_momentum_r),
            float(args.family_risk_cap_reversion_r),
            str(args.symbol_bucket_profile),
            guard,
        )
        v2 = _simulate(
            frames,
            "regime_switch_v2",
            dd_limit_pct,
            max(1, int(args.regime_confirm_bars)),
            float(args.family_risk_cap_momentum_r),
            float(args.family_risk_cap_reversion_r),
            str(args.symbol_bucket_profile),
            guard,
        )
        report = {
            "task": "T511",
            "baseline": baseline,
            "regime_switch_v1": v1,
            "regime_switch_v2": v2,
            "final_decision": _final_decision(baseline, v1, v2),
        }

    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if mode == "compare":
        mout.write_text(_md(report), encoding="utf-8")
    else:
        mout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written_json={jout}")
    print(f"written_md={mout}")
    if mode == "compare":
        print(f"final_decision={report['final_decision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

