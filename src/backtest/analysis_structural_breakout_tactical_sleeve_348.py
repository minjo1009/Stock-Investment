from __future__ import annotations

import argparse
import math
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table
from src.backtest.analysis_structural_breakout_conditional_edge_integration_342 import (
    _apply_cost_scaled,
    _f,
    _portfolio_metrics,
)
from src.backtest.analysis_structural_breakout_coverage_corrected_revalidation_346 import (
    _corrected_build_split_frames,
    _corrected_entry_only_master,
)
from src.backtest.analysis_structural_breakout_strong_subset_validation_340 import (
    DB_PATH,
    DEFAULT_COST_SCENARIOS,
    ROLLING_WINDOWS,
    _current_subset_mask,
    _rolling_label,
)
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import _load_intraday_bars


DEFAULT_OUT_DIR = Path("docs/reports/task_348_tactical_breakout_sleeve")
SUPPORTED_SECTOR = "software_internet"
NUMERIC_EXECUTION_FEATURES = [
    "price_vs_session_vwap_at_breakout",
    "vwap_deviation_at_breakout",
    "vwap_slope_prebreak",
    "breakout_hold_duration_bars",
    "breakout_bar_close_location",
    "return_next_3bars",
    "return_next_5bars",
    "adverse_excursion_next_3bars",
    "intraday_pullback_depth_3bars",
    "breakout_window_volume_surge",
    "volume_persistence_3bars",
    "relative_volume_percentile",
    "rejection_wick_ratio",
    "failed_break_count_prebreak",
    "false_break_attempts_prebreak",
]
CATEGORICAL_EXECUTION_FEATURES = [
    "vwap_response",
    "breakout_response",
    "vwap_reversion_flag_3bars",
    "session_timing_bucket",
]


def _prepare_corrected_entry_master() -> pd.DataFrame:
    intraday_df = _load_intraday_bars(DB_PATH)
    _, feature_parts = _corrected_build_split_frames(intraday_df)
    master = _corrected_entry_only_master(feature_parts).copy()
    master["trade_id"] = master["trade_id"].astype(str)
    master["entry_ts"] = pd.to_datetime(master["entry_ts"], errors="coerce", utc=True)
    master["exit_ts"] = pd.to_datetime(master["exit_date"], errors="coerce", utc=True)
    missing_exit = master["exit_ts"].isna()
    master.loc[missing_exit, "exit_ts"] = master.loc[missing_exit, "entry_ts"] + pd.to_timedelta(
        pd.to_numeric(master.loc[missing_exit, "holding_days"], errors="coerce").fillna(1.0),
        unit="D",
    )
    master["breakout_timestamp"] = pd.to_datetime(master["breakout_timestamp"], errors="coerce", utc=True)
    master["realized_R"] = pd.to_numeric(master["realized_R"], errors="coerce")
    return master.reset_index(drop=True)


def _session_timing_bucket(ts: pd.Timestamp | str | None) -> str:
    if ts is None or pd.isna(ts):
        return "unknown"
    stamp = pd.Timestamp(ts)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize("UTC")
    local = stamp.tz_convert(ZoneInfo("America/New_York"))
    session_open = local.normalize() + pd.Timedelta(hours=9, minutes=30)
    minutes = float((local - session_open).total_seconds() / 60.0)
    if minutes < 0:
        return "unknown"
    if minutes < 30:
        return "first_30m"
    if minutes >= 330:
        return "last_hour"
    return "mid_session"


def _coarse_band(train_series: pd.Series, eval_series: pd.Series) -> tuple[pd.Series, pd.Series]:
    train_num = pd.to_numeric(train_series, errors="coerce")
    eval_num = pd.to_numeric(eval_series, errors="coerce")
    if train_num.notna().sum() < 5:
        return (
            pd.Series(["missing" if pd.isna(v) else "mid" for v in train_num], index=train_series.index),
            pd.Series(["missing" if pd.isna(v) else "mid" for v in eval_num], index=eval_series.index),
        )
    low = float(train_num.quantile(0.30))
    high = float(train_num.quantile(0.70))

    def _band(value: float) -> str:
        if pd.isna(value):
            return "missing"
        if value < low:
            return "low"
        if value > high:
            return "high"
        return "mid"

    return train_num.map(_band), eval_num.map(_band)


def _add_execution_bands(master: pd.DataFrame) -> pd.DataFrame:
    out = master.copy()
    train_df = out[out["current_split"] == "train"].copy()
    for feature in NUMERIC_EXECUTION_FEATURES:
        if feature not in out.columns:
            continue
        train_band, eval_band = _coarse_band(train_df[feature], out[feature])
        out[f"{feature}_band348"] = eval_band.values
    return out


def _execution_quality_score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    vwap_good = (
        (out["vwap_response"].astype(str) == "vwap_hold")
        | (pd.to_numeric(out["price_vs_session_vwap_at_breakout"], errors="coerce") > 0)
    )
    breakout_good = (
        (out["breakout_response"].astype(str) == "breakout_hold")
        | (pd.to_numeric(out["breakout_hold_duration_bars"], errors="coerce") >= 1)
    )
    volume_good = (
        (out.get("volume_persistence_3bars_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "high")
        | (out.get("breakout_window_volume_surge_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "high")
    )
    adverse_bad = (
        (out.get("adverse_excursion_next_3bars_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "high")
        | (out.get("intraday_pullback_depth_3bars_band348", pd.Series(index=out.index, dtype=object)).astype(str) == "high")
    )
    score = vwap_good.astype(int) + breakout_good.astype(int) + volume_good.astype(int) - adverse_bad.astype(int)
    out["execution_quality_score"] = score
    out["execution_quality_bucket"] = np.where(score >= 2, "strong", np.where(score <= 0, "weak", "mixed"))
    return out


def _build_sleeve_frames(master: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = master[_current_subset_mask(master)].copy()
    supported = base[base["sector_group"].astype(str) == SUPPORTED_SECTOR].copy()
    return {
        "base_tactical_sleeve": base.reset_index(drop=True),
        "supported_tactical_sleeve": supported.reset_index(drop=True),
    }


def _uniform_scaled(df: pd.DataFrame) -> pd.DataFrame:
    scoped = df.copy()
    scoped["size_multiplier"] = 1.0
    scoped["scaled_R"] = pd.to_numeric(scoped["realized_R"], errors="coerce")
    return scoped


def _annual_trade_frequency(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    start = pd.Timestamp(df["entry_ts"].min())
    end = pd.Timestamp(df["entry_ts"].max())
    years = max((end - start).days / 365.25, 1.0 / 365.25)
    return float(len(df) / years)


def _longest_inactive_period_days(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    days = pd.to_datetime(df["entry_ts"], utc=True, errors="coerce").dt.normalize().dropna().sort_values().unique()
    if len(days) <= 1:
        return 0
    diffs = np.diff(days).astype("timedelta64[D]").astype(int)
    return int(max(int(d) for d in diffs))


def _capital_utilization_ratio(sleeve_df: pd.DataFrame, eligible_df: pd.DataFrame) -> float:
    if eligible_df.empty:
        return 0.0
    sleeve_days = set(pd.to_datetime(sleeve_df["entry_ts"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d"))
    eligible_days = set(pd.to_datetime(eligible_df["entry_ts"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d"))
    return float(len(sleeve_days) / max(len(eligible_days), 1))


def _cost_expectancy(df: pd.DataFrame, slippage_rate: float, fee_rate: float) -> float:
    scoped = _uniform_scaled(df)
    scoped["scaled_R"] = _apply_cost_scaled(scoped, slippage_rate, fee_rate)
    return float(pd.to_numeric(scoped["scaled_R"], errors="coerce").mean()) if not scoped.empty else math.nan


def _sleeve_performance_rows(master: pd.DataFrame, sleeve_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    scenarios = [
        ("cost_1x_expectancy", DEFAULT_COST_SCENARIOS[0].slippage_rate, DEFAULT_COST_SCENARIOS[0].fee_rate),
        ("cost_2x_expectancy", DEFAULT_COST_SCENARIOS[1].slippage_rate, DEFAULT_COST_SCENARIOS[1].fee_rate),
        ("cost_3x_expectancy", DEFAULT_COST_SCENARIOS[2].slippage_rate, DEFAULT_COST_SCENARIOS[2].fee_rate),
    ]
    for sleeve_name, sleeve_df in sleeve_frames.items():
        split_map = {
            "full_period": sleeve_df.copy(),
            "anchored_oos": sleeve_df[sleeve_df["current_split"] == "anchored_oos"].copy(),
        }
        eligible_map = {
            "full_period": master.copy(),
            "anchored_oos": master[master["current_split"] == "anchored_oos"].copy(),
        }
        for scope_name, scoped in split_map.items():
            perf = _uniform_scaled(scoped)
            metrics = _portfolio_metrics(perf)
            row = {
                "sleeve_name": sleeve_name,
                "scope": scope_name,
                "window_id": "",
                "trade_count": int(len(scoped)),
                "annual_trade_frequency": _f(_annual_trade_frequency(scoped)),
                "expectancy": metrics["expectancy"],
                "sharpe_proxy": metrics["sharpe"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "return_pct": metrics["return_pct"],
                "capital_utilization_ratio": _f(_capital_utilization_ratio(scoped, eligible_map[scope_name])),
                "longest_inactive_period_days": _longest_inactive_period_days(scoped),
            }
            for label, slip, fee in scenarios:
                row[label] = _f(_cost_expectancy(scoped, slip, fee)) if not scoped.empty else math.nan
            rows.append(row)
        for window in ROLLING_WINDOWS:
            train_df = master[
                (master["entry_ts"] >= pd.Timestamp(window.train_start, tz="UTC"))
                & (master["entry_ts"] <= pd.Timestamp(window.train_end, tz="UTC"))
            ].copy()
            oos_df = master[
                (master["entry_ts"] >= pd.Timestamp(window.oos_start, tz="UTC"))
                & (master["entry_ts"] <= pd.Timestamp(window.oos_end, tz="UTC"))
            ].copy()
            labeled_oos = _rolling_label(train_df, oos_df) if not train_df.empty and not oos_df.empty else oos_df.copy()
            labeled_oos["entry_ts"] = pd.to_datetime(labeled_oos["entry_ts"], errors="coerce", utc=True)
            labeled_oos["breakout_timestamp"] = pd.to_datetime(labeled_oos["breakout_timestamp"], errors="coerce", utc=True)
            rolling_sleeves = _build_sleeve_frames(labeled_oos)
            scoped = rolling_sleeves[sleeve_name].copy()
            perf = _uniform_scaled(scoped)
            metrics = _portfolio_metrics(perf)
            row = {
                "sleeve_name": sleeve_name,
                "scope": "rolling_window",
                "window_id": window.window_id,
                "trade_count": int(len(scoped)),
                "annual_trade_frequency": _f(_annual_trade_frequency(scoped)),
                "expectancy": metrics["expectancy"],
                "sharpe_proxy": metrics["sharpe"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "return_pct": metrics["return_pct"],
                "capital_utilization_ratio": _f(_capital_utilization_ratio(scoped, labeled_oos)),
                "longest_inactive_period_days": _longest_inactive_period_days(scoped),
            }
            for label, slip, fee in scenarios:
                row[label] = _f(_cost_expectancy(scoped, slip, fee)) if not scoped.empty else math.nan
            rows.append(row)
    return pd.DataFrame(rows)


def _share(df: pd.DataFrame, label: str) -> float:
    if df.empty:
        return math.nan
    return float((df["cluster_label_base"].astype(str) == label).mean())


def _execution_quality_features(master: pd.DataFrame, sleeve_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for sleeve_name, sleeve_df in sleeve_frames.items():
        scoped = sleeve_df.copy()
        scoped["sleeve_name"] = sleeve_name
        scoped["session_timing_bucket"] = scoped["breakout_timestamp"].map(_session_timing_bucket)
        rows.append(scoped)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    out = _add_execution_bands(out)
    out = _execution_quality_score(out)
    return out


def _diagnostic_rows(features_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for sleeve_name in sorted(features_df["sleeve_name"].astype(str).unique()):
        sleeve_df = features_df[features_df["sleeve_name"].astype(str) == sleeve_name].copy()
        for scope_name, scoped in (
            ("full_period", sleeve_df),
            ("anchored_oos", sleeve_df[sleeve_df["current_split"] == "anchored_oos"].copy()),
        ):
            for feature in NUMERIC_EXECUTION_FEATURES:
                band_col = f"{feature}_band348"
                if band_col not in scoped.columns:
                    continue
                for band, band_df in scoped.groupby(band_col, dropna=False):
                    realized = pd.to_numeric(band_df["realized_R"], errors="coerce")
                    rows.append(
                        {
                            "sleeve_name": sleeve_name,
                            "scope": scope_name,
                            "feature_name": feature,
                            "band_or_bucket": str(band),
                            "trade_count": int(len(band_df)),
                            "win_rate": _f(float((realized > 0).mean()) * 100.0) if not band_df.empty else math.nan,
                            "expectancy": _f(float(realized.mean())) if not band_df.empty else math.nan,
                            "clean_continuation_share": _f(_share(band_df, "clean_continuation")),
                            "dead_breakout_share": _f(_share(band_df, "dead_breakout")),
                            "failed_pop_share": _f(_share(band_df, "failed_pop")),
                        }
                    )
            for feature in CATEGORICAL_EXECUTION_FEATURES + ["execution_quality_bucket"]:
                if feature not in scoped.columns:
                    continue
                for bucket, bucket_df in scoped.groupby(feature, dropna=False):
                    realized = pd.to_numeric(bucket_df["realized_R"], errors="coerce")
                    rows.append(
                        {
                            "sleeve_name": sleeve_name,
                            "scope": scope_name,
                            "feature_name": feature,
                            "band_or_bucket": str(bucket),
                            "trade_count": int(len(bucket_df)),
                            "win_rate": _f(float((realized > 0).mean()) * 100.0) if not bucket_df.empty else math.nan,
                            "expectancy": _f(float(realized.mean())) if not bucket_df.empty else math.nan,
                            "clean_continuation_share": _f(_share(bucket_df, "clean_continuation")),
                            "dead_breakout_share": _f(_share(bucket_df, "dead_breakout")),
                            "failed_pop_share": _f(_share(bucket_df, "failed_pop")),
                        }
                    )
    return pd.DataFrame(rows)


def _comparison_numeric(df_pos: pd.DataFrame, df_neg: pd.DataFrame, feature: str) -> dict[str, object]:
    pos_vals = pd.to_numeric(df_pos.get(feature), errors="coerce")
    neg_vals = pd.to_numeric(df_neg.get(feature), errors="coerce")
    pos_mean = float(pos_vals.mean()) if pos_vals.notna().any() else math.nan
    neg_mean = float(neg_vals.mean()) if neg_vals.notna().any() else math.nan
    return {
        "feature_name": feature,
        "bucket_or_stat": "mean",
        "positive_group_value": _f(pos_mean) if not math.isnan(pos_mean) else math.nan,
        "negative_group_value": _f(neg_mean) if not math.isnan(neg_mean) else math.nan,
        "delta": _f(pos_mean - neg_mean) if not math.isnan(pos_mean) and not math.isnan(neg_mean) else math.nan,
        "positive_trade_count": int(pos_vals.notna().sum()),
        "negative_trade_count": int(neg_vals.notna().sum()),
    }


def _comparison_categorical(df_pos: pd.DataFrame, df_neg: pd.DataFrame, feature: str, bucket: str) -> dict[str, object]:
    pos_share = float((df_pos[feature].astype(str) == bucket).mean()) if not df_pos.empty else math.nan
    neg_share = float((df_neg[feature].astype(str) == bucket).mean()) if not df_neg.empty else math.nan
    return {
        "feature_name": feature,
        "bucket_or_stat": bucket,
        "positive_group_value": _f(pos_share) if not math.isnan(pos_share) else math.nan,
        "negative_group_value": _f(neg_share) if not math.isnan(neg_share) else math.nan,
        "delta": _f(pos_share - neg_share) if not math.isnan(pos_share) and not math.isnan(neg_share) else math.nan,
        "positive_trade_count": int(len(df_pos)),
        "negative_trade_count": int(len(df_neg)),
    }


def _good_vs_bad_rows(features_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    comparisons = [
        ("winner_vs_loser", lambda df: pd.to_numeric(df["realized_R"], errors="coerce") > 0, lambda df: pd.to_numeric(df["realized_R"], errors="coerce") <= 0),
        ("clean_continuation_vs_dead_breakout", lambda df: df["cluster_label_base"].astype(str) == "clean_continuation", lambda df: df["cluster_label_base"].astype(str) == "dead_breakout"),
        ("clean_continuation_vs_failed_pop", lambda df: df["cluster_label_base"].astype(str) == "clean_continuation", lambda df: df["cluster_label_base"].astype(str) == "failed_pop"),
    ]
    for sleeve_name in sorted(features_df["sleeve_name"].astype(str).unique()):
        scoped = features_df[features_df["sleeve_name"].astype(str) == sleeve_name].copy()
        for comparison_name, pos_fn, neg_fn in comparisons:
            pos_df = scoped[pos_fn(scoped)].copy()
            neg_df = scoped[neg_fn(scoped)].copy()
            for feature in NUMERIC_EXECUTION_FEATURES:
                if feature not in scoped.columns:
                    continue
                row = _comparison_numeric(pos_df, neg_df, feature)
                row["sleeve_name"] = sleeve_name
                row["comparison_scope"] = comparison_name
                rows.append(row)
            for feature in CATEGORICAL_EXECUTION_FEATURES + ["execution_quality_bucket"]:
                if feature not in scoped.columns:
                    continue
                for bucket in sorted(scoped[feature].astype(str).dropna().unique().tolist()):
                    row = _comparison_categorical(pos_df, neg_df, feature, bucket)
                    row["sleeve_name"] = sleeve_name
                    row["comparison_scope"] = comparison_name
                    rows.append(row)
    return pd.DataFrame(rows)


def _capacity_rows(master: pd.DataFrame, sleeve_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for sleeve_name, sleeve_df in sleeve_frames.items():
        for scope_name, scoped in (
            ("full_period", sleeve_df),
            ("anchored_oos", sleeve_df[sleeve_df["current_split"] == "anchored_oos"].copy()),
        ):
            if scoped.empty:
                rows.append(
                    {
                        "sleeve_name": sleeve_name,
                        "scope": scope_name,
                        "trade_count": 0,
                        "symbol_concentration_share": math.nan,
                        "sector_concentration_share": math.nan,
                        "average_simultaneous_signals": 0.0,
                        "max_simultaneous_signals": 0,
                        "turnover_proxy": 0.0,
                        "capital_utilization_ratio": 0.0,
                        "estimated_capacity_risk": "high",
                    }
                )
                continue
            day_counts = scoped.groupby(pd.to_datetime(scoped["entry_ts"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d")).size()
            symbol_share = float(scoped["symbol"].astype(str).value_counts(normalize=True).iloc[0])
            sector_share = float(scoped["sector_group"].astype(str).value_counts(normalize=True).iloc[0])
            avg_sim = float(day_counts.mean()) if not day_counts.empty else 0.0
            max_sim = int(day_counts.max()) if not day_counts.empty else 0
            turnover = _annual_trade_frequency(scoped)
            util = _capital_utilization_ratio(scoped, master if scope_name == "full_period" else master[master["current_split"] == "anchored_oos"].copy())
            if symbol_share > 0.50 or sector_share > 0.75 or avg_sim < 1.2:
                capacity_risk = "high"
            elif symbol_share > 0.35 or sector_share > 0.60 or avg_sim < 1.5:
                capacity_risk = "medium"
            else:
                capacity_risk = "low"
            rows.append(
                {
                    "sleeve_name": sleeve_name,
                    "scope": scope_name,
                    "trade_count": int(len(scoped)),
                    "symbol_concentration_share": _f(symbol_share),
                    "sector_concentration_share": _f(sector_share),
                    "average_simultaneous_signals": _f(avg_sim),
                    "max_simultaneous_signals": max_sim,
                    "turnover_proxy": _f(turnover),
                    "capital_utilization_ratio": _f(util),
                    "estimated_capacity_risk": capacity_risk,
                }
            )
    return pd.DataFrame(rows)


def _shadow_spec() -> pd.DataFrame:
    rows = [
        ("field", "date", "Daily observation date."),
        ("field", "candidate_symbols", "Symbols that qualified for tactical sleeve review that day."),
        ("field", "condition_met", "Whether tactical sleeve condition was met."),
        ("field", "execution_quality_score", "Interpretable additive execution-quality score."),
        ("field", "vwap_hold_or_rejection", "VWAP behavior state at/after breakout."),
        ("field", "breakout_hold_duration", "Bars spent above breakout level."),
        ("field", "volume_persistence", "Post-breakout volume persistence signal."),
        ("field", "selected_or_not_selected", "Shadow sleeve selection flag."),
        ("field", "realized_1d_R", "Forward 1-day R outcome."),
        ("field", "realized_3d_R", "Forward 3-day R outcome."),
        ("field", "realized_5d_R", "Forward 5-day R outcome."),
        ("field", "slippage_estimate", "Estimated execution slippage against modeled fill."),
        ("field", "sector_concentration", "Daily sector concentration among sleeve candidates."),
        ("metric", "condition_met_frequency", "How often tactical sleeve candidates occur."),
        ("metric", "condition_met_expectancy", "Average realized expectancy of sleeve candidates."),
        ("metric", "condition_met_vs_non_condition_spread", "Spread between sleeve and non-sleeve outcomes."),
        ("metric", "execution_quality_bucket_performance", "Performance split by weak/mixed/strong execution score."),
        ("metric", "slippage_drift", "Live slippage drift vs historical expectation."),
        ("metric", "edge_decay", "Rolling degradation in sleeve expectancy or hit rate."),
        ("metric", "sector_concentration", "Concentration drift that may signal capacity stress."),
    ]
    return pd.DataFrame(rows, columns=["row_type", "name", "description"])


def _diagnostic_summary(good_bad_df: pd.DataFrame, features_df: pd.DataFrame) -> dict[str, object]:
    scoped = good_bad_df[
        (good_bad_df["sleeve_name"] == "base_tactical_sleeve")
        & (good_bad_df["comparison_scope"] == "winner_vs_loser")
    ].copy()
    def _delta(feature: str, bucket: str = "mean") -> float:
        match = scoped[(scoped["feature_name"] == feature) & (scoped["bucket_or_stat"] == bucket)]
        if match.empty:
            return math.nan
        return float(pd.to_numeric(match.iloc[0]["delta"], errors="coerce"))

    vwap_better = bool((_delta("price_vs_session_vwap_at_breakout") > 0) or (_delta("vwap_response", "vwap_hold") > 0))
    breakout_hold_better = bool((_delta("breakout_hold_duration_bars") > 0) or (_delta("breakout_response", "breakout_hold") > 0))
    volume_matters = bool((_delta("volume_persistence_3bars") > 0) or (_delta("breakout_window_volume_surge") > 0))
    adverse_predictive = bool((_delta("adverse_excursion_next_3bars") < 0) or (_delta("intraday_pullback_depth_3bars") < 0))

    bucket_df = features_df[features_df["sleeve_name"] == "base_tactical_sleeve"].copy()
    session_exp = bucket_df.groupby("session_timing_bucket")["realized_R"].mean() if not bucket_df.empty else pd.Series(dtype=float)
    session_trade_counts = bucket_df.groupby("session_timing_bucket").size() if not bucket_df.empty else pd.Series(dtype=int)
    valid_sessions = session_exp[session_trade_counts.reindex(session_exp.index).fillna(0) >= 3]
    session_matters = bool((valid_sessions.max() - valid_sessions.min()) > 0.1) if len(valid_sessions) >= 2 else False
    score = sum(int(v) for v in (vwap_better, breakout_hold_better, volume_matters, adverse_predictive, session_matters))
    return {
        "winners_hold_vwap_better": vwap_better,
        "losers_fail_breakout_faster": breakout_hold_better,
        "volume_persistence_matters": volume_matters,
        "early_adverse_excursion_predictive": adverse_predictive,
        "session_timing_matters": session_matters,
        "diagnostic_strength_score": score,
    }


def _final_decision(perf_df: pd.DataFrame, capacity_df: pd.DataFrame, diagnostic_summary: dict[str, object]) -> pd.DataFrame:
    anchored = perf_df[
        (perf_df["sleeve_name"] == "base_tactical_sleeve")
        & (perf_df["scope"] == "anchored_oos")
    ].iloc[0]
    rolling = perf_df[
        (perf_df["sleeve_name"] == "base_tactical_sleeve")
        & (perf_df["scope"] == "rolling_window")
    ].copy()
    rolling_positive = int((pd.to_numeric(rolling["expectancy"], errors="coerce") > 0).sum())
    capacity = capacity_df[
        (capacity_df["sleeve_name"] == "base_tactical_sleeve")
        & (capacity_df["scope"] == "anchored_oos")
    ].iloc[0]
    score = int(diagnostic_summary["diagnostic_strength_score"])
    anchored_expectancy = float(pd.to_numeric(pd.Series([anchored["expectancy"]]), errors="coerce").iloc[0])
    cost_1x = float(pd.to_numeric(pd.Series([anchored["cost_1x_expectancy"]]), errors="coerce").iloc[0])
    cost_2x = float(pd.to_numeric(pd.Series([anchored["cost_2x_expectancy"]]), errors="coerce").iloc[0])
    inactive_days = int(anchored["longest_inactive_period_days"])
    util_ratio = float(anchored["capital_utilization_ratio"])
    capacity_risk = str(capacity["estimated_capacity_risk"])

    if anchored_expectancy <= 0 or cost_1x <= 0 or (inactive_days > 250 and util_ratio < 0.05):
        decision = "NO_TACTICAL_EDGE"
        reason = "Corrected tactical sleeve remains non-positive or practically unusable after cost/inactivity checks."
    elif score < 3 or capacity_risk == "high" or cost_2x <= 0:
        decision = "TACTICAL_EDGE_RESEARCH_ONLY"
        reason = "Sleeve exists, but execution-quality separation or cost/capacity robustness is still weak."
    elif rolling_positive >= 3 and score >= 4 and cost_2x > 0 and capacity_risk in {"low", "medium"}:
        decision = "TACTICAL_EDGE_SMALL_CAPITAL_READY"
        reason = "Sleeve is positive, execution-quality diagnostics separate good vs bad breakouts, and 2x cost remains survivable."
    else:
        decision = "TACTICAL_EDGE_SHADOW_READY"
        reason = "Sleeve is promising enough for shadow monitoring, but cost or concentration still blocks live capital."

    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "anchored_oos_expectancy": _f(anchored_expectancy),
                "anchored_oos_cost_1x_expectancy": _f(cost_1x),
                "anchored_oos_cost_2x_expectancy": _f(cost_2x),
                "rolling_positive_windows": rolling_positive,
                "diagnostic_strength_score": score,
                "capacity_risk": capacity_risk,
            }
        ]
    )


def _report(
    out_dir: Path,
    perf_df: pd.DataFrame,
    diagnostics_df: pd.DataFrame,
    good_bad_df: pd.DataFrame,
    capacity_df: pd.DataFrame,
    final_df: pd.DataFrame,
    diagnostic_summary: dict[str, object],
) -> None:
    final_row = final_df.iloc[0]
    anchored = perf_df[
        (perf_df["sleeve_name"] == "base_tactical_sleeve")
        & (perf_df["scope"] == "anchored_oos")
    ].iloc[0]
    lines = [
        "# Task 348 - Tactical Breakout Sleeve & Execution-Quality Model",
        "",
        f"- decision: {final_row['decision']}",
        f"- anchored_oos_expectancy: {final_row['anchored_oos_expectancy']}",
        f"- anchored_oos_cost_2x_expectancy: {final_row['anchored_oos_cost_2x_expectancy']}",
        f"- rolling_positive_windows: {final_row['rolling_positive_windows']}",
        f"- diagnostic_strength_score: {final_row['diagnostic_strength_score']}",
        f"- capacity_risk: {final_row['capacity_risk']}",
        "",
        "## Final Interpretation",
        f"1. Core portfolio alpha or tactical sleeve alpha: tactical sleeve alpha.",
        f"2. Current bottleneck: {'execution quality and capacity' if int(final_row['diagnostic_strength_score']) < 4 or str(final_row['capacity_risk']) != 'low' else 'capacity'} .",
        "3. Shadow must prove: execution-quality bucket persistence, cost/slippage stability, and concentration drift control before live capital.",
        f"4. Continue research, shadow monitor, or stop: {final_row['decision']}.",
        "",
        "## Sleeve Snapshot",
        *(
            _markdown_table(
                pd.DataFrame(
                    [
                        {
                            "trade_count": anchored["trade_count"],
                            "annual_trade_frequency": anchored["annual_trade_frequency"],
                            "expectancy": anchored["expectancy"],
                            "sharpe_proxy": anchored["sharpe_proxy"],
                            "max_drawdown_pct": anchored["max_drawdown_pct"],
                            "capital_utilization_ratio": anchored["capital_utilization_ratio"],
                            "longest_inactive_period_days": anchored["longest_inactive_period_days"],
                        }
                    ]
                )
            )
        ),
        "",
        "## Execution-Quality Answers",
        f"- winners_hold_vwap_better: {diagnostic_summary['winners_hold_vwap_better']}",
        f"- losers_fail_breakout_faster: {diagnostic_summary['losers_fail_breakout_faster']}",
        f"- volume_persistence_matters: {diagnostic_summary['volume_persistence_matters']}",
        f"- early_adverse_excursion_predictive: {diagnostic_summary['early_adverse_excursion_predictive']}",
        f"- session_timing_matters: {diagnostic_summary['session_timing_matters']}",
    ]
    (out_dir / "task_348_tactical_breakout_sleeve.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 348 tactical breakout sleeve")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    master = _prepare_corrected_entry_master()
    sleeve_frames = _build_sleeve_frames(master)
    perf_df = _sleeve_performance_rows(master, sleeve_frames)
    features_df = _execution_quality_features(master, sleeve_frames)
    diagnostics_df = _diagnostic_rows(features_df)
    good_bad_df = _good_vs_bad_rows(features_df)
    capacity_df = _capacity_rows(master, sleeve_frames)
    shadow_df = _shadow_spec()
    diagnostic_summary = _diagnostic_summary(good_bad_df, features_df)
    final_df = _final_decision(perf_df, capacity_df, diagnostic_summary)

    perf_df.to_csv(out_dir / "task_348_tactical_sleeve_performance.csv", index=False)
    features_df.to_csv(out_dir / "task_348_execution_quality_features.csv", index=False)
    diagnostics_df.to_csv(out_dir / "task_348_execution_quality_diagnostics.csv", index=False)
    good_bad_df.to_csv(out_dir / "task_348_good_vs_bad_breakout_diagnostics.csv", index=False)
    capacity_df.to_csv(out_dir / "task_348_sleeve_capacity_concentration.csv", index=False)
    shadow_df.to_csv(out_dir / "task_348_shadow_monitoring_spec.csv", index=False)
    final_df.to_csv(out_dir / "task_348_final_decision.csv", index=False)
    _report(out_dir, perf_df, diagnostics_df, good_bad_df, capacity_df, final_df, diagnostic_summary)


if __name__ == "__main__":
    main()
