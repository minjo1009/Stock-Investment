from __future__ import annotations

import argparse
import concurrent.futures
import math
import os
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_tbl_314 import EntryMode, LifecycleMode, StopMode, StrategyConfig, run_tbl_backtest
from src.backtest.data_loader import DEFAULT_BASE_DIR, load_daily_bars
from src.strategy.conditions import prepare_condition_frame

INITIAL_CAPITAL = 100_000.0
RISK_PER_TRADE_PCT = 1.0
MAX_TOTAL_OPEN_RISK_PCT = 5.0 / 100.0
MAX_POSITIONS = 5
MAX_SYMBOL_WEIGHT_PCT = 25.0 / 100.0
DAILY_LOSS_LIMIT_PCT = 3.0 / 100.0
FEE_RATE = 0.0005
SLIPPAGE_BPS = 10.0

LEVERAGED_ETF = {"TQQQ", "SOXL", "UPRO", "TNA", "FAS", "LABU", "QLD", "USD", "SSO"}
INVERSE_ETF = {"SQQQ", "SPXU"}


@dataclass(frozen=True)
class StructuralConfig:
    strategy_mode: str = "STRUCTURAL_BREAKOUT_V1"
    universe_mode: str = "STOCK_ONLY"
    exclude_leveraged: bool = True
    exclude_inverse: bool = True
    structure_mode: str = "RANGE_COMPRESSION"
    breakout_trigger_mode: str = "HIGH_TOUCH"
    entry_model: str = "BREAKOUT_LEVEL_WITH_SLIPPAGE"
    stop_mode: str = "ATR_STOP"
    entry_bar_stop_mode: str = "DISABLE_ENTRY_BAR_STOP"
    range_lookback: int = 20
    max_range_width_pct: float = 0.10
    max_atr_pct: float = 0.08
    pivot_left: int = 3
    pivot_right: int = 3
    max_pivot_age: int = 40
    donchian_n: int = 55
    breakout_buffer_pct: float = 0.001
    max_gap_over_entry_pct: float = 0.05
    max_gap_pct: float = 0.08
    atr_multiplier: float = 2.0
    trailing_atr_multiplier: float = 3.0
    max_holding_days: int = 20
    min_avg_dollar_volume_20: float = 20_000_000.0
    min_close_location: float = 0.60
    max_return_3d: float = 0.12
    max_return_5d: float = 0.20
    max_close_to_sma20: float = 1.15
    volume_multiplier: float = 1.2
    min_initial_r_pct: float = 0.02
    max_initial_r_pct: float = 0.12
    apply_regime_filter: bool = False
    regime_block_if_unavailable: bool = False


@dataclass
class Position:
    symbol: str
    signal_date: pd.Timestamp
    entry_date: pd.Timestamp
    entry_price: float
    breakout_level: float
    breakout_level_source: str
    stop_price: float
    initial_stop: float
    atr_entry: float
    initial_r: float
    initial_r_pct: float
    quantity: float
    highest_close: float
    entry_open: float
    planned_entry_price: float
    filled_at_open: bool
    bars_held: int = 0
    original_quantity: float = 0.0
    realized_pnl_accum: float = 0.0
    realized_fee_accum: float = 0.0
    reduced_quantity_accum: float = 0.0
    size_action_taken: bool = False
    exit_action_taken: bool = False
    pending_action: str = ""
    pending_action_fraction: float = 0.0
    pending_action_rule: str = ""
    pending_action_trigger_date: str = ""
    triggered_rules: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PostEntryOverlayConfig:
    post_entry_rule_mode: str = "baseline"
    size_reduction_fraction: float = 0.5
    validation_bands: dict[str, dict[str, float]] | None = None


@dataclass(frozen=True)
class PreEntryFilterConfig:
    regime_conditioned_filter_mode: str = "off"
    regime_conditioned_rules: tuple[dict[str, Any], ...] = ()
    path_probability_filter_mode: str = "off"
    path_probability_rules: tuple[dict[str, Any], ...] = ()
    regime_filter_mode: str = "off"
    entry_quality_filter_mode: str = "off"
    entry_quality_score_bands: dict[str, float] | None = None
    bad_regimes: tuple[str, ...] = ()
    weak_regimes: tuple[str, ...] = ()
    sector_crowding_policy: dict[str, Any] | None = None
    metadata_lookup: dict[str, dict[str, Any]] | None = None
    weak_entry_reduce_fraction: float = 0.5
    weak_regime_reduce_fraction: float = 0.5


def _asset_type(symbol: str) -> str:
    s = str(symbol).upper()
    if s in LEVERAGED_ETF:
        return "LEVERAGED_ETF"
    if s in INVERSE_ETF:
        return "INVERSE_ETF"
    return "STOCK"


def _load_stock_symbols(base_dir: Path, cfg: StructuralConfig) -> list[str]:
    syms = sorted(p.stem.upper() for p in base_dir.glob("*.csv"))
    out: list[str] = []
    for s in syms:
        at = _asset_type(s)
        if cfg.exclude_leveraged and at == "LEVERAGED_ETF":
            continue
        if cfg.exclude_inverse and at == "INVERSE_ETF":
            continue
        if cfg.universe_mode == "STOCK_ONLY" and at != "STOCK":
            continue
        out.append(s)
    return out


def _prepare_symbol_frame(symbol: str, base_dir: Path) -> pd.DataFrame:
    raw = load_daily_bars(symbol, base_dir=base_dir)
    frame = prepare_condition_frame(raw).copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.sort_values("timestamp").reset_index(drop=True)

    close = pd.to_numeric(frame["close"], errors="coerce")
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    volume = pd.to_numeric(frame["volume"], errors="coerce")

    frame["atr_prev"] = pd.to_numeric(frame["atr14"], errors="coerce").shift(1)
    frame["std5_prev"] = close.pct_change().rolling(5).std(ddof=0).shift(1)
    frame["std20_prev"] = close.pct_change().rolling(20).std(ddof=0).shift(1)
    frame["avg_volume_20_prev"] = volume.rolling(20).mean().shift(1)
    frame["avg_dollar_volume_20"] = (close * volume).rolling(20).mean().shift(1)
    frame["turnover"] = close * volume
    frame["close_location"] = (close - low) / (high - low).replace(0.0, pd.NA)
    frame["ret_3d"] = close.pct_change(3)
    frame["ret_5d"] = close.pct_change(5)
    frame["sma20"] = close.rolling(20).mean()
    frame["close_to_sma20"] = close / frame["sma20"]
    frame["prev_close"] = close.shift(1)
    frame["gap_pct"] = frame["open"] / frame["prev_close"] - 1.0

    for n in (20, 55, 126, 252):
        frame[f"donchian_high_{n}"] = high.rolling(n).max().shift(1)

    return frame


def _build_pivot_levels(frame: pd.DataFrame, left: int, right: int) -> pd.DataFrame:
    high = pd.to_numeric(frame["high"], errors="coerce")
    level = pd.Series(index=frame.index, dtype=float)
    pdate = pd.Series(index=frame.index, dtype="datetime64[ns, UTC]")
    cdate = pd.Series(index=frame.index, dtype="datetime64[ns, UTC]")
    latest_level = None
    latest_pdate = None
    latest_cdate = None
    for i in range(len(frame)):
        p = i - right
        if p >= left:
            v = high.iloc[p]
            left_slice = high.iloc[p - left : p]
            right_slice = high.iloc[p + 1 : p + 1 + right]
            if pd.notna(v) and len(right_slice) == right and (v > left_slice.max()) and (v >= right_slice.max()):
                latest_level = float(v)
                latest_pdate = frame.iloc[p]["timestamp"]
                latest_cdate = frame.iloc[p + right]["timestamp"]
        level.iloc[i] = latest_level if latest_level is not None else math.nan
        pdate.iloc[i] = latest_pdate if latest_pdate is not None else pd.NaT
        cdate.iloc[i] = latest_cdate if latest_cdate is not None else pd.NaT
    out = frame.copy()
    out["pivot_level"] = level
    out["pivot_date"] = pdate
    out["pivot_confirmed_date"] = cdate
    return out


def _structure_signal(frame: pd.DataFrame, i: int, cfg: StructuralConfig) -> dict[str, Any] | None:
    row = frame.iloc[i]
    if cfg.structure_mode == "LONG_DONCHIAN":
        col = f"donchian_high_{cfg.donchian_n}"
        if pd.isna(row.get(col)):
            return None
        return {
            "breakout_level": float(row[col]),
            "breakout_level_source": col.upper(),
            "range_low": math.nan,
            "range_inbox_ratio": math.nan,
            "pivot_date": pd.NaT,
            "pivot_confirmed_date": pd.NaT,
            "pivot_age": math.nan,
        }

    if cfg.structure_mode == "RANGE_COMPRESSION":
        lo = int(cfg.range_lookback)
        if i - lo < 0:
            return None
        prev = frame.iloc[i - lo : i]
        range_high = float(pd.to_numeric(prev["high"], errors="coerce").max())
        range_low = float(pd.to_numeric(prev["low"], errors="coerce").min())
        prev_close = float(frame.iloc[i - 1]["close"])
        if prev_close <= 0:
            return None
        width = (range_high - range_low) / prev_close
        atr_prev = row.get("atr_prev")
        atr_pct = float(atr_prev / prev_close) if pd.notna(atr_prev) and prev_close > 0 else math.nan
        inbox_ratio = float(((prev["close"] <= range_high) & (prev["close"] >= range_low)).mean()) if len(prev) else math.nan
        if pd.isna(row.get("std5_prev")) or pd.isna(row.get("std20_prev")):
            return None
        if not (
            width <= cfg.max_range_width_pct
            and float(row["std5_prev"]) < float(row["std20_prev"])
            and (not pd.isna(atr_pct) and atr_pct <= cfg.max_atr_pct)
        ):
            return None
        return {
            "breakout_level": range_high,
            "breakout_level_source": "RANGE_COMPRESSION",
            "range_low": range_low,
            "range_inbox_ratio": inbox_ratio,
            "pivot_date": pd.NaT,
            "pivot_confirmed_date": pd.NaT,
            "pivot_age": math.nan,
        }

    if cfg.structure_mode == "PIVOT_HIGH":
        level = row.get("pivot_level")
        pdate = row.get("pivot_date")
        cdate = row.get("pivot_confirmed_date")
        ts = row["timestamp"]
        if pd.isna(level) or pd.isna(cdate) or not (ts > cdate):
            return None
        age = (ts - pdate).days if pd.notna(pdate) else math.nan
        if pd.notna(age) and age > cfg.max_pivot_age:
            return None
        return {
            "breakout_level": float(level),
            "breakout_level_source": "PIVOT_HIGH",
            "range_low": math.nan,
            "range_inbox_ratio": math.nan,
            "pivot_date": pdate,
            "pivot_confirmed_date": cdate,
            "pivot_age": float(age) if pd.notna(age) else math.nan,
        }
    return None


def _apply_filters(row: pd.Series, cfg: StructuralConfig) -> tuple[bool, list[str], str | None]:
    passed: list[str] = []
    if pd.isna(row.get("avg_dollar_volume_20")) or float(row["avg_dollar_volume_20"]) < cfg.min_avg_dollar_volume_20:
        return False, passed, "rejected_by_liquidity"
    passed.append("liquidity")

    if pd.isna(row.get("avg_volume_20_prev")) or pd.isna(row.get("volume")):
        return False, passed, "rejected_by_liquidity"
    if float(row["volume"]) < float(row["avg_volume_20_prev"]) * cfg.volume_multiplier:
        return False, passed, "rejected_by_liquidity"
    passed.append("volume")

    if float(row.get("ret_3d", 0.0)) > cfg.max_return_3d or float(row.get("ret_5d", 0.0)) > cfg.max_return_5d:
        return False, passed, "rejected_by_overextension"
    if pd.notna(row.get("close_to_sma20")) and float(row["close_to_sma20"]) > cfg.max_close_to_sma20:
        return False, passed, "rejected_by_overextension"
    passed.append("overextension")

    if pd.notna(row.get("gap_pct")) and float(row["gap_pct"]) > cfg.max_gap_pct:
        return False, passed, "rejected_by_gap_pct"
    passed.append("gap_pct")

    if cfg.breakout_trigger_mode == "HIGH_WITH_CLOSE_CONFIRM":
        if pd.isna(row.get("close_location")) or float(row["close_location"]) < cfg.min_close_location:
            return False, passed, "rejected_by_close_location"
        passed.append("close_location")
    return True, passed, None


def _safe_quantile_band(value: float, low: float, high: float, *, lower_is_bad: bool) -> str:
    if math.isnan(value):
        return "unknown"
    if lower_is_bad:
        if value <= low:
            return "weak"
        if value >= high:
            return "strong"
        return "mixed"
    if value >= high:
        return "high"
    if value <= low:
        return "low"
    return "mid"


def _future_window_metrics(frame: pd.DataFrame, entry_ts: pd.Timestamp, entry_price: float, horizon: int) -> dict[str, float]:
    if entry_ts not in frame.index or entry_price <= 0:
        return {"follow": math.nan, "adverse": math.nan, "retrace": math.nan}
    try:
        loc = int(frame.index.get_loc(entry_ts))
    except TypeError:
        return {"follow": math.nan, "adverse": math.nan, "retrace": math.nan}
    end_loc = min(loc + horizon - 1, len(frame) - 1)
    window = frame.iloc[loc : end_loc + 1]
    max_high = pd.to_numeric(window["high"], errors="coerce").max()
    min_low = pd.to_numeric(window["low"], errors="coerce").min()
    last_close = pd.to_numeric(window["close"], errors="coerce").iloc[-1]
    follow = max_high / entry_price - 1.0 if pd.notna(max_high) else math.nan
    adverse = min_low / entry_price - 1.0 if pd.notna(min_low) else math.nan
    retrace = 1.0 - (last_close / max_high) if pd.notna(max_high) and pd.notna(last_close) and max_high > 0 else math.nan
    return {"follow": float(follow), "adverse": float(adverse), "retrace": float(retrace)}


def _overlay_trade_id(symbol: str, signal_date: pd.Timestamp, entry_date: pd.Timestamp, breakout_level: float) -> str:
    return "|".join(
        [
            str(symbol),
            str(pd.Timestamp(signal_date).date()),
            str(pd.Timestamp(entry_date).date()),
            f"{float(breakout_level):.6f}",
        ]
    )


def _overlay_enabled(overlay: PostEntryOverlayConfig | None, rule: str) -> bool:
    if overlay is None:
        return False
    mode = str(overlay.post_entry_rule_mode)
    if mode == "baseline":
        return False
    if rule == "exit":
        return mode in {"exit_only", "exit_plus_size"}
    if rule == "size":
        return mode in {"size_only", "exit_plus_size"}
    return False


def _pre_entry_key(symbol: str, ts: pd.Timestamp) -> str:
    return f"{str(symbol).upper()}|{pd.Timestamp(ts).date().isoformat()}"


def _regime_conditioned_rule_match(
    metadata: dict[str, Any],
    regime_state: str,
    rule: dict[str, Any],
) -> bool:
    if str(rule.get("regime_state", "")) != regime_state:
        return False
    for condition in rule.get("conditions", ()):
        feature = str(condition.get("feature", ""))
        operator = str(condition.get("operator", "band_in"))
        values = condition.get("values", ())
        if not isinstance(values, (list, tuple, set)):
            values = (values,)
        feature_band = str(metadata.get(f"{feature}_band", ""))
        if operator == "band_in":
            if feature_band not in {str(value) for value in values}:
                return False
        elif operator == "band_not_in":
            if feature_band in {str(value) for value in values}:
                return False
        elif operator == "bool_is":
            expected = bool(condition.get("value"))
            if bool(metadata.get(feature, False)) != expected:
                return False
        else:
            return False
    return True


def _path_probability_rule_match(
    metadata: dict[str, Any],
    rule: dict[str, Any],
) -> bool:
    probability_key = str(rule.get("probability_key", ""))
    operator = str(rule.get("operator", "gt"))
    threshold = float(rule.get("threshold", math.nan))
    value = metadata.get(probability_key, math.nan)
    if pd.isna(value) or math.isnan(threshold):
        return False
    current = float(value)
    if operator == "gt":
        return current > threshold
    if operator == "ge":
        return current >= threshold
    if operator == "lt":
        return current < threshold
    if operator == "le":
        return current <= threshold
    return False


def _pre_entry_decision(
    symbol: str,
    ts: pd.Timestamp,
    pre_entry_filter: PreEntryFilterConfig | None,
) -> dict[str, Any]:
    if pre_entry_filter is None or pre_entry_filter.metadata_lookup is None:
        return {"action": "allow", "size_multiplier": 1.0, "reasons": [], "metadata": {}}
    metadata = pre_entry_filter.metadata_lookup.get(_pre_entry_key(symbol, ts), {})
    reasons: list[str] = []
    action = "allow"
    size_multiplier = 1.0

    if pre_entry_filter.path_probability_filter_mode != "off":
        for rule in pre_entry_filter.path_probability_rules:
            if not _path_probability_rule_match(metadata, rule):
                continue
            reasons.append(f"path_rule:{str(rule.get('rule_id', 'unnamed'))}")
            rule_action = str(rule.get("action", "allow"))
            if rule_action == "skip":
                action = "skip"
                size_multiplier = 0.0
                break
            if rule_action == "reduce":
                action = "reduce"
                size_multiplier = min(size_multiplier, float(rule.get("size_multiplier", 0.5)))
            if rule_action == "allow":
                continue

    regime_state = str(metadata.get("regime_state", ""))
    if pre_entry_filter.regime_conditioned_filter_mode != "off":
        for rule in pre_entry_filter.regime_conditioned_rules:
            if not _regime_conditioned_rule_match(metadata, regime_state, rule):
                continue
            reasons.append(f"rule:{str(rule.get('rule_id', 'unnamed'))}")
            rule_action = str(rule.get("action", "skip"))
            if rule_action == "skip":
                action = "skip"
                size_multiplier = 0.0
                break
            if rule_action == "reduce":
                action = "reduce"
                size_multiplier = min(size_multiplier, float(rule.get("size_multiplier", 0.5)))

    if pre_entry_filter.regime_filter_mode != "off":
        if regime_state in set(pre_entry_filter.bad_regimes):
            reasons.append(f"bad_regime:{regime_state}")
            action = "skip"
        elif regime_state in set(pre_entry_filter.weak_regimes):
            reasons.append(f"weak_regime:{regime_state}")
            action = "reduce"
            size_multiplier = min(size_multiplier, float(pre_entry_filter.weak_regime_reduce_fraction))

    entry_quality_band = str(metadata.get("entry_quality_band", ""))
    if pre_entry_filter.entry_quality_filter_mode != "off":
        if entry_quality_band == "low":
            reasons.append("entry_quality_low")
            action = "skip"
        elif entry_quality_band == "mid" and action != "skip":
            reasons.append("entry_quality_mid")
            action = "reduce"
            size_multiplier = min(size_multiplier, float(pre_entry_filter.weak_entry_reduce_fraction))

    policy = pre_entry_filter.sector_crowding_policy or {}
    if action != "skip":
        if bool(metadata.get("sector_crowding_high", False)) and entry_quality_band != "high":
            reasons.append("sector_crowding_high")
            if str(policy.get("high_crowding_action", "reduce")) == "skip":
                action = "skip"
            else:
                action = "reduce"
                size_multiplier = min(size_multiplier, float(policy.get("reduce_fraction", 0.5)))

    if action == "reduce":
        size_multiplier = max(min(float(size_multiplier), 1.0), 0.0)
        if size_multiplier >= 0.999999:
            action = "allow"
            reasons = []
    return {"action": action, "size_multiplier": size_multiplier, "reasons": reasons, "metadata": metadata}


def _evaluate_overlay_signal(
    frame: pd.DataFrame,
    pos: Position,
    horizon: int,
    overlay: PostEntryOverlayConfig | None,
) -> dict[str, Any]:
    if overlay is None or overlay.validation_bands is None:
        return {"trigger": False, "rule_name": "", "bands": {}}
    metrics = _future_window_metrics(frame, pos.entry_date, pos.entry_price, horizon)
    bands = overlay.validation_bands
    if horizon == 3:
        ft_bands = bands.get("follow_through_3d_pct", {})
        mae_bands = bands.get("adverse_excursion_3d_pct", {})
        ft_band = _safe_quantile_band(metrics["follow"], float(ft_bands.get("low", math.nan)), float(ft_bands.get("high", math.nan)), lower_is_bad=True)
        mae_value = abs(metrics["adverse"]) if not math.isnan(metrics["adverse"]) else math.nan
        mae_band = _safe_quantile_band(mae_value, float(mae_bands.get("low_abs", math.nan)), float(mae_bands.get("high_abs", math.nan)), lower_is_bad=False)
        return {
            "trigger": ft_band == "mixed" and mae_band == "high",
            "rule_name": "mixed_ft_high_mae",
            "bands": {"ft_3d_band": ft_band, "mae_3d_band": mae_band},
        }
    ft_bands = bands.get("follow_through_5d_pct", {})
    retrace_bands = bands.get("post_breakout_retrace_5d_pct", {})
    ft_band = _safe_quantile_band(metrics["follow"], float(ft_bands.get("low", math.nan)), float(ft_bands.get("high", math.nan)), lower_is_bad=True)
    retrace_band = _safe_quantile_band(metrics["retrace"], float(retrace_bands.get("low", math.nan)), float(retrace_bands.get("high", math.nan)), lower_is_bad=False)
    return {
        "trigger": ft_band == "weak" or retrace_band == "high",
        "rule_name": "weak_ft5_or_high_retrace5",
        "bands": {"ft_5d_band": ft_band, "retrace_5d_band": retrace_band},
    }


def _build_trade_row(
    pos: Position,
    row: pd.Series,
    *,
    ts: pd.Timestamp,
    exit_price: float,
    reason: str,
    scenario_name: str,
) -> dict[str, Any]:
    fee = abs(exit_price * pos.quantity) * FEE_RATE
    pnl = (exit_price - pos.entry_price) * pos.quantity - fee
    total_pnl = pos.realized_pnl_accum + pnl
    denominator = pos.initial_r * max(pos.original_quantity, pos.quantity)
    realized_r = total_pnl / denominator if denominator > 0 else 0.0
    return {
        "trade_id": _overlay_trade_id(pos.symbol, pos.signal_date, pos.entry_date, pos.breakout_level),
        "symbol": pos.symbol,
        "signal_date": str(pos.signal_date.date()),
        "entry_date": str(pos.entry_date.date()),
        "breakout_level": round(pos.breakout_level, 6),
        "entry_price": round(pos.entry_price, 6),
        "entry_open": round(pos.entry_open, 6),
        "planned_entry_price": round(pos.planned_entry_price, 6),
        "filled_at_open": pos.filled_at_open,
        "stop_price": round(pos.initial_stop, 6),
        "exit_date": str(ts.date()),
        "exit_reason": reason,
        "realized_R": round(realized_r, 6),
        "structure_mode": scenario_name.split("|")[0],
        "trigger_mode": scenario_name.split("|")[1] if "|" in scenario_name else "",
        "stop_mode": scenario_name.split("|")[3] if "|" in scenario_name and len(scenario_name.split("|")) > 3 else "",
        "pivot_date": "",
        "pivot_confirmed_date": "",
        "pivot_age": "",
        "breakout_level_source": pos.breakout_level_source,
        "gap_pct": round(float(row.get("gap_pct", 0.0)) if pd.notna(row.get("gap_pct")) else 0.0, 6),
        "gap_over_entry_pct": round(float(row["open"]) / pos.entry_price - 1.0, 6),
        "initial_R_pct": round(pos.initial_r_pct, 6),
        "filters_passed": "runtime",
        "notional": round(pos.entry_price * max(pos.original_quantity, pos.quantity), 6),
        "volume_participation": round(min(max(pos.original_quantity, pos.quantity) / max(float(row.get("volume", 1.0)), 1.0), 1.0), 6),
        "holding_days": int(pos.bars_held),
        "overlay_trigger_rules": "|".join(pos.triggered_rules),
        "overlay_trigger_count": len(pos.triggered_rules),
        "overlay_reduced_quantity": round(pos.reduced_quantity_accum, 6),
        "overlay_realized_pnl_accum": round(pos.realized_pnl_accum, 6),
    }


def _metrics(trades: list[dict[str, Any]], equity_curve: list[tuple[pd.Timestamp, float]]) -> dict[str, float]:
    eq = pd.Series([v for _, v in equity_curve], index=pd.to_datetime([t for t, _ in equity_curve], utc=True)).sort_index() if equity_curve else pd.Series(dtype=float)
    eqd = eq.resample("1D").last().ffill().dropna() if not eq.empty else pd.Series(dtype=float)
    final_equity = float(eqd.iloc[-1]) if not eqd.empty else INITIAL_CAPITAL
    start = eqd.index[0] if not eqd.empty else pd.Timestamp.utcnow()
    end = eqd.index[-1] if not eqd.empty else start
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = ((final_equity / INITIAL_CAPITAL) ** (1.0 / years) - 1.0) * 100.0 if final_equity > 0 else -100.0
    peak = -1e18
    mdd = 0.0
    for v in eqd.tolist():
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    rets = eqd.pct_change().dropna()
    sharpe = float(rets.mean() / rets.std(ddof=0) * math.sqrt(252)) if len(rets) > 2 and float(rets.std(ddof=0)) > 0 else 0.0
    rs = [float(t["realized_R"]) for t in trades]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r < 0]
    avg_win = statistics.fmean(wins) if wins else 0.0
    avg_loss = statistics.fmean(losses) if losses else 0.0
    win_rate = float(len(wins) / len(rs)) if rs else 0.0
    expectancy = float(sum(rs) / len(rs)) if rs else 0.0
    pf = float(sum(wins) / abs(sum(losses))) if losses else (999.0 if wins else 0.0)
    avg_holding = statistics.fmean(float(t.get("holding_days", 0)) for t in trades) if trades else 0.0
    total_r = float(sum(rs)) if rs else 0.0
    month_totals: dict[str, float] = {}
    for trade in trades:
        exit_month = str(trade.get("exit_date", ""))[:7]
        month_totals[exit_month] = month_totals.get(exit_month, 0.0) + float(trade.get("realized_R", 0.0))
    worst_month = min(month_totals.items(), key=lambda item: item[1])[0] if month_totals else ""
    worst_month_r = min(month_totals.values()) if month_totals else 0.0
    max_losing_streak = 0
    current_losing_streak = 0
    for trade in trades:
        if float(trade.get("realized_R", 0.0)) < 0:
            current_losing_streak += 1
            max_losing_streak = max(max_losing_streak, current_losing_streak)
        else:
            current_losing_streak = 0
    return {
        "cagr_pct": round(cagr, 6),
        "sharpe": round(sharpe, 6),
        "max_drawdown_pct": round(mdd * 100.0, 6),
        "expectancy_r": round(expectancy, 6),
        "trade_count": len(rs),
        "win_rate": round(win_rate, 6),
        "avg_win_r": round(avg_win, 6),
        "avg_loss_r": round(avg_loss, 6),
        "profit_factor": round(pf, 6),
        "total_return_pct": round((final_equity / INITIAL_CAPITAL - 1.0) * 100.0, 6),
        "total_r": round(total_r, 6),
        "avg_holding_days": round(avg_holding, 6),
        "worst_month": worst_month,
        "worst_month_r": round(worst_month_r, 6),
        "max_losing_streak": int(max_losing_streak),
    }


def _prepare_preloaded_frames(base_dir: Path, symbols: list[str]) -> tuple[dict[str, pd.DataFrame], list[pd.Timestamp]]:
    frames: dict[str, pd.DataFrame] = {}
    for s in symbols:
        fr = _prepare_symbol_frame(s, base_dir)
        # Precompute default pivot(3,3) once for reuse across scenarios.
        fr = _build_pivot_levels(fr, left=3, right=3)
        frames[s] = fr.set_index("timestamp", drop=False)
    timestamps = sorted({pd.Timestamp(ts) for fr in frames.values() for ts in fr.index})
    return frames, timestamps


def run_structural_backtest(
    cfg: StructuralConfig,
    base_dir: Path,
    *,
    preloaded_frames: dict[str, pd.DataFrame] | None = None,
    preloaded_timestamps: list[pd.Timestamp] | None = None,
    preloaded_symbols: list[str] | None = None,
    overlay: PostEntryOverlayConfig | None = None,
    pre_entry_filter: PreEntryFilterConfig | None = None,
) -> dict[str, Any]:
    symbols = list(preloaded_symbols) if preloaded_symbols is not None else _load_stock_symbols(base_dir, cfg)
    if preloaded_frames is None or preloaded_timestamps is None:
        frames, timestamps = _prepare_preloaded_frames(base_dir, symbols)
    else:
        frames = {symbol: preloaded_frames[symbol] for symbol in symbols if symbol in preloaded_frames}
        timestamps = preloaded_timestamps

    scenario_name = _scenario_name(cfg)
    cash = float(INITIAL_CAPITAL)
    positions: dict[str, Position] = {}
    trades: list[dict[str, Any]] = []
    equity_curve: list[tuple[pd.Timestamp, float]] = []
    overlay_trigger_log: list[dict[str, Any]] = []
    pre_entry_filter_log: list[dict[str, Any]] = []
    rejections = {k: 0 for k in [
        "rejected_by_open_risk",
        "rejected_by_symbol_weight",
        "rejected_by_daily_loss",
        "rejected_by_invalid_R",
        "rejected_by_liquidity",
        "rejected_by_overextension",
        "rejected_by_regime",
        "rejected_by_gap_pct",
        "rejected_by_gap_over_entry",
    ]}
    rejection_samples: list[dict[str, Any]] = []
    entry_diagnostics = {
        "triggered_candidates": 0,
        "filter_passed_candidates": 0,
        "planned_entries": 0,
        "executed_entries": 0,
        "open_gt_planned_entry_count": 0,
        "open_gt_actual_entry_count": 0,
        "fill_at_open_count": 0,
    }

    day = None
    day_start_equity = INITIAL_CAPITAL
    realized_today = 0.0

    for ts in timestamps:
        if day != ts.date():
            day = ts.date()
            mv = sum(float(frames[s].loc[ts]["close"]) * p.quantity for s, p in positions.items() if ts in frames[s].index)
            day_start_equity = cash + mv
            realized_today = 0.0

        for sym, pos in list(positions.items()):
            if ts not in frames[sym].index:
                continue
            row = frames[sym].loc[ts]

            if pos.pending_action:
                action_price = float(row["open"])
                qty_before = float(pos.quantity)
                if pos.pending_action == "reduce" and pos.quantity > 0:
                    reduce_qty = math.floor(pos.quantity * pos.pending_action_fraction)
                    if reduce_qty <= 0 and pos.quantity >= 1:
                        reduce_qty = 1
                    reduce_qty = min(float(reduce_qty), float(pos.quantity))
                    if reduce_qty > 0:
                        fee = abs(action_price * reduce_qty) * FEE_RATE
                        pnl = (action_price - pos.entry_price) * reduce_qty - fee
                        cash += action_price * reduce_qty - fee
                        realized_today += pnl
                        pos.realized_pnl_accum += pnl
                        pos.realized_fee_accum += fee
                        pos.reduced_quantity_accum += reduce_qty
                        pos.quantity -= reduce_qty
                        overlay_trigger_log.append(
                            {
                                "trade_id": _overlay_trade_id(pos.symbol, pos.signal_date, pos.entry_date, pos.breakout_level),
                                "rule": pos.pending_action_rule,
                                "action": "reduce_next_open",
                                "trigger_date": pos.pending_action_trigger_date,
                                "execution_date": str(ts.date()),
                                "execution_price": round(action_price, 6),
                                "quantity_before": round(qty_before, 6),
                                "quantity_changed": round(reduce_qty, 6),
                                "quantity_after": round(pos.quantity, 6),
                            }
                        )
                    pos.pending_action = ""
                    pos.pending_action_fraction = 0.0
                    pos.pending_action_rule = ""
                    pos.pending_action_trigger_date = ""
                elif pos.pending_action == "exit" and pos.quantity > 0:
                    overlay_trigger_log.append(
                        {
                            "trade_id": _overlay_trade_id(pos.symbol, pos.signal_date, pos.entry_date, pos.breakout_level),
                            "rule": pos.pending_action_rule,
                            "action": "exit_next_open",
                            "trigger_date": pos.pending_action_trigger_date,
                            "execution_date": str(ts.date()),
                            "execution_price": round(action_price, 6),
                            "quantity_before": round(qty_before, 6),
                            "quantity_changed": round(pos.quantity, 6),
                            "quantity_after": 0.0,
                        }
                    )
                    trades.append(
                        _build_trade_row(
                            pos,
                            row,
                            ts=ts,
                            exit_price=action_price,
                            reason="OVERLAY_EXIT_DAY5",
                            scenario_name=scenario_name,
                        )
                    )
                    fee = abs(action_price * pos.quantity) * FEE_RATE
                    pnl = (action_price - pos.entry_price) * pos.quantity - fee
                    cash += action_price * pos.quantity - fee
                    realized_today += pnl
                    del positions[sym]
                    continue
                else:
                    pos.pending_action = ""
                    pos.pending_action_fraction = 0.0
                    pos.pending_action_rule = ""
                    pos.pending_action_trigger_date = ""

            pos.bars_held += 1
            pos.highest_close = max(pos.highest_close, float(row["close"]))
            atr = float(row["atr_prev"]) if pd.notna(row.get("atr_prev")) else pos.atr_entry
            trail = pos.highest_close - cfg.trailing_atr_multiplier * atr
            stop = max(pos.stop_price, trail)
            stop_hit = float(row["low"]) <= stop
            if cfg.entry_bar_stop_mode == "DISABLE_ENTRY_BAR_STOP" and ts == pos.entry_date:
                stop_hit = False
            time_hit = pos.bars_held > cfg.max_holding_days
            if not stop_hit and not time_hit:
                if _overlay_enabled(overlay, "size") and (not pos.size_action_taken) and pos.bars_held == 3:
                    decision = _evaluate_overlay_signal(frames[sym], pos, 3, overlay)
                    if decision["trigger"]:
                        pos.size_action_taken = True
                        pos.pending_action = "reduce"
                        pos.pending_action_fraction = float(overlay.size_reduction_fraction if overlay is not None else 0.0)
                        pos.pending_action_rule = str(decision["rule_name"])
                        pos.pending_action_trigger_date = str(ts.date())
                        pos.triggered_rules.append(str(decision["rule_name"]))
                if _overlay_enabled(overlay, "exit") and (not pos.exit_action_taken) and pos.bars_held == 5:
                    decision = _evaluate_overlay_signal(frames[sym], pos, 5, overlay)
                    if decision["trigger"]:
                        pos.exit_action_taken = True
                        pos.pending_action = "exit"
                        pos.pending_action_fraction = 1.0
                        pos.pending_action_rule = str(decision["rule_name"])
                        pos.pending_action_trigger_date = str(ts.date())
                        pos.triggered_rules.append(str(decision["rule_name"]))
                pos.stop_price = stop
                continue
            reason = "TRAILING_STOP" if stop_hit else "TIME_EXIT"
            exit_price = stop if stop_hit else float(row["close"])
            if float(row["open"]) < exit_price:
                exit_price = float(row["open"])
            fee = abs(exit_price * pos.quantity) * FEE_RATE
            pnl = (exit_price - pos.entry_price) * pos.quantity - fee
            cash += exit_price * pos.quantity - fee
            realized_today += pnl
            trades.append(_build_trade_row(pos, row, ts=ts, exit_price=exit_price, reason=reason, scenario_name=scenario_name))
            del positions[sym]
            continue

        for sym, fr in frames.items():
            if sym in positions or ts not in fr.index:
                continue
            i = int(fr.index.get_loc(ts))
            if i < 30:
                continue
            row = fr.loc[ts]
            sig = _structure_signal(fr, i, cfg)
            if sig is None:
                continue
            breakout_level = float(sig["breakout_level"])
            trigger_level = breakout_level * (1.0 + cfg.breakout_buffer_pct)
            high = float(row["high"])
            close = float(row["close"])
            open_px = float(row["open"])
            trigger = high >= trigger_level
            if cfg.breakout_trigger_mode == "HIGH_WITH_CLOSE_CONFIRM":
                trigger = trigger and close >= breakout_level
            if not trigger:
                continue
            entry_diagnostics["triggered_candidates"] += 1
            ok, passed, reason = _apply_filters(row, cfg)
            if not ok:
                rejections[reason] += 1
                rejection_samples.append({"symbol": sym, "date": str(ts.date()), "reason": reason})
                continue
            entry_diagnostics["filter_passed_candidates"] += 1
            pre_entry_decision = _pre_entry_decision(sym, ts, pre_entry_filter)
            if pre_entry_decision["action"] == "skip":
                rejections["rejected_by_regime"] += 1
                pre_entry_filter_log.append(
                    {
                        "symbol": sym,
                        "date": str(ts.date()),
                        "action": "skip",
                        "size_multiplier": 0.0,
                        "reasons": "|".join(pre_entry_decision["reasons"]),
                        "regime_state": str(pre_entry_decision["metadata"].get("regime_state", "")),
                        "entry_quality_band": str(pre_entry_decision["metadata"].get("entry_quality_band", "")),
                        "entry_quality_score": pre_entry_decision["metadata"].get("entry_quality_score", math.nan),
                    }
                )
                continue
            if open_px > trigger_level * (1.0 + cfg.max_gap_over_entry_pct):
                rejections["rejected_by_gap_over_entry"] += 1
                rejection_samples.append({"symbol": sym, "date": str(ts.date()), "reason": "rejected_by_gap_over_entry"})
                continue
            planned_entry_price = trigger_level
            if cfg.entry_model == "CLOSE_CONFIRM_NEXT_OPEN" and cfg.breakout_trigger_mode == "HIGH_WITH_CLOSE_CONFIRM":
                planned_entry_price = open_px
                entry_price = open_px
            elif cfg.entry_model == "BREAKOUT_LEVEL_WITH_SLIPPAGE":
                planned_entry_price = trigger_level * (1.0 + SLIPPAGE_BPS / 10000.0)
                entry_price = planned_entry_price
                if open_px > entry_price:
                    entry_price = open_px
            else:
                planned_entry_price = trigger_level
                entry_price = open_px if open_px > trigger_level else trigger_level
            entry_diagnostics["planned_entries"] += 1
            if open_px > planned_entry_price:
                entry_diagnostics["open_gt_planned_entry_count"] += 1
            if open_px > entry_price:
                entry_diagnostics["open_gt_actual_entry_count"] += 1
            filled_at_open = math.isclose(open_px, entry_price, rel_tol=0.0, abs_tol=1e-9)
            if filled_at_open:
                entry_diagnostics["fill_at_open_count"] += 1
            prev_close = float(row["prev_close"]) if pd.notna(row.get("prev_close")) else open_px
            gap_pct = open_px / prev_close - 1.0 if prev_close > 0 else 0.0
            if gap_pct > cfg.max_gap_pct:
                rejections["rejected_by_gap_pct"] += 1
                continue
            atr = float(row["atr_prev"]) if pd.notna(row.get("atr_prev")) else 0.0
            if atr <= 0:
                rejections["rejected_by_invalid_R"] += 1
                continue
            initial_stop = float(sig["range_low"]) if cfg.stop_mode == "STRUCTURE_LOW_STOP" and pd.notna(sig.get("range_low")) else entry_price - cfg.atr_multiplier * atr
            initial_r = entry_price - initial_stop
            if initial_r <= 0:
                rejections["rejected_by_invalid_R"] += 1
                continue
            initial_r_pct = initial_r / entry_price
            if initial_r_pct < cfg.min_initial_r_pct or initial_r_pct > cfg.max_initial_r_pct:
                rejections["rejected_by_invalid_R"] += 1
                continue
            if len(positions) >= MAX_POSITIONS:
                rejections["rejected_by_open_risk"] += 1
                continue
            mv = sum(float(frames[s].loc[ts]["close"]) * p.quantity for s, p in positions.items() if ts in frames[s].index)
            open_risk = sum(max(p.entry_price - p.stop_price, 0.0) * p.quantity for p in positions.values())
            equity = cash + mv
            if realized_today <= -(day_start_equity * DAILY_LOSS_LIMIT_PCT):
                rejections["rejected_by_daily_loss"] += 1
                continue
            qty = math.floor((equity * RISK_PER_TRADE_PCT / 100.0) / initial_r)
            cap_qty = math.floor((equity * MAX_SYMBOL_WEIGHT_PCT) / entry_price)
            qty = min(qty, cap_qty)
            if pre_entry_decision["action"] == "reduce":
                qty = math.floor(qty * float(pre_entry_decision["size_multiplier"]))
            if qty <= 0:
                rejections["rejected_by_symbol_weight"] += 1
                continue
            if (open_risk + qty * initial_r) / max(equity, 1.0) > MAX_TOTAL_OPEN_RISK_PCT:
                rejections["rejected_by_open_risk"] += 1
                continue
            fee = abs(entry_price * qty) * FEE_RATE
            cash -= entry_price * qty + fee
            entry_diagnostics["executed_entries"] += 1
            if pre_entry_decision["action"] == "reduce":
                pre_entry_filter_log.append(
                    {
                        "symbol": sym,
                        "date": str(ts.date()),
                        "action": "reduce",
                        "size_multiplier": float(pre_entry_decision["size_multiplier"]),
                        "reasons": "|".join(pre_entry_decision["reasons"]),
                        "regime_state": str(pre_entry_decision["metadata"].get("regime_state", "")),
                        "entry_quality_band": str(pre_entry_decision["metadata"].get("entry_quality_band", "")),
                        "entry_quality_score": pre_entry_decision["metadata"].get("entry_quality_score", math.nan),
                    }
                )
            positions[sym] = Position(
                symbol=sym,
                signal_date=ts,
                entry_date=ts,
                entry_price=entry_price,
                breakout_level=breakout_level,
                breakout_level_source=str(sig["breakout_level_source"]),
                stop_price=initial_stop,
                initial_stop=initial_stop,
                atr_entry=atr,
                initial_r=initial_r,
                initial_r_pct=initial_r_pct,
                quantity=float(qty),
                original_quantity=float(qty),
                highest_close=float(row["close"]),
                entry_open=open_px,
                planned_entry_price=planned_entry_price,
                filled_at_open=filled_at_open,
            )

        mv = sum(float(frames[s].loc[ts]["close"]) * p.quantity for s, p in positions.items() if ts in frames[s].index)
        equity_curve.append((ts, cash + mv))

    if timestamps:
        ts = timestamps[-1]
        for sym, pos in list(positions.items()):
            if ts not in frames[sym].index:
                continue
            row = frames[sym].loc[ts]
            exit_price = float(row["close"])
            fee = abs(exit_price * pos.quantity) * FEE_RATE
            pnl = (exit_price - pos.entry_price) * pos.quantity - fee
            cash += exit_price * pos.quantity - fee
            trades.append(_build_trade_row(pos, row, ts=ts, exit_price=exit_price, reason="FINAL_LIQUIDATION", scenario_name=scenario_name))
            del positions[sym]
        equity_curve.append((ts, cash))

    metrics = _metrics(trades, equity_curve)
    by_symbol: dict[str, list[float]] = {}
    by_exit: dict[str, int] = {}
    for t in trades:
        by_symbol.setdefault(t["symbol"], []).append(float(t["realized_R"]))
        by_exit[t["exit_reason"]] = by_exit.get(t["exit_reason"], 0) + 1
    symbol_rows = []
    for sym, vals in sorted(by_symbol.items()):
        total_r = float(sum(vals))
        wins = sum(1 for v in vals if v > 0)
        symbol_rows.append({"symbol": sym, "trade_count": len(vals), "win_rate": wins / len(vals) if vals else 0.0, "expectancy_r": total_r / len(vals) if vals else 0.0, "total_r": total_r})
    total_r_all = sum(float(t["realized_R"]) for t in trades)
    sorted_sym = sorted(symbol_rows, key=lambda x: x["total_r"], reverse=True)
    top1_share = (sorted_sym[0]["total_r"] / total_r_all) if sorted_sym and total_r_all != 0 else 0.0
    top3_share = (sum(s["total_r"] for s in sorted_sym[:3]) / total_r_all) if sorted_sym and total_r_all != 0 else 0.0
    avg_notional = statistics.fmean(float(t["notional"]) for t in trades) if trades else 0.0
    avg_part = statistics.fmean(float(t["volume_participation"]) for t in trades) if trades else 0.0
    executed_entries = int(entry_diagnostics["executed_entries"])
    triggered_candidates = int(entry_diagnostics["triggered_candidates"])
    filter_passed_candidates = int(entry_diagnostics["filter_passed_candidates"])

    def _ratio(numerator: int, denominator: int) -> float:
        return round(float(numerator / denominator), 6) if denominator > 0 else 0.0

    return {
        "config": cfg.__dict__,
        "overlay": {
            "post_entry_rule_mode": overlay.post_entry_rule_mode if overlay is not None else "baseline",
            "size_reduction_fraction": overlay.size_reduction_fraction if overlay is not None else 0.0,
        },
        "pre_entry_filter": {
            "regime_filter_mode": pre_entry_filter.regime_filter_mode if pre_entry_filter is not None else "off",
            "entry_quality_filter_mode": pre_entry_filter.entry_quality_filter_mode if pre_entry_filter is not None else "off",
        },
        "symbols": symbols,
        "metrics": metrics,
        "trade_log": trades,
        "diagnostics": {
            "by_symbol": symbol_rows,
            "by_exit_reason": [{"exit_reason": k, "count": v} for k, v in sorted(by_exit.items())],
            "rejections": [{"reason": k, "count": v} for k, v in sorted(rejections.items())],
            "rejection_samples": rejection_samples[:200],
            "top1_symbol_total_R_share": round(top1_share, 6),
            "top3_symbol_total_R_share": round(top3_share, 6),
            "avg_notional_per_trade": round(avg_notional, 6),
            "avg_volume_participation": round(avg_part, 6),
            "capacity_warning": bool(avg_part > 0.02),
            "concentration_invalid": bool(top1_share > 0.40 or top3_share > 0.70),
            "triggered_candidates": triggered_candidates,
            "filter_passed_candidates": filter_passed_candidates,
            "executed_entries": executed_entries,
            "open_gt_planned_entry_count": int(entry_diagnostics["open_gt_planned_entry_count"]),
            "open_gt_actual_entry_count": int(entry_diagnostics["open_gt_actual_entry_count"]),
            "fill_at_open_count": int(entry_diagnostics["fill_at_open_count"]),
            "open_gt_planned_entry_ratio": _ratio(int(entry_diagnostics["open_gt_planned_entry_count"]), executed_entries),
            "open_gt_actual_entry_ratio": _ratio(int(entry_diagnostics["open_gt_actual_entry_count"]), executed_entries),
            "fill_at_open_ratio": _ratio(int(entry_diagnostics["fill_at_open_count"]), executed_entries),
            "rejected_by_gap_over_entry_ratio_vs_triggered": _ratio(int(rejections["rejected_by_gap_over_entry"]), triggered_candidates),
            "rejected_by_gap_over_entry_ratio_vs_filter_passed": _ratio(int(rejections["rejected_by_gap_over_entry"]), filter_passed_candidates),
            "overlay_trigger_log": overlay_trigger_log,
            "pre_entry_filter_log": pre_entry_filter_log,
        },
    }


def _scenario_name(cfg: StructuralConfig) -> str:
    parts = [
        cfg.structure_mode,
        cfg.breakout_trigger_mode,
        cfg.entry_model,
        cfg.stop_mode,
        cfg.entry_bar_stop_mode,
        f"atr{cfg.atr_multiplier}",
        f"hold{cfg.max_holding_days}",
        f"liq{int(cfg.min_avg_dollar_volume_20)}",
    ]
    if cfg.structure_mode == "RANGE_COMPRESSION":
        parts.extend([f"lb{cfg.range_lookback}", f"w{cfg.max_range_width_pct:.2f}"])
    elif cfg.structure_mode == "LONG_DONCHIAN":
        parts.append(f"n{cfg.donchian_n}")
    elif cfg.structure_mode == "PIVOT_HIGH":
        parts.append(f"age{cfg.max_pivot_age}")
    return "|".join(parts)


def _quick_configs() -> list[StructuralConfig]:
    return [
        StructuralConfig(structure_mode="RANGE_COMPRESSION", range_lookback=20, max_range_width_pct=0.10, atr_multiplier=2.0, max_holding_days=20),
        StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=20, atr_multiplier=2.0, max_holding_days=20),
        StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=55, atr_multiplier=2.0, max_holding_days=20),
        StructuralConfig(structure_mode="PIVOT_HIGH", max_pivot_age=40, atr_multiplier=2.0, max_holding_days=20),
    ]


def _full_configs(quick_results: list[dict[str, Any]]) -> list[StructuralConfig]:
    positive = {r["config"]["structure_mode"] for r in quick_results if float(r["metrics"]["expectancy_r"]) > 0}
    out: list[StructuralConfig] = []
    if "RANGE_COMPRESSION" in positive:
        for lb in (10, 20, 30):
            for w in (0.06, 0.10, 0.15):
                for sm in ("ATR_STOP", "STRUCTURE_LOW_STOP"):
                    for atr in (1.5, 2.0, 2.5):
                        for h in (10, 20, 30):
                            out.append(StructuralConfig(structure_mode="RANGE_COMPRESSION", range_lookback=lb, max_range_width_pct=w, stop_mode=sm, atr_multiplier=atr, max_holding_days=h))
    if "LONG_DONCHIAN" in positive:
        for n in (20, 55, 126, 252):
            for atr in (1.5, 2.0, 2.5):
                for h in (10, 20, 30):
                    out.append(StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=n, atr_multiplier=atr, max_holding_days=h))
    if "PIVOT_HIGH" in positive:
        for age in (20, 40, 60):
            for atr in (1.5, 2.0, 2.5):
                for h in (10, 20, 30):
                    out.append(StructuralConfig(structure_mode="PIVOT_HIGH", max_pivot_age=age, atr_multiplier=atr, max_holding_days=h))
    return out


def _chunked(items: list[StructuralConfig], n: int) -> list[list[StructuralConfig]]:
    n = max(1, n)
    return [items[i::n] for i in range(n) if items[i::n]]


def _run_config_batch_worker(payload: dict[str, Any]) -> list[dict[str, Any]]:
    base_dir = Path(payload["base_dir"])
    symbols = list(payload["symbols"])
    cfg_dicts = list(payload["configs"])
    pre_frames, pre_ts = _prepare_preloaded_frames(base_dir, symbols)
    out: list[dict[str, Any]] = []
    for c in cfg_dicts:
        cfg = StructuralConfig(**c)
        out.append(
            run_structural_backtest(
                cfg,
                base_dir,
                preloaded_frames=pre_frames,
                preloaded_timestamps=pre_ts,
                preloaded_symbols=symbols,
            )
        )
    return out


def _run_config_list(
    configs: list[StructuralConfig],
    *,
    base_dir: Path,
    stocks: list[str],
    jobs: int,
) -> list[dict[str, Any]]:
    if not configs:
        return []
    if jobs <= 1:
        pre_frames, pre_ts = _prepare_preloaded_frames(base_dir, stocks)
        return [
            run_structural_backtest(
                cfg,
                base_dir,
                preloaded_frames=pre_frames,
                preloaded_timestamps=pre_ts,
                preloaded_symbols=stocks,
            )
            for cfg in configs
        ]

    workers = max(1, min(jobs, len(configs)))
    chunks = _chunked(configs, workers)
    payloads = [
        {
            "base_dir": str(base_dir),
            "symbols": list(stocks),
            "configs": [c.__dict__ for c in chunk],
        }
        for chunk in chunks
    ]
    out: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_run_config_batch_worker, p) for p in payloads]
        for fut in concurrent.futures.as_completed(futures):
            out.extend(fut.result())
    return out


def _label(metrics: dict[str, Any], diag: dict[str, Any]) -> str:
    if (
        int(metrics["trade_count"]) >= 50
        and float(metrics["expectancy_r"]) > 0
        and float(metrics["sharpe"]) > 0.5
        and float(metrics["profit_factor"]) > 1.2
        and not bool(diag.get("concentration_invalid", False))
    ):
        return "valid"
    if int(metrics["trade_count"]) >= 50 and float(metrics["expectancy_r"]) > 0 and 0.2 <= float(metrics["sharpe"]) <= 0.5:
        return "weak_but_interesting"
    return "reject"


def write_outputs(results: list[dict[str, Any]], out_dir: Path, baseline: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    by_symbol_rows: list[dict[str, Any]] = []
    by_exit_rows: list[dict[str, Any]] = []
    reject_rows: list[dict[str, Any]] = []

    for r in results:
        cfg = StructuralConfig(**r["config"])
        m = r["metrics"]
        d = r["diagnostics"]
        summary_rows.append({
            "scenario": _scenario_name(cfg),
            "structure_mode": cfg.structure_mode,
            "trigger_mode": cfg.breakout_trigger_mode,
            "entry_model": cfg.entry_model,
            "stop_mode": cfg.stop_mode,
            "atr_multiplier": cfg.atr_multiplier,
            "max_holding_days": cfg.max_holding_days,
            **m,
            "top1_symbol_total_R_share": d["top1_symbol_total_R_share"],
            "top3_symbol_total_R_share": d["top3_symbol_total_R_share"],
            "avg_notional_per_trade": d["avg_notional_per_trade"],
            "avg_volume_participation": d["avg_volume_participation"],
            "triggered_candidates": d["triggered_candidates"],
            "executed_entries": d["executed_entries"],
            "open_gt_planned_entry_ratio": d["open_gt_planned_entry_ratio"],
            "open_gt_actual_entry_ratio": d["open_gt_actual_entry_ratio"],
            "fill_at_open_ratio": d["fill_at_open_ratio"],
            "rejected_by_gap_over_entry_ratio_vs_triggered": d["rejected_by_gap_over_entry_ratio_vs_triggered"],
            "capacity_warning": d["capacity_warning"],
            "label": _label(m, d),
        })
        trades.extend(r["trade_log"])
        by_symbol_rows.extend([{"scenario": _scenario_name(cfg), **x} for x in d["by_symbol"]])
        by_exit_rows.extend([{"scenario": _scenario_name(cfg), **x} for x in d["by_exit_reason"]])
        reject_rows.extend([{"scenario": _scenario_name(cfg), **x} for x in d["rejections"]])

    sdf = pd.DataFrame(summary_rows)
    sdf.to_csv(out_dir / "summary_matrix.csv", index=False)
    pd.DataFrame(by_symbol_rows).to_csv(out_dir / "diagnostics_by_symbol.csv", index=False)
    pd.DataFrame(by_exit_rows).to_csv(out_dir / "diagnostics_by_exit_reason.csv", index=False)
    pd.DataFrame(reject_rows).to_csv(out_dir / "rejection_report.csv", index=False)
    pd.DataFrame(trades).to_csv(out_dir / "trade_log.csv", index=False)

    md = [
        "# Task 322 Structural Breakout Summary",
        "",
        "## Baseline",
        f"- CAGR: {baseline['metrics']['cagr_pct']}%",
        f"- Sharpe: {baseline['metrics']['sharpe']}",
        f"- Expectancy R: {baseline['metrics']['expectancy_r']}",
        f"- Trades: {baseline['metrics']['trade_count']}",
        "",
        "|scenario|label|cagr|sharpe|expectancy_r|trades|pf|top1|top3|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in sdf.sort_values(["label", "sharpe"], ascending=[True, False]).head(30).iterrows():
        md.append(f"|{r['scenario']}|{r['label']}|{r['cagr_pct']}|{r['sharpe']}|{r['expectancy_r']}|{int(r['trade_count'])}|{r['profit_factor']}|{r['top1_symbol_total_R_share']}|{r['top3_symbol_total_R_share']}|")
    (out_dir / "summary_matrix.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    rep = [
        "# Task 322 Structural Breakout Report",
        f"- total_scenarios: {len(summary_rows)}",
        f"- valid: {int((sdf['label'] == 'valid').sum()) if not sdf.empty else 0}",
        f"- weak_but_interesting: {int((sdf['label'] == 'weak_but_interesting').sum()) if not sdf.empty else 0}",
        f"- reject: {int((sdf['label'] == 'reject').sum()) if not sdf.empty else 0}",
    ]
    (out_dir / "task_322_structural_breakout_report.md").write_text("\n".join(rep) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task 322 structural breakout")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--out-dir", type=str, default="docs/reports/task_322_structural_breakout")
    parser.add_argument("--quick-only", action="store_true")
    parser.add_argument("--max-full-scenarios", type=int, default=0)
    parser.add_argument("--jobs", type=int, default=0)
    args = parser.parse_args(argv)

    base_dir = Path(args.data_dir)
    stocks = [s for s in sorted(p.stem.upper() for p in base_dir.glob("*.csv")) if _asset_type(s) == "STOCK"]
    cpu = os.cpu_count() or 1
    jobs = int(args.jobs) if int(args.jobs) > 0 else min(4, cpu)
    jobs = max(1, jobs)
    baseline_cfg = StrategyConfig(entry_mode=EntryMode.NEXT_OPEN, lifecycle_mode=LifecycleMode.SIMPLE, stop_mode=StopMode.NEXT_BAR_ONLY, exclude_leveraged=True, exclude_inverse=True)
    baseline = run_tbl_backtest(symbols=stocks, base_dir=base_dir, volume_multiplier=1.5, config=baseline_cfg)

    quick = _run_config_list(_quick_configs(), base_dir=base_dir, stocks=stocks, jobs=jobs)
    full_cfgs = _full_configs(quick)
    if args.max_full_scenarios > 0:
        full_cfgs = full_cfgs[: int(args.max_full_scenarios)]
    full = [] if args.quick_only else _run_config_list(full_cfgs, base_dir=base_dir, stocks=stocks, jobs=jobs)
    bias_cfgs = [
        StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=55, entry_bar_stop_mode="ALLOW_SAME_BAR_STOP"),
        StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=55, entry_bar_stop_mode="DISABLE_ENTRY_BAR_STOP"),
    ]
    bias = _run_config_list(bias_cfgs, base_dir=base_dir, stocks=stocks, jobs=min(jobs, 2))
    all_results = quick + full + bias
    write_outputs(all_results, Path(args.out_dir), baseline)
    print(f"written_dir={args.out_dir}")
    print(f"quick_scenarios={len(quick)}")
    print(f"full_scenarios={len(full)}")
    print(f"total_scenarios={len(all_results)}")
    print(f"jobs={jobs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
