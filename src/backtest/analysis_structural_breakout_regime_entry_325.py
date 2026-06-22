from __future__ import annotations

import argparse
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    PostEntryOverlayConfig,
    PreEntryFilterConfig,
    StructuralConfig,
    _future_window_metrics,
    _load_stock_symbols,
    _prepare_preloaded_frames,
    _safe_quantile_band,
    _scenario_name,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_best_combo_323plus import (
    DEFAULT_OUT_DIR as TASK323_OUT_DIR,
    RANKED_INPUT,
    _anchored_oos_window,
    _balanced_rank_frame,
    _build_universe_state_lookup,
    _cagr_rank_frame,
    _config_from_scenario,
    _load_ranked_input,
    _mann_whitney_and_effect,
    _overlap_groups,
    _percentile_stats,
    _sector_bucket,
    _select_top_n,
)
from src.backtest.analysis_structural_breakout_audit_323 import _run_period_reruns, _trade_overlap_matrix
from src.backtest.analysis_structural_breakout_exit_size_324 import _load_validation_bands


DEFAULT_OUT_DIR = Path("docs/reports/task_325_regime_entry_rebuild")
DUAL_MAP_FRAME = Path(TASK323_OUT_DIR) / "selected_recent_6m_dual_map_trade_frame.csv"


def _slice_timestamps(timestamps: list[pd.Timestamp], start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    return [ts for ts in timestamps if start <= ts <= end]


def _select_top10_pool(
    *,
    base_dir: Path,
    ranked_input: Path,
    candidate_pool: int,
    jobs: int,
    stocks: list[str],
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
) -> list[str]:
    latest_end = max(timestamps)
    anchored_window = _anchored_oos_window(latest_end)
    train_timestamps = _slice_timestamps(timestamps, timestamps[0], anchored_window.train_end)
    ranked_input_df = _load_ranked_input(ranked_input)
    balanced_candidates_df = _balanced_rank_frame(ranked_input_df).head(candidate_pool).copy()
    cagr_candidates_df = _cagr_rank_frame(ranked_input_df).head(candidate_pool).copy()
    candidate_df = (
        pd.concat([balanced_candidates_df, cagr_candidates_df], ignore_index=True)
        .drop_duplicates(subset=["scenario"])
        .reset_index(drop=True)
    )
    candidate_cfgs = [_config_from_scenario(scenario) for scenario in candidate_df["scenario"].tolist()]
    train_results = _run_period_reruns(
        candidate_cfgs,
        base_dir=base_dir,
        stocks=stocks,
        jobs=jobs,
        frames=frames,
        timestamps=train_timestamps,
    )
    train_rows = []
    for result in train_results:
        scenario = _scenario_name(StructuralConfig(**result["config"]))
        metrics = result["metrics"]
        train_rows.append(
            {
                "scenario": scenario,
                "cagr_pct": metrics["cagr_pct"],
                "sharpe": metrics["sharpe"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "expectancy_r": metrics["expectancy_r"],
                "trade_count": metrics["trade_count"],
                "label_rank": int(
                    ranked_input_df.loc[ranked_input_df["scenario"] == scenario, "label_rank"].iloc[0]
                )
                if scenario in set(ranked_input_df["scenario"])
                else 9,
            }
        )
    train_ranked_df = pd.DataFrame(train_rows)
    train_balanced_df = _balanced_rank_frame(train_ranked_df)
    train_cagr_df = _cagr_rank_frame(train_ranked_df)
    train_metrics_by_scenario = {row["scenario"]: row for row in train_rows}
    overlap_df = _trade_overlap_matrix(train_results)
    representative_by_scenario = _overlap_groups(overlap_df, train_metrics_by_scenario)
    combined_ranked = (
        pd.concat([train_balanced_df, train_cagr_df], ignore_index=True)
        .drop_duplicates(subset=["scenario"])
        .reset_index(drop=True)
    )
    selected = _select_top_n(combined_ranked, representative_by_scenario, top_n=10)
    if len(selected) != 10:
        raise ValueError(f"expected 10 scenarios in Task 325 pool, got {len(selected)}")
    return selected


def _build_rs_lookup(
    frames: dict[str, pd.DataFrame],
    symbols: list[str],
    *,
    horizon: int,
) -> dict[tuple[str, str], float]:
    by_date: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for symbol in symbols:
        frame = frames[symbol].copy()
        close = pd.to_numeric(frame["close"], errors="coerce")
        values = close.pct_change(horizon).shift(1)
        dates = pd.to_datetime(frame["timestamp"], utc=True).dt.date.astype(str)
        for date_key, value in zip(dates, values):
            if pd.notna(value):
                by_date[str(date_key)].append((symbol, float(value)))
    lookup: dict[tuple[str, str], float] = {}
    for date_key, rows in by_date.items():
        rows = sorted(rows, key=lambda item: item[1])
        denom = max(len(rows), 1)
        for idx, (symbol, _) in enumerate(rows, start=1):
            lookup[(symbol, date_key)] = idx / denom
    return lookup


def _safe_ratio(numerator: Any, denominator: Any) -> float:
    try:
        n = float(numerator)
        d = float(denominator)
    except (TypeError, ValueError):
        return math.nan
    if not math.isfinite(n) or not math.isfinite(d) or d == 0.0:
        return math.nan
    return n / d


def _build_regime_lookup(
    base_dir: Path,
    universe_state_lookup: dict[str, dict[str, float]],
) -> dict[str, dict[str, Any]]:
    from src.backtest.analysis_structural_breakout_322 import load_daily_bars

    qld = load_daily_bars("QLD", base_dir=base_dir).copy()
    qld["timestamp"] = pd.to_datetime(qld["timestamp"], utc=True)
    qld = qld.sort_values("timestamp").reset_index(drop=True)
    close = pd.to_numeric(qld["close"], errors="coerce")
    qld["close"] = close
    qld["sma20"] = close.rolling(20, min_periods=20).mean()
    qld["sma50"] = close.rolling(50, min_periods=50).mean()
    qld["sma200"] = close.rolling(200, min_periods=200).mean()
    qld["std5"] = close.pct_change().rolling(5).std(ddof=0)
    qld["std20"] = close.pct_change().rolling(20).std(ddof=0)
    qld["ret5"] = close.pct_change(5)
    qld["ret20"] = close.pct_change(20)
    qld["ret60"] = close.pct_change(60)
    qld["high20"] = close.rolling(20, min_periods=20).max()
    qld["high60"] = close.rolling(60, min_periods=60).max()
    qld["low20"] = close.rolling(20, min_periods=20).min()
    qld["low60"] = close.rolling(60, min_periods=60).min()
    qld["close_prev"] = qld["close"].shift(1)
    for col in ("sma20", "sma50", "sma200", "std5", "std20", "ret5", "ret20", "ret60", "high20", "high60", "low20", "low60"):
        qld[f"{col}_prev"] = qld[col].shift(1)
    qld["sma20_slope5_prev"] = (qld["sma20"].shift(1) - qld["sma20"].shift(6)) / qld["sma20"].shift(6)
    qld["sma50_slope5_prev"] = (qld["sma50"].shift(1) - qld["sma50"].shift(6)) / qld["sma50"].shift(6)
    qld["dd20_prev"] = qld["close_prev"] / qld["high20_prev"] - 1.0
    qld["dd60_prev"] = qld["close_prev"] / qld["high60_prev"] - 1.0
    qld["recovery20_prev"] = qld["close_prev"] / qld["low20_prev"] - 1.0
    qld["recovery60_prev"] = qld["close_prev"] / qld["low60_prev"] - 1.0

    lookup: dict[str, dict[str, Any]] = {}

    for row in qld.itertuples(index=False):
        date_key = pd.Timestamp(row.timestamp).date().isoformat()
        state = universe_state_lookup.get(date_key, {})
        row_dict = row._asdict()
        close_prev = row_dict.get("close_prev")
        sma200_prev = row_dict.get("sma200_prev")
        ret5 = float(row_dict["ret5_prev"]) if pd.notna(row_dict.get("ret5_prev")) else math.nan
        ret20 = float(row_dict["ret20_prev"]) if pd.notna(row_dict.get("ret20_prev")) else math.nan
        ret60 = float(row_dict["ret60_prev"]) if pd.notna(row_dict.get("ret60_prev")) else math.nan
        vol_ratio = _safe_ratio(row_dict.get("std5_prev"), row_dict.get("std20_prev"))
        slope20 = float(row_dict["sma20_slope5_prev"]) if pd.notna(row_dict.get("sma20_slope5_prev")) else math.nan
        slope50 = float(row_dict["sma50_slope5_prev"]) if pd.notna(row_dict.get("sma50_slope5_prev")) else math.nan
        dd20 = float(row_dict["dd20_prev"]) if pd.notna(row_dict.get("dd20_prev")) else math.nan
        dd60 = float(row_dict["dd60_prev"]) if pd.notna(row_dict.get("dd60_prev")) else math.nan
        recovery20 = float(row_dict["recovery20_prev"]) if pd.notna(row_dict.get("recovery20_prev")) else math.nan
        breadth20 = float(state.get("breadth_above_sma20", math.nan))
        breadth50 = float(state.get("breadth_above_sma50", math.nan))
        breadth200 = float(state.get("breadth_above_sma200", math.nan))
        breadth_pos20 = float(state.get("breadth_positive_20d", math.nan))
        dispersion20 = float(state.get("dispersion_20d", math.nan))
        mean_corr = float(state.get("mean_pairwise_corr", math.nan))
        dominance = float(state.get("top_sector_dominance_score", math.nan))
        semis_ratio = float(state.get("semis_concentration_ratio", math.nan))
        tech_ratio = float(state.get("tech_concentration_ratio", math.nan))
        corr_spike = bool(state.get("correlation_spike", False))

        if pd.isna(close_prev) or pd.isna(sma200_prev):
            regime = "rebound_chop"
        elif float(close_prev) <= float(sma200_prev):
            if (not math.isnan(ret5) and ret5 > 0.0) and (not math.isnan(recovery20) and recovery20 > 0.05):
                regime = "risk_off_reversal"
            else:
                regime = "high_vol_chop"
        elif (not math.isnan(ret20) and ret20 >= 0.14) or ((not math.isnan(dd20) and dd20 > -0.015) and (not math.isnan(dominance) and dominance >= 0.32)):
            regime = "late_extension"
        elif (not math.isnan(ret20) and ret20 > 0.04) and ((not math.isnan(breadth50) and breadth50 < 0.52) or (not math.isnan(dominance) and dominance >= 0.35) or (not math.isnan(semis_ratio) and semis_ratio >= 0.22)):
            regime = "narrow_leadership_trend"
        elif (not math.isnan(ret20) and ret20 > 0.02) and (not math.isnan(ret5) and ret5 <= 0.0) and (((not math.isnan(dd20)) and dd20 <= -0.03) or ((not math.isnan(dd60)) and dd60 <= -0.06)):
            regime = "failed_recovery"
        elif (not math.isnan(vol_ratio) and vol_ratio >= 1.15) and ((not math.isnan(dispersion20) and dispersion20 > 0.12) or corr_spike):
            regime = "high_vol_chop"
        elif (not math.isnan(ret20) and ret20 > 0.03) and (not math.isnan(breadth50) and breadth50 < 0.58) and (not math.isnan(slope20) and slope20 > -0.002):
            regime = "rebound_chop"
        elif (not math.isnan(ret20) and ret20 > 0.05) and (not math.isnan(breadth50) and breadth50 >= 0.60) and (not math.isnan(breadth_pos20) and breadth_pos20 >= 0.58):
            regime = "broad_trend"
        elif (not math.isnan(ret20) and ret20 > 0.02) and (not math.isnan(slope20) and slope20 > 0.0) and (not math.isnan(slope50) and slope50 >= 0.0) and (not math.isnan(dominance) and dominance < 0.30) and not corr_spike:
            regime = "clean_trend"
        else:
            regime = "rebound_chop"

        lookup[date_key] = {
            "regime_state": regime,
            "ret5_prev": ret5,
            "ret20_prev": ret20,
            "ret60_prev": ret60,
            "vol_ratio_prev": vol_ratio,
            "slope20_prev": slope20,
            "slope50_prev": slope50,
            "dd20_prev": dd20,
            "dd60_prev": dd60,
            "recovery20_prev": recovery20,
            "breadth_above_sma20": breadth20,
            "breadth_above_sma50": breadth50,
            "breadth_above_sma200": breadth200,
            "breadth_positive_20d": breadth_pos20,
            "dispersion_20d": dispersion20,
            "mean_pairwise_corr": mean_corr,
            "correlation_spike": corr_spike,
            "top_sector_dominance_score": dominance,
            "semis_concentration_ratio": semis_ratio,
            "tech_concentration_ratio": tech_ratio,
        }
    return lookup


def _build_entry_feature_lookup(
    frames: dict[str, pd.DataFrame],
    symbols: list[str],
    universe_state_lookup: dict[str, dict[str, float]],
    regime_lookup: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    rs20_lookup = _build_rs_lookup(frames, symbols, horizon=20)
    rs60_lookup = _build_rs_lookup(frames, symbols, horizon=60)

    sector_date_rows: list[dict[str, Any]] = []
    for symbol in symbols:
        sector = _sector_bucket(symbol)
        frame = frames[symbol].copy()
        close = pd.to_numeric(frame["close"], errors="coerce")
        date_key = pd.to_datetime(frame["timestamp"], utc=True).dt.date.astype(str)
        ret20_pre = close.pct_change(20).shift(1)
        sector_date_rows.append(pd.DataFrame({"symbol": symbol, "sector_bucket": sector, "date_key": date_key, "ret20_pre": ret20_pre}))
    sector_df = pd.concat(sector_date_rows, ignore_index=True) if sector_date_rows else pd.DataFrame()
    sector_lookup: dict[tuple[str, str], dict[str, float]] = {}
    if not sector_df.empty:
        sector_grouped = (
            sector_df.groupby(["date_key", "sector_bucket"], as_index=False)
            .agg(
                sector_breadth=("ret20_pre", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean()) if len(s) else math.nan),
                sector_ret20_mean=("ret20_pre", lambda s: float(pd.to_numeric(s, errors="coerce").mean()) if len(s) else math.nan),
            )
        )
        for row in sector_grouped.to_dict("records"):
            sector_lookup[(str(row["date_key"]), str(row["sector_bucket"]))] = {
                "sector_breadth": float(row["sector_breadth"]),
                "sector_ret20_mean": float(row["sector_ret20_mean"]),
            }

    metadata_lookup: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        frame = frames[symbol].copy()
        close = pd.to_numeric(frame["close"], errors="coerce")
        high = pd.to_numeric(frame["high"], errors="coerce")
        low = pd.to_numeric(frame["low"], errors="coerce")
        volume = pd.to_numeric(frame["volume"], errors="coerce")
        sector = _sector_bucket(symbol)

        frame["ret_5d_pre"] = close.pct_change(5).shift(1)
        frame["ret_10d_pre"] = close.pct_change(10).shift(1)
        frame["ret_20d_pre"] = close.pct_change(20).shift(1)
        frame["ret_60d_pre"] = close.pct_change(60).shift(1)
        frame["sma50"] = close.rolling(50, min_periods=50).mean()
        frame["sma200"] = close.rolling(200, min_periods=200).mean()
        frame["dist_to_sma20_pct"] = close.shift(1) / frame["sma20"].shift(1) - 1.0
        frame["dist_to_sma50_pct"] = close.shift(1) / frame["sma50"].shift(1) - 1.0
        frame["dist_to_sma200_pct"] = close.shift(1) / frame["sma200"].shift(1) - 1.0
        range_high10 = high.rolling(10, min_periods=10).max().shift(1)
        range_low10 = low.rolling(10, min_periods=10).min().shift(1)
        frame["range_width_10_pre"] = (range_high10 - range_low10) / close.shift(1)
        frame["vol_contraction_ratio"] = frame["std5_prev"] / frame["std20_prev"]
        frame["squeeze_quality"] = frame["std20_prev"] / frame["std5_prev"]
        frame["close_location_pre"] = frame["close_location"].shift(1)
        avg_volume_60 = volume.rolling(60, min_periods=60).mean().shift(1)
        frame["volume_confirmation_pre"] = frame["avg_volume_20_prev"] / avg_volume_60
        frame["turnover_pre"] = (close.shift(1) * volume.shift(1))
        frame["dollar_volume_pre"] = frame["avg_dollar_volume_20"]
        frame["recent_high20_pre"] = high.rolling(20, min_periods=20).max().shift(1)
        frame["pre_breakout_distance_pct"] = close.shift(1) / frame["recent_high20_pre"] - 1.0
        breakout_fail = ((high >= frame["recent_high20_pre"]) & (close <= frame["recent_high20_pre"])).astype(float)
        frame["recent_failed_breakouts_20d"] = breakout_fail.shift(1).rolling(20, min_periods=1).sum()
        frame["date_key"] = pd.to_datetime(frame["timestamp"], utc=True).dt.date.astype(str)

        for row in frame.itertuples(index=False):
            date_key = str(row.date_key)
            universe = universe_state_lookup.get(date_key, {})
            regime = regime_lookup.get(date_key, {})
            sector_state = sector_lookup.get((date_key, sector), {})
            rs20 = rs20_lookup.get((symbol, date_key), math.nan)
            rs60 = rs60_lookup.get((symbol, date_key), math.nan)
            sector_crowding_high = (
                (_sector_bucket(symbol) in {"semis", "software/internet", "other tech"})
                and (
                    bool(universe.get("correlation_spike", False))
                    or float(universe.get("top_sector_dominance_score", 0.0)) >= 0.35
                    or float(universe.get("semis_concentration_ratio", 0.0)) >= 0.22
                    or float(universe.get("tech_concentration_ratio", 0.0)) >= 0.65
                )
            )
            metadata_lookup[f"{symbol}|{date_key}"] = {
                "symbol": symbol,
                "date_key": date_key,
                "sector_bucket": sector,
                "regime_state": str(regime.get("regime_state", "")),
                "ret_5d_pre": float(row.ret_5d_pre) if pd.notna(row.ret_5d_pre) else math.nan,
                "ret_10d_pre": float(row.ret_10d_pre) if pd.notna(row.ret_10d_pre) else math.nan,
                "ret_20d_pre": float(row.ret_20d_pre) if pd.notna(row.ret_20d_pre) else math.nan,
                "dist_to_sma20_pct": float(row.dist_to_sma20_pct) if pd.notna(row.dist_to_sma20_pct) else math.nan,
                "dist_to_sma50_pct": float(row.dist_to_sma50_pct) if pd.notna(row.dist_to_sma50_pct) else math.nan,
                "dist_to_sma200_pct": float(row.dist_to_sma200_pct) if pd.notna(row.dist_to_sma200_pct) else math.nan,
                "range_width_10_pre": float(row.range_width_10_pre) if pd.notna(row.range_width_10_pre) else math.nan,
                "vol_contraction_ratio": float(row.vol_contraction_ratio) if pd.notna(row.vol_contraction_ratio) else math.nan,
                "squeeze_quality": float(row.squeeze_quality) if pd.notna(row.squeeze_quality) else math.nan,
                "close_location_pre": float(row.close_location_pre) if pd.notna(row.close_location_pre) else math.nan,
                "volume_confirmation_pre": float(row.volume_confirmation_pre) if pd.notna(row.volume_confirmation_pre) else math.nan,
                "dollar_volume_pre": float(row.dollar_volume_pre) if pd.notna(row.dollar_volume_pre) else math.nan,
                "turnover_pre": float(row.turnover_pre) if pd.notna(row.turnover_pre) else math.nan,
                "rs_percentile_20d": float(rs20) if not math.isnan(rs20) else math.nan,
                "rs_percentile_60d": float(rs60) if not math.isnan(rs60) else math.nan,
                "sector_breadth": float(sector_state.get("sector_breadth", math.nan)),
                "sector_rs_percentile": float(sector_state.get("sector_ret20_mean", math.nan)),
                "sector_crowding_high": bool(sector_crowding_high),
                "recent_failed_breakouts_20d": float(row.recent_failed_breakouts_20d) if pd.notna(row.recent_failed_breakouts_20d) else math.nan,
                "pre_breakout_distance_pct": float(row.pre_breakout_distance_pct) if pd.notna(row.pre_breakout_distance_pct) else math.nan,
                "breadth_above_sma20": float(universe.get("breadth_above_sma20", math.nan)),
                "breadth_above_sma50": float(universe.get("breadth_above_sma50", math.nan)),
                "breadth_positive_20d": float(universe.get("breadth_positive_20d", math.nan)),
                "dispersion_20d": float(universe.get("dispersion_20d", math.nan)),
                "mean_pairwise_corr": float(universe.get("mean_pairwise_corr", math.nan)),
                "top_sector_dominance_score": float(universe.get("top_sector_dominance_score", math.nan)),
                "semis_concentration_ratio": float(universe.get("semis_concentration_ratio", math.nan)),
                "tech_concentration_ratio": float(universe.get("tech_concentration_ratio", math.nan)),
            }
    return metadata_lookup


def _enrich_trade_frame(
    scenario: str,
    result: dict[str, Any],
    frames: dict[str, pd.DataFrame],
    metadata_lookup: dict[str, dict[str, Any]],
    scope_name: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade in result["trade_log"]:
        symbol = str(trade["symbol"])
        date_key = str(trade["entry_date"])
        metadata = metadata_lookup.get(f"{symbol}|{date_key}", {}).copy()
        frame = frames[symbol]
        entry_ts = pd.Timestamp(date_key, tz="UTC")
        follow3 = _future_window_metrics(frame, entry_ts, float(trade["entry_price"]), 3)
        follow5 = _future_window_metrics(frame, entry_ts, float(trade["entry_price"]), 5)
        prev_idx = frame.index.get_loc(entry_ts) - 1 if entry_ts in frame.index else -1
        prev_close = math.nan
        if prev_idx >= 0:
            prev_close = float(pd.to_numeric(frame.iloc[prev_idx]["close"], errors="coerce"))
        pre_breakout_strength = _safe_ratio(prev_close, trade["breakout_level"])
        pre_breakout_strength = pre_breakout_strength - 1.0 if not math.isnan(pre_breakout_strength) else math.nan
        gap_over_planned = _safe_ratio(trade["entry_open"], trade["planned_entry_price"])
        gap_over_planned = gap_over_planned - 1.0 if not math.isnan(gap_over_planned) else math.nan
        rows.append(
            {
                "scope": scope_name,
                "scenario": scenario,
                "scenario_family": str(trade.get("structure_mode", "")),
                "trade_id": str(trade["trade_id"]),
                "symbol": symbol,
                "sector_bucket": _sector_bucket(symbol),
                "entry_date": date_key,
                "exit_date": str(trade["exit_date"]),
                "realized_R": float(trade["realized_R"]),
                "holding_days": int(trade["holding_days"]),
                "breakout_level": float(trade["breakout_level"]),
                "entry_price": float(trade["entry_price"]),
                "planned_entry_price": float(trade["planned_entry_price"]),
                "entry_open": float(trade["entry_open"]),
                "gap_over_planned_entry_pct": gap_over_planned,
                "breakout_strength_pct": _safe_ratio(trade["entry_price"], trade["breakout_level"]) - 1.0,
                "pre_breakout_distance_pct": pre_breakout_strength,
                "follow_through_3d_pct": follow3["follow"],
                "follow_through_5d_pct": follow5["follow"],
                "post_breakout_retrace_3d_pct": follow3["retrace"],
                "post_breakout_retrace_5d_pct": follow5["retrace"],
                "adverse_excursion_3d_pct": follow3["adverse"],
                "adverse_excursion_5d_pct": follow5["adverse"],
                **metadata,
            }
        )
    return pd.DataFrame(rows)


def _apply_outcome_groups(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    low_cut = float(out["realized_R"].quantile(0.30))
    high_cut = float(out["realized_R"].quantile(0.70))
    out["outcome_group"] = "neutral"
    out.loc[out["realized_R"] <= low_cut, "outcome_group"] = "losers"
    out.loc[out["realized_R"] >= high_cut, "outcome_group"] = "winners"
    low10 = float(out["realized_R"].quantile(0.10))
    high10 = float(out["realized_R"].quantile(0.90))
    out["is_worst_decile"] = out["realized_R"] <= low10
    out["is_best_decile"] = out["realized_R"] >= high10
    return out


def _drawdown_proxy(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    cumulative = pd.to_numeric(values, errors="coerce").fillna(0.0).cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    return float(drawdown.min())


def _regime_rebuild_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if df.empty:
        return pd.DataFrame()
    for regime, scoped in df.groupby("regime_state"):
        sector_mix = Counter(scoped["sector_bucket"].astype(str))
        scenario_mix = Counter(scoped["scenario_family"].astype(str))
        rows.append(
            {
                "regime": regime,
                "trade_count": int(len(scoped)),
                "total_r": round(float(scoped["realized_R"].sum()), 6),
                "expectancy_r": round(float(scoped["realized_R"].mean()), 6),
                "win_rate": round(float((scoped["realized_R"] > 0).mean()), 6),
                "average_r": round(float(scoped["realized_R"].mean()), 6),
                "drawdown_proxy": round(_drawdown_proxy(scoped["realized_R"]), 6),
                "avg_holding_days": round(float(pd.to_numeric(scoped["holding_days"], errors="coerce").mean()), 6),
                "avg_follow_through_3d_pct": round(float(pd.to_numeric(scoped["follow_through_3d_pct"], errors="coerce").mean()), 6),
                "avg_follow_through_5d_pct": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").mean()), 6),
                "avg_retrace_3d_pct": round(float(pd.to_numeric(scoped["post_breakout_retrace_3d_pct"], errors="coerce").mean()), 6),
                "avg_retrace_5d_pct": round(float(pd.to_numeric(scoped["post_breakout_retrace_5d_pct"], errors="coerce").mean()), 6),
                "top_sector": sector_mix.most_common(1)[0][0] if sector_mix else "",
                "top_sector_share": round(sector_mix.most_common(1)[0][1] / len(scoped), 6) if sector_mix else math.nan,
                "top_scenario_family": scenario_mix.most_common(1)[0][0] if scenario_mix else "",
                "top_scenario_share": round(scenario_mix.most_common(1)[0][1] / len(scoped), 6) if scenario_mix else math.nan,
            }
        )
    return pd.DataFrame(rows).sort_values(["expectancy_r", "trade_count"]).reset_index(drop=True)


def _regime_transition_diagnostics(regime_lookup: dict[str, dict[str, Any]]) -> pd.DataFrame:
    dates = sorted(regime_lookup.keys())
    if not dates:
        return pd.DataFrame()
    transitions: list[dict[str, Any]] = []
    prev_regime = None
    streak = 0
    for date_key in dates:
        regime = str(regime_lookup[date_key].get("regime_state", ""))
        if prev_regime is None:
            prev_regime = regime
            streak = 1
            continue
        if regime == prev_regime:
            streak += 1
        else:
            transitions.append({"from_regime": prev_regime, "to_regime": regime, "streak_length": streak})
            prev_regime = regime
            streak = 1
    if prev_regime is not None:
        transitions.append({"from_regime": prev_regime, "to_regime": prev_regime, "streak_length": streak})
    grouped = (
        pd.DataFrame(transitions)
        .groupby(["from_regime", "to_regime"], as_index=False)
        .agg(transition_count=("streak_length", "size"), avg_streak_before=("streak_length", "mean"), max_streak_before=("streak_length", "max"))
    )
    return grouped.sort_values(["transition_count", "avg_streak_before"], ascending=[False, False]).reset_index(drop=True)


def _regime_trade_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grouped = (
        df.groupby(["regime_state", "sector_bucket", "scenario_family"], as_index=False)
        .agg(trade_count=("realized_R", "size"), total_r=("realized_R", "sum"), win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())))
    )
    return grouped.sort_values(["regime_state", "trade_count"], ascending=[True, False]).reset_index(drop=True)


ENTRY_FEATURES = [
    "ret_5d_pre",
    "ret_10d_pre",
    "ret_20d_pre",
    "dist_to_sma20_pct",
    "dist_to_sma50_pct",
    "dist_to_sma200_pct",
    "range_width_10_pre",
    "vol_contraction_ratio",
    "squeeze_quality",
    "close_location_pre",
    "volume_confirmation_pre",
    "dollar_volume_pre",
    "rs_percentile_20d",
    "rs_percentile_60d",
    "sector_breadth",
    "sector_rs_percentile",
    "recent_failed_breakouts_20d",
    "pre_breakout_distance_pct",
    "gap_over_planned_entry_pct",
    "breakout_strength_pct",
]


def _comparison_stats(df: pd.DataFrame, lhs_mask: pd.Series, rhs_mask: pd.Series, *, label: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    lhs_df = df[lhs_mask].copy()
    rhs_df = df[rhs_mask].copy()
    scenario_signs: dict[str, dict[str, int]] = defaultdict(dict)
    for feature in ENTRY_FEATURES:
        lhs_values = pd.to_numeric(lhs_df[feature], errors="coerce").dropna()
        rhs_values = pd.to_numeric(rhs_df[feature], errors="coerce").dropna()
        lhs_stats = _percentile_stats(lhs_values)
        rhs_stats = _percentile_stats(rhs_values)
        test = _mann_whitney_and_effect(lhs_values.tolist(), rhs_values.tolist())
        effect = float(test["effect_size"]) if not math.isnan(test["effect_size"]) else 0.0
        sign = 1 if effect > 0 else -1 if effect < 0 else 0
        for scenario, scoped in df.groupby("scenario"):
            lhs_local_mask = lhs_mask.loc[scoped.index]
            rhs_local_mask = rhs_mask.loc[scoped.index]
            lvals = pd.to_numeric(scoped.loc[lhs_local_mask, feature], errors="coerce").dropna()
            rvals = pd.to_numeric(scoped.loc[rhs_local_mask, feature], errors="coerce").dropna()
            if lvals.empty or rvals.empty:
                continue
            local_effect = _mann_whitney_and_effect(lvals.tolist(), rvals.tolist())["effect_size"]
            if not math.isnan(local_effect):
                scenario_signs[feature][scenario] = 1 if float(local_effect) > 0 else -1 if float(local_effect) < 0 else 0
        consistency = 0.0
        if scenario_signs[feature]:
            same_sign = sum(1 for value in scenario_signs[feature].values() if value == sign)
            consistency = same_sign / max(len(scenario_signs[feature]), 1)
        separation_score = abs(effect) * (1.0 if (not math.isnan(test["p_value"]) and float(test["p_value"]) <= 0.10) else 0.5) * max(consistency, 0.25)
        rows.append(
            {
                "comparison_type": label,
                "feature": feature,
                "lhs_count": int(lhs_stats["count"]),
                "lhs_mean": lhs_stats["mean"],
                "lhs_median": lhs_stats["median"],
                "lhs_p75": lhs_stats["p75"],
                "lhs_p90": lhs_stats["p90"],
                "lhs_p95": lhs_stats["p95"],
                "rhs_count": int(rhs_stats["count"]),
                "rhs_mean": rhs_stats["mean"],
                "rhs_median": rhs_stats["median"],
                "rhs_p75": rhs_stats["p75"],
                "rhs_p90": rhs_stats["p90"],
                "rhs_p95": rhs_stats["p95"],
                "mann_whitney_p_value": test["p_value"],
                "effect_size": test["effect_size"],
                "separation_score": round(float(separation_score), 6),
                "scenario_consistency": round(float(consistency), 6),
                "preferred_direction": "higher_is_better" if effect > 0 else ("lower_is_better" if effect < 0 else "no_clear_edge"),
            }
        )
    return pd.DataFrame(rows).sort_values(["separation_score", "scenario_consistency"], ascending=[False, False]).reset_index(drop=True)


def _entry_feature_frame(df_full: pd.DataFrame, df_oos: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    full_grouped = _apply_outcome_groups(df_full)
    oos_grouped = _apply_outcome_groups(df_oos)
    full_comp = _comparison_stats(full_grouped, full_grouped["outcome_group"] == "winners", full_grouped["outcome_group"] == "losers", label="winners_vs_losers_full")
    full_tail = _comparison_stats(full_grouped, full_grouped["is_best_decile"], full_grouped["is_worst_decile"], label="best_vs_worst_full")
    oos_comp = _comparison_stats(oos_grouped, oos_grouped["outcome_group"] == "winners", oos_grouped["outcome_group"] == "losers", label="winners_vs_losers_oos")
    oos_tail = _comparison_stats(oos_grouped, oos_grouped["is_best_decile"], oos_grouped["is_worst_decile"], label="best_vs_worst_oos")
    comparison = pd.concat([full_comp, full_tail, oos_comp, oos_tail], ignore_index=True)

    stability_rows: list[dict[str, Any]] = []
    full_main = full_comp.set_index("feature")
    oos_main = oos_comp.set_index("feature")
    for feature in ENTRY_FEATURES:
        full_effect = float(full_main.loc[feature, "effect_size"]) if feature in full_main.index and pd.notna(full_main.loc[feature, "effect_size"]) else 0.0
        oos_effect = float(oos_main.loc[feature, "effect_size"]) if feature in oos_main.index and pd.notna(oos_main.loc[feature, "effect_size"]) else 0.0
        same_sign = (full_effect == 0.0 or oos_effect == 0.0) or ((full_effect > 0) == (oos_effect > 0))
        mean_sep = statistics.fmean(
            [
                float(full_main.loc[feature, "separation_score"]) if feature in full_main.index else 0.0,
                float(oos_main.loc[feature, "separation_score"]) if feature in oos_main.index else 0.0,
            ]
        )
        stability_rows.append(
            {
                "feature": feature,
                "full_effect_size": round(full_effect, 6),
                "oos_effect_size": round(oos_effect, 6),
                "same_sign_full_vs_oos": bool(same_sign),
                "full_separation_score": round(float(full_main.loc[feature, "separation_score"]) if feature in full_main.index else 0.0, 6),
                "oos_separation_score": round(float(oos_main.loc[feature, "separation_score"]) if feature in oos_main.index else 0.0, 6),
                "importance": round(float(mean_sep), 6),
                "stability": round(
                    0.5 * (1.0 if same_sign else 0.0)
                    + 0.5 * statistics.fmean(
                        [
                            float(full_main.loc[feature, "scenario_consistency"]) if feature in full_main.index else 0.0,
                            float(oos_main.loc[feature, "scenario_consistency"]) if feature in oos_main.index else 0.0,
                        ]
                    ),
                    6,
                ),
            }
        )
    features_df = pd.DataFrame(stability_rows).sort_values(["importance", "stability"], ascending=[False, False]).reset_index(drop=True)
    top_features = features_df.head(5)["feature"].tolist()
    features_df["keep_flag"] = features_df["feature"].isin(top_features)
    separation = features_df[features_df["keep_flag"]].copy()
    separation["direction"] = separation["feature"].map(lambda feature: full_main.loc[feature, "preferred_direction"] if feature in full_main.index else "no_clear_edge")
    return features_df, comparison, separation


def _score_entry_quality_for_metadata(
    metadata_lookup: dict[str, dict[str, Any]],
    separation: pd.DataFrame,
) -> tuple[dict[str, dict[str, Any]], dict[str, float]]:
    selected = separation.to_dict("records")
    score_values: list[float] = []
    feature_bands: dict[str, tuple[float, float]] = {}
    for record in selected:
        feature = str(record["feature"])
        values = [float(meta.get(feature)) for meta in metadata_lookup.values() if pd.notna(meta.get(feature))]
        series = pd.Series(values, dtype=float)
        if series.empty:
            raise ValueError(f"Task 325 missing pre-entry feature values for: {feature}")
        feature_bands[feature] = (float(series.quantile(0.30)), float(series.quantile(0.70)))

    for metadata in metadata_lookup.values():
        feature_scores: list[float] = []
        for record in selected:
            feature = str(record["feature"])
            value = metadata.get(feature, math.nan)
            direction = str(record["direction"])
            low, high = feature_bands[feature]
            if pd.isna(value):
                continue
            if direction == "lower_is_better":
                band = _safe_quantile_band(float(value), low, high, lower_is_bad=False)
                feature_scores.append(2.0 if band == "low" else 1.0 if band == "mid" else 0.0)
            elif direction == "higher_is_better":
                band = _safe_quantile_band(float(value), low, high, lower_is_bad=True)
                feature_scores.append(2.0 if band == "strong" else 1.0 if band == "mixed" else 0.0)
        score = statistics.fmean(feature_scores) if feature_scores else math.nan
        metadata["entry_quality_score"] = round(float(score), 6) if not math.isnan(score) else math.nan
        score_values.append(float(score) if not math.isnan(score) else math.nan)

    score_series = pd.Series(score_values, dtype=float).dropna()
    if score_series.empty:
        raise ValueError("Task 325 could not compute entry quality score bands")
    low_band = float(score_series.quantile(0.30))
    high_band = float(score_series.quantile(0.70))
    for metadata in metadata_lookup.values():
        score = metadata.get("entry_quality_score", math.nan)
        if pd.isna(score):
            metadata["entry_quality_band"] = "unknown"
        elif float(score) <= low_band:
            metadata["entry_quality_band"] = "low"
        elif float(score) >= high_band:
            metadata["entry_quality_band"] = "high"
        else:
            metadata["entry_quality_band"] = "mid"
    return metadata_lookup, {"low": low_band, "high": high_band}


def _regime_entry_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grouped = (
        df.groupby(["regime_state", "entry_quality_band"], as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            expectancy=("realized_R", "mean"),
            win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
            total_r=("realized_R", "sum"),
        )
    )
    rows = []
    for record in grouped.to_dict("records"):
        scoped = df[(df["regime_state"] == record["regime_state"]) & (df["entry_quality_band"] == record["entry_quality_band"])]
        record["drawdown_proxy"] = round(_drawdown_proxy(scoped["realized_R"]), 6)
        rows.append(record)
    return pd.DataFrame(rows).sort_values(["regime_state", "entry_quality_band"]).reset_index(drop=True)


def _regime_sector_entry_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    sector_group = df["sector_bucket"].map(lambda value: "tech" if str(value) in {"software/internet", "other tech"} else value)
    scoped = df.assign(sector_group=sector_group)
    grouped = (
        scoped.groupby(["regime_state", "sector_group", "entry_quality_band"], as_index=False)
        .agg(trade_count=("realized_R", "size"), expectancy=("realized_R", "mean"), win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())), total_r=("realized_R", "sum"))
    )
    return grouped.sort_values(["regime_state", "sector_group", "entry_quality_band"]).reset_index(drop=True)


def _choose_regime_filters(regime_full: pd.DataFrame, regime_oos: pd.DataFrame) -> tuple[list[str], list[str]]:
    full_lookup = regime_full.set_index("regime")["expectancy_r"].to_dict() if not regime_full.empty else {}
    oos_lookup = regime_oos.set_index("regime")["expectancy_r"].to_dict() if not regime_oos.empty else {}
    bad: list[str] = []
    weak: list[str] = []
    for regime in sorted(set(full_lookup) | set(oos_lookup)):
        full_exp = float(full_lookup.get(regime, 0.0))
        oos_exp = float(oos_lookup.get(regime, 0.0))
        if full_exp < 0.0 and oos_exp < 0.0:
            bad.append(regime)
        elif full_exp < 0.0 or oos_exp < 0.0:
            weak.append(regime)
    return bad, weak


def _variant_pre_entry_filter(
    variant: str,
    *,
    metadata_lookup: dict[str, dict[str, Any]],
    entry_bands: dict[str, float],
    bad_regimes: list[str],
    weak_regimes: list[str],
) -> PreEntryFilterConfig | None:
    if variant == "baseline":
        return None
    regime_mode = "diagnostic_filter" if variant in {"regime_filter_only", "regime_plus_entry_filter", "regime_plus_entry_plus_size50"} else "off"
    entry_mode = "diagnostic_filter" if variant in {"entry_quality_filter_only", "regime_plus_entry_filter", "regime_plus_entry_plus_size50"} else "off"
    return PreEntryFilterConfig(
        regime_filter_mode=regime_mode,
        entry_quality_filter_mode=entry_mode,
        entry_quality_score_bands=entry_bands,
        bad_regimes=tuple(bad_regimes),
        weak_regimes=tuple(weak_regimes),
        sector_crowding_policy={"high_crowding_action": "reduce", "reduce_fraction": 0.5},
        metadata_lookup=metadata_lookup,
        weak_entry_reduce_fraction=0.5,
        weak_regime_reduce_fraction=0.5,
    )


def _variant_overlay(variant: str, validation_bands: dict[str, dict[str, float]]) -> PostEntryOverlayConfig | None:
    if variant != "regime_plus_entry_plus_size50":
        return None
    return PostEntryOverlayConfig(post_entry_rule_mode="size_only", size_reduction_fraction=0.5, validation_bands=validation_bands)


def _run_variant_results(
    scenarios: list[str],
    variants: list[str],
    *,
    base_dir: Path,
    stocks: list[str],
    frames: dict[str, pd.DataFrame],
    full_timestamps: list[pd.Timestamp],
    oos_timestamps: list[pd.Timestamp],
    metadata_lookup: dict[str, dict[str, Any]],
    entry_bands: dict[str, float],
    bad_regimes: list[str],
    weak_regimes: list[str],
    validation_bands: dict[str, dict[str, float]],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    results: dict[tuple[str, str, str], dict[str, Any]] = {}
    scope_map = {"full_period": full_timestamps, "anchored_oos": oos_timestamps}
    for scenario in scenarios:
        cfg = _config_from_scenario(scenario)
        for variant in variants:
            pre_entry = _variant_pre_entry_filter(
                variant,
                metadata_lookup=metadata_lookup,
                entry_bands=entry_bands,
                bad_regimes=bad_regimes,
                weak_regimes=weak_regimes,
            )
            overlay = _variant_overlay(variant, validation_bands)
            for scope_name, scoped_timestamps in scope_map.items():
                results[(scenario, variant, scope_name)] = run_structural_backtest(
                    cfg,
                    base_dir,
                    preloaded_frames=frames,
                    preloaded_timestamps=scoped_timestamps,
                    preloaded_symbols=stocks,
                    pre_entry_filter=pre_entry,
                    overlay=overlay,
                )
    return results


def _aggregate_variant_rows(results: dict[tuple[str, str, str], dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scenario, variant, scope), result in results.items():
        metrics = result["metrics"]
        rows.append(
            {
                "scenario": scenario,
                "variant": variant,
                "scope": scope,
                "cagr_pct": metrics["cagr_pct"],
                "sharpe": metrics["sharpe"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "total_return_pct": metrics["total_return_pct"],
                "total_r": metrics["total_r"],
                "expectancy_r": metrics["expectancy_r"],
                "win_rate": metrics["win_rate"],
                "trade_count": metrics["trade_count"],
                "avg_holding_days": metrics["avg_holding_days"],
                "avg_loss_r": metrics["avg_loss_r"],
                "avg_win_r": metrics["avg_win_r"],
                "profit_factor": metrics["profit_factor"],
                "worst_month": metrics["worst_month"],
                "worst_month_r": metrics["worst_month_r"],
                "max_losing_streak": metrics["max_losing_streak"],
            }
        )
    return pd.DataFrame(rows)


def _summary_table(summary: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        summary.groupby(["variant", "scope"], as_index=False)
        .agg(
            cagr_pct=("cagr_pct", "mean"),
            sharpe=("sharpe", "mean"),
            max_drawdown_pct=("max_drawdown_pct", "mean"),
            total_return_pct=("total_return_pct", "mean"),
            total_r=("total_r", "mean"),
            expectancy_r=("expectancy_r", "mean"),
            win_rate=("win_rate", "mean"),
            trade_count=("trade_count", "mean"),
            avg_holding_days=("avg_holding_days", "mean"),
            avg_loss_r=("avg_loss_r", "mean"),
            avg_win_r=("avg_win_r", "mean"),
            profit_factor=("profit_factor", "mean"),
            max_losing_streak=("max_losing_streak", "mean"),
        )
    )
    return grouped.sort_values(["scope", "variant"]).reset_index(drop=True)


def _collect_filter_log(results: dict[tuple[str, str, str], dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (scenario, variant, scope), result in results.items():
        for record in result["diagnostics"].get("pre_entry_filter_log", []):
            rows.append({"scenario": scenario, "variant": variant, "scope": scope, **record})
    return pd.DataFrame(rows)


def _bucket_total_r(trades: pd.DataFrame, bucket_col: str) -> pd.DataFrame:
    if trades.empty or bucket_col not in trades.columns:
        return pd.DataFrame()
    grouped = trades.groupby(["variant", "scope", bucket_col], as_index=False).agg(total_r=("realized_R", "sum"), trade_count=("realized_R", "size"))
    return grouped


def _build_variant_trade_frame(
    results: dict[tuple[str, str, str], dict[str, Any]],
    frames: dict[str, pd.DataFrame],
    metadata_lookup: dict[str, dict[str, Any]],
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for (scenario, variant, scope), result in results.items():
        frame = _enrich_trade_frame(scenario, result, frames, metadata_lookup, scope)
        frame["variant"] = variant
        rows.append(frame)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _robustness_check(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    baseline = trades[trades["variant"] == "baseline"].copy()
    rows: list[dict[str, Any]] = []
    dimensions = {
        "scenario": "scenario",
        "sector": "sector_bucket",
        "regime": "regime_state",
        "month": "entry_date",
        "symbol_group": "symbol",
    }
    for scope in sorted(trades["scope"].unique()):
        baseline_scope = baseline[baseline["scope"] == scope]
        for variant in sorted(v for v in trades["variant"].unique() if v != "baseline"):
            variant_scope = trades[(trades["scope"] == scope) & (trades["variant"] == variant)]
            for dimension, column in dimensions.items():
                base_grouped = baseline_scope.groupby(column)["realized_R"].sum()
                var_grouped = variant_scope.groupby(column)["realized_R"].sum()
                keys = sorted(set(base_grouped.index) | set(var_grouped.index))
                if not keys:
                    continue
                deltas = [(str(key), float(var_grouped.get(key, 0.0) - base_grouped.get(key, 0.0))) for key in keys]
                positive = sum(1 for _, delta in deltas if delta > 0)
                total_abs = sum(abs(delta) for _, delta in deltas) or 1.0
                dominant_share = max(abs(delta) for _, delta in deltas) / total_abs if deltas else 0.0
                rows.append(
                    {
                        "variant": variant,
                        "scope": scope,
                        "dimension": dimension,
                        "group_count": len(deltas),
                        "positive_delta_groups": positive,
                        "positive_delta_share": round(positive / max(len(deltas), 1), 6),
                        "dominant_group_share": round(float(dominant_share), 6),
                        "robustness_level": "high" if positive / max(len(deltas), 1) >= 0.60 and dominant_share < 0.40 else "medium" if positive / max(len(deltas), 1) >= 0.45 and dominant_share < 0.55 else "low",
                    }
                )
    return pd.DataFrame(rows)


def _variant_label(variant: str, summary_lookup: dict[tuple[str, str], dict[str, Any]], robustness: pd.DataFrame) -> str:
    if variant == "baseline":
        return "REJECT"
    base_oos = summary_lookup.get(("baseline", "anchored_oos"), {})
    var_oos = summary_lookup.get((variant, "anchored_oos"), {})
    base_full = summary_lookup.get(("baseline", "full_period"), {})
    var_full = summary_lookup.get((variant, "full_period"), {})
    oos_expect_improve = float(var_oos.get("expectancy_r", -999.0)) > float(base_oos.get("expectancy_r", -999.0))
    oos_mdd_improve = float(var_oos.get("max_drawdown_pct", 999.0)) < float(base_oos.get("max_drawdown_pct", 999.0))
    full_damage = float(var_full.get("total_return_pct", 0.0)) < float(base_full.get("total_return_pct", 0.0)) - 2.0
    trade_count_ok = float(var_oos.get("trade_count", 0.0)) >= float(base_oos.get("trade_count", 0.0)) * 0.60
    variant_rob = robustness[robustness["variant"] == variant]
    min_rob = "low"
    if not variant_rob.empty:
        levels = set(variant_rob["robustness_level"].astype(str))
        if "low" in levels:
            min_rob = "low"
        elif "medium" in levels:
            min_rob = "medium"
        else:
            min_rob = "high"
    if oos_expect_improve and oos_mdd_improve and trade_count_ok and not full_damage and min_rob in {"medium", "high"}:
        return "PROMOTE"
    if oos_expect_improve and oos_mdd_improve and full_damage:
        return "DEFENSIVE_ONLY"
    if min_rob == "low":
        return "REJECT"
    return "NEEDS_MORE_TESTING"


def _write_report(
    out_dir: Path,
    summary: pd.DataFrame,
    regime_full: pd.DataFrame,
    regime_oos: pd.DataFrame,
    features_df: pd.DataFrame,
    separation: pd.DataFrame,
    regime_entry_matrix: pd.DataFrame,
    integrated_summary: pd.DataFrame,
    robustness: pd.DataFrame,
    labels: dict[str, str],
    bad_regimes: list[str],
    weak_regimes: list[str],
) -> None:
    def _df_to_markdown(df: pd.DataFrame) -> list[str]:
        if df.empty:
            return ["_No rows_"]
        cols = [str(column) for column in df.columns]
        lines = [
            "| " + " | ".join(cols) + " |",
            "| " + " | ".join(["---"] * len(cols)) + " |",
        ]
        for record in df.to_dict("records"):
            cells = []
            for column in cols:
                value = record.get(column, "")
                if isinstance(value, float):
                    cells.append("" if math.isnan(value) else f"{value:.6g}")
                else:
                    cells.append(str(value))
            lines.append("| " + " | ".join(cells) + " |")
        return lines

    lines: list[str] = []
    lines.append("# Task 325: Regime & Entry Quality Rebuild")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("- Task 324 showed post-entry rescue helps, but it does not fix the source of weak entries.")
    lines.append(f"- Rebuilt regime filter bad states: `{', '.join(bad_regimes) or 'none'}`.")
    lines.append(f"- Rebuilt regime filter weak states: `{', '.join(weak_regimes) or 'none'}`.")
    top_features = separation["feature"].tolist()
    lines.append(f"- Entry quality score was reduced to `{', '.join(top_features)}`.")
    lines.append("")
    lines.append("## What Task 324 Proved")
    lines.append("")
    lines.append("- Size overlay can soften drawdowns, but OOS stayed negative.")
    lines.append("- That pushed this task toward pre-entry regime and quality repair rather than more exit logic.")
    lines.append("")
    lines.append("## Why Regime and Entry Remain Broken")
    lines.append("")
    if not regime_oos.empty:
        worst = regime_oos.iloc[0]
        best = regime_oos.sort_values("expectancy_r", ascending=False).iloc[0]
        lines.append(f"- Worst rebuilt OOS regime: `{worst['regime']}` with expectancy `{worst['expectancy_r']:.3f}R` across `{int(worst['trade_count'])}` trades.")
        lines.append(f"- Best rebuilt OOS regime: `{best['regime']}` with expectancy `{best['expectancy_r']:.3f}R` across `{int(best['trade_count'])}` trades.")
    if not separation.empty:
        lines.append(f"- Strongest entry discriminators: `{', '.join(separation['feature'].head(3).tolist())}`.")
    lines.append("")
    lines.append("## New Regime Map")
    lines.append("")
    if not regime_oos.empty:
        lines.extend(_df_to_markdown(regime_oos))
        lines.append("")
    lines.append("## Entry Quality Separation Layer")
    lines.append("")
    if not separation.empty:
        lines.extend(_df_to_markdown(separation[["feature", "importance", "stability", "direction"]]))
        lines.append("")
    lines.append("## Regime × Entry Interaction")
    lines.append("")
    if not regime_entry_matrix.empty:
        lines.extend(_df_to_markdown(regime_entry_matrix))
        lines.append("")
    lines.append("## Integrated Filter Test")
    lines.append("")
    if not integrated_summary.empty:
        lines.extend(_df_to_markdown(integrated_summary))
        lines.append("")
    lines.append("## Robustness Review")
    lines.append("")
    if not robustness.empty:
        lines.extend(_df_to_markdown(robustness))
        lines.append("")
    lines.append("## Final Recommendation")
    lines.append("")
    lines.append(f"- regime filter: `{labels['regime_filter_only']}`")
    lines.append(f"- entry filter: `{labels['entry_quality_filter_only']}`")
    lines.append(f"- regime + entry: `{labels['regime_plus_entry_filter']}`")
    lines.append(f"- regime + entry + size50: `{labels['regime_plus_entry_plus_size50']}`")
    lines.append("")
    lines.append("The target here is not a prettier rescue layer. It is fewer low-quality entries at the source.")
    (out_dir / "task_325_regime_entry_rebuild.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 325: regime and entry quality rebuild for structural breakout.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--ranked-input", default=str(RANKED_INPUT))
    parser.add_argument("--candidate-pool", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ranked_input = Path(args.ranked_input)

    stocks = _load_stock_symbols(base_dir, StructuralConfig())
    frames, timestamps = _prepare_preloaded_frames(base_dir, stocks)
    scenarios = _select_top10_pool(
        base_dir=base_dir,
        ranked_input=ranked_input,
        candidate_pool=args.candidate_pool,
        jobs=args.jobs,
        stocks=stocks,
        frames=frames,
        timestamps=timestamps,
    )

    latest_end = max(timestamps)
    anchored = _anchored_oos_window(latest_end)
    full_timestamps = timestamps
    oos_timestamps = _slice_timestamps(timestamps, anchored.test_start, anchored.test_end)

    universe_state_lookup = _build_universe_state_lookup(frames, stocks)
    regime_lookup = _build_regime_lookup(base_dir, universe_state_lookup)
    metadata_lookup = _build_entry_feature_lookup(frames, stocks, universe_state_lookup, regime_lookup)

    baseline_results: dict[tuple[str, str], dict[str, Any]] = {}
    baseline_trade_frames: list[pd.DataFrame] = []
    for scenario in scenarios:
        cfg = _config_from_scenario(scenario)
        full_result = run_structural_backtest(cfg, base_dir, preloaded_frames=frames, preloaded_timestamps=full_timestamps, preloaded_symbols=stocks)
        oos_result = run_structural_backtest(cfg, base_dir, preloaded_frames=frames, preloaded_timestamps=oos_timestamps, preloaded_symbols=stocks)
        baseline_results[(scenario, "full_period")] = full_result
        baseline_results[(scenario, "anchored_oos")] = oos_result
        baseline_trade_frames.append(_enrich_trade_frame(scenario, full_result, frames, metadata_lookup, "full_period"))
        baseline_trade_frames.append(_enrich_trade_frame(scenario, oos_result, frames, metadata_lookup, "anchored_oos"))

    baseline_trade_df = pd.concat(baseline_trade_frames, ignore_index=True) if baseline_trade_frames else pd.DataFrame()
    full_trade_df = baseline_trade_df[baseline_trade_df["scope"] == "full_period"].copy()
    oos_trade_df = baseline_trade_df[baseline_trade_df["scope"] == "anchored_oos"].copy()

    regime_full = _regime_rebuild_table(full_trade_df)
    regime_oos = _regime_rebuild_table(oos_trade_df)
    transition_df = _regime_transition_diagnostics(regime_lookup)
    trade_distribution_df = _regime_trade_distribution(oos_trade_df)

    entry_features_df, comparison_df, separation_df = _entry_feature_frame(full_trade_df, oos_trade_df)
    metadata_lookup, entry_bands = _score_entry_quality_for_metadata(metadata_lookup, separation_df)
    for trade_df in (full_trade_df, oos_trade_df):
        trade_df["entry_quality_score"] = trade_df.apply(lambda row: metadata_lookup.get(f"{row['symbol']}|{row['entry_date']}", {}).get("entry_quality_score", math.nan), axis=1)
        trade_df["entry_quality_band"] = trade_df.apply(lambda row: metadata_lookup.get(f"{row['symbol']}|{row['entry_date']}", {}).get("entry_quality_band", "unknown"), axis=1)

    regime_entry_matrix_df = _regime_entry_matrix(oos_trade_df)
    regime_sector_entry_matrix_df = _regime_sector_entry_matrix(oos_trade_df)
    bad_regimes, weak_regimes = _choose_regime_filters(regime_full, regime_oos)

    validation_bands = _load_validation_bands(Path(DUAL_MAP_FRAME))
    variants = ["baseline", "regime_filter_only", "entry_quality_filter_only", "regime_plus_entry_filter", "regime_plus_entry_plus_size50"]
    integrated_results = _run_variant_results(
        scenarios,
        variants,
        base_dir=base_dir,
        stocks=stocks,
        frames=frames,
        full_timestamps=full_timestamps,
        oos_timestamps=oos_timestamps,
        metadata_lookup=metadata_lookup,
        entry_bands=entry_bands,
        bad_regimes=bad_regimes,
        weak_regimes=weak_regimes,
        validation_bands=validation_bands,
    )

    summary_df = _aggregate_variant_rows(integrated_results)
    integrated_summary_df = _summary_table(summary_df)
    oos_comparison_df = integrated_summary_df[integrated_summary_df["scope"] == "anchored_oos"].copy()
    full_comparison_df = integrated_summary_df[integrated_summary_df["scope"] == "full_period"].copy()
    filter_log_df = _collect_filter_log(integrated_results)
    variant_trade_df = _build_variant_trade_frame(integrated_results, frames, metadata_lookup)
    robustness_df = _robustness_check(variant_trade_df)

    summary_lookup = {
        (str(row["variant"]), str(row["scope"])): row
        for row in integrated_summary_df.to_dict("records")
    }
    labels = {
        variant: _variant_label(variant, summary_lookup, robustness_df)
        for variant in ["regime_filter_only", "entry_quality_filter_only", "regime_plus_entry_filter", "regime_plus_entry_plus_size50"]
    }
    integrated_summary_df["recommendation"] = integrated_summary_df["variant"].map(lambda variant: labels.get(str(variant), "REJECT") if str(variant) != "baseline" else "REJECT")

    entry_features_df.to_csv(out_dir / "task_325_entry_quality_features.csv", index=False)
    comparison_df.to_csv(out_dir / "task_325_entry_success_failure_comparison.csv", index=False)
    separation_df.to_csv(out_dir / "task_325_entry_separation_layer.csv", index=False)
    regime_full.to_csv(out_dir / "task_325_regime_rebuild.csv", index=False)
    transition_df.to_csv(out_dir / "task_325_regime_transition_diagnostics.csv", index=False)
    trade_distribution_df.to_csv(out_dir / "task_325_regime_trade_distribution.csv", index=False)
    regime_entry_matrix_df.to_csv(out_dir / "task_325_regime_entry_matrix.csv", index=False)
    regime_sector_entry_matrix_df.to_csv(out_dir / "task_325_regime_sector_entry_matrix.csv", index=False)
    integrated_summary_df.to_csv(out_dir / "task_325_integrated_filter_summary.csv", index=False)
    oos_comparison_df.to_csv(out_dir / "task_325_oos_comparison.csv", index=False)
    full_comparison_df.to_csv(out_dir / "task_325_full_period_comparison.csv", index=False)
    filter_log_df.to_csv(out_dir / "task_325_trade_filter_log.csv", index=False)
    robustness_df.to_csv(out_dir / "task_325_robustness_check.csv", index=False)

    _write_report(
        out_dir,
        summary_df,
        regime_full,
        regime_oos,
        entry_features_df,
        separation_df,
        regime_entry_matrix_df,
        integrated_summary_df,
        robustness_df,
        labels,
        bad_regimes,
        weak_regimes,
    )


if __name__ == "__main__":
    main()
