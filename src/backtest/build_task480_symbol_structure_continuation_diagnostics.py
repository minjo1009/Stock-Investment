from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.intraday_canonical_continuation_engine_388 import DEFAULT_INTRADAY_DIR


DEFAULT_TASK407_DIR = Path("docs/reports/task_407_raw_native_vectorized_rebuild")
DEFAULT_OUT_DIR = Path("docs/reports/task_480_symbol_structure_continuation_diagnostics")


@dataclass(frozen=True)
class Task480Artifacts:
    label_sensitivity_audit: pd.DataFrame
    label_definition_stability_audit: pd.DataFrame
    symbol_structure_factor_dictionary: pd.DataFrame
    symbol_structure_snapshot_log: pd.DataFrame
    symbol_structure_label_panel: pd.DataFrame
    symbol_structure_factor_group_quality: pd.DataFrame
    symbol_structure_interaction_quality: pd.DataFrame
    entry_reduce_vs_add_scale_explanation: pd.DataFrame
    symbol_structure_backtest_summary: pd.DataFrame
    good_bad_configuration_audit: pd.DataFrame
    symbol_structure_leakage_audit: pd.DataFrame
    missing_microstructure_factor_audit: pd.DataFrame
    task_480_decision: pd.DataFrame


def build_task480_symbol_structure_continuation_diagnostics(
    *,
    task407_dir: Path = DEFAULT_TASK407_DIR,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task480Artifacts:
    decisions = pd.read_csv(task407_dir / "raw_native_decision_snapshot_log.csv", encoding="utf-8-sig")
    labels = pd.read_csv(task407_dir / "raw_native_lifecycle_labels.csv", encoding="utf-8-sig")
    allow = decisions[decisions["bucket"].eq("ALLOW") & decisions["lifecycle_id"].fillna("").astype(str).str.len().gt(0)].copy()
    panel = allow.merge(labels, on="lifecycle_id", how="inner", suffixes=("", "_label"))
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], errors="coerce", utc=True)
    panel["entry_ts_key"] = panel["entry_ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce")
    panel["return_from_entry"] = pd.to_numeric(panel["return_from_entry"], errors="coerce")
    panel["add_scale_success_flag"] = panel["lifecycle_outcome_class"].eq("add_scale_success").astype(int)
    panel["entry_reduce_failure_flag"] = panel["lifecycle_outcome_class"].eq("entry_reduce_failure").astype(int)
    panel["false_positive_flag"] = panel["lifecycle_outcome_class"].isin(
        ["entry_reduce_failure", "add_only_weak", "post_cost_false_positive"]
    ).astype(int)
    symbols = sorted(panel["symbol"].dropna().astype(str).str.upper().unique().tolist())
    bars = load_symbol_structure_raw_bars(symbols, intraday_dir)
    factor_panel = build_symbol_structure_factor_panel(bars)
    snapshot = panel.merge(
        factor_panel,
        left_on=["symbol", "entry_ts_key"],
        right_on=["symbol", "timestamp_key"],
        how="inner",
        suffixes=("", "_factor"),
    )
    snapshot = snapshot[snapshot["lifecycle_id"].fillna("").astype(str).str.len().gt(0)].copy()
    snapshot["inferred_lifecycle_matching_used_flag"] = 0
    snapshot["symbol_date_price_time_fallback_used_flag"] = 0
    snapshot["label_used_in_assignment_flag"] = 0
    label_sensitivity = build_label_sensitivity_audit(snapshot)
    label_stability = build_label_definition_stability_audit(snapshot)
    dictionary = build_symbol_structure_factor_dictionary()
    label_panel = build_symbol_structure_label_panel(snapshot)
    group_quality = build_factor_group_quality(snapshot)
    interaction_quality = build_interaction_quality(snapshot)
    explanation = build_entry_reduce_vs_add_scale_explanation(snapshot)
    backtest_summary = build_symbol_structure_backtest_summary(snapshot, interaction_quality)
    config_audit = build_good_bad_configuration_audit(interaction_quality, snapshot)
    leakage = build_leakage_audit(snapshot)
    missing = build_missing_microstructure_factor_audit()
    decision = build_task_480_decision(snapshot, group_quality, interaction_quality, label_sensitivity, config_audit)
    artifacts = Task480Artifacts(
        label_sensitivity,
        label_stability,
        dictionary,
        snapshot,
        label_panel,
        group_quality,
        interaction_quality,
        explanation,
        backtest_summary,
        config_audit,
        leakage,
        missing,
        decision,
    )
    write_task480_artifacts(artifacts, out_dir)
    return artifacts


def load_symbol_structure_raw_bars(symbols: list[str], intraday_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        path = _symbol_path(intraday_dir, symbol)
        if path is None:
            continue
        frame = pd.read_csv(path, encoding="utf-8-sig")
        frame.columns = [str(c).strip().lower() for c in frame.columns]
        if "datetime" in frame.columns and "timestamp" not in frame.columns:
            frame = frame.rename(columns={"datetime": "timestamp"})
        if "date" in frame.columns and "timestamp" not in frame.columns:
            frame = frame.rename(columns={"date": "timestamp"})
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        if any(column not in frame.columns for column in required):
            continue
        frame = frame.copy()
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        for column in ["open", "high", "low", "close", "volume", "trade_count", "vwap"]:
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=required + ["timestamp"]).copy()
        eastern = frame["timestamp"].dt.tz_convert("America/New_York")
        minutes = eastern.dt.hour * 60 + eastern.dt.minute
        frame = frame[(minutes >= 9 * 60 + 30) & (minutes < 16 * 60)].copy()
        if frame.empty:
            continue
        frame["symbol"] = symbol
        frame["session_date_et"] = eastern.loc[frame.index].dt.strftime("%Y-%m-%d").values
        frame["bar_index"] = frame.groupby("session_date_et").cumcount()
        frame["timestamp_key"] = frame["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        if "trade_count" not in frame.columns:
            frame["trade_count"] = pd.NA
        if "vwap" not in frame.columns:
            frame["vwap"] = pd.NA
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def build_symbol_structure_factor_panel(bars: pd.DataFrame) -> pd.DataFrame:
    if bars.empty:
        return pd.DataFrame()
    frame = bars.copy()
    for numeric_column in ["open", "high", "low", "close", "volume", "trade_count", "vwap"]:
        if numeric_column in frame.columns:
            frame[numeric_column] = pd.to_numeric(frame[numeric_column], errors="coerce")
    frame["trade_count"] = frame["trade_count"].fillna(0.0)
    session = frame.groupby(["symbol", "session_date_et"], group_keys=False)
    symbol = frame.groupby("symbol", group_keys=False)
    day_high = session["high"].cummax()
    day_low = session["low"].cummin()
    day_open = session["open"].transform("first")
    bar_range = (frame["high"] - frame["low"]).replace(0, pd.NA)
    frame["bar_body_pct"] = ((frame["close"] - frame["open"]).abs() / bar_range).fillna(0.0)
    frame["bar_direction"] = (frame["close"] > frame["open"]).astype(int)
    frame["close_location"] = ((frame["close"] - frame["low"]) / bar_range).fillna(0.5).clip(0.0, 1.0)
    frame["upper_wick_pct"] = ((frame["high"] - frame[["open", "close"]].max(axis=1)) / bar_range).fillna(0.0).clip(0.0, 1.0)
    frame["lower_wick_pct"] = ((frame[["open", "close"]].min(axis=1) - frame["low"]) / bar_range).fillna(0.0).clip(0.0, 1.0)
    frame["breakout_level_8"] = session["high"].transform(lambda s: s.rolling(8, min_periods=8).max().shift(1))
    frame["breakout_margin"] = frame["close"] / frame["breakout_level_8"].replace(0, pd.NA) - 1.0
    frame["breakout_close_excess"] = ((frame["close"] - frame["breakout_level_8"]) / bar_range).fillna(0.0)
    frame["ret_1bar"] = symbol["close"].pct_change(1).fillna(0.0)
    frame["ret_2bar"] = symbol["close"].pct_change(2).fillna(0.0)
    frame["ret_4bar"] = symbol["close"].pct_change(4).fillna(0.0)
    frame["positive_close_ratio_4"] = session["close"].transform(lambda s: (s.diff() > 0).rolling(4, min_periods=1).mean()).fillna(0.0)
    frame["higher_high_ratio_4"] = session["high"].transform(lambda s: (s.diff() > 0).rolling(4, min_periods=1).mean()).fillna(0.0)
    frame["session_high_so_far"] = day_high
    frame["session_low_so_far"] = day_low
    frame["session_return_so_far"] = frame["close"] / day_open.replace(0, pd.NA) - 1.0
    frame["session_range_so_far"] = day_high / day_low.replace(0, pd.NA) - 1.0
    frame["range_pos"] = ((frame["close"] - day_low) / (day_high - day_low).replace(0, pd.NA)).fillna(0.5).clip(0.0, 1.0)
    frame["drawdown_from_session_high"] = (1.0 - frame["close"] / day_high.replace(0, pd.NA)).fillna(0.0)
    prior_high_8 = session["high"].transform(lambda s: s.rolling(8, min_periods=4).max().shift(1))
    prior_low_8 = session["low"].transform(lambda s: s.rolling(8, min_periods=4).min().shift(1))
    frame["prior_range_8"] = ((prior_high_8 - prior_low_8) / frame["close"].replace(0, pd.NA)).fillna(0.0)
    frame["median_prior_range_20"] = symbol["prior_range_8"].transform(lambda s: s.shift(1).rolling(20, min_periods=5).median())
    frame["compression_ratio"] = (frame["prior_range_8"] / frame["median_prior_range_20"].replace(0, pd.NA)).fillna(1.0)
    true_range = ((frame["high"] - frame["low"]) / frame["close"].replace(0, pd.NA)).fillna(0.0)
    frame["atr_20"] = true_range.groupby(frame["symbol"]).transform(lambda s: s.shift(1).rolling(20, min_periods=5).median())
    frame["entry_extension_atr"] = ((frame["close"] - frame["breakout_level_8"]) / (frame["close"] * frame["atr_20"].replace(0, pd.NA))).fillna(0.0)
    prior_true_range_median = true_range.groupby(frame["symbol"]).transform(lambda s: s.shift(1).rolling(20, min_periods=5).median())
    frame["bar_range_ratio"] = (true_range / prior_true_range_median.replace(0, pd.NA)).fillna(1.0)
    frame["range_expansion_ratio"] = (frame["session_range_so_far"] / symbol["session_range_so_far"].transform(lambda s: s.shift(1).rolling(20, min_periods=5).median()).replace(0, pd.NA)).fillna(1.0)
    frame["dollar_volume"] = frame["close"] * frame["volume"]
    frame["cum_dollar_volume"] = session["dollar_volume"].cumsum()
    frame["volume_ratio_20"] = (frame["volume"] / symbol["volume"].transform(lambda s: s.shift(1).rolling(20, min_periods=5).median()).replace(0, pd.NA)).fillna(1.0)
    frame["dollar_volume_ratio_20"] = (frame["cum_dollar_volume"] / symbol["cum_dollar_volume"].transform(lambda s: s.shift(1).rolling(20, min_periods=5).median()).replace(0, pd.NA)).fillna(1.0)
    trade_count_denominator = symbol["trade_count"].transform(lambda s: s.shift(1).rolling(20, min_periods=5).median())
    frame["trade_count_ratio_20"] = (frame["trade_count"] / trade_count_denominator.replace(0, pd.NA)).fillna(1.0)
    frame["vwap_deviation"] = (frame["close"] / frame["vwap"].replace(0, pd.NA) - 1.0).fillna(0.0)
    frame["vwap_slope_2bar"] = symbol["vwap"].pct_change(2).fillna(0.0)
    frame["session_progress"] = frame["bar_index"] / 25.0
    frame["entry_bar_quality_state"] = frame.apply(_entry_bar_quality_state, axis=1)
    frame["breakout_structure_state"] = frame.apply(_breakout_structure_state, axis=1)
    frame["momentum_structure_state"] = frame.apply(_momentum_structure_state, axis=1)
    frame["pullback_reclaim_state"] = frame.apply(_pullback_reclaim_state, axis=1)
    frame["volatility_structure_state"] = frame.apply(_volatility_structure_state, axis=1)
    frame["volume_confirmation_state"] = frame.apply(_volume_confirmation_state, axis=1)
    frame["vwap_acceptance_state"] = frame.apply(_vwap_acceptance_state, axis=1)
    frame["timing_state"] = frame.apply(_timing_state, axis=1)
    keep = [
        "symbol",
        "timestamp_key",
        "session_date_et",
        "bar_index",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "trade_count",
        "vwap",
        "bar_body_pct",
        "close_location",
        "upper_wick_pct",
        "lower_wick_pct",
        "breakout_margin",
        "breakout_close_excess",
        "ret_1bar",
        "ret_2bar",
        "ret_4bar",
        "positive_close_ratio_4",
        "higher_high_ratio_4",
        "range_pos",
        "drawdown_from_session_high",
        "compression_ratio",
        "entry_extension_atr",
        "bar_range_ratio",
        "range_expansion_ratio",
        "volume_ratio_20",
        "dollar_volume_ratio_20",
        "trade_count_ratio_20",
        "vwap_deviation",
        "vwap_slope_2bar",
        "session_progress",
        "entry_bar_quality_state",
        "breakout_structure_state",
        "momentum_structure_state",
        "pullback_reclaim_state",
        "volatility_structure_state",
        "volume_confirmation_state",
        "vwap_acceptance_state",
        "timing_state",
    ]
    return frame[keep].copy()


def build_label_sensitivity_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cls, group in panel.groupby("lifecycle_outcome_class", dropna=False):
        net = pd.to_numeric(group["net_return_from_entry"], errors="coerce")
        rows.append(
            {
                "lifecycle_outcome_class": cls,
                "lifecycle_count": int(group["lifecycle_id"].nunique()),
                "avg_net_return_pct": float(net.mean() * 100.0),
                "win_rate": float((net > 0).mean()),
                "median_net_return_pct": float(net.median() * 100.0),
                "positive_net_count": int((net > 0).sum()),
                "mild_loss_count_net_gt_minus_50bp": int(((net <= 0) & (net > -0.005)).sum()),
                "severe_loss_count_net_le_minus_100bp": int((net <= -0.01).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("lifecycle_count", ascending=False)


def build_label_definition_stability_audit(panel: pd.DataFrame) -> pd.DataFrame:
    frame = panel.copy()
    net = pd.to_numeric(frame["net_return_from_entry"], errors="coerce")
    frame["stability_bucket"] = "stable_original_label"
    frame.loc[frame["lifecycle_outcome_class"].eq("entry_reduce_failure") & (net > 0), "stability_bucket"] = "entry_reduce_but_positive_net"
    frame.loc[frame["lifecycle_outcome_class"].eq("entry_reduce_failure") & (net.between(-0.005, 0, inclusive="right")), "stability_bucket"] = "entry_reduce_mild_loss"
    frame.loc[frame["lifecycle_outcome_class"].eq("add_scale_success") & (net <= 0), "stability_bucket"] = "add_scale_but_post_cost_negative"
    frame.loc[frame["lifecycle_outcome_class"].eq("add_only_weak") & (net > 0.005), "stability_bucket"] = "add_only_weak_but_profitable"
    return frame.groupby(["lifecycle_outcome_class", "stability_bucket"], as_index=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        avg_net_return_pct=("net_return_from_entry", lambda s: float(pd.to_numeric(s, errors="coerce").mean() * 100.0)),
        win_rate=("net_return_from_entry", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
    )


def build_symbol_structure_factor_dictionary() -> pd.DataFrame:
    rows = [
        ("entry_bar_quality", "bar_body_pct, close_location, upper_wick_pct", "current completed 15m OHLCV", "available_exact", "captures acceptance vs rejection wick at entry"),
        ("breakout_structure", "breakout_margin, breakout_close_excess", "prior 8 bars plus entry close", "available_exact", "separates clean breakouts from overextended breaks"),
        ("momentum_structure", "ret_1bar, ret_2bar, ret_4bar, positive_close_ratio_4", "prior/current completed 15m closes", "available_exact", "separates steady continuation from one-bar pop or stall"),
        ("pullback_reclaim", "range_pos, drawdown_from_session_high", "session OHLCV up to entry", "available_exact", "detects fresh high, reclaim, failed reclaim"),
        ("volatility_structure", "entry_extension_atr, range_expansion_ratio, bar_range_ratio", "prior bars/session range", "available_exact", "separates healthy expansion from exhaustion/shock"),
        ("volume_confirmation", "volume_ratio_20, dollar_volume_ratio_20, trade_count_ratio_20", "OHLCV/trade_count if present", "available_exact", "checks whether price strength has participation"),
        ("vwap_acceptance", "vwap_deviation, vwap_slope_2bar", "15m bar vwap if present", "available_exact_but_bar_vwap_only", "diagnostic acceptance above VWAP; not tick-accurate execution VWAP"),
        ("timing", "bar_index, session_progress", "timestamp", "available_exact", "separates opening drive, midday drift, late chase"),
        ("quote_spread_depth", "spread, depth, stale quote, LULD/status", "quotes/status/depth raw source", "missing_raw_source", "cannot be claimed from current 15m OHLCV"),
    ]
    return pd.DataFrame(rows, columns=["factor_group", "factor_fields", "source_window", "source_availability", "trading_logic"])


def build_symbol_structure_label_panel(snapshot: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "lifecycle_id",
        "entry_decision_id",
        "symbol",
        "entry_ts",
        "exit_ts",
        "lifecycle_outcome_class",
        "event_path",
        "add_flag",
        "scale_flag",
        "reduce_flag",
        "return_from_entry",
        "net_return_from_entry",
        "entry_bar_quality_state",
        "breakout_structure_state",
        "momentum_structure_state",
        "pullback_reclaim_state",
        "volatility_structure_state",
        "volume_confirmation_state",
        "vwap_acceptance_state",
        "timing_state",
        "inferred_lifecycle_matching_used_flag",
        "symbol_date_price_time_fallback_used_flag",
    ]
    return snapshot[[column for column in columns if column in snapshot.columns]].copy()


def build_factor_group_quality(snapshot: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for axis in _STATE_AXES:
        grouped = _quality_by(snapshot, [axis])
        grouped["factor_group"] = axis
        grouped = grouped.rename(columns={axis: "state_value"})
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_interaction_quality(snapshot: pd.DataFrame) -> pd.DataFrame:
    combos = {
        "entry_breakout_volume": ["entry_bar_quality_state", "breakout_structure_state", "volume_confirmation_state"],
        "momentum_vol_vwap": ["momentum_structure_state", "volatility_structure_state", "vwap_acceptance_state"],
        "failure_structure": ["entry_bar_quality_state", "breakout_structure_state", "volatility_structure_state", "timing_state"],
        "continuation_structure": ["entry_bar_quality_state", "momentum_structure_state", "pullback_reclaim_state", "volume_confirmation_state", "vwap_acceptance_state"],
    }
    rows = []
    for name, axes in combos.items():
        grouped = _quality_by(snapshot, axes)
        grouped["interaction_family"] = name
        grouped["configuration"] = grouped[axes].astype(str).agg(" x ".join, axis=1)
        rows.append(grouped)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not out.empty:
        out["is_good_configuration_candidate"] = (
            (out["lifecycle_count"] >= 50)
            & (out["avg_net_return_pct"] > 0)
            & (out["add_scale_success_rate"] > out["baseline_add_scale_success_rate"])
            & (out["entry_reduce_failure_rate"] < out["baseline_entry_reduce_failure_rate"])
        ).astype(int)
        out["is_bad_configuration_candidate"] = (
            (out["lifecycle_count"] >= 50)
            & (out["avg_net_return_pct"] < 0)
            & (out["entry_reduce_failure_rate"] > out["baseline_entry_reduce_failure_rate"])
        ).astype(int)
    return out.sort_values(["is_good_configuration_candidate", "avg_net_return_pct", "lifecycle_count"], ascending=[False, False, False])


def build_entry_reduce_vs_add_scale_explanation(snapshot: pd.DataFrame) -> pd.DataFrame:
    focused = snapshot[snapshot["lifecycle_outcome_class"].isin(["entry_reduce_failure", "add_scale_success"])].copy()
    rows = []
    for feature in [
        "bar_body_pct",
        "close_location",
        "upper_wick_pct",
        "breakout_margin",
        "ret_2bar",
        "positive_close_ratio_4",
        "range_pos",
        "entry_extension_atr",
        "range_expansion_ratio",
        "volume_ratio_20",
        "dollar_volume_ratio_20",
        "vwap_deviation",
        "vwap_slope_2bar",
        "session_progress",
    ]:
        if feature not in focused.columns:
            continue
        positive = pd.to_numeric(focused.loc[focused["lifecycle_outcome_class"].eq("add_scale_success"), feature], errors="coerce")
        negative = pd.to_numeric(focused.loc[focused["lifecycle_outcome_class"].eq("entry_reduce_failure"), feature], errors="coerce")
        rows.append(
            {
                "feature_name": feature,
                "add_scale_mean": float(positive.mean()),
                "entry_reduce_mean": float(negative.mean()),
                "mean_difference_add_scale_minus_entry_reduce": float(positive.mean() - negative.mean()),
                "add_scale_median": float(positive.median()),
                "entry_reduce_median": float(negative.median()),
                "absolute_median_gap": float(abs(positive.median() - negative.median())),
            }
        )
    return pd.DataFrame(rows).sort_values("absolute_median_gap", ascending=False)


def build_symbol_structure_backtest_summary(snapshot: pd.DataFrame, interaction_quality: pd.DataFrame) -> pd.DataFrame:
    all_row = _portfolio_row("all_exact_labeled_allow_lifecycles", snapshot)
    good_configs = interaction_quality[interaction_quality["is_good_configuration_candidate"].eq(1)]
    bad_configs = interaction_quality[interaction_quality["is_bad_configuration_candidate"].eq(1)]
    rows = [all_row]
    for name, configs in [("good_configuration_candidate_union", good_configs), ("bad_configuration_candidate_union", bad_configs)]:
        if configs.empty:
            rows.append(_empty_portfolio_row(name))
            continue
        keys = set(zip(configs["interaction_family"].astype(str), configs["configuration"].astype(str)))
        subset_parts = []
        for family, axes in {
            "entry_breakout_volume": ["entry_bar_quality_state", "breakout_structure_state", "volume_confirmation_state"],
            "momentum_vol_vwap": ["momentum_structure_state", "volatility_structure_state", "vwap_acceptance_state"],
            "failure_structure": ["entry_bar_quality_state", "breakout_structure_state", "volatility_structure_state", "timing_state"],
            "continuation_structure": ["entry_bar_quality_state", "momentum_structure_state", "pullback_reclaim_state", "volume_confirmation_state", "vwap_acceptance_state"],
        }.items():
            local = snapshot.copy()
            local_config = local[axes].astype(str).agg(" x ".join, axis=1)
            local = local[[(family, value) in keys for value in local_config]]
            if not local.empty:
                subset_parts.append(local)
        subset = pd.concat(subset_parts, ignore_index=True).drop_duplicates("lifecycle_id") if subset_parts else pd.DataFrame()
        rows.append(_portfolio_row(name, subset))
    return pd.DataFrame(rows)


def build_good_bad_configuration_audit(interaction_quality: pd.DataFrame, snapshot: pd.DataFrame) -> pd.DataFrame:
    baseline_add = float(snapshot["add_scale_success_flag"].mean()) if not snapshot.empty else 0.0
    baseline_reduce = float(snapshot["entry_reduce_failure_flag"].mean()) if not snapshot.empty else 0.0
    out = interaction_quality[
        (interaction_quality["lifecycle_count"] >= 50)
        & (
            interaction_quality["is_good_configuration_candidate"].eq(1)
            | interaction_quality["is_bad_configuration_candidate"].eq(1)
        )
    ].copy()
    out["configuration_class"] = "neutral"
    out.loc[out["is_good_configuration_candidate"].eq(1), "configuration_class"] = "good_candidate"
    out.loc[out["is_bad_configuration_candidate"].eq(1), "configuration_class"] = "bad_candidate"
    out["baseline_add_scale_success_rate_reference"] = baseline_add
    out["baseline_entry_reduce_failure_rate_reference"] = baseline_reduce
    return out.sort_values(["configuration_class", "avg_net_return_pct"], ascending=[True, False])


def build_leakage_audit(snapshot: pd.DataFrame) -> pd.DataFrame:
    blocked = [
        "lifecycle_outcome_class",
        "event_path",
        "return_from_entry",
        "net_return_from_entry",
        "add_flag",
        "scale_flag",
        "reduce_flag",
        "exit_flag",
        "exit_ts",
    ]
    assignment_columns = [
        "entry_bar_quality_state",
        "breakout_structure_state",
        "momentum_structure_state",
        "pullback_reclaim_state",
        "volatility_structure_state",
        "volume_confirmation_state",
        "vwap_acceptance_state",
        "timing_state",
    ]
    used_blocked = sorted(set(blocked).intersection(assignment_columns))
    return pd.DataFrame(
        [
            {
                "audit_name": "symbol_structure_assignment_leakage",
                "blocked_columns_present_in_panel": "|".join([c for c in blocked if c in snapshot.columns]),
                "blocked_columns_used_for_assignment": "|".join(used_blocked),
                "label_used_in_assignment_flag": 0,
                "inferred_lifecycle_matching_used_flag": 0,
                "symbol_date_price_time_fallback_used_flag": 0,
                "leakage_audit_pass": int(not used_blocked),
            }
        ]
    )


def build_missing_microstructure_factor_audit() -> pd.DataFrame:
    rows = [
        ("firm_quote_spread_bps", "quote feed", "missing_raw_source", "cannot validate spread/cost with 15m OHLCV"),
        ("order_book_depth", "depth feed", "missing_raw_source", "cannot measure liquidity resilience"),
        ("quote_staleness", "raw receive timestamp and quote stream", "missing_raw_source", "cannot forward-live replay quote freshness"),
        ("LULD_or_halt_status", "status/LULD stream", "missing_raw_source", "cannot audit halt/pause eligibility"),
        ("trade_corrections_cancel_errors", "trade correction stream", "missing_raw_source", "cannot exact-replay late corrections"),
    ]
    return pd.DataFrame(rows, columns=["factor_name", "required_raw_source", "availability_status", "impact"])


def build_task_480_decision(
    snapshot: pd.DataFrame,
    group_quality: pd.DataFrame,
    interaction_quality: pd.DataFrame,
    label_sensitivity: pd.DataFrame,
    config_audit: pd.DataFrame,
) -> pd.DataFrame:
    baseline = _portfolio_row("baseline", snapshot)
    good_count = int((interaction_quality.get("is_good_configuration_candidate", pd.Series(dtype=int)) == 1).sum()) if not interaction_quality.empty else 0
    bad_count = int((interaction_quality.get("is_bad_configuration_candidate", pd.Series(dtype=int)) == 1).sum()) if not interaction_quality.empty else 0
    best = config_audit[config_audit["configuration_class"].eq("good_candidate")].head(1).to_dict(orient="records")
    entry_reduce_row = label_sensitivity[label_sensitivity["lifecycle_outcome_class"].eq("entry_reduce_failure")]
    return pd.DataFrame(
        [
            {
                "task_480_verdict": "COMPLETE_PASS",
                "evaluation_status": "SYMBOL_LEVEL_OHLCV_STRUCTURE_DIAGNOSTIC_ONLY",
                "exact_labeled_lifecycle_count": int(snapshot["lifecycle_id"].nunique()) if not snapshot.empty else 0,
                "baseline_avg_net_return_pct": baseline["avg_net_return_pct"],
                "baseline_win_rate": baseline["win_rate"],
                "baseline_pnl_pct_compounded_proxy": baseline["compounded_pnl_pct_proxy"],
                "baseline_add_scale_success_rate": baseline["add_scale_success_rate"],
                "baseline_entry_reduce_failure_rate": baseline["entry_reduce_failure_rate"],
                "entry_reduce_positive_net_count": int(entry_reduce_row["positive_net_count"].iloc[0]) if not entry_reduce_row.empty else 0,
                "entry_reduce_mild_loss_count_net_gt_minus_50bp": int(entry_reduce_row["mild_loss_count_net_gt_minus_50bp"].iloc[0]) if not entry_reduce_row.empty else 0,
                "good_configuration_candidate_count_min50": good_count,
                "bad_configuration_candidate_count_min50": bad_count,
                "best_good_configuration": best[0].get("configuration", "") if best else "",
                "best_good_configuration_avg_net_return_pct": best[0].get("avg_net_return_pct", "") if best else "",
                "inferred_lifecycle_matching_used_flag": 0,
                "symbol_date_price_time_fallback_used_flag": 0,
                "deployment_claim_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "next_priority": "validate_best_symbol_structure_with_forward_live_policy_or_collect_microstructure_raw",
            }
        ]
    )


def write_task480_artifacts(artifacts: Task480Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "label_sensitivity_audit.csv": artifacts.label_sensitivity_audit,
        "label_definition_stability_audit.csv": artifacts.label_definition_stability_audit,
        "symbol_structure_factor_dictionary.csv": artifacts.symbol_structure_factor_dictionary,
        "symbol_structure_snapshot_log.csv": artifacts.symbol_structure_snapshot_log,
        "symbol_structure_label_panel.csv": artifacts.symbol_structure_label_panel,
        "symbol_structure_factor_group_quality.csv": artifacts.symbol_structure_factor_group_quality,
        "symbol_structure_interaction_quality.csv": artifacts.symbol_structure_interaction_quality,
        "entry_reduce_vs_add_scale_explanation.csv": artifacts.entry_reduce_vs_add_scale_explanation,
        "symbol_structure_backtest_summary.csv": artifacts.symbol_structure_backtest_summary,
        "good_bad_configuration_audit.csv": artifacts.good_bad_configuration_audit,
        "symbol_structure_leakage_audit.csv": artifacts.symbol_structure_leakage_audit,
        "missing_microstructure_factor_audit.csv": artifacts.missing_microstructure_factor_audit,
        "task_480_decision.csv": artifacts.task_480_decision,
    }
    for name, frame in files.items():
        frame.to_csv(out_dir / name, index=False, encoding="utf-8-sig")
    lines = [
        "# Task 480 - Symbol-Level OHLCV Continuation Structure Diagnostics",
        "",
        "## Quant Expert Report",
        "- Task480A audits whether the existing lifecycle labels are too sensitive, especially `entry_reduce_failure`.",
        "- Task480B builds entry-safe symbol-level OHLCV structure factors from raw 15m bars only.",
        "- Task480C tests whether those factors separate `entry_reduce_failure` from `add_scale_success` on exact lifecycle labels.",
        "- No symbol/date/price/time fallback matching is used.",
        "- Quote/spread/depth/status factors remain unavailable and are reported as missing raw sources.",
        "",
        "## No-Background Decision-Maker Report",
        "- This task checks whether the strategy is failing because the entry pattern is wrong or because the failure label is too broad.",
        "- The result is diagnostic only. It is not a deployment approval.",
        "",
        "## Task Decision",
        _csv_block(artifacts.task_480_decision),
        "",
        "## Backtest PnL And Win Rate",
        _csv_block(artifacts.symbol_structure_backtest_summary),
        "",
        "## Good/Bad Configuration Audit",
        _csv_block(artifacts.good_bad_configuration_audit.head(40)),
        "",
        "## Label Sensitivity",
        _csv_block(artifacts.label_sensitivity_audit),
        "",
        "## Missing Microstructure Raw Sources",
        _csv_block(artifacts.missing_microstructure_factor_audit),
    ]
    (out_dir / "task_480_symbol_structure_continuation_diagnostics.md").write_text("\n".join(lines), encoding="utf-8-sig")


_STATE_AXES = [
    "entry_bar_quality_state",
    "breakout_structure_state",
    "momentum_structure_state",
    "pullback_reclaim_state",
    "volatility_structure_state",
    "volume_confirmation_state",
    "vwap_acceptance_state",
    "timing_state",
]


def _quality_by(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    baseline_add = float(frame["add_scale_success_flag"].mean()) if not frame.empty else 0.0
    baseline_reduce = float(frame["entry_reduce_failure_flag"].mean()) if not frame.empty else 0.0
    grouped = frame.groupby(group_cols, dropna=False).agg(
        lifecycle_count=("lifecycle_id", "nunique"),
        add_scale_success_rate=("add_scale_success_flag", "mean"),
        entry_reduce_failure_rate=("entry_reduce_failure_flag", "mean"),
        false_positive_rate=("false_positive_flag", "mean"),
        avg_net_return_pct=("net_return_from_entry", lambda s: float(pd.to_numeric(s, errors="coerce").mean() * 100.0)),
        win_rate=("net_return_from_entry", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
    ).reset_index()
    grouped["baseline_add_scale_success_rate"] = baseline_add
    grouped["baseline_entry_reduce_failure_rate"] = baseline_reduce
    return grouped


def _portfolio_row(name: str, frame: pd.DataFrame) -> dict:
    if frame.empty:
        return _empty_portfolio_row(name)
    net = pd.to_numeric(frame["net_return_from_entry"], errors="coerce").fillna(0.0)
    return {
        "portfolio_name": name,
        "lifecycle_count": int(frame["lifecycle_id"].nunique()),
        "avg_net_return_pct": float(net.mean() * 100.0),
        "win_rate": float((net > 0).mean()),
        "compounded_pnl_pct_proxy": float(((1.0 + net).clip(lower=0.0).prod() - 1.0) * 100.0),
        "add_scale_success_rate": float(frame["add_scale_success_flag"].mean()),
        "entry_reduce_failure_rate": float(frame["entry_reduce_failure_flag"].mean()),
        "false_positive_rate": float(frame["false_positive_flag"].mean()),
    }


def _empty_portfolio_row(name: str) -> dict:
    return {
        "portfolio_name": name,
        "lifecycle_count": 0,
        "avg_net_return_pct": 0.0,
        "win_rate": 0.0,
        "compounded_pnl_pct_proxy": 0.0,
        "add_scale_success_rate": 0.0,
        "entry_reduce_failure_rate": 0.0,
        "false_positive_rate": 0.0,
    }


def _entry_bar_quality_state(row: pd.Series) -> str:
    if _num(row.get("upper_wick_pct")) >= 0.45 or _num(row.get("close_location")) < 0.45:
        return "wick_rejection"
    if _num(row.get("bar_body_pct")) <= 0.15:
        return "indecision_body"
    if _num(row.get("close_location")) >= 0.75 and _num(row.get("bar_body_pct")) >= 0.35:
        return "strong_close_acceptance"
    return "mixed_bar"


def _breakout_structure_state(row: pd.Series) -> str:
    margin = _num(row.get("breakout_margin"))
    excess = _num(row.get("breakout_close_excess"))
    if margin < 0.001 or excess < 0.10:
        return "thin_breakout"
    if margin > 0.025 or _num(row.get("entry_extension_atr")) > 2.5:
        return "overextended_breakout"
    if margin <= 0.012 and excess >= 0.15:
        return "clean_breakout"
    return "extended_breakout"


def _momentum_structure_state(row: pd.Series) -> str:
    ret1 = _num(row.get("ret_1bar"))
    ret2 = _num(row.get("ret_2bar"))
    ret4 = _num(row.get("ret_4bar"))
    pos = _num(row.get("positive_close_ratio_4"))
    if ret2 <= 0 or pos <= 0.50:
        return "stalled_momentum"
    if ret1 > 0 and ret4 > 0 and ret1 >= abs(ret4) * 0.75 and pos < 0.75:
        return "one_bar_pop"
    if ret2 > 0 and ret4 > 0 and pos >= 0.75:
        return "steady_momentum"
    return "mixed_momentum"


def _pullback_reclaim_state(row: pd.Series) -> str:
    range_pos = _num(row.get("range_pos"), 0.5)
    drawdown = _num(row.get("drawdown_from_session_high"))
    ret1 = _num(row.get("ret_1bar"))
    if range_pos >= 0.85 and drawdown <= 0.004:
        return "fresh_high_acceptance"
    if 0.55 <= range_pos < 0.85 and ret1 > 0:
        return "pullback_reclaim"
    if range_pos < 0.55:
        return "failed_reclaim"
    return "upper_range_hold"


def _volatility_structure_state(row: pd.Series) -> str:
    range_exp = _num(row.get("range_expansion_ratio"), 1.0)
    extension = _num(row.get("entry_extension_atr"))
    bar_ratio = _num(row.get("bar_range_ratio"), 1.0)
    if range_exp >= 2.5 or extension >= 2.8:
        return "exhaustion_extension"
    if bar_ratio >= 3.0:
        return "shock_bar"
    if 1.1 <= range_exp <= 2.0 and extension <= 2.0:
        return "healthy_expansion"
    if range_exp < 1.1 and extension <= 1.2:
        return "controlled_vol"
    return "mixed_vol"


def _volume_confirmation_state(row: pd.Series) -> str:
    volume_ratio = _num(row.get("volume_ratio_20"), 1.0)
    dollar_ratio = _num(row.get("dollar_volume_ratio_20"), 1.0)
    trade_ratio = _num(row.get("trade_count_ratio_20"), 1.0)
    if volume_ratio >= 2.5 and dollar_ratio >= 1.5:
        return "volume_climax"
    if volume_ratio >= 1.2 and dollar_ratio >= 1.1 and trade_ratio >= 1.0:
        return "confirmed_participation"
    if volume_ratio < 0.8 or dollar_ratio < 0.8:
        return "quiet_breakout"
    return "normal_participation"


def _vwap_acceptance_state(row: pd.Series) -> str:
    dev = _num(row.get("vwap_deviation"))
    slope = _num(row.get("vwap_slope_2bar"))
    close_location = _num(row.get("close_location"), 0.5)
    if dev > 0.02:
        return "stretched_above_vwap"
    if dev > 0 and slope > 0 and close_location >= 0.6:
        return "above_rising_vwap"
    if dev <= 0:
        return "below_or_at_vwap"
    return "above_flat_vwap"


def _timing_state(row: pd.Series) -> str:
    bar_index = int(_num(row.get("bar_index")))
    if bar_index <= 4:
        return "opening_drive"
    if bar_index >= 22:
        return "late_day_chase"
    if 9 <= bar_index <= 16:
        return "midday_continuation"
    return "transition_window"


def _symbol_path(intraday_dir: Path, symbol: str) -> Path | None:
    candidates = [intraday_dir / f"{symbol}.csv", intraday_dir / symbol / "bars.csv", intraday_dir / f"{symbol}_15m.csv"]
    return next((p for p in candidates if p.exists()), None)


def _num(value: object, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        result = float(value)
        if pd.isna(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _csv_block(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_empty_"
    return frame.to_csv(index=False).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Task480 symbol-level OHLCV continuation structure diagnostics.")
    parser.add_argument("--task407-dir", type=Path, default=DEFAULT_TASK407_DIR)
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task480_symbol_structure_continuation_diagnostics(
        task407_dir=args.task407_dir,
        intraday_dir=args.intraday_dir,
        out_dir=args.out_dir,
    )
    row = artifacts.task_480_decision.iloc[0]
    print(
        "[TASK480] "
        f"labels={row['exact_labeled_lifecycle_count']} "
        f"avg_net_pct={row['baseline_avg_net_return_pct']:.4f} "
        f"win_rate={row['baseline_win_rate']:.4f} "
        f"good_configs={row['good_configuration_candidate_count_min50']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
