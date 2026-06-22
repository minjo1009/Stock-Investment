from __future__ import annotations

import argparse
import math
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.backtest.analysis_structural_breakout_intraday_evaluation_fix_338 import _build_split_frames
from src.backtest.analysis_structural_breakout_true_intraday_feasibility_336 import (
    DB_PATH,
    ENTRY_ONLY,
    IMMEDIATE_POST_BREAK,
    WINDOW_MODES,
    _load_intraday_bars,
)
from src.backtest.analysis_structural_breakout_behavior_state_monetization_334 import _markdown_table


DEFAULT_OUT_DIR = Path("docs/reports/task_339_intraday_signal_strengthening")
MIN_TRADES_PER_SUBSET = 20
TOP_SUBSET_LIMIT = 10
BAD_BEHAVIOR_STATES = {"dead_breakout", "weak_breakout"}
FOCUSED_BEHAVIOR_STATES = {"clean_continuation", "failed_pop", "dead_breakout", "weak_breakout"}
SETUP_FAMILIES = {"RANGE_COMPRESSION": "range_compression", "PIVOT_HIGH": "pivot_high"}
ALLOWED_TRIPLE_PATTERNS = (
    ("time_of_day", "sector_group", "intraday_structure"),
    ("time_of_day", "setup_type", "intraday_structure"),
    ("sector_group", "volatility_regime", "intraday_structure"),
)
HOLDOUT_MIN_TRADES = 5


def _breakout_time_bucket(ts_value: Any) -> str:
    ts = pd.to_datetime(ts_value, utc=True, errors="coerce")
    if pd.isna(ts):
        return "unknown"
    local_ts = ts.tz_convert("America/New_York")
    minutes = int(local_ts.hour * 60 + local_ts.minute)
    if minutes < 10 * 60:
        return "early_session"
    if minutes >= 15 * 60:
        return "last_hour"
    return "mid_session"


def _sector_group(value: Any) -> str:
    text = str(value)
    if text == "semis":
        return "semis"
    if text == "software/internet":
        return "software_internet"
    return "others"


def _breakout_subtype(value: Any) -> str:
    tokens = [token for token in str(value).split("|") if token]
    if len(tokens) >= 2:
        return f"{tokens[0]}|{tokens[1]}"
    return tokens[0] if tokens else "unknown"


def _train_binary_bucket(train_series: pd.Series, series: pd.Series, low_label: str, high_label: str) -> pd.Series:
    train_numeric = pd.to_numeric(train_series, errors="coerce")
    threshold = float(train_numeric.median()) if train_numeric.notna().any() else 0.0
    numeric = pd.to_numeric(series, errors="coerce")
    return pd.Series(np.where(numeric > threshold, high_label, low_label), index=series.index)


def _vwap_response(series: pd.DataFrame, window_mode: str) -> pd.Series:
    base = pd.to_numeric(series["price_vs_session_vwap_at_breakout"], errors="coerce") > 0
    if window_mode == IMMEDIATE_POST_BREAK and "vwap_reversion_flag_3bars" in series.columns:
        revert = pd.to_numeric(series["vwap_reversion_flag_3bars"], errors="coerce").fillna(1.0) == 0
        ok = base & revert
    else:
        ok = base
    return pd.Series(np.where(ok, "vwap_hold", "vwap_reject"), index=series.index)


def _breakout_response(series: pd.DataFrame, window_mode: str) -> pd.Series:
    if window_mode == ENTRY_ONLY:
        numeric = pd.to_numeric(series["breakout_bar_close_location"], errors="coerce")
        return pd.Series(np.where(numeric >= 0.5, "breakout_hold", "immediate_failure"), index=series.index)
    numeric = pd.to_numeric(series["breakout_hold_duration_bars"], errors="coerce")
    return pd.Series(np.where(numeric >= 1.0, "breakout_hold", "immediate_failure"), index=series.index)


def _behavior_bucket(value: Any) -> str:
    text = str(value)
    if text in FOCUSED_BEHAVIOR_STATES:
        return text
    return "other_behavior"


def _prepare_master_frame(feature_parts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    combined_parts = []
    for split_name, frame in feature_parts.items():
        if frame.empty:
            continue
        scoped = frame.copy()
        scoped["split"] = split_name
        combined_parts.append(scoped)
    master = pd.concat(combined_parts, ignore_index=True) if combined_parts else pd.DataFrame()
    if master.empty:
        return master
    for window_mode in WINDOW_MODES:
        mask = master["window_mode"] == window_mode
        scoped = master.loc[mask].copy()
        train_scoped = scoped[scoped["split"] == "train"].copy()
        master.loc[mask, "time_of_day"] = scoped["breakout_timestamp"].map(_breakout_time_bucket)
        master.loc[mask, "sector_group"] = scoped["sector_bucket"].map(_sector_group)
        master.loc[mask, "setup_type"] = scoped["scenario_family"].map(lambda value: SETUP_FAMILIES.get(str(value), "other_setup"))
        master.loc[mask, "breakout_subtype"] = scoped["scenario"].map(_breakout_subtype)
        master.loc[mask, "behavior_state"] = scoped["cluster_label_base"].map(_behavior_bucket)
        master.loc[mask, "atr_regime"] = _train_binary_bucket(train_scoped["range_width_10_pre"], scoped["range_width_10_pre"], "low_atr", "high_atr").values
        master.loc[mask, "contraction_regime"] = _train_binary_bucket(train_scoped["vol_contraction_ratio"], scoped["vol_contraction_ratio"], "vol_contracting", "vol_expanding").values
        master.loc[mask, "volume_surge_regime"] = _train_binary_bucket(
            train_scoped["breakout_window_volume_surge"],
            scoped["breakout_window_volume_surge"],
            "weak_volume_surge",
            "strong_volume_surge",
        ).values
        master.loc[mask, "vwap_response"] = _vwap_response(scoped, window_mode).values
        master.loc[mask, "breakout_response"] = _breakout_response(scoped, window_mode).values
    return master.reset_index(drop=True)


def _axis_catalog(train_df: pd.DataFrame) -> dict[str, list[str]]:
    breakout_counts = train_df["breakout_subtype"].astype(str).value_counts()
    return {
        "time_of_day": ["early_session", "mid_session", "last_hour"],
        "sector_group": ["semis", "software_internet", "others"],
        "setup_type": ["range_compression", "pivot_high"],
        "breakout_subtype": [value for value, count in breakout_counts.items() if int(count) >= MIN_TRADES_PER_SUBSET],
        "behavior_state": ["clean_continuation", "failed_pop", "dead_breakout", "weak_breakout"],
        "atr_regime": ["high_atr", "low_atr"],
        "contraction_regime": ["vol_expanding", "vol_contracting"],
        "volume_surge_regime": ["strong_volume_surge", "weak_volume_surge"],
        "vwap_response": ["vwap_hold", "vwap_reject"],
        "breakout_response": ["breakout_hold", "immediate_failure"],
    }


def _deployability(axis_names: tuple[str, ...]) -> str:
    return "diagnostic_only" if "behavior_state" in axis_names else "live_eligible"


def _subset_definition_text(conditions: dict[str, str]) -> str:
    return " AND ".join(f"{key}={value}" for key, value in sorted(conditions.items()))


def _subset_id(window_mode: str, conditions: dict[str, str]) -> str:
    parts = [window_mode] + [f"{key}:{value}" for key, value in sorted(conditions.items())]
    return "|".join(parts)


def _candidate_conditions(train_df: pd.DataFrame) -> list[dict[str, Any]]:
    axis_values = _axis_catalog(train_df)
    candidates: list[dict[str, Any]] = []
    single_axes = list(axis_values.keys())
    axis_groups = {
        "intraday_structure": ["volume_surge_regime", "vwap_response", "breakout_response"],
        "volatility_regime": ["atr_regime", "contraction_regime"],
    }
    for axis_name in single_axes:
        for value in axis_values[axis_name]:
            candidates.append({"axis_names": (axis_name,), "conditions": {axis_name: value}})
    for axis_a, axis_b in combinations(single_axes, 2):
        for value_a in axis_values[axis_a]:
            for value_b in axis_values[axis_b]:
                candidates.append({"axis_names": (axis_a, axis_b), "conditions": {axis_a: value_a, axis_b: value_b}})
    for pattern in ALLOWED_TRIPLE_PATTERNS:
        first_axes = axis_groups.get(pattern[0], [pattern[0]])
        second_axes = axis_groups.get(pattern[1], [pattern[1]])
        third_axes = axis_groups.get(pattern[2], [pattern[2]])
        for axis_a in first_axes:
            for axis_b in second_axes:
                for axis_c in third_axes:
                    for value_a in axis_values[axis_a]:
                        for value_b in axis_values[axis_b]:
                            for value_c in axis_values[axis_c]:
                                candidates.append(
                                    {
                                        "axis_names": (axis_a, axis_b, axis_c),
                                        "conditions": {axis_a: value_a, axis_b: value_b, axis_c: value_c},
                                    }
                                )
    deduped: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        key = _subset_definition_text(candidate["conditions"])
        deduped[key] = candidate
    return list(deduped.values())


def _apply_conditions(df: pd.DataFrame, conditions: dict[str, str]) -> pd.DataFrame:
    scoped = df.copy()
    for key, value in conditions.items():
        scoped = scoped[scoped[key].astype(str) == str(value)]
    return scoped


def _baseline_stats(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {
            "expectancy": math.nan,
            "clean_precision": math.nan,
            "bad_share": math.nan,
            "return_proxy": math.nan,
        }
    realized = pd.to_numeric(df["realized_R"], errors="coerce")
    clean_precision = float((df["cluster_label_base"].astype(str) == "clean_continuation").mean())
    bad_share = float(df["cluster_label_base"].astype(str).isin(BAD_BEHAVIOR_STATES).mean())
    return {
        "expectancy": float(realized.mean()),
        "clean_precision": clean_precision,
        "bad_share": bad_share,
        "return_proxy": float(realized.sum()),
    }


def _saved_loss_missed_gain(universe_df: pd.DataFrame, kept_df: pd.DataFrame) -> tuple[float, float]:
    kept_ids = set(kept_df["trade_id"].astype(str).tolist())
    skipped = universe_df[~universe_df["trade_id"].astype(str).isin(kept_ids)].copy()
    realized = pd.to_numeric(skipped["realized_R"], errors="coerce")
    saved_loss = float((-realized[realized < 0]).sum())
    missed_gain = float(realized[realized > 0].sum())
    return saved_loss, missed_gain


def _symbol_concentration_share(df: pd.DataFrame) -> float:
    if df.empty:
        return math.nan
    abs_sum = pd.to_numeric(df["realized_R"], errors="coerce").abs()
    total = float(abs_sum.sum())
    if total <= 0:
        return 1.0
    by_symbol = df.assign(abs_r=abs_sum).groupby("symbol")["abs_r"].sum()
    return float(by_symbol.max() / total)


def _holdout_rows_for_subset(window_df: pd.DataFrame, subset_df: pd.DataFrame, subset_id: str) -> pd.DataFrame:
    rows = []
    oos_df = window_df[window_df["split"] == "anchored_oos"].copy()
    if oos_df.empty:
        return pd.DataFrame()
    group_specs = [
        ("symbol", "symbol"),
        ("sector_holdout", "sector_group"),
        ("time_split_oos", "entry_month"),
    ]
    work = oos_df.copy()
    work["entry_month"] = pd.to_datetime(work["entry_date"], errors="coerce").dt.to_period("M").astype(str)
    subset_oos = subset_df[subset_df["split"] == "anchored_oos"].copy()
    subset_oos["entry_month"] = pd.to_datetime(subset_oos["entry_date"], errors="coerce").dt.to_period("M").astype(str)
    for holdout_type, group_col in group_specs:
        for group_value, group_df in work.groupby(group_col):
            subset_group = subset_oos[subset_oos[group_col].astype(str) == str(group_value)].copy()
            if len(group_df) < HOLDOUT_MIN_TRADES or len(subset_group) < HOLDOUT_MIN_TRADES:
                rows.append(
                    {
                        "subset_id": subset_id,
                        "holdout_type": holdout_type,
                        "holdout_value": str(group_value),
                        "trade_count": int(len(subset_group)),
                        "lift_vs_baseline": math.nan,
                        "expectancy_delta": math.nan,
                        "status": "insufficient_sample",
                    }
                )
                continue
            base = _baseline_stats(group_df)
            realized = pd.to_numeric(subset_group["realized_R"], errors="coerce")
            clean_precision = float((subset_group["cluster_label_base"].astype(str) == "clean_continuation").mean())
            rows.append(
                {
                    "subset_id": subset_id,
                    "holdout_type": holdout_type,
                    "holdout_value": str(group_value),
                    "trade_count": int(len(subset_group)),
                    "lift_vs_baseline": round(clean_precision - base["clean_precision"], 6),
                    "expectancy_delta": round(float(realized.mean()) - base["expectancy"], 6),
                    "status": "ok",
                }
            )
    for group_value, group_df in work.groupby("scenario_family"):
        subset_group = subset_oos[subset_oos["scenario_family"].astype(str) == str(group_value)].copy()
        status = "ok" if len(group_df) >= MIN_TRADES_PER_SUBSET and len(subset_group) >= HOLDOUT_MIN_TRADES else "insufficient_sample"
        rows.append(
            {
                "subset_id": subset_id,
                "holdout_type": "scenario_holdout",
                "holdout_value": str(group_value),
                "trade_count": int(len(subset_group)),
                "lift_vs_baseline": round(float((subset_group["cluster_label_base"].astype(str) == "clean_continuation").mean()) - _baseline_stats(group_df)["clean_precision"], 6) if status == "ok" else math.nan,
                "expectancy_delta": round(float(pd.to_numeric(subset_group["realized_R"], errors="coerce").mean()) - _baseline_stats(group_df)["expectancy"], 6) if status == "ok" else math.nan,
                "status": status,
            }
        )
    return pd.DataFrame(rows)


def _evaluate_candidates_for_window(window_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df = window_df[window_df["split"] == "train"].copy()
    oos_df = window_df[window_df["split"] == "anchored_oos"].copy()
    oos_base = _baseline_stats(oos_df)
    definitions = []
    signal_rows = []
    holdout_rows = []
    for candidate in _candidate_conditions(train_df):
        conditions = candidate["conditions"]
        subset_id = _subset_id(str(window_df["window_mode"].iloc[0]), conditions)
        subset_train = _apply_conditions(train_df, conditions)
        subset_oos = _apply_conditions(oos_df, conditions)
        deployability = _deployability(candidate["axis_names"])
        trade_count = int(len(subset_oos))
        status = "ok"
        discard_reason = ""
        if trade_count < MIN_TRADES_PER_SUBSET:
            status = "discarded"
            discard_reason = "insufficient_oos_subset_trades"
        definitions.append(
            {
                "window_mode": str(window_df["window_mode"].iloc[0]),
                "subset_id": subset_id,
                "subset_definition": _subset_definition_text(conditions),
                "deployability": deployability,
                "axis_names": "|".join(candidate["axis_names"]),
                "train_trade_count": int(len(subset_train)),
                "anchored_oos_trade_count": trade_count,
                "status": status,
                "discard_reason": discard_reason,
            }
        )
        if status != "ok":
            continue
        clean_precision = float((subset_oos["cluster_label_base"].astype(str) == "clean_continuation").mean())
        bad_recall = float(subset_oos["cluster_label_base"].astype(str).isin(BAD_BEHAVIOR_STATES).sum() / max(int(oos_df["cluster_label_base"].astype(str).isin(BAD_BEHAVIOR_STATES).sum()), 1))
        realized = pd.to_numeric(subset_oos["realized_R"], errors="coerce")
        expectancy = float(realized.mean())
        expectancy_delta = expectancy - oos_base["expectancy"]
        lift_vs_baseline = clean_precision - oos_base["clean_precision"]
        saved_loss, missed_gain = _saved_loss_missed_gain(oos_df, subset_oos)
        symbol_share = _symbol_concentration_share(subset_oos)
        holdout_df = _holdout_rows_for_subset(window_df, _apply_conditions(window_df, conditions), subset_id)
        holdout_rows.append(holdout_df)
        ok_holdouts = holdout_df[holdout_df["status"] == "ok"].copy()
        holdout_mean_lift = float(pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce").mean()) if not ok_holdouts.empty else math.nan
        holdout_positive_share = float((pd.to_numeric(ok_holdouts["lift_vs_baseline"], errors="coerce") > 0).mean()) if not ok_holdouts.empty else 0.0
        signal_rows.append(
            {
                "window_mode": str(window_df["window_mode"].iloc[0]),
                "subset_id": subset_id,
                "subset_definition": _subset_definition_text(conditions),
                "deployability": deployability,
                "trade_count": trade_count,
                "oos_lift_vs_baseline": round(lift_vs_baseline, 6),
                "oos_expectancy": round(expectancy, 6),
                "expectancy_delta": round(expectancy_delta, 6),
                "saved_loss": round(saved_loss, 6),
                "missed_gain": round(missed_gain, 6),
                "clean_state_precision": round(clean_precision, 6),
                "bad_state_recall": round(bad_recall, 6),
                "holdout_mean_lift": round(holdout_mean_lift, 6) if not math.isnan(holdout_mean_lift) else math.nan,
                "holdout_positive_share": round(holdout_positive_share, 6),
                "symbol_concentration_share": round(symbol_share, 6) if not math.isnan(symbol_share) else math.nan,
            }
        )
    return pd.DataFrame(definitions), pd.concat(holdout_rows, ignore_index=True) if holdout_rows else pd.DataFrame(), pd.DataFrame(signal_rows)


def _normalize_component(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    min_val = float(numeric.min()) if numeric.notna().any() else 0.0
    max_val = float(numeric.max()) if numeric.notna().any() else 0.0
    if math.isclose(min_val, max_val):
        return pd.Series(np.where(numeric.notna(), 0.5, math.nan), index=series.index)
    return (numeric - min_val) / (max_val - min_val)


def _score_signal_strength(signal_df: pd.DataFrame) -> pd.DataFrame:
    if signal_df.empty:
        return signal_df
    scored = signal_df.copy()
    if "trade_count" not in scored.columns:
        scored["trade_count"] = 0
    holdout_norm = _normalize_component(scored["holdout_mean_lift"]).fillna(0.0)
    concentration_component = pd.Series(
        np.where(
            pd.to_numeric(scored["symbol_concentration_share"], errors="coerce").fillna(1.0) <= 0.60,
            1.0,
            np.maximum(0.0, 1.0 - ((pd.to_numeric(scored["symbol_concentration_share"], errors="coerce").fillna(1.0) - 0.60) / 0.40)),
        ),
        index=scored.index,
    )
    scored["robustness_score"] = (
        0.4 * holdout_norm
        + 0.4 * pd.to_numeric(scored["holdout_positive_share"], errors="coerce").fillna(0.0)
        + 0.2 * concentration_component
    )
    lift_norm = _normalize_component(scored["oos_lift_vs_baseline"]).fillna(0.0)
    exp_norm = _normalize_component(scored["expectancy_delta"]).fillna(0.0)
    net_norm = _normalize_component(pd.to_numeric(scored["saved_loss"], errors="coerce").fillna(0.0) - pd.to_numeric(scored["missed_gain"], errors="coerce").fillna(0.0)).fillna(0.0)
    scored["signal_strength_score"] = 0.35 * lift_norm + 0.25 * exp_norm + 0.20 * net_norm + 0.20 * pd.to_numeric(scored["robustness_score"], errors="coerce").fillna(0.0)
    return scored.sort_values(["signal_strength_score", "expectancy_delta", "trade_count"], ascending=[False, False, False]).reset_index(drop=True)


def _subset_strategy_rows(signal_df: pd.DataFrame, master_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    top = signal_df[signal_df["signal_strength_score"] > 0].head(TOP_SUBSET_LIMIT).copy()
    for _, row in top.iterrows():
        subset_id = str(row["subset_id"])
        window_mode = str(row["window_mode"])
        full_window = master_df[(master_df["window_mode"] == window_mode) & (master_df["split"].isin(["anchored_oos", "full_period"]))].copy()
        conditions = {}
        for token in str(row["subset_definition"]).split(" AND "):
            key, value = token.split("=", 1)
            conditions[key] = value
        subset = _apply_conditions(full_window, conditions)
        for scope_name in ("anchored_oos", "full_period"):
            scope_full = full_window[full_window["split"] == scope_name].copy()
            scope_subset = subset[subset["split"] == scope_name].copy()
            if scope_full.empty or scope_subset.empty:
                continue
            saved_loss, missed_gain = _saved_loss_missed_gain(scope_full, scope_subset)
            rows.append(
                {
                    "window_mode": window_mode,
                    "subset_id": subset_id,
                    "subset_definition": row["subset_definition"],
                    "deployability": row["deployability"],
                    "scope": scope_name,
                    "baseline_trade_count": int(len(scope_full)),
                    "subset_trade_count": int(len(scope_subset)),
                    "baseline_expectancy": round(float(pd.to_numeric(scope_full["realized_R"], errors="coerce").mean()), 6),
                    "subset_expectancy": round(float(pd.to_numeric(scope_subset["realized_R"], errors="coerce").mean()), 6),
                    "baseline_return_proxy": round(float(pd.to_numeric(scope_full["realized_R"], errors="coerce").sum()), 6),
                    "subset_return_proxy": round(float(pd.to_numeric(scope_subset["realized_R"], errors="coerce").sum()), 6),
                    "saved_loss": round(saved_loss, 6),
                    "missed_gain": round(missed_gain, 6),
                    "trade_retention_ratio": round(float(len(scope_subset) / max(len(scope_full), 1)), 6),
                }
            )
    return pd.DataFrame(rows)


def _final_decision(signal_df: pd.DataFrame, strategy_df: pd.DataFrame) -> pd.DataFrame:
    if signal_df.empty:
        return pd.DataFrame([{"decision": "NO_STRONG_SUBSET", "decision_reason": "no subset met minimum OOS trade count threshold"}])
    positive = signal_df[
        (pd.to_numeric(signal_df["oos_lift_vs_baseline"], errors="coerce") > 0)
        & (pd.to_numeric(signal_df["expectancy_delta"], errors="coerce") > 0)
        & (pd.to_numeric(signal_df["saved_loss"], errors="coerce") > pd.to_numeric(signal_df["missed_gain"], errors="coerce"))
    ].copy()
    if positive.empty:
        return pd.DataFrame([{"decision": "NO_STRONG_SUBSET", "decision_reason": "no subset delivered positive OOS lift and positive expectancy delta"}])
    clear = positive[
        (positive["deployability"].astype(str) == "live_eligible")
        & (pd.to_numeric(positive["holdout_mean_lift"], errors="coerce") > 0)
        & (pd.to_numeric(positive["symbol_concentration_share"], errors="coerce") <= 0.60)
    ].copy()
    if not clear.empty:
        best = clear.sort_values("signal_strength_score", ascending=False).iloc[0]
        return pd.DataFrame(
            [
                {
                    "decision": "CLEAR_STRONG_SUBSET",
                    "decision_reason": f"live-eligible subset {best['subset_id']} passed OOS, holdout, and concentration checks",
                }
            ]
        )
    best = positive.sort_values("signal_strength_score", ascending=False).iloc[0]
    return pd.DataFrame(
        [
            {
                "decision": "PARTIAL_STRONG_SUBSET",
                "decision_reason": f"subset {best['subset_id']} shows localized OOS edge but holdout support or deployability remains limited",
            }
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Task 339: intraday signal strengthening via edge localization.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--db-path", default=str(DB_PATH))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    intraday_df = _load_intraday_bars(Path(args.db_path))
    _, feature_parts = _build_split_frames(intraday_df)
    master_df = _prepare_master_frame(feature_parts)

    definition_parts = []
    signal_parts = []
    holdout_parts = []
    for window_mode in WINDOW_MODES:
        window_df = master_df[master_df["window_mode"] == window_mode].copy()
        if window_df.empty:
            continue
        definitions_df, holdout_df, signal_df = _evaluate_candidates_for_window(window_df)
        definition_parts.append(definitions_df)
        holdout_parts.append(holdout_df)
        signal_parts.append(signal_df)

    subset_definitions_df = pd.concat(definition_parts, ignore_index=True) if definition_parts else pd.DataFrame()
    holdout_df = pd.concat(holdout_parts, ignore_index=True) if holdout_parts else pd.DataFrame()
    signal_df = pd.concat(signal_parts, ignore_index=True) if signal_parts else pd.DataFrame()
    scored_signal_df = _score_signal_strength(signal_df)
    strategy_df = _subset_strategy_rows(scored_signal_df, master_df)
    final_decision_df = _final_decision(scored_signal_df, strategy_df)

    md_lines = [
        "# Task 339: Intraday Signal Strengthening via Edge Localization",
        "",
        f"- Final decision: `{final_decision_df.iloc[0]['decision']}`.",
        "",
        "## Top Signal Subsets",
        "",
    ]
    md_lines.extend(_markdown_table(scored_signal_df.head(10)))
    md_lines.extend(["", "## Subset Strategy Performance", ""])
    md_lines.extend(_markdown_table(strategy_df.head(20)))
    md_lines.extend(["", "## Holdout Results", ""])
    md_lines.extend(_markdown_table(holdout_df.head(20)))
    md_lines.extend(
        [
            "",
            "## Final Answer",
            "",
            "- This report localizes where intraday signal is already strong instead of trying to improve global signal quality.",
            "- `live_eligible` subsets exclude ex-post behavior-state conditions.",
            "- `diagnostic_only` subsets may still explain where signal concentrates even if they are not directly tradable.",
        ]
    )

    subset_definitions_df.to_csv(out_dir / "task_339_subset_definitions.csv", index=False)
    scored_signal_df.to_csv(out_dir / "task_339_subset_signal_strength.csv", index=False)
    strategy_df.to_csv(out_dir / "task_339_subset_strategy_performance.csv", index=False)
    holdout_df.to_csv(out_dir / "task_339_holdout_results.csv", index=False)
    final_decision_df.to_csv(out_dir / "task_339_final_decision.csv", index=False)
    (out_dir / "task_339_intraday_signal_strengthening.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
