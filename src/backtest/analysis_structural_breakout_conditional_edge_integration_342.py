from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import (
    _load_frozen_behavior_state,
    _markdown_table,
)
from src.backtest.analysis_structural_breakout_intraday_signal_strengthening_339 import _sector_group
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import (
    DB_PATH,
    DEFAULT_COST_SCENARIOS,
    INITIAL_CAPITAL,
    ROLLING_WINDOWS,
    _current_subset_mask,
    _load_entry_only_master,
    _rolling_label,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import _load_intraday_bars


DEFAULT_OUT_DIR = Path("docs/reports/task_342_conditional_edge_integration")
TARGET_REGIME_SECTOR = "software_internet"
PRIMARY_VARIANTS = {"overlay_1p5_1p0", "overlay_1p5_0p5", "overlay_2p0_1p0", "overlay_2p0_0p5"}
WINDOW_MODE = "entry_only"


@dataclass(frozen=True)
class OverlayVariant:
    name: str
    size_up: float
    size_down: float
    uncovered_size: float
    variant_type: str


VARIANTS: tuple[OverlayVariant, ...] = (
    OverlayVariant("baseline_equal", 1.0, 1.0, 1.0, "baseline"),
    OverlayVariant("overlay_1p5_1p0", 1.5, 1.0, 1.0, "primary"),
    OverlayVariant("overlay_1p5_0p5", 1.5, 0.5, 1.0, "primary"),
    OverlayVariant("overlay_2p0_1p0", 2.0, 1.0, 1.0, "primary"),
    OverlayVariant("overlay_2p0_0p5", 2.0, 0.5, 1.0, "primary"),
    OverlayVariant("conservative_1p5_1p0", 1.5, 1.0, 1.0, "conservative"),
    OverlayVariant("filter_skip", 1.0, 0.0, 1.0, "aggressive_filter"),
    OverlayVariant("filter_reduce_0p25", 1.0, 0.25, 1.0, "aggressive_filter"),
)


def _f(value: float, digits: int = 6) -> float:
    return float(round(float(value), digits))


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return float(a / b)


def _max_drawdown_pct(equity_points: list[tuple[datetime, float]]) -> float:
    if not equity_points:
        return 0.0
    peak = equity_points[0][1]
    max_dd = 0.0
    for _ts, eq in equity_points:
        peak = max(peak, eq)
        if peak <= 0:
            continue
        dd = (peak - eq) / peak
        max_dd = max(max_dd, dd)
    return float(max_dd * 100.0)


def _daily_sharpe(equity_points: list[tuple[datetime, float]]) -> float:
    if not equity_points:
        return 0.0
    series = pd.Series(
        data=[value for _ts, value in equity_points],
        index=pd.to_datetime([ts for ts, _value in equity_points], utc=True),
    ).sort_index()
    daily = series.resample("1D").last().ffill().dropna()
    if len(daily) < 3:
        return 0.0
    rets = daily.pct_change().dropna()
    if rets.empty:
        return 0.0
    std = float(rets.std(ddof=0))
    if std <= 0:
        return 0.0
    return float((rets.mean() / std) * math.sqrt(252))


def _cagr(initial_capital: float, final_capital: float, start: datetime, end: datetime) -> float:
    if initial_capital <= 0 or final_capital <= 0:
        return -100.0
    years = max((pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25, 1.0 / 365.25)
    return float(((final_capital / initial_capital) ** (1.0 / years) - 1.0) * 100.0)


def _identity_split(full_df: pd.DataFrame, train_df: pd.DataFrame, oos_df: pd.DataFrame) -> pd.DataFrame:
    out = full_df.copy()
    train_ids = set(train_df["trade_id"].astype(str))
    oos_ids = set(oos_df["trade_id"].astype(str))
    out["current_split"] = np.where(
        out["trade_id"].astype(str).isin(oos_ids),
        "anchored_oos",
        np.where(out["trade_id"].astype(str).isin(train_ids), "train", "unmapped"),
    )
    return out


def _load_overlay_master() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df, oos_df, full_df = _load_frozen_behavior_state()
    master = _identity_split(full_df.copy(), train_df, oos_df)
    master["entry_ts"] = pd.to_datetime(master["entry_date"], errors="coerce", utc=True)
    master["exit_ts"] = pd.to_datetime(master["exit_date"], errors="coerce", utc=True)
    missing_exit = master["exit_ts"].isna()
    master.loc[missing_exit, "exit_ts"] = master.loc[missing_exit, "entry_ts"] + pd.to_timedelta(
        pd.to_numeric(master.loc[missing_exit, "holding_days"], errors="coerce").fillna(1.0),
        unit="D",
    )
    master["sector_group"] = master["sector_bucket"].map(_sector_group)
    master["realized_R"] = pd.to_numeric(master["realized_R"], errors="coerce")
    master["holding_days"] = pd.to_numeric(master["holding_days"], errors="coerce")

    coverage_flags = pd.read_csv(
        "docs/reports/task_338_intraday_evaluation_fix/task_338_trade_coverage_flags.csv"
    )
    coverage_flags = coverage_flags[coverage_flags["split"] == "full_period"].copy()
    coverage_flags = coverage_flags[["trade_id", "is_covered", "missing_reason"]].drop_duplicates("trade_id")
    coverage_flags["trade_id"] = coverage_flags["trade_id"].astype(str)
    master = master.merge(coverage_flags, on="trade_id", how="left")
    master["is_covered"] = master["is_covered"].fillna(False).astype(bool)
    master["missing_reason"] = master["missing_reason"].fillna("")

    covered_entry_master = _load_entry_only_master(DB_PATH).copy()
    covered_entry_master["trade_id"] = covered_entry_master["trade_id"].astype(str)
    covered_entry_master["entry_ts"] = pd.to_datetime(covered_entry_master["entry_ts"], errors="coerce", utc=True)
    if "exit_ts" in covered_entry_master.columns:
        covered_entry_master["exit_ts"] = pd.to_datetime(covered_entry_master["exit_ts"], errors="coerce", utc=True)
    covered_entry_master["is_base_subset"] = _current_subset_mask(covered_entry_master)
    covered_entry_master["is_condition_met"] = covered_entry_master["is_base_subset"] & (
        covered_entry_master["sector_group"].astype(str) == TARGET_REGIME_SECTOR
    )
    flag_df = covered_entry_master[["trade_id", "is_base_subset", "is_condition_met"]].drop_duplicates("trade_id")
    master = master.merge(flag_df, on="trade_id", how="left")
    master["is_base_subset"] = np.where(master["is_base_subset"].isna(), False, master["is_base_subset"]).astype(bool)
    master["is_condition_met"] = np.where(master["is_condition_met"].isna(), False, master["is_condition_met"]).astype(bool)
    return master.reset_index(drop=True), covered_entry_master.reset_index(drop=True)


def _condition_ids_for_window(covered_entry_master: pd.DataFrame, window: Any) -> tuple[set[str], set[str], int]:
    train_start = pd.Timestamp(window.train_start, tz="UTC")
    train_end = pd.Timestamp(window.train_end, tz="UTC")
    oos_start = pd.Timestamp(window.oos_start, tz="UTC")
    oos_end = pd.Timestamp(window.oos_end, tz="UTC")
    train_mask = (covered_entry_master["entry_ts"] >= train_start) & (
        covered_entry_master["entry_ts"] <= train_end
    )
    oos_mask = (covered_entry_master["entry_ts"] >= oos_start) & (
        covered_entry_master["entry_ts"] <= oos_end
    )
    train_df = covered_entry_master[train_mask].copy()
    oos_df = covered_entry_master[oos_mask].copy()
    labeled_oos = _rolling_label(train_df, oos_df) if not train_df.empty and not oos_df.empty else oos_df.copy()
    labeled_oos["sector_group"] = labeled_oos["sector_group"].fillna(labeled_oos["sector_bucket"].map(_sector_group))
    base_oos = labeled_oos[_current_subset_mask(labeled_oos)].copy()
    condition_oos = base_oos[base_oos["sector_group"].astype(str) == TARGET_REGIME_SECTOR].copy()
    covered_ids = set(labeled_oos["trade_id"].astype(str))
    condition_ids = set(condition_oos["trade_id"].astype(str))
    return covered_ids, condition_ids, int(len(base_oos))


def _assign_multiplier(
    df: pd.DataFrame,
    variant: OverlayVariant,
    universe_name: str,
    *,
    condition_mask: pd.Series | None = None,
    covered_mask: pd.Series | None = None,
) -> pd.DataFrame:
    scoped = df.copy()
    cond = condition_mask if condition_mask is not None else scoped["is_condition_met"].astype(bool)
    covered = covered_mask if covered_mask is not None else scoped["is_covered"].astype(bool)
    if universe_name == "covered_only":
        scoped = scoped[covered].copy()
        cond = cond.loc[scoped.index]
        covered = covered.loc[scoped.index]
        scoped["size_multiplier"] = np.where(cond, variant.size_up, variant.size_down)
    else:
        scoped["size_multiplier"] = np.where(cond, variant.size_up, np.where(covered, variant.size_down, variant.uncovered_size))
    scoped["condition_met_effective"] = cond.astype(bool)
    scoped["scaled_R"] = pd.to_numeric(scoped["realized_R"], errors="coerce") * pd.to_numeric(scoped["size_multiplier"], errors="coerce")
    return scoped


def _daily_curve_from_event_returns(df: pd.DataFrame, column: str = "scaled_R") -> tuple[pd.Series, list[tuple[pd.Timestamp, float]]]:
    scoped = df.sort_values("entry_ts").copy()
    if scoped.empty:
        return pd.Series(dtype=float), []
    equity = INITIAL_CAPITAL
    points: list[tuple[pd.Timestamp, float]] = []
    for row in scoped.itertuples(index=False):
        realized_r = float(getattr(row, column))
        equity *= max(1.0 + (realized_r / 100.0), 0.01)
        ts = pd.Timestamp(row.exit_ts if getattr(row, "exit_ts", None) is not None else row.entry_ts)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        points.append((ts, equity))
    daily_curve = pd.Series([v for _, v in points], index=pd.to_datetime([t for t, _ in points], utc=True)).sort_index()
    daily_curve = daily_curve.resample("1D").last().ffill().dropna()
    return daily_curve, points


def _drawdown_duration_days(daily_curve: pd.Series) -> int:
    if daily_curve.empty:
        return 0
    running_max = daily_curve.cummax()
    underwater = daily_curve < running_max
    max_duration = 0
    cur = 0
    for is_under in underwater.tolist():
        if is_under:
            cur += 1
            max_duration = max(max_duration, cur)
        else:
            cur = 0
    return int(max_duration)


def _tail_risk(series: pd.Series, q: float) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return math.nan
    return float(numeric.quantile(q))


def _concentration_share(df: pd.DataFrame, group_col: str, value_col: str = "scaled_R") -> float:
    if df.empty:
        return math.nan
    abs_r = pd.to_numeric(df[value_col], errors="coerce").abs()
    total = float(abs_r.sum())
    if total <= 0:
        return 0.0
    grouped = df.assign(abs_r=abs_r).groupby(group_col)["abs_r"].sum()
    return float(grouped.max() / total) if not grouped.empty else math.nan


def _portfolio_metrics(df: pd.DataFrame, column: str = "scaled_R") -> dict[str, Any]:
    if df.empty:
        return {
            "final_capital_proxy": INITIAL_CAPITAL,
            "return_pct": 0.0,
            "cagr": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "expectancy": math.nan,
            "trade_count": 0,
            "drawdown_duration_days": 0,
            "returns_volatility": 0.0,
            "tail_risk_p05": math.nan,
            "tail_risk_p01": math.nan,
            "daily_curve": pd.Series(dtype=float),
        }
    daily_curve, points = _daily_curve_from_event_returns(df, column=column)
    realized = pd.to_numeric(df[column], errors="coerce")
    wins = realized[realized > 0]
    losses = realized[realized < 0]
    gross_profit = float(wins.sum())
    gross_loss_abs = abs(float(losses.sum()))
    profit_factor = (gross_profit / gross_loss_abs) if gross_loss_abs > 0 else float("inf")
    win_rate = float((realized > 0).mean()) * 100.0 if not realized.empty else 0.0
    final_capital = float(daily_curve.iloc[-1]) if not daily_curve.empty else INITIAL_CAPITAL
    start = pd.Timestamp(df["entry_ts"].min())
    end = pd.Timestamp(df["exit_ts"].max())
    daily_returns = daily_curve.pct_change().dropna() if not daily_curve.empty else pd.Series(dtype=float)
    metrics = {
        "final_capital_proxy": _f(final_capital, 2),
        "return_pct": _f(_safe_div(final_capital - INITIAL_CAPITAL, INITIAL_CAPITAL) * 100.0),
        "cagr": _f(_cagr(INITIAL_CAPITAL, final_capital, start.to_pydatetime(), end.to_pydatetime())),
        "sharpe": _f(_daily_sharpe(points)),
        "max_drawdown_pct": _f(_max_drawdown_pct(points)),
        "profit_factor": _f(profit_factor),
        "win_rate": _f(win_rate),
        "expectancy": _f(float(realized.mean())),
        "trade_count": int(len(df)),
        "drawdown_duration_days": int(_drawdown_duration_days(daily_curve)),
        "returns_volatility": _f(float(daily_returns.std(ddof=0)) if not daily_returns.empty else 0.0),
        "tail_risk_p05": _f(_tail_risk(realized, 0.05)) if not realized.empty else math.nan,
        "tail_risk_p01": _f(_tail_risk(realized, 0.01)) if not realized.empty else math.nan,
        "daily_curve": daily_curve,
    }
    return metrics


def _variant_lookup() -> dict[str, OverlayVariant]:
    return {variant.name: variant for variant in VARIANTS}


def _portfolio_comparison(master_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[tuple[str, str, str], pd.DataFrame], pd.DataFrame]:
    rows = []
    scoped_frames: dict[tuple[str, str, str], pd.DataFrame] = {}
    oos_rows = []
    split_frames = {
        "full_period": master_df.copy(),
        "anchored_oos": master_df[master_df["current_split"] == "anchored_oos"].copy(),
    }
    for universe_name in ("covered_only", "hybrid_full"):
        for scope_name, scope_df in split_frames.items():
            for variant in VARIANTS:
                assigned = _assign_multiplier(scope_df, variant, universe_name)
                metrics = _portfolio_metrics(assigned)
                rows.append(
                    {
                        "universe": universe_name,
                        "scope": scope_name,
                        "variant": variant.name,
                        "variant_type": variant.variant_type,
                        "cagr": metrics["cagr"],
                        "sharpe": metrics["sharpe"],
                        "max_drawdown_pct": metrics["max_drawdown_pct"],
                        "expectancy": metrics["expectancy"],
                        "profit_factor": metrics["profit_factor"],
                        "win_rate": metrics["win_rate"],
                        "trade_count": metrics["trade_count"],
                        "final_capital_proxy": metrics["final_capital_proxy"],
                        "return_pct": metrics["return_pct"],
                    }
                )
                scoped_frames[(universe_name, scope_name, variant.name)] = assigned
            base = next(row for row in rows if row["universe"] == universe_name and row["scope"] == scope_name and row["variant"] == "baseline_equal")
            for row in [r for r in rows if r["universe"] == universe_name and r["scope"] == scope_name]:
                if row["variant"] == "baseline_equal":
                    continue
                oos_rows.append(
                    {
                        "universe": universe_name,
                        "variant": row["variant"],
                        "variant_type": row["variant_type"],
                        "baseline_sharpe": base["sharpe"],
                        "overlay_sharpe": row["sharpe"],
                        "sharpe_delta": _f(float(row["sharpe"]) - float(base["sharpe"])),
                        "baseline_max_drawdown_pct": base["max_drawdown_pct"],
                        "overlay_max_drawdown_pct": row["max_drawdown_pct"],
                        "mdd_delta": _f(float(row["max_drawdown_pct"]) - float(base["max_drawdown_pct"])),
                        "baseline_cagr": base["cagr"],
                        "overlay_cagr": row["cagr"],
                        "cagr_delta": _f(float(row["cagr"]) - float(base["cagr"])),
                        "baseline_expectancy": base["expectancy"],
                        "overlay_expectancy": row["expectancy"],
                        "expectancy_delta": _f(float(row["expectancy"]) - float(base["expectancy"])) if not pd.isna(row["expectancy"]) and not pd.isna(base["expectancy"]) else math.nan,
                        "trade_count": row["trade_count"],
                        "scope": scope_name,
                    }
                )
    portfolio_df = pd.DataFrame(rows)
    oos_df = pd.DataFrame([row for row in oos_rows if row["scope"] == "anchored_oos"])
    return portfolio_df, scoped_frames, oos_df


def _risk_metrics(portfolio_df: pd.DataFrame, scoped_frames: dict[tuple[str, str, str], pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for (universe_name, scope_name, variant_name), frame in scoped_frames.items():
        metrics = _portfolio_metrics(frame)
        rows.append(
            {
                "universe": universe_name,
                "scope": scope_name,
                "variant": variant_name,
                "drawdown_depth_pct": metrics["max_drawdown_pct"],
                "drawdown_duration_days": metrics["drawdown_duration_days"],
                "returns_volatility": metrics["returns_volatility"],
                "tail_risk_p05": metrics["tail_risk_p05"],
                "tail_risk_p01": metrics["tail_risk_p01"],
                "symbol_concentration_share": _f(_concentration_share(frame, "symbol")),
                "sector_concentration_share": _f(_concentration_share(frame, "sector_group")),
                "top_symbol": str(frame.assign(abs_r=pd.to_numeric(frame["scaled_R"], errors="coerce").abs()).groupby("symbol")["abs_r"].sum().sort_values(ascending=False).index[0]) if not frame.empty else "",
                "top_sector": str(frame.assign(abs_r=pd.to_numeric(frame["scaled_R"], errors="coerce").abs()).groupby("sector_group")["abs_r"].sum().sort_values(ascending=False).index[0]) if not frame.empty else "",
            }
        )
    return pd.DataFrame(rows)


def _contribution_analysis(scoped_frames: dict[tuple[str, str, str], pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for (universe_name, scope_name, variant_name), frame in scoped_frames.items():
        if scope_name != "anchored_oos":
            continue
        total_return = float(pd.to_numeric(frame["scaled_R"], errors="coerce").sum())
        for bucket_name, scoped in (
            ("condition_met", frame[frame["condition_met_effective"]].copy()),
            ("non_condition", frame[~frame["condition_met_effective"]].copy()),
        ):
            realized = pd.to_numeric(scoped["scaled_R"], errors="coerce")
            rows.append(
                {
                    "universe": universe_name,
                    "variant": variant_name,
                    "bucket": bucket_name,
                    "trade_count": int(len(scoped)),
                    "return_contribution": _f(float(realized.sum())) if not realized.empty else 0.0,
                    "expectancy": _f(float(realized.mean())) if not realized.empty else math.nan,
                    "win_rate": _f(float((realized > 0).mean()) * 100.0) if not realized.empty else math.nan,
                    "capital_weighted_contribution": _f(_safe_div(float(realized.sum()), total_return)) if abs(total_return) > 1e-9 else 0.0,
                }
            )
    return pd.DataFrame(rows)


def _rolling_oos(master_df: pd.DataFrame, covered_entry_master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    variant_lookup = _variant_lookup()
    for universe_name in ("covered_only", "hybrid_full"):
        for window in ROLLING_WINDOWS:
            oos_start = pd.Timestamp(window.oos_start, tz="UTC")
            oos_end = pd.Timestamp(window.oos_end, tz="UTC")
            oos_mask_full = (master_df["entry_ts"] >= oos_start) & (master_df["entry_ts"] <= oos_end)
            oos_full = master_df[oos_mask_full].copy()
            covered_ids, condition_ids, subset_count = _condition_ids_for_window(covered_entry_master, window)
            cond_mask = oos_full["trade_id"].astype(str).isin(condition_ids)
            covered_mask = oos_full["trade_id"].astype(str).isin(covered_ids)
            baseline_frame = _assign_multiplier(oos_full, variant_lookup["baseline_equal"], universe_name, condition_mask=cond_mask, covered_mask=covered_mask)
            baseline_metrics = _portfolio_metrics(baseline_frame)
            for variant in VARIANTS:
                if variant.name == "baseline_equal":
                    continue
                overlay_frame = _assign_multiplier(oos_full, variant, universe_name, condition_mask=cond_mask, covered_mask=covered_mask)
                overlay_metrics = _portfolio_metrics(overlay_frame)
                rows.append(
                    {
                        "universe": universe_name,
                        "window_id": window.window_id,
                        "variant": variant.name,
                        "variant_type": variant.variant_type,
                        "subset_trade_count": int(subset_count),
                        "condition_met_trade_count": int(cond_mask.sum()),
                        "baseline_expectancy": baseline_metrics["expectancy"],
                        "overlay_expectancy": overlay_metrics["expectancy"],
                        "baseline_sharpe_proxy": baseline_metrics["sharpe"],
                        "overlay_sharpe_proxy": overlay_metrics["sharpe"],
                        "baseline_mdd_proxy": baseline_metrics["max_drawdown_pct"],
                        "overlay_mdd_proxy": overlay_metrics["max_drawdown_pct"],
                        "status": "ok" if len(overlay_frame) > 0 else "insufficient_sample",
                    }
                )
    return pd.DataFrame(rows)


def _apply_cost_scaled(df: pd.DataFrame, slippage_rate: float, fee_rate: float) -> pd.Series:
    cost_r = (float(slippage_rate) + float(fee_rate)) / 0.01
    multiplier = pd.to_numeric(df["size_multiplier"], errors="coerce").fillna(1.0)
    realized = pd.to_numeric(df["scaled_R"], errors="coerce")
    return realized - (cost_r * multiplier)


def _execution_stress(scoped_frames: dict[tuple[str, str, str], pd.DataFrame]) -> pd.DataFrame:
    scenarios = [
        ("baseline_cost", DEFAULT_COST_SCENARIOS[0].slippage_rate, DEFAULT_COST_SCENARIOS[0].fee_rate),
        ("cost_2x", DEFAULT_COST_SCENARIOS[1].slippage_rate, DEFAULT_COST_SCENARIOS[1].fee_rate),
        ("cost_3x", DEFAULT_COST_SCENARIOS[2].slippage_rate, DEFAULT_COST_SCENARIOS[2].fee_rate),
    ]
    rows = []
    for (universe_name, scope_name, variant_name), frame in scoped_frames.items():
        if scope_name != "anchored_oos":
            continue
        for scenario_name, slippage, fee in scenarios:
            adjusted_frame = frame.copy()
            adjusted_frame["scaled_R"] = _apply_cost_scaled(frame, slippage, fee)
            metrics = _portfolio_metrics(adjusted_frame)
            rows.append(
                {
                    "universe": universe_name,
                    "variant": variant_name,
                    "scenario": scenario_name,
                    "expectancy_after_cost": metrics["expectancy"],
                    "sharpe_after_cost": metrics["sharpe"],
                    "return_after_cost": metrics["return_pct"],
                    "mdd_after_cost": metrics["max_drawdown_pct"],
                    "trade_count": metrics["trade_count"],
                    "edge_survives_cost": bool(metrics["expectancy"] > 0),
                }
            )
    return pd.DataFrame(rows)


def _best_primary_variant(portfolio_df: pd.DataFrame) -> str:
    anchored = portfolio_df[
        (portfolio_df["universe"] == "hybrid_full")
        & (portfolio_df["scope"] == "anchored_oos")
        & (portfolio_df["variant"].isin(PRIMARY_VARIANTS))
    ].copy()
    baseline = portfolio_df[
        (portfolio_df["universe"] == "hybrid_full")
        & (portfolio_df["scope"] == "anchored_oos")
        & (portfolio_df["variant"] == "baseline_equal")
    ].iloc[0]
    anchored["sharpe_delta"] = pd.to_numeric(anchored["sharpe"], errors="coerce") - float(baseline["sharpe"])
    anchored["mdd_improvement"] = float(baseline["max_drawdown_pct"]) - pd.to_numeric(anchored["max_drawdown_pct"], errors="coerce")
    anchored["expectancy_delta"] = pd.to_numeric(anchored["expectancy"], errors="coerce") - float(baseline["expectancy"])
    anchored = anchored.sort_values(["sharpe_delta", "mdd_improvement", "expectancy_delta", "cagr"], ascending=[False, False, False, False])
    return str(anchored.iloc[0]["variant"])


def _final_decision(
    portfolio_df: pd.DataFrame,
    rolling_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    stress_df: pd.DataFrame,
) -> pd.DataFrame:
    best_variant = _best_primary_variant(portfolio_df)
    base = portfolio_df[
        (portfolio_df["universe"] == "hybrid_full")
        & (portfolio_df["scope"] == "anchored_oos")
        & (portfolio_df["variant"] == "baseline_equal")
    ].iloc[0]
    best = portfolio_df[
        (portfolio_df["universe"] == "hybrid_full")
        & (portfolio_df["scope"] == "anchored_oos")
        & (portfolio_df["variant"] == best_variant)
    ].iloc[0]
    rolling_best = rolling_df[(rolling_df["universe"] == "hybrid_full") & (rolling_df["variant"] == best_variant)].copy()
    rolling_positive = int(((pd.to_numeric(rolling_best["overlay_sharpe_proxy"], errors="coerce") > pd.to_numeric(rolling_best["baseline_sharpe_proxy"], errors="coerce")) & (pd.to_numeric(rolling_best["overlay_expectancy"], errors="coerce") >= pd.to_numeric(rolling_best["baseline_expectancy"], errors="coerce"))).sum())
    best_risk = risk_df[(risk_df["universe"] == "hybrid_full") & (risk_df["scope"] == "anchored_oos") & (risk_df["variant"] == best_variant)].iloc[0]
    base_risk = risk_df[(risk_df["universe"] == "hybrid_full") & (risk_df["scope"] == "anchored_oos") & (risk_df["variant"] == "baseline_equal")].iloc[0]
    stress_best = stress_df[(stress_df["universe"] == "hybrid_full") & (stress_df["variant"] == best_variant)].copy()
    survives_2x = bool(stress_best.loc[stress_best["scenario"] == "cost_2x", "edge_survives_cost"].astype(bool).any())
    survives_3x = bool(stress_best.loc[stress_best["scenario"] == "cost_3x", "edge_survives_cost"].astype(bool).any())
    sharpe_up = float(best["sharpe"]) > float(base["sharpe"])
    mdd_down = float(best["max_drawdown_pct"]) < float(base["max_drawdown_pct"])
    expectancy_up = float(best["expectancy"]) >= float(base["expectancy"])
    cagr_up = float(best["cagr"]) >= float(base["cagr"])
    concentration_ok = float(best_risk["symbol_concentration_share"]) <= max(0.60, float(base_risk["symbol_concentration_share"]) + 0.10)

    if (not sharpe_up) or (not mdd_down) or ((not expectancy_up) and (not cagr_up)) or (rolling_positive < 2) or (not survives_2x):
        decision = "NO_IMPROVEMENT"
        reason = f"{best_variant} did not deliver robust hybrid_full anchored OOS improvement after rolling or cost checks"
    elif rolling_positive < 3 or not concentration_ok:
        decision = "WEAK_IMPROVEMENT"
        reason = f"{best_variant} improved anchored OOS but remains fragile across rolling windows or concentration checks"
    elif survives_2x and sharpe_up and mdd_down and expectancy_up and concentration_ok:
        full_best = portfolio_df[
            (portfolio_df["universe"] == "hybrid_full")
            & (portfolio_df["scope"] == "full_period")
            & (portfolio_df["variant"] == best_variant)
        ].iloc[0]
        full_base = portfolio_df[
            (portfolio_df["universe"] == "hybrid_full")
            & (portfolio_df["scope"] == "full_period")
            & (portfolio_df["variant"] == "baseline_equal")
        ].iloc[0]
        if survives_3x and float(full_best["sharpe"]) >= float(full_base["sharpe"]) and float(full_best["cagr"]) >= float(full_base["cagr"]):
            decision = "DEPLOYABLE_OVERLAY"
            reason = f"{best_variant} improved hybrid_full OOS/full-period metrics and survived severe cost stress"
        else:
            decision = "MEANINGFUL_IMPROVEMENT"
            reason = f"{best_variant} improved hybrid_full anchored OOS and rolling behavior with acceptable concentration"
    else:
        decision = "WEAK_IMPROVEMENT"
        reason = f"{best_variant} showed only partial overlay improvement"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "best_primary_variant": best_variant,
                "anchored_oos_sharpe_delta": _f(float(best["sharpe"]) - float(base["sharpe"])),
                "anchored_oos_mdd_delta": _f(float(best["max_drawdown_pct"]) - float(base["max_drawdown_pct"])),
                "anchored_oos_expectancy_delta": _f(float(best["expectancy"]) - float(base["expectancy"])),
                "rolling_positive_windows": rolling_positive,
                "survives_cost_2x": survives_2x,
                "survives_cost_3x": survives_3x,
                "symbol_concentration_share": _f(float(best_risk["symbol_concentration_share"])),
                "sector_concentration_share": _f(float(best_risk["sector_concentration_share"])),
            }
        ]
    )


def _markdown_report(
    out_dir: Path,
    portfolio_df: pd.DataFrame,
    oos_df: pd.DataFrame,
    rolling_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    stress_df: pd.DataFrame,
    final_decision_df: pd.DataFrame,
) -> None:
    best_variant = str(final_decision_df.iloc[0]["best_primary_variant"])
    decision = str(final_decision_df.iloc[0]["decision"])
    best_oos = oos_df[(oos_df["universe"] == "hybrid_full") & (oos_df["variant"] == best_variant)].iloc[0]
    best_risk = risk_df[(risk_df["universe"] == "hybrid_full") & (risk_df["scope"] == "anchored_oos") & (risk_df["variant"] == best_variant)].iloc[0]
    lines: list[str] = [
        "# Task 342: Conditional Edge Integration & Portfolio-Level Validation",
        "",
        f"Final decision: **{decision}**",
        "",
        "## Best Overlay",
        "",
        f"- best_primary_variant: `{best_variant}`",
        f"- anchored_oos_sharpe_delta: `{best_oos['sharpe_delta']}`",
        f"- anchored_oos_mdd_delta: `{best_oos['mdd_delta']}`",
        f"- anchored_oos_expectancy_delta: `{best_oos['expectancy_delta']}`",
        f"- symbol_concentration_share: `{best_risk['symbol_concentration_share']}`",
        f"- sector_concentration_share: `{best_risk['sector_concentration_share']}`",
        "",
        "## Hybrid Full Anchored OOS Comparison",
        "",
    ]
    lines.extend(
        _markdown_table(
            oos_df[oos_df["universe"] == "hybrid_full"][
                ["variant", "baseline_sharpe", "overlay_sharpe", "sharpe_delta", "baseline_max_drawdown_pct", "overlay_max_drawdown_pct", "mdd_delta", "expectancy_delta"]
            ]
        )
    )
    lines.extend(
        [
            "",
            "## Rolling OOS",
            "",
        ]
    )
    lines.extend(
        _markdown_table(
            rolling_df[(rolling_df["universe"] == "hybrid_full") & (rolling_df["variant"] == best_variant)][
                ["window_id", "subset_trade_count", "condition_met_trade_count", "baseline_expectancy", "overlay_expectancy", "baseline_sharpe_proxy", "overlay_sharpe_proxy", "baseline_mdd_proxy", "overlay_mdd_proxy"]
            ]
        )
    )
    lines.extend(
        [
            "",
            "## Cost Stress",
            "",
        ]
    )
    lines.extend(
        _markdown_table(
            stress_df[(stress_df["universe"] == "hybrid_full") & (stress_df["variant"] == best_variant)][
                ["scenario", "expectancy_after_cost", "sharpe_after_cost", "return_after_cost", "mdd_after_cost", "edge_survives_cost"]
            ]
        )
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Overlay improved Sharpe: `{float(best_oos['sharpe_delta']) > 0}`",
            f"- Overlay reduced drawdown: `{float(best_oos['mdd_delta']) < 0}`",
            f"- CAGR / expectancy preserved or improved: `{float(best_oos['cagr_delta']) >= 0 or float(best_oos['expectancy_delta']) >= 0}`",
            f"- Rolling OOS improvement repeated: `{int(final_decision_df.iloc[0]['rolling_positive_windows'])}` windows",
            f"- Cost stress survived through 2x: `{bool(final_decision_df.iloc[0]['survives_cost_2x'])}`",
            f"- Next step: {'production shadow overlay' if decision in {'MEANINGFUL_IMPROVEMENT', 'DEPLOYABLE_OVERLAY'} else 'research-only monitoring'}",
        ]
    )
    (out_dir / "task_342_integration_report.md").write_text("\n".join(lines), encoding="utf-8")


def run(output_dir: Path = DEFAULT_OUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    master_df, covered_entry_master = _load_overlay_master()
    portfolio_df, scoped_frames, oos_df = _portfolio_comparison(master_df)
    rolling_df = _rolling_oos(master_df, covered_entry_master)
    contribution_df = _contribution_analysis(scoped_frames)
    risk_df = _risk_metrics(portfolio_df, scoped_frames)
    stress_df = _execution_stress(scoped_frames)
    final_decision_df = _final_decision(portfolio_df, rolling_df, risk_df, stress_df)

    portfolio_df.to_csv(output_dir / "task_342_portfolio_comparison.csv", index=False)
    oos_df.to_csv(output_dir / "task_342_oos_comparison.csv", index=False)
    rolling_df.to_csv(output_dir / "task_342_rolling_oos.csv", index=False)
    contribution_df.to_csv(output_dir / "task_342_contribution_analysis.csv", index=False)
    risk_df.to_csv(output_dir / "task_342_risk_metrics.csv", index=False)
    stress_df.to_csv(output_dir / "task_342_execution_stress.csv", index=False)
    final_decision_df.to_csv(output_dir / "task_342_final_decision.csv", index=False)
    _markdown_report(output_dir, portfolio_df, oos_df, rolling_df, risk_df, stress_df, final_decision_df)


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 342: conditional edge integration and portfolio-level validation.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    run(args.output_dir)


if __name__ == "__main__":
    main()
