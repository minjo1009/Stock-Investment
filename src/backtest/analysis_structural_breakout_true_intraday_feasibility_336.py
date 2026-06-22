from __future__ import annotations

import argparse
import math
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import (
    BAD_STATE_BASES,
    CLEAN_STATE_BASE,
    PRE_ENTRY_PREDICTOR_FEATURES,
    _load_frozen_behavior_state,
    _markdown_table,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_336_intraday_information")
DB_PATH = Path("trading.db")
ENTRY_ONLY = "entry_only"
IMMEDIATE_POST_BREAK = "immediate_post_break"
WINDOW_MODES = (ENTRY_ONLY, IMMEDIATE_POST_BREAK)
TRAIN_BAND_Q_LOW = 0.30
TRAIN_BAND_Q_HIGH = 0.70
MIN_PREBREAK_BARS = 3
MIN_POSTBREAK_BARS = 5
MIN_HOLDOUT_TRAIN_COUNT = 20
MIN_HOLDOUT_OOS_COUNT = 5
RANDOM_STATE = 42

CORE_FEATURES = list(PRE_ENTRY_PREDICTOR_FEATURES)
INTRADAY_A_VOLUME = [
    "breakout_window_volume_surge",
    "relative_volume_percentile",
    "volume_persistence_3bars",
    "volume_decay_rate",
]
INTRADAY_B_PRICE = [
    "breakout_bar_range_expansion",
    "breakout_bar_close_location",
    "multi_bar_follow_through_3bars",
    "intraday_pullback_depth_3bars",
]
INTRADAY_C_VWAP = [
    "price_vs_session_vwap_at_breakout",
    "vwap_deviation_at_breakout",
    "vwap_reversion_flag_3bars",
    "vwap_slope_prebreak",
]
INTRADAY_D_IMMEDIATE = [
    "return_next_3bars",
    "return_next_5bars",
    "adverse_excursion_next_3bars",
    "breakout_hold_duration_bars",
]
INTRADAY_E_FAILURE = [
    "failed_break_count_prebreak",
    "rejection_wick_ratio",
    "false_break_attempts_prebreak",
]
INTRADAY_ONLY_FEATURES = INTRADAY_A_VOLUME + INTRADAY_B_PRICE + INTRADAY_C_VWAP + INTRADAY_E_FAILURE
ALL_INTRADAY_ENTRY = INTRADAY_A_VOLUME + INTRADAY_B_PRICE + INTRADAY_C_VWAP + INTRADAY_E_FAILURE
ALL_INTRADAY_POST = ALL_INTRADAY_ENTRY + INTRADAY_D_IMMEDIATE
RANK_TARGET_ORDER = {
    "dead_breakout": 0,
    "early_failure": 0,
    "weak_breakout": 0,
    "volatile_whipsaw": 0,
    "failed_pop": 1,
    "slow_grind": 1,
    "uneven_continuation": 1,
    "clean_continuation": 2,
}
FORBIDDEN_FUTURE_COLUMNS = {
    "follow_through_3d_pct",
    "follow_through_5d_pct",
    "retrace_3d_pct",
    "retrace_5d_pct",
    "mae_3d_pct",
    "mae_5d_pct",
    "mfe_3d_pct",
    "mfe_5d_pct",
    "realized_R",
    "holding_days",
    "path_type",
}


def _load_intraday_bars(db_path: Path) -> pd.DataFrame:
    con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT symbol, bar_start_ts, bar_end_ts, open, high, low, close, volume
            FROM market_bars_5m
            ORDER BY symbol, bar_start_ts
            """,
            con,
        )
    finally:
        con.close()
    if df.empty:
        return pd.DataFrame(columns=["symbol", "bar_start_ts", "bar_end_ts", "open", "high", "low", "close", "volume", "bar_date"])
    df["bar_start_ts"] = pd.to_datetime(df["bar_start_ts"], utc=True, errors="coerce")
    df["bar_end_ts"] = pd.to_datetime(df["bar_end_ts"], utc=True, errors="coerce")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["symbol", "bar_start_ts", "open", "high", "low", "close"]).reset_index(drop=True)
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["bar_date"] = df["bar_start_ts"].dt.strftime("%Y-%m-%d")
    return df


def _derive_target(df: pd.DataFrame, target_name: str) -> pd.Series:
    if target_name == "bad_state":
        return df["cluster_label_base"].astype(str).isin(BAD_STATE_BASES).astype(int)
    if target_name == "clean_state":
        return (df["cluster_label_base"].astype(str) == CLEAN_STATE_BASE).astype(int)
    if target_name == "continuation_quality_rank":
        return df["cluster_label_base"].astype(str).map(lambda value: RANK_TARGET_ORDER.get(str(value), 1)).astype(int)
    raise ValueError(f"unsupported target: {target_name}")


def _available_features(df: pd.DataFrame, features: list[str]) -> list[str]:
    return list(dict.fromkeys(feature for feature in features if feature in df.columns))


def _coverage_row(trade_row: pd.Series, intraday_df: pd.DataFrame) -> dict[str, Any]:
    symbol = str(trade_row.get("symbol", "")).upper()
    entry_date = pd.to_datetime(trade_row.get("entry_date"), errors="coerce")
    date_key = entry_date.strftime("%Y-%m-%d") if not pd.isna(entry_date) else ""
    symbol_bars = intraday_df[intraday_df["symbol"] == symbol]
    if symbol_bars.empty:
        return {
            "coverage_status": "missing_symbol",
            "entry_only_status": "missing_symbol",
            "immediate_post_break_status": "missing_symbol",
            "session_bar_count": 0,
            "breakout_bar_index": math.nan,
            "breakout_timestamp": "",
        }
    session = symbol_bars[symbol_bars["bar_date"] == date_key].copy()
    if session.empty:
        return {
            "coverage_status": "missing_date",
            "entry_only_status": "missing_date",
            "immediate_post_break_status": "missing_date",
            "session_bar_count": 0,
            "breakout_bar_index": math.nan,
            "breakout_timestamp": "",
        }
    breakout_level = pd.to_numeric(pd.Series([trade_row.get("breakout_level")]), errors="coerce").iloc[0]
    if pd.isna(breakout_level):
        return {
            "coverage_status": "insufficient_window",
            "entry_only_status": "insufficient_window",
            "immediate_post_break_status": "insufficient_window",
            "session_bar_count": int(len(session)),
            "breakout_bar_index": math.nan,
            "breakout_timestamp": "",
        }
    breakout_hits = session.index[session["high"] >= float(breakout_level)].tolist()
    if not breakout_hits:
        return {
            "coverage_status": "insufficient_window",
            "entry_only_status": "insufficient_window",
            "immediate_post_break_status": "insufficient_window",
            "session_bar_count": int(len(session)),
            "breakout_bar_index": math.nan,
            "breakout_timestamp": "",
        }
    session = session.reset_index(drop=True)
    breakout_idx = int(session.index[session["high"] >= float(breakout_level)][0])
    entry_only_status = "covered" if breakout_idx >= MIN_PREBREAK_BARS else "insufficient_window"
    immediate_status = "covered" if (breakout_idx >= MIN_PREBREAK_BARS and len(session) > breakout_idx + MIN_POSTBREAK_BARS) else "insufficient_window"
    coverage_status = "covered" if (entry_only_status == "covered" or immediate_status == "covered") else "insufficient_window"
    breakout_ts = session.loc[breakout_idx, "bar_start_ts"]
    return {
        "coverage_status": coverage_status,
        "entry_only_status": entry_only_status,
        "immediate_post_break_status": immediate_status,
        "session_bar_count": int(len(session)),
        "breakout_bar_index": breakout_idx,
        "breakout_timestamp": breakout_ts.isoformat(),
    }


def _session_vwap(session: pd.DataFrame) -> pd.Series:
    typical = (session["high"] + session["low"] + session["close"]) / 3.0
    vol = pd.to_numeric(session["volume"], errors="coerce").fillna(0.0)
    weighted = (typical * vol).cumsum()
    denom = vol.cumsum()
    fallback = typical.expanding().mean()
    return weighted.div(denom.replace(0, np.nan)).fillna(fallback)


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator in (0.0, -0.0) or pd.isna(denominator):
        return math.nan
    return float(numerator / denominator)


def _extract_intraday_features(session: pd.DataFrame, breakout_idx: int, breakout_level: float, window_mode: str) -> dict[str, Any]:
    session = session.reset_index(drop=True).copy()
    pre = session.iloc[:breakout_idx].copy()
    breakout_bar = session.iloc[breakout_idx]
    post3 = session.iloc[breakout_idx + 1 : breakout_idx + 4].copy()
    post5 = session.iloc[breakout_idx + 1 : breakout_idx + 6].copy()
    session["session_vwap"] = _session_vwap(session)

    range_series = pd.to_numeric(pre["high"], errors="coerce") - pd.to_numeric(pre["low"], errors="coerce")
    vol_series = pd.to_numeric(pre["volume"], errors="coerce")
    pre_median_range = float(range_series.median()) if not range_series.empty else math.nan
    pre_median_vol = float(vol_series.median()) if not vol_series.empty else math.nan
    breakout_range = float(breakout_bar["high"] - breakout_bar["low"])
    breakout_close = float(breakout_bar["close"])
    breakout_open = float(breakout_bar["open"])
    breakout_high = float(breakout_bar["high"])
    breakout_low = float(breakout_bar["low"])
    breakout_vol = float(breakout_bar["volume"])
    breakout_vwap = float(session.loc[breakout_idx, "session_vwap"])
    price_vs_vwap = _safe_div(breakout_close, breakout_vwap) - 1.0 if not pd.isna(breakout_vwap) else math.nan
    deviation_vwap = breakout_close - breakout_vwap if not pd.isna(breakout_vwap) else math.nan

    pre_vol_sorted = vol_series.dropna().sort_values()
    if len(pre_vol_sorted) == 0:
        rel_vol_pct = math.nan
    else:
        rel_vol_pct = float((pre_vol_sorted <= breakout_vol).mean())

    def _wick_ratio() -> float:
        body_high = max(breakout_open, breakout_close)
        body_low = min(breakout_open, breakout_close)
        upper_wick = max(breakout_high - body_high, 0.0)
        lower_wick = max(body_low - breakout_low, 0.0)
        return _safe_div(max(upper_wick, lower_wick), breakout_range)

    pre_touch_mask = pd.to_numeric(pre["high"], errors="coerce") >= float(breakout_level)
    pre_close_below = pd.to_numeric(pre["close"], errors="coerce") < float(breakout_level)
    false_break_attempts = int((pre_touch_mask & pre_close_below).sum())

    feature_row = {
        "breakout_window_volume_surge": _safe_div(breakout_vol, pre_median_vol),
        "relative_volume_percentile": rel_vol_pct,
        "volume_persistence_3bars": math.nan,
        "volume_decay_rate": math.nan,
        "breakout_bar_range_expansion": _safe_div(breakout_range, pre_median_range),
        "breakout_bar_close_location": _safe_div(breakout_close - breakout_low, breakout_range),
        "multi_bar_follow_through_3bars": math.nan,
        "intraday_pullback_depth_3bars": math.nan,
        "price_vs_session_vwap_at_breakout": price_vs_vwap,
        "vwap_deviation_at_breakout": deviation_vwap,
        "vwap_reversion_flag_3bars": math.nan,
        "vwap_slope_prebreak": math.nan,
        "return_next_3bars": math.nan,
        "return_next_5bars": math.nan,
        "adverse_excursion_next_3bars": math.nan,
        "breakout_hold_duration_bars": math.nan,
        "failed_break_count_prebreak": int(pre_touch_mask.sum()),
        "rejection_wick_ratio": _wick_ratio(),
        "false_break_attempts_prebreak": false_break_attempts,
    }

    if len(pre) >= 2:
        pre_vwap = session.loc[: breakout_idx - 1, "session_vwap"].tail(min(3, len(pre)))
        feature_row["vwap_slope_prebreak"] = float(pre_vwap.iloc[-1] - pre_vwap.iloc[0]) if len(pre_vwap) >= 2 else math.nan

    if window_mode == IMMEDIATE_POST_BREAK and len(post3) >= 3:
        post3_vol = pd.to_numeric(post3["volume"], errors="coerce")
        feature_row["volume_persistence_3bars"] = _safe_div(float(post3_vol.mean()), pre_median_vol)
        feature_row["volume_decay_rate"] = float(post3_vol.iloc[-1] - breakout_vol) if len(post3_vol) else math.nan
        post3_close = float(pd.to_numeric(post3["close"], errors="coerce").iloc[-1])
        post3_high = float(pd.to_numeric(post3["high"], errors="coerce").max())
        post3_low = float(pd.to_numeric(post3["low"], errors="coerce").min())
        feature_row["multi_bar_follow_through_3bars"] = _safe_div(post3_high - breakout_close, breakout_close)
        feature_row["intraday_pullback_depth_3bars"] = _safe_div(breakout_close - post3_low, breakout_close)
        feature_row["return_next_3bars"] = _safe_div(post3_close - breakout_close, breakout_close)
        feature_row["adverse_excursion_next_3bars"] = _safe_div(breakout_close - post3_low, breakout_close)
        post_vwap = session.loc[breakout_idx + 1 : breakout_idx + 3, "session_vwap"]
        post_close = session.loc[breakout_idx + 1 : breakout_idx + 3, "close"]
        feature_row["vwap_reversion_flag_3bars"] = int(bool(((post_close < post_vwap)).any()))
        hold_bars = session.loc[breakout_idx + 1 : breakout_idx + 5, "close"]
        feature_row["breakout_hold_duration_bars"] = int((pd.to_numeric(hold_bars, errors="coerce") >= float(breakout_level)).sum())
    if window_mode == IMMEDIATE_POST_BREAK and len(post5) >= 5:
        post5_close = float(pd.to_numeric(post5["close"], errors="coerce").iloc[-1])
        feature_row["return_next_5bars"] = _safe_div(post5_close - breakout_close, breakout_close)

    return feature_row


def _build_intraday_subset(trades_df: pd.DataFrame, intraday_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    coverage_rows = []
    feature_rows = []
    for _, trade_row in trades_df.iterrows():
        coverage = _coverage_row(trade_row, intraday_df)
        base_record = trade_row.to_dict()
        base_record.update(coverage)
        coverage_rows.append(base_record)
        if coverage["coverage_status"] != "covered":
            continue
        symbol = str(trade_row["symbol"]).upper()
        date_key = pd.to_datetime(trade_row["entry_date"], errors="coerce").strftime("%Y-%m-%d")
        session = intraday_df[(intraday_df["symbol"] == symbol) & (intraday_df["bar_date"] == date_key)].copy().reset_index(drop=True)
        breakout_idx = int(coverage["breakout_bar_index"])
        breakout_level = float(pd.to_numeric(pd.Series([trade_row.get("breakout_level")]), errors="coerce").iloc[0])
        for window_mode in WINDOW_MODES:
            status_col = "entry_only_status" if window_mode == ENTRY_ONLY else "immediate_post_break_status"
            if coverage[status_col] != "covered":
                continue
            features = _extract_intraday_features(session, breakout_idx, breakout_level, window_mode)
            row = trade_row.to_dict()
            row.update(
                {
                    "window_mode": window_mode,
                    "coverage_status": coverage["coverage_status"],
                    "breakout_bar_index": breakout_idx,
                    "breakout_timestamp": coverage["breakout_timestamp"],
                    "coverage_trade_count": 1,
                }
            )
            row.update(features)
            feature_rows.append(row)
    return pd.DataFrame(coverage_rows), pd.DataFrame(feature_rows)


def _add_train_only_bands(train_df: pd.DataFrame, eval_df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_out = train_df.copy()
    eval_out = eval_df.copy()
    for feature in features:
        if feature not in train_out.columns:
            continue
        train_series = pd.to_numeric(train_out[feature], errors="coerce")
        if train_series.notna().sum() < 5:
            continue
        low = float(train_series.quantile(TRAIN_BAND_Q_LOW))
        high = float(train_series.quantile(TRAIN_BAND_Q_HIGH))

        def _band(value: Any) -> str:
            numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.isna(numeric):
                return "missing"
            if numeric < low:
                return "low"
            if numeric > high:
                return "high"
            return "mid"

        band_col = f"{feature}_band336"
        train_out[band_col] = train_out[feature].map(_band)
        eval_out[band_col] = eval_out[feature].map(_band)
    return train_out, eval_out


def _numeric_and_categorical(df: pd.DataFrame, features: list[str]) -> tuple[list[str], list[str]]:
    numeric_cols = []
    categorical_cols = []
    for feature in features:
        if feature not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[feature]) or pd.api.types.is_bool_dtype(df[feature]):
            numeric_cols.append(feature)
        else:
            categorical_cols.append(feature)
    return numeric_cols, categorical_cols


def _fit_logistic_local(train_df: pd.DataFrame, y_train: pd.Series, features: list[str]) -> Pipeline:
    numeric_cols, categorical_cols = _numeric_and_categorical(train_df, features)
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", Pipeline(steps=[("impute", SimpleImputer(strategy="median"))]), numeric_cols),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            ),
        ]
    )
    model = Pipeline(
        steps=[
            ("prep", preprocessor),
            ("model", LogisticRegression(max_iter=2000, random_state=RANDOM_STATE)),
        ]
    )
    model.fit(train_df[features], y_train)
    return model


def _majority_predictor(y_train: pd.Series, count: int) -> np.ndarray:
    majority = y_train.mode().iloc[0]
    return np.asarray([majority] * count)


def _predict_band_probability(train_df: pd.DataFrame, eval_df: pd.DataFrame, target_name: str, features: list[str]) -> np.ndarray:
    y_train = _derive_target(train_df, target_name).astype(str)
    band_features = [f"{feature}_band336" for feature in features if f"{feature}_band336" in train_df.columns]
    classes = sorted(y_train.unique().tolist())
    tables: dict[str, dict[str, dict[str, float]]] = {}
    for feature in band_features:
        tables[feature] = {}
        for value, scoped in train_df.groupby(feature):
            dist = y_train.loc[scoped.index].value_counts(normalize=True).to_dict()
            tables[feature][str(value)] = {str(label): float(prob) for label, prob in dist.items()}
    preds = []
    for _, row in eval_df.iterrows():
        agg = {cls: 0.0 for cls in classes}
        used = 0
        for feature in band_features:
            value = str(row.get(feature, ""))
            dist = tables.get(feature, {}).get(value)
            if not dist:
                continue
            for cls in classes:
                agg[cls] += float(dist.get(cls, 0.0))
            used += 1
        if used == 0:
            preds.append(classes[0] if classes else "0")
        else:
            preds.append(max(agg.items(), key=lambda item: item[1])[0])
    return np.asarray(preds, dtype=object)


def _ranking_correlation(y_true: pd.Series, preds: np.ndarray) -> float:
    y_true_num = pd.to_numeric(y_true, errors="coerce")
    pred_num = pd.to_numeric(pd.Series(preds, index=y_true.index), errors="coerce")
    if y_true_num.notna().sum() < 2 or pred_num.notna().sum() < 2:
        return math.nan
    return float(y_true_num.corr(pred_num, method="spearman"))


def _metric_row(y_true: pd.Series, preds: np.ndarray, target_name: str) -> dict[str, Any]:
    y_true_series = y_true.astype(str)
    pred_series = pd.Series(preds, index=y_true.index).astype(str)
    majority = float(y_true_series.value_counts(normalize=True).max()) if not y_true_series.empty else 0.0
    accuracy = float((y_true_series == pred_series).mean()) if not y_true_series.empty else 0.0
    row = {
        "accuracy": round(accuracy, 6),
        "majority_baseline_accuracy": round(majority, 6),
        "lift_vs_baseline": round(accuracy - majority, 6),
        "bad_state_recall": math.nan,
        "clean_state_precision": math.nan,
        "ranking_correlation": math.nan,
    }
    if target_name == "bad_state":
        pred_pos = pred_series == "1"
        true_pos = y_true_series == "1"
        row["bad_state_recall"] = round(float((pred_pos & true_pos).sum() / max(int(true_pos.sum()), 1)), 6)
    elif target_name == "clean_state":
        pred_pos = pred_series == "1"
        true_pos = y_true_series == "1"
        row["clean_state_precision"] = round(float((pred_pos & true_pos).sum() / max(int(pred_pos.sum()), 1)), 6)
    elif target_name == "continuation_quality_rank":
        row["ranking_correlation"] = round(_ranking_correlation(y_true, preds), 6) if not math.isnan(_ranking_correlation(y_true, preds)) else math.nan
    return row


def _feature_set_features(window_mode: str, feature_set: str) -> list[str]:
    if feature_set == "core_only":
        return CORE_FEATURES
    if feature_set == "intraday_only_entry_only":
        return ALL_INTRADAY_ENTRY if window_mode == ENTRY_ONLY else []
    if feature_set == "intraday_only_immediate_post_break":
        return ALL_INTRADAY_POST if window_mode == IMMEDIATE_POST_BREAK else []
    if feature_set == "core_plus_intraday_entry_only":
        return CORE_FEATURES + ALL_INTRADAY_ENTRY if window_mode == ENTRY_ONLY else []
    if feature_set == "core_plus_intraday_immediate_post_break":
        return CORE_FEATURES + ALL_INTRADAY_POST if window_mode == IMMEDIATE_POST_BREAK else []
    if feature_set == "intraday_plus_volume":
        return INTRADAY_A_VOLUME + INTRADAY_B_PRICE
    if feature_set == "intraday_plus_vwap":
        return INTRADAY_B_PRICE + INTRADAY_C_VWAP
    if feature_set == "all_combined_entry_only":
        return CORE_FEATURES + ALL_INTRADAY_ENTRY if window_mode == ENTRY_ONLY else []
    if feature_set == "all_combined_immediate_post_break":
        return CORE_FEATURES + ALL_INTRADAY_POST if window_mode == IMMEDIATE_POST_BREAK else []
    raise ValueError(feature_set)


def _evaluate_subset(train_df: pd.DataFrame, eval_df: pd.DataFrame, target_name: str, feature_set: str, window_mode: str, model_name: str) -> dict[str, Any]:
    features = _available_features(train_df, _feature_set_features(window_mode, feature_set))
    if len(train_df) == 0 or len(eval_df) == 0 or not features:
        return {
            "window_mode": window_mode,
            "feature_set": feature_set,
            "target": target_name,
            "model": model_name,
            "scope": str(eval_df["scope"].iloc[0]) if not eval_df.empty and "scope" in eval_df.columns else "eval",
            "accuracy": math.nan,
            "majority_baseline_accuracy": math.nan,
            "lift_vs_baseline": math.nan,
            "bad_state_recall": math.nan,
            "clean_state_precision": math.nan,
            "ranking_correlation": math.nan,
            "coverage_trade_count": int(len(eval_df)),
            "coverage_ratio": 0.0,
            "status": "insufficient_intraday_coverage",
        }
    y_train = _derive_target(train_df, target_name)
    y_eval = _derive_target(eval_df, target_name)
    train_banded, eval_banded = _add_train_only_bands(train_df, eval_df, features)
    if model_name == "majority":
        preds = _majority_predictor(y_train, len(eval_df))
    elif model_name == "band_probability":
        preds = _predict_band_probability(train_banded, eval_banded, target_name, features)
    elif model_name == "logistic":
        model = _fit_logistic_local(train_df, y_train, features)
        preds = model.predict(eval_df[features])
    else:
        raise ValueError(model_name)
    row = _metric_row(y_eval, preds, target_name)
    row.update(
        {
            "window_mode": window_mode,
            "feature_set": feature_set,
            "target": target_name,
            "model": model_name,
            "scope": str(eval_df["scope"].iloc[0]),
            "coverage_trade_count": int(len(eval_df)),
            "coverage_ratio": round(float(len(eval_df) / max(len(train_df) + len(eval_df), 1)), 6),
            "status": "ok",
        }
    )
    return row


def _mapping_rows(train_df: pd.DataFrame, window_mode: str) -> pd.DataFrame:
    rows = []
    feature_families = {
        "volume_participation": INTRADAY_A_VOLUME,
        "price_structure": INTRADAY_B_PRICE,
        "vwap_positioning": INTRADAY_C_VWAP,
        "immediate_follow_through_quality": INTRADAY_D_IMMEDIATE,
        "micro_failure_signals": INTRADAY_E_FAILURE,
    }
    for family_name, features in feature_families.items():
        available = _available_features(train_df, features)
        if window_mode == ENTRY_ONLY and family_name == "immediate_follow_through_quality":
            continue
        banded_train, _ = _add_train_only_bands(train_df, train_df, available)
        for feature in available:
            band_col = f"{feature}_band336"
            if band_col not in banded_train.columns:
                continue
            for band, scoped in banded_train.groupby(band_col):
                dist = scoped["cluster_label"].astype(str).value_counts(normalize=True)
                for cluster_label, prob in dist.items():
                    rows.append(
                        {
                            "window_mode": window_mode,
                            "family_name": family_name,
                            "feature_name": feature,
                            "feature_band": str(band),
                            "cluster_label": str(cluster_label),
                            "cluster_probability": round(float(prob), 6),
                            "trade_count": int(len(scoped)),
                        }
                    )
    return pd.DataFrame(rows)


def _diagnostic_overlay_rows(train_df: pd.DataFrame, eval_df: pd.DataFrame, feature_set: str, window_mode: str, scope_name: str) -> tuple[dict[str, Any], pd.DataFrame]:
    features = _available_features(train_df, _feature_set_features(window_mode, feature_set))
    if len(train_df) == 0 or len(eval_df) == 0 or not features:
        return (
            {
                "window_mode": window_mode,
                "feature_set": feature_set,
                "policy_name": "bad_skip_clean_fullsize",
                "scope": scope_name,
                "baseline_expectancy": math.nan,
                "diagnostic_expectancy": math.nan,
                "baseline_return_proxy": math.nan,
                "diagnostic_return_proxy": math.nan,
                "saved_loss": math.nan,
                "missed_gain": math.nan,
                "trade_count": 0,
                "diagnostic_trade_count": 0,
                "coverage_trade_count": 0,
                "status": "insufficient_intraday_coverage",
            },
            pd.DataFrame(),
        )
    bad_model = _fit_logistic_local(train_df, _derive_target(train_df, "bad_state"), features)
    clean_model = _fit_logistic_local(train_df, _derive_target(train_df, "clean_state"), features)
    bad_proba_train = bad_model.predict_proba(train_df[features])
    clean_proba_train = clean_model.predict_proba(train_df[features])
    bad_idx = list(bad_model.classes_).index(1) if 1 in set(bad_model.classes_) else list(bad_model.classes_).index("1")
    clean_idx = list(clean_model.classes_).index(1) if 1 in set(clean_model.classes_) else list(clean_model.classes_).index("1")
    bad_cut = float(np.quantile(bad_proba_train[:, bad_idx], 2 / 3))
    clean_cut = float(np.quantile(clean_proba_train[:, clean_idx], 2 / 3))
    bad_scores = bad_model.predict_proba(eval_df[features])[:, bad_idx]
    clean_scores = clean_model.predict_proba(eval_df[features])[:, clean_idx]
    pred_bad = bad_scores >= bad_cut
    pred_clean = clean_scores >= clean_cut

    out = eval_df.copy()
    out["pred_bad_state"] = pred_bad.astype(int)
    out["pred_clean_state"] = pred_clean.astype(int)
    out["diagnostic_multiplier"] = np.where(pred_bad, 0.0, np.where(pred_clean, 1.25, 1.0))
    out["diagnostic_adjusted_R"] = pd.to_numeric(out["realized_R"], errors="coerce") * pd.to_numeric(out["diagnostic_multiplier"], errors="coerce")
    baseline_return = float(pd.to_numeric(out["realized_R"], errors="coerce").sum())
    adjusted_return = float(pd.to_numeric(out["diagnostic_adjusted_R"], errors="coerce").sum())
    baseline_expectancy = float(pd.to_numeric(out["realized_R"], errors="coerce").mean()) if not out.empty else math.nan
    adjusted_expectancy = float(pd.to_numeric(out.loc[out["diagnostic_multiplier"] > 0, "diagnostic_adjusted_R"], errors="coerce").mean()) if (out["diagnostic_multiplier"] > 0).any() else math.nan
    saved_loss = float((-pd.to_numeric(out.loc[(out["diagnostic_multiplier"] == 0.0) & (pd.to_numeric(out["realized_R"], errors="coerce") < 0), "realized_R"], errors="coerce")).sum())
    missed_gain = float(pd.to_numeric(out.loc[(out["diagnostic_multiplier"] == 0.0) & (pd.to_numeric(out["realized_R"], errors="coerce") > 0), "realized_R"], errors="coerce").sum())
    metrics = {
        "window_mode": window_mode,
        "feature_set": feature_set,
        "policy_name": "bad_skip_clean_fullsize",
        "scope": scope_name,
        "baseline_expectancy": round(baseline_expectancy, 6),
        "diagnostic_expectancy": round(adjusted_expectancy, 6) if not pd.isna(adjusted_expectancy) else math.nan,
        "baseline_return_proxy": round(baseline_return, 6),
        "diagnostic_return_proxy": round(adjusted_return, 6),
        "saved_loss": round(saved_loss, 6),
        "missed_gain": round(missed_gain, 6),
        "trade_count": int(len(out)),
        "diagnostic_trade_count": int((out["diagnostic_multiplier"] > 0).sum()),
        "coverage_trade_count": int(len(out)),
        "status": "ok",
    }
    delta = out[
        [
            "scope",
            "trade_id",
            "symbol",
            "scenario",
            "cluster_label",
            "cluster_label_base",
            "realized_R",
            "pred_bad_state",
            "pred_clean_state",
            "diagnostic_multiplier",
            "diagnostic_adjusted_R",
        ]
    ].copy()
    delta["window_mode"] = window_mode
    delta["feature_set"] = feature_set
    return metrics, delta


def _holdout_results(train_df: pd.DataFrame, oos_df: pd.DataFrame, window_mode: str, feature_set: str, target_name: str, model_name: str) -> pd.DataFrame:
    features = _available_features(train_df, _feature_set_features(window_mode, feature_set))
    rows = []
    if len(train_df) == 0 or not features:
        for holdout_type in ("symbol", "sector_bucket", "scenario", "time_split_oos"):
            rows.append(
                {
                    "window_mode": window_mode,
                    "feature_set": feature_set,
                    "target": target_name,
                    "model": model_name,
                    "holdout_type": holdout_type,
                    "holdout_value": "",
                    "coverage_trade_count": 0,
                    "status": "insufficient_intraday_coverage",
                }
            )
        return pd.DataFrame(rows)
    for group_col in ("symbol", "sector_bucket", "scenario"):
        counts = train_df[group_col].astype(str).value_counts()
        for group, count in counts.items():
            if int(count) < MIN_HOLDOUT_TRAIN_COUNT:
                rows.append(
                    {
                        "window_mode": window_mode,
                        "feature_set": feature_set,
                        "target": target_name,
                        "model": model_name,
                        "holdout_type": group_col,
                        "holdout_value": str(group),
                        "coverage_trade_count": 0,
                        "status": "insufficient_density",
                    }
                )
                continue
            holdout_df = train_df[train_df[group_col].astype(str) == str(group)].copy()
            fit_df = train_df[train_df[group_col].astype(str) != str(group)].copy()
            row = _evaluate_subset(fit_df, holdout_df, target_name, feature_set, window_mode, model_name)
            row["holdout_type"] = group_col
            row["holdout_value"] = str(group)
            rows.append(row)
    oos_work = oos_df.copy()
    if not oos_work.empty:
        oos_work["entry_month"] = pd.to_datetime(oos_work["entry_date"], errors="coerce").dt.to_period("M").astype(str)
        for month, scoped in oos_work.groupby("entry_month"):
            if len(scoped) < MIN_HOLDOUT_OOS_COUNT:
                rows.append(
                    {
                        "window_mode": window_mode,
                        "feature_set": feature_set,
                        "target": target_name,
                        "model": model_name,
                        "holdout_type": "time_split_oos",
                        "holdout_value": str(month),
                        "coverage_trade_count": int(len(scoped)),
                        "status": "insufficient_density",
                    }
                )
                continue
            row = _evaluate_subset(train_df, scoped, target_name, feature_set, window_mode, model_name)
            row["holdout_type"] = "time_split_oos"
            row["holdout_value"] = str(month)
            rows.append(row)
    return pd.DataFrame(rows)


def _feature_definitions_df(coverage_df: pd.DataFrame, intraday_feature_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    coverage_counts = coverage_df["coverage_status"].astype(str).value_counts().to_dict() if not coverage_df.empty else {}
    for family_name, features in {
        "volume_participation": INTRADAY_A_VOLUME,
        "price_structure": INTRADAY_B_PRICE,
        "vwap_positioning": INTRADAY_C_VWAP,
        "immediate_follow_through_quality": INTRADAY_D_IMMEDIATE,
        "micro_failure_signals": INTRADAY_E_FAILURE,
    }.items():
        for feature in features:
            rows.append(
                {
                    "family_name": family_name,
                    "feature_name": feature,
                    "available_in_entry_only": feature not in INTRADAY_D_IMMEDIATE,
                    "available_in_immediate_post_break": True,
                    "coverage_total_trades": int(len(coverage_df)),
                    "coverage_covered_trades": int(coverage_counts.get("covered", 0)),
                    "coverage_missing_symbol": int(coverage_counts.get("missing_symbol", 0)),
                    "coverage_missing_date": int(coverage_counts.get("missing_date", 0)),
                    "coverage_insufficient_window": int(coverage_counts.get("insufficient_window", 0)),
                    "phase": "phase_1_subset_feasibility",
                }
            )
    rows.append(
        {
            "family_name": "phase_2_prerequisite",
            "feature_name": "full_historical_intraday_ingestion",
            "available_in_entry_only": False,
            "available_in_immediate_post_break": False,
            "coverage_total_trades": int(len(coverage_df)),
            "coverage_covered_trades": int(coverage_counts.get("covered", 0)),
            "coverage_missing_symbol": int(coverage_counts.get("missing_symbol", 0)),
            "coverage_missing_date": int(coverage_counts.get("missing_date", 0)),
            "coverage_insufficient_window": int(coverage_counts.get("insufficient_window", 0)),
            "phase": "phase_2_full_historical_archive_required",
        }
    )
    return pd.DataFrame(rows)


def _final_decision(prediction_df: pd.DataFrame, holdout_df: pd.DataFrame, economic_df: pd.DataFrame, coverage_df: pd.DataFrame) -> pd.DataFrame:
    covered_total = int((coverage_df["coverage_status"] == "covered").sum()) if not coverage_df.empty else 0
    if covered_total == 0:
        return pd.DataFrame(
            [
                {
                    "decision": "NO_INTRADAY_EDGE",
                    "decision_reason": "current intraday archive has zero overlap with frozen trade universe; feasibility not testable without Phase 2 historical ingestion",
                    "covered_trade_count": 0,
                    "positive_oos_lift_exists": False,
                    "best_bad_state_recall": math.nan,
                    "best_clean_state_precision": math.nan,
                    "holdout_mean_lift": math.nan,
                }
            ]
        )
    oos_rows = prediction_df[(prediction_df["scope"] == "anchored_oos") & (prediction_df["status"] == "ok")].copy()
    positive_oos_lift = bool((pd.to_numeric(oos_rows["lift_vs_baseline"], errors="coerce") > 0).any()) if not oos_rows.empty else False
    best_bad_recall = float(pd.to_numeric(oos_rows["bad_state_recall"], errors="coerce").max()) if not oos_rows.empty else math.nan
    best_clean_precision = float(pd.to_numeric(oos_rows["clean_state_precision"], errors="coerce").max()) if not oos_rows.empty else math.nan
    ok_holdouts = holdout_df[holdout_df.get("status", "ok") == "ok"].copy()
    holdout_mean_lift = float(pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce").mean()) if not ok_holdouts.empty else math.nan
    econ_ok = economic_df[economic_df.get("status", "ok") == "ok"].copy()
    saved_gt_missed = bool(((pd.to_numeric(econ_ok["saved_loss"], errors="coerce") > pd.to_numeric(econ_ok["missed_gain"], errors="coerce")).any())) if not econ_ok.empty else False
    expectancy_improved = bool(((pd.to_numeric(econ_ok["diagnostic_expectancy"], errors="coerce") > pd.to_numeric(econ_ok["baseline_expectancy"], errors="coerce")).any())) if not econ_ok.empty else False
    decision = "NO_INTRADAY_EDGE"
    reason = "covered subset did not show stable OOS intraday signal"
    if positive_oos_lift and expectancy_improved and saved_gt_missed:
        decision = "PARTIAL_INTRADAY_EDGE"
        reason = "covered subset shows some OOS intraday signal but coverage and/or holdout support remain limited"
        if not math.isnan(holdout_mean_lift) and holdout_mean_lift > 0:
            decision = "STRONG_INTRADAY_EDGE"
            reason = "covered subset shows stable OOS intraday signal across holdouts"
    return pd.DataFrame(
        [
            {
                "decision": decision,
                "decision_reason": reason,
                "covered_trade_count": covered_total,
                "positive_oos_lift_exists": positive_oos_lift,
                "best_bad_state_recall": round(best_bad_recall, 6) if not math.isnan(best_bad_recall) else math.nan,
                "best_clean_state_precision": round(best_clean_precision, 6) if not math.isnan(best_clean_precision) else math.nan,
                "holdout_mean_lift": round(holdout_mean_lift, 6) if not math.isnan(holdout_mean_lift) else math.nan,
            }
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 336: true intraday information feasibility.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--db-path", default=str(DB_PATH))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frozen_train, frozen_oos, frozen_full = _load_frozen_behavior_state()
    intraday_df = _load_intraday_bars(Path(args.db_path))
    coverage_df, feature_df = _build_intraday_subset(frozen_full, intraday_df)
    coverage_df = coverage_df.sort_values(["scope", "symbol", "entry_date"]).reset_index(drop=True) if not coverage_df.empty else coverage_df
    feature_def_df = _feature_definitions_df(coverage_df, feature_df)

    prediction_rows = []
    mapping_rows = []
    economic_rows = []
    trade_delta_rows = []
    holdout_rows = []

    if not feature_df.empty:
        for window_mode in WINDOW_MODES:
            scoped_all = feature_df[feature_df["window_mode"] == window_mode].copy()
            train_df = scoped_all[scoped_all["scope"] == "train"].copy()
            oos_df = scoped_all[scoped_all["scope"] == "anchored_oos"].copy()
            full_df = scoped_all[scoped_all["scope"] == "full_period"].copy()
            if not train_df.empty:
                mapping_rows.append(_mapping_rows(train_df, window_mode))
            for feature_set in [
                "core_only",
                "intraday_only_entry_only",
                "intraday_only_immediate_post_break",
                "core_plus_intraday_entry_only",
                "core_plus_intraday_immediate_post_break",
                "intraday_plus_volume",
                "intraday_plus_vwap",
                "all_combined_entry_only",
                "all_combined_immediate_post_break",
            ]:
                for scope_name, scoped_eval in [("train", train_df), ("anchored_oos", oos_df), ("full_period", full_df)]:
                    for target_name in ["bad_state", "clean_state", "continuation_quality_rank"]:
                        for model_name in ["majority", "band_probability", "logistic"]:
                            prediction_rows.append(_evaluate_subset(train_df, scoped_eval, target_name, feature_set, window_mode, model_name))
                metrics, delta = _diagnostic_overlay_rows(train_df, oos_df if not oos_df.empty else full_df.iloc[:0].copy(), feature_set, window_mode, "anchored_oos")
                economic_rows.append(metrics)
                if not delta.empty:
                    trade_delta_rows.append(delta)
                holdout_rows.append(_holdout_results(train_df, oos_df, window_mode, feature_set, "bad_state", "band_probability"))
                holdout_rows.append(_holdout_results(train_df, oos_df, window_mode, feature_set, "clean_state", "band_probability"))
    else:
        for window_mode in WINDOW_MODES:
            for feature_set in [
                "core_only",
                "intraday_only_entry_only",
                "intraday_only_immediate_post_break",
                "core_plus_intraday_entry_only",
                "core_plus_intraday_immediate_post_break",
                "intraday_plus_volume",
                "intraday_plus_vwap",
                "all_combined_entry_only",
                "all_combined_immediate_post_break",
            ]:
                for target_name in ["bad_state", "clean_state", "continuation_quality_rank"]:
                    for model_name in ["majority", "band_probability", "logistic"]:
                        prediction_rows.append(
                            {
                                "window_mode": window_mode,
                                "feature_set": feature_set,
                                "target": target_name,
                                "model": model_name,
                                "scope": "anchored_oos",
                                "accuracy": math.nan,
                                "majority_baseline_accuracy": math.nan,
                                "lift_vs_baseline": math.nan,
                                "bad_state_recall": math.nan,
                                "clean_state_precision": math.nan,
                                "ranking_correlation": math.nan,
                                "coverage_trade_count": 0,
                                "coverage_ratio": 0.0,
                                "status": "insufficient_intraday_coverage",
                            }
                        )
                economic_rows.append(
                    {
                        "window_mode": window_mode,
                        "feature_set": feature_set,
                        "policy_name": "bad_skip_clean_fullsize",
                        "scope": "anchored_oos",
                        "baseline_expectancy": math.nan,
                        "diagnostic_expectancy": math.nan,
                        "baseline_return_proxy": math.nan,
                        "diagnostic_return_proxy": math.nan,
                        "saved_loss": math.nan,
                        "missed_gain": math.nan,
                        "trade_count": 0,
                        "diagnostic_trade_count": 0,
                        "coverage_trade_count": 0,
                        "status": "insufficient_intraday_coverage",
                    }
                )
                holdout_rows.append(
                    pd.DataFrame(
                        [
                            {
                                "window_mode": window_mode,
                                "feature_set": feature_set,
                                "target": "bad_state",
                                "model": "band_probability",
                                "holdout_type": "symbol",
                                "holdout_value": "",
                                "coverage_trade_count": 0,
                                "status": "insufficient_intraday_coverage",
                            }
                        ]
                    )
                )

    prediction_df = pd.DataFrame(prediction_rows)
    mapping_df = pd.concat(mapping_rows, ignore_index=True) if mapping_rows else pd.DataFrame(
        columns=["window_mode", "family_name", "feature_name", "feature_band", "cluster_label", "cluster_probability", "trade_count"]
    )
    economic_df = pd.DataFrame(economic_rows)
    trade_delta_df = pd.concat(trade_delta_rows, ignore_index=True) if trade_delta_rows else pd.DataFrame(
        columns=["scope", "trade_id", "symbol", "scenario", "cluster_label", "cluster_label_base", "realized_R", "pred_bad_state", "pred_clean_state", "diagnostic_multiplier", "diagnostic_adjusted_R", "window_mode", "feature_set"]
    )
    holdout_df = pd.concat(holdout_rows, ignore_index=True) if holdout_rows else pd.DataFrame()
    final_decision_df = _final_decision(prediction_df, holdout_df, economic_df, coverage_df)

    md_lines = [
        "# Task 336: True Intraday Information Feasibility",
        "",
        f"- Final decision: `{final_decision_df.iloc[0]['decision']}`.",
        f"- Covered trade count: `{final_decision_df.iloc[0]['covered_trade_count']}`.",
        "",
        "## Coverage Summary",
        "",
    ]
    if not coverage_df.empty:
        coverage_summary = coverage_df["coverage_status"].astype(str).value_counts().rename_axis("coverage_status").reset_index(name="trade_count")
        md_lines.extend(_markdown_table(coverage_summary))
    else:
        md_lines.append("_No covered or auditable trades found._")
    md_lines.extend(["", "## Intraday Feature Definitions", ""])
    md_lines.extend(_markdown_table(feature_def_df.head(24)))
    md_lines.extend(["", "## Prediction Metrics", ""])
    md_lines.extend(_markdown_table(prediction_df.head(24)))
    md_lines.extend(["", "## Holdout Results", ""])
    md_lines.extend(_markdown_table(holdout_df.head(24)))
    md_lines.extend(["", "## Economic Action Test", ""])
    md_lines.extend(_markdown_table(economic_df.head(24)))
    md_lines.extend(
        [
            "",
            "## Final Answer",
            "",
            "- Entry-only track is the deployable-relevance test.",
            "- Immediate-post-break track is the micro-confirmation feasibility test.",
            "- If current intraday archive has no overlap or no stable signal, Phase 2 historical intraday ingestion is required before any production conclusion.",
        ]
    )

    feature_def_df.to_csv(out_dir / "task_336_intraday_feature_definitions.csv", index=False)
    prediction_df.to_csv(out_dir / "task_336_prediction_metrics.csv", index=False)
    mapping_df.to_csv(out_dir / "task_336_intraday_to_behavior_mapping.csv", index=False)
    economic_df.to_csv(out_dir / "task_336_economic_action_test.csv", index=False)
    trade_delta_df.to_csv(out_dir / "task_336_trade_level_delta.csv", index=False)
    holdout_df.to_csv(out_dir / "task_336_holdout_results.csv", index=False)
    final_decision_df.to_csv(out_dir / "task_336_final_decision.csv", index=False)
    prediction_df.to_csv(out_dir / "task_336_intraday_ablation.csv", index=False)
    (out_dir / "task_336_intraday_information.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
