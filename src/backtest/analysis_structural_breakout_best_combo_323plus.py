from __future__ import annotations

import argparse
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Any

import pandas as pd

from src.backtest.analysis_structural_breakout_322 import (
    DEFAULT_BASE_DIR,
    StructuralConfig,
    _asset_type,
    _prepare_preloaded_frames,
    _scenario_name,
    run_structural_backtest,
)
from src.backtest.analysis_structural_breakout_audit_323 import _run_period_reruns, _trade_overlap_matrix
from src.backtest.data_loader import load_daily_bars


RANKED_INPUT = Path("docs/reports/task_323_structural_breakout_audit/all_scenarios_ranked.csv")
DEFAULT_OUT_DIR = "docs/reports/task_323_best_combo_evaluation"
TRAIN_END_DATE = "2025-10-31"
TEST_START_DATE = "2025-11-01"
ROLLING_TRAIN_MONTHS = 24
TEST_MONTHS = 6
WALK_FORWARD_MIN_TRAIN_MONTHS = 18
ANATOMY_FEATURE_COLUMNS = [
    "ret_5d_pre",
    "ret_10d_pre",
    "ret_20d_pre",
    "dist_to_sma20_pct",
    "dist_to_sma50_pct",
    "dist_to_sma200_pct",
    "gap_from_prev_close_pct",
    "gap_over_planned_entry_pct",
    "vol_expansion_ratio",
    "atr_pct_pre",
]
FEATURE_BIN_SPECS: dict[str, list[tuple[str, float | None, float | None]]] = {
    "ret_5d_pre": [("<0", None, 0.0), ("0~5%", 0.0, 0.05), ("5~10%", 0.05, 0.10), ("10%+", 0.10, None)],
    "ret_10d_pre": [("<0", None, 0.0), ("0~8%", 0.0, 0.08), ("8~15%", 0.08, 0.15), ("15%+", 0.15, None)],
    "ret_20d_pre": [("<0", None, 0.0), ("0~12%", 0.0, 0.12), ("12~20%", 0.12, 0.20), ("20%+", 0.20, None)],
    "dist_to_sma20_pct": [("<2%", None, 0.02), ("2~5%", 0.02, 0.05), ("5~8%", 0.05, 0.08), ("8%+", 0.08, None)],
    "gap_over_planned_entry_pct": [("<=0", None, 0.0), ("0~1%", 0.0, 0.01), ("1~3%", 0.01, 0.03), ("3%+", 0.03, None)],
    "vol_expansion_ratio": [("<1.0", None, 1.0), ("1.0~1.25", 1.0, 1.25), ("1.25~1.5", 1.25, 1.5), ("1.5+", 1.5, None)],
}
FAILURE_DISTRIBUTION_FEATURES = [
    "ret_20d_pre",
    "dist_to_sma20_pct",
    "gap_over_planned_entry_pct",
    "vol_expansion_ratio",
    "realized_R",
]
WINNER_LOSER_COMPARE_FEATURES = [
    "ret_5d_pre",
    "ret_10d_pre",
    "ret_20d_pre",
    "dist_to_sma20_pct",
    "dist_to_sma50_pct",
    "dist_to_sma200_pct",
    "vol_expansion_ratio",
    "gap_over_planned_entry_pct",
    "breakout_strength_pct",
    "follow_through_1d_pct",
    "follow_through_3d_pct",
    "follow_through_5d_pct",
    "post_breakout_retrace_3d_pct",
    "post_breakout_retrace_5d_pct",
    "adverse_excursion_3d_pct",
    "adverse_excursion_5d_pct",
    "rs_percentile_20d",
]
AI_SEMI_LEADERS = {
    "AMD", "NVDA", "AVGO", "QCOM", "TSM", "ARM", "SMCI", "MU", "AMAT", "LRCX", "KLAC", "MRVL", "ASML",
}
SEMI_SYMBOLS = {
    "AMD", "NVDA", "AVGO", "QCOM", "TSM", "ARM", "MU", "AMAT", "LRCX", "KLAC", "MRVL", "ASML", "ADI", "NXPI",
    "MCHP", "ON", "TXN", "INTC", "SMCI",
}
SOFTWARE_INTERNET_SYMBOLS = {
    "AMZN", "GOOGL", "META", "NFLX", "MSFT", "CRM", "NOW", "SNOW", "SHOP", "UBER", "ORCL", "PANW", "CRWD",
    "DDOG", "MDB", "ZS", "NET", "TEAM",
}
OTHER_TECH_SYMBOLS = {"AAPL", "TSLA"}


@dataclass(frozen=True)
class OOSWindow:
    name: str
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp


def _config_from_scenario(scenario: str) -> StructuralConfig:
    parts = str(scenario).split("|")
    if len(parts) < 8:
        raise ValueError(f"invalid scenario id: {scenario}")
    kwargs: dict[str, Any] = {
        "structure_mode": parts[0],
        "breakout_trigger_mode": parts[1],
        "entry_model": parts[2],
        "stop_mode": parts[3],
        "entry_bar_stop_mode": parts[4],
        "atr_multiplier": float(parts[5].removeprefix("atr")),
        "max_holding_days": int(parts[6].removeprefix("hold")),
        "min_avg_dollar_volume_20": float(parts[7].removeprefix("liq")),
    }
    if kwargs["structure_mode"] == "RANGE_COMPRESSION":
        kwargs["range_lookback"] = int(parts[8].removeprefix("lb"))
        kwargs["max_range_width_pct"] = float(parts[9].removeprefix("w"))
    elif kwargs["structure_mode"] == "LONG_DONCHIAN":
        kwargs["donchian_n"] = int(parts[8].removeprefix("n"))
    elif kwargs["structure_mode"] == "PIVOT_HIGH":
        kwargs["max_pivot_age"] = int(parts[8].removeprefix("age"))
    return StructuralConfig(**kwargs)


def _load_ranked_input(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"ranked input is empty: {path}")
    parsed_rows: list[dict[str, Any]] = []
    for scenario in df["scenario"].tolist():
        cfg = _config_from_scenario(str(scenario))
        parsed_rows.append(
            {
                "scenario": _scenario_name(cfg),
                "family": cfg.structure_mode,
                "trigger_mode_cfg": cfg.breakout_trigger_mode,
                "entry_model_cfg": cfg.entry_model,
                "stop_mode_cfg": cfg.stop_mode,
                "entry_bar_stop_mode_cfg": cfg.entry_bar_stop_mode,
                "atr_multiplier_cfg": cfg.atr_multiplier,
                "max_holding_days_cfg": cfg.max_holding_days,
                "min_avg_dollar_volume_20_cfg": cfg.min_avg_dollar_volume_20,
                "range_lookback_cfg": cfg.range_lookback if cfg.structure_mode == "RANGE_COMPRESSION" else math.nan,
                "max_range_width_pct_cfg": cfg.max_range_width_pct if cfg.structure_mode == "RANGE_COMPRESSION" else math.nan,
                "donchian_n_cfg": cfg.donchian_n if cfg.structure_mode == "LONG_DONCHIAN" else math.nan,
                "max_pivot_age_cfg": cfg.max_pivot_age if cfg.structure_mode == "PIVOT_HIGH" else math.nan,
            }
        )
    parsed = pd.DataFrame(parsed_rows)
    merged = df.merge(parsed, on="scenario", how="left")
    merged["label_rank"] = pd.to_numeric(merged.get("label_rank"), errors="coerce").fillna(9)
    return merged


def _latest_data_end(base_dir: Path) -> pd.Timestamp:
    latest: pd.Timestamp | None = None
    for csv_path in sorted(base_dir.glob("*.csv")):
        frame = pd.read_csv(csv_path, usecols=["timestamp"])
        ts = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").dropna()
        if ts.empty:
            continue
        current = pd.Timestamp(ts.max())
        if latest is None or current > latest:
            latest = current
    if latest is None:
        raise ValueError(f"no timestamps found in {base_dir}")
    return latest


def _recent_six_month_window(end_ts: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    end = pd.Timestamp(end_ts, tz="UTC") if pd.Timestamp(end_ts).tzinfo is None else pd.Timestamp(end_ts).tz_convert("UTC")
    end_period = end.tz_localize(None).to_period("M")
    start = (end_period - 5).to_timestamp(how="start").tz_localize("UTC")
    return start, end


def _slice_timestamps(timestamps: list[pd.Timestamp], start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    return [ts for ts in timestamps if start <= ts <= end]


def _balanced_rank_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ["label_rank", "sharpe", "expectancy_r", "cagr_pct", "trade_count", "max_drawdown_pct"],
        ascending=[True, False, False, False, False, True],
    ).reset_index(drop=True)


def _cagr_rank_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        ["label_rank", "cagr_pct", "sharpe", "expectancy_r", "trade_count", "max_drawdown_pct"],
        ascending=[True, False, False, False, False, True],
    ).reset_index(drop=True)


def _representative_scenario(group: list[str], metrics_by_scenario: dict[str, dict[str, Any]]) -> str:
    return sorted(
        group,
        key=lambda scenario: (
            -float(metrics_by_scenario[scenario]["sharpe"]),
            float(metrics_by_scenario[scenario]["max_drawdown_pct"]),
            -float(metrics_by_scenario[scenario]["trade_count"]),
            -float(metrics_by_scenario[scenario]["cagr_pct"]),
            scenario,
        ),
    )[0]


def _overlap_groups(overlap_df: pd.DataFrame, metrics_by_scenario: dict[str, dict[str, Any]]) -> dict[str, str]:
    scenarios = overlap_df["scenario"].tolist()
    parent = {scenario: scenario for scenario in scenarios}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    for row in overlap_df.itertuples(index=False):
        lhs = str(row[0])
        for rhs, value in zip(overlap_df.columns[1:], row[1:]):
            if lhs >= str(rhs):
                continue
            if float(value) >= 0.999999:
                union(lhs, str(rhs))

    groups: dict[str, list[str]] = defaultdict(list)
    for scenario in scenarios:
        groups[find(scenario)].append(scenario)

    representative_by_scenario: dict[str, str] = {}
    for group in groups.values():
        rep = _representative_scenario(group, metrics_by_scenario)
        for scenario in group:
            representative_by_scenario[scenario] = rep
    return representative_by_scenario


def _select_top_n(ranked_df: pd.DataFrame, representative_by_scenario: dict[str, str], *, top_n: int) -> list[str]:
    selected: list[str] = []
    seen: set[str] = set()
    for scenario in ranked_df["scenario"].tolist():
        rep = representative_by_scenario.get(str(scenario), str(scenario))
        if rep in seen:
            continue
        selected.append(rep)
        seen.add(rep)
        if len(selected) >= top_n:
            break
    return selected


def _select_mixed_top3(balanced_ranked: pd.DataFrame, cagr_ranked: pd.DataFrame, representative_by_scenario: dict[str, str]) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for scenario in _select_top_n(balanced_ranked, representative_by_scenario, top_n=2):
        selected.append({"scenario": scenario, "selection_group": "BALANCED"})
        seen.add(scenario)
    for scenario in _select_top_n(cagr_ranked, representative_by_scenario, top_n=len(cagr_ranked)):
        if scenario in seen:
            continue
        selected.append({"scenario": scenario, "selection_group": "CAGR"})
        break
    if len(selected) < 3:
        combined = pd.concat([balanced_ranked, cagr_ranked], ignore_index=True).drop_duplicates(subset=["scenario"])
        for scenario in _select_top_n(combined, representative_by_scenario, top_n=len(combined)):
            if scenario in seen:
                continue
            selected.append({"scenario": scenario, "selection_group": "MIXED"})
            seen.add(scenario)
            if len(selected) == 3:
                break
    if len(selected) != 3:
        raise ValueError(f"expected exactly 3 selected scenarios, got {len(selected)}")
    return selected


def _period_result_by_scenario(
    configs: list[StructuralConfig],
    *,
    base_dir: Path,
    stocks: list[str],
    jobs: int,
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
) -> dict[str, dict[str, Any]]:
    effective_jobs = jobs if len(configs) > 6 else 1
    results = _run_period_reruns(configs, base_dir=base_dir, stocks=stocks, jobs=effective_jobs, frames=frames, timestamps=timestamps)
    return {_scenario_name(StructuralConfig(**result["config"])): result for result in results}


def _symbol_contribution_df(result: dict[str, Any]) -> pd.DataFrame:
    total_r_all = sum(float(t["realized_R"]) for t in result["trade_log"])
    rows: list[dict[str, Any]] = []
    for row in result["diagnostics"]["by_symbol"]:
        share = float(row["total_r"]) / total_r_all if total_r_all else 0.0
        rows.append({**row, "total_r_share": round(share, 6)})
    return pd.DataFrame(rows).sort_values("total_r", ascending=False).reset_index(drop=True)


def _entry_type_of_trade(trade: dict[str, Any]) -> str:
    return "gap_open_fill" if bool(trade.get("filled_at_open", False)) else "planned_breakout_fill"


def _safe_ratio(numerator: Any, denominator: Any) -> float:
    if pd.isna(numerator) or pd.isna(denominator) or float(denominator) == 0.0:
        return math.nan
    return float(numerator) / float(denominator)


def _classify_market_regime(row: pd.Series) -> tuple[str, str]:
    close_prev = row.get("close_prev")
    sma200_prev = row.get("sma200_prev")
    if pd.isna(close_prev) or pd.isna(sma200_prev) or float(close_prev) <= float(sma200_prev):
        return "risk_off", "risk_off"

    dist20 = _safe_ratio(close_prev, row.get("sma20_prev"))
    dist20 = dist20 - 1.0 if not math.isnan(dist20) else math.nan
    ret5 = float(row.get("ret_5d_prev")) if pd.notna(row.get("ret_5d_prev")) else math.nan
    ret20 = float(row.get("ret_20d_prev")) if pd.notna(row.get("ret_20d_prev")) else math.nan
    std5 = row.get("std5_prev")
    std20 = row.get("std20_prev")
    vol_ratio = _safe_ratio(std5, std20)

    if (not math.isnan(dist20) and dist20 >= 0.08) or (not math.isnan(ret20) and ret20 >= 0.18):
        return "risk_on", "risk_on_overextended"
    if (not math.isnan(ret5) and ret5 <= 0.0) and (not math.isnan(vol_ratio) and vol_ratio >= 1.25):
        return "risk_on", "risk_on_high_vol_slowdown"
    if (not math.isnan(ret5) and ret5 <= 0.0) and (not math.isnan(dist20) and dist20 >= 0.03):
        return "risk_on", "risk_on_cooling"
    return "risk_on", "risk_on_healthy"


def _build_market_regime_lookup(base_dir: Path) -> dict[str, dict[str, Any]]:
    qld = load_daily_bars("QLD", base_dir=base_dir).copy()
    qld["timestamp"] = pd.to_datetime(qld["timestamp"], utc=True)
    qld = qld.sort_values("timestamp").reset_index(drop=True)
    qld["close"] = pd.to_numeric(qld["close"], errors="coerce")
    qld["std5"] = qld["close"].pct_change().rolling(5).std(ddof=0)
    qld["std20"] = qld["close"].pct_change().rolling(20).std(ddof=0)
    qld["sma20"] = qld["close"].rolling(20, min_periods=20).mean()
    qld["sma50"] = qld["close"].rolling(50, min_periods=50).mean()
    qld["sma200"] = qld["close"].rolling(200, min_periods=200).mean()
    qld["ret_5d"] = qld["close"].pct_change(5)
    qld["ret_20d"] = qld["close"].pct_change(20)
    qld["close_prev"] = qld["close"].shift(1)
    qld["sma20_prev"] = qld["sma20"].shift(1)
    qld["sma50_prev"] = qld["sma50"].shift(1)
    qld["sma200_prev"] = qld["sma200"].shift(1)
    qld["ret_5d_prev"] = qld["ret_5d"].shift(1)
    qld["ret_20d_prev"] = qld["ret_20d"].shift(1)
    qld["std5_prev"] = qld["std5"].shift(1)
    qld["std20_prev"] = qld["std20"].shift(1)
    lookup: dict[str, dict[str, Any]] = {}
    for row in qld.itertuples(index=False):
        ts = pd.Timestamp(row.timestamp).date().isoformat()
        row_series = pd.Series(row._asdict())
        base, detail = _classify_market_regime(row_series)
        lookup[ts] = {"market_regime_base": base, "market_regime_detail": detail}
    return lookup


def _build_symbol_feature_lookup(frames: dict[str, pd.DataFrame]) -> dict[str, dict[str, dict[str, float]]]:
    lookup: dict[str, dict[str, dict[str, float]]] = {}
    for symbol, frame in frames.items():
        enriched = frame.copy()
        close = pd.to_numeric(enriched["close"], errors="coerce")
        enriched["ret_10d"] = close.pct_change(10)
        enriched["sma50"] = close.rolling(50, min_periods=50).mean()
        enriched["sma200"] = close.rolling(200, min_periods=200).mean()
        enriched["ret_5d_pre"] = enriched["ret_5d"].shift(1)
        enriched["ret_10d_pre"] = enriched["ret_10d"].shift(1)
        enriched["ret_20d_pre"] = close.pct_change(20).shift(1)
        enriched["dist_to_sma20_pct"] = close.shift(1) / enriched["sma20"].shift(1) - 1.0
        enriched["dist_to_sma50_pct"] = close.shift(1) / enriched["sma50"].shift(1) - 1.0
        enriched["dist_to_sma200_pct"] = close.shift(1) / enriched["sma200"].shift(1) - 1.0
        enriched["gap_from_prev_close_pct"] = pd.to_numeric(enriched["gap_pct"], errors="coerce")
        enriched["vol_expansion_ratio"] = enriched["std5_prev"] / enriched["std20_prev"]
        enriched["atr_pct_pre"] = enriched["atr_prev"] / enriched["prev_close"]
        enriched["date_key"] = pd.to_datetime(enriched["timestamp"], utc=True).dt.date.astype(str)
        feature_cols = [column for column in ANATOMY_FEATURE_COLUMNS if column != "gap_over_planned_entry_pct"]
        cols = ["date_key", *feature_cols]
        symbol_lookup: dict[str, dict[str, float]] = {}
        for row in enriched[cols].itertuples(index=False):
            row_dict = {name: (float(value) if pd.notna(value) else math.nan) for name, value in zip(cols[1:], row[1:])}
            symbol_lookup[str(row[0])] = row_dict
        lookup[symbol] = symbol_lookup
    return lookup


def _recent_trade_frame(
    result: dict[str, Any],
    regime_lookup: dict[str, dict[str, Any]],
    symbol_feature_lookup: dict[str, dict[str, dict[str, float]]],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade in result["trade_log"]:
        exit_date = pd.Timestamp(str(trade["exit_date"]), tz="UTC")
        entry_date = pd.Timestamp(str(trade["entry_date"]), tz="UTC")
        symbol = str(trade["symbol"])
        date_key = str(entry_date.date())
        regime = regime_lookup.get(date_key, {"market_regime_base": "risk_off", "market_regime_detail": "risk_off"})
        feature_row = symbol_feature_lookup.get(symbol, {}).get(date_key, {})
        gap_over_planned = _safe_ratio(trade.get("entry_open"), trade.get("planned_entry_price"))
        gap_over_planned = gap_over_planned - 1.0 if not math.isnan(gap_over_planned) else math.nan
        rows.append(
            {
                "scenario": _scenario_name(StructuralConfig(**result["config"])),
                "symbol": symbol,
                "entry_date": date_key,
                "exit_date": str(exit_date.date()),
                "month_bucket": exit_date.strftime("%Y-%m"),
                "realized_R": float(trade["realized_R"]),
                "entry_type": _entry_type_of_trade(trade),
                "market_regime_base": regime["market_regime_base"],
                "market_regime_detail": regime["market_regime_detail"],
                "gap_over_planned_entry_pct": gap_over_planned,
                **{column: feature_row.get(column, math.nan) for column in ANATOMY_FEATURE_COLUMNS if column != "gap_over_planned_entry_pct"},
            }
        )
    return pd.DataFrame(rows)


def _loss_breakdown(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["scenario", column, "loss_r_sum", "loss_trade_count", "avg_loss_r", "loss_share"])
    losses = df[df["realized_R"] < 0].copy()
    if losses.empty:
        return pd.DataFrame(columns=["scenario", column, "loss_r_sum", "loss_trade_count", "avg_loss_r", "loss_share"])
    grouped = (
        losses.groupby(["scenario", column], as_index=False)
        .agg(loss_r_sum=("realized_R", "sum"), loss_trade_count=("realized_R", "size"), avg_loss_r=("realized_R", "mean"))
        .sort_values(["scenario", "loss_r_sum"])
    )
    totals = grouped.groupby("scenario")["loss_r_sum"].transform(lambda s: abs(float(s.sum())) if float(s.sum()) != 0 else 1.0)
    grouped["loss_share"] = grouped["loss_r_sum"].abs() / totals

    all_grouped = (
        losses.groupby(column, as_index=False)
        .agg(loss_r_sum=("realized_R", "sum"), loss_trade_count=("realized_R", "size"), avg_loss_r=("realized_R", "mean"))
        .sort_values("loss_r_sum")
    )
    total_loss_all = abs(float(all_grouped["loss_r_sum"].sum())) if not all_grouped.empty and float(all_grouped["loss_r_sum"].sum()) != 0 else 1.0
    all_grouped["loss_share"] = all_grouped["loss_r_sum"].abs() / total_loss_all
    all_grouped.insert(0, "scenario", "ALL")
    return pd.concat([grouped, all_grouped], ignore_index=True)


def _feature_summary(loss_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if loss_df.empty:
        return pd.DataFrame(columns=["scenario", "feature", "count", "median", "mean", "p25", "p75"])
    for scenario in [*sorted(loss_df["scenario"].unique()), "ALL"]:
        subset = loss_df if scenario == "ALL" else loss_df[loss_df["scenario"] == scenario]
        for feature in ANATOMY_FEATURE_COLUMNS:
            values = pd.to_numeric(subset[feature], errors="coerce").dropna()
            rows.append(
                {
                    "scenario": scenario,
                    "feature": feature,
                    "count": int(values.shape[0]),
                    "median": round(float(values.median()), 6) if not values.empty else math.nan,
                    "mean": round(float(values.mean()), 6) if not values.empty else math.nan,
                    "p25": round(float(values.quantile(0.25)), 6) if not values.empty else math.nan,
                    "p75": round(float(values.quantile(0.75)), 6) if not values.empty else math.nan,
                }
            )
    return pd.DataFrame(rows)


def _assign_feature_bin(value: float, bins: list[tuple[str, float | None, float | None]]) -> str | None:
    if math.isnan(value):
        return None
    for label, lower, upper in bins:
        lower_ok = lower is None or value >= lower
        upper_ok = upper is None or value < upper
        if lower_ok and upper_ok:
            return label
    return bins[-1][0] if bins else None


def _feature_bin_breakdown(loss_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if loss_df.empty:
        return pd.DataFrame(columns=["scenario", "feature", "bin_label", "loss_r_sum", "loss_trade_count", "loss_share"])
    for scenario in [*sorted(loss_df["scenario"].unique()), "ALL"]:
        subset = loss_df if scenario == "ALL" else loss_df[loss_df["scenario"] == scenario]
        total_loss = abs(float(subset["realized_R"].sum())) if not subset.empty and float(subset["realized_R"].sum()) != 0 else 1.0
        for feature, bins in FEATURE_BIN_SPECS.items():
            feature_rows: list[dict[str, Any]] = []
            for _, row in subset.iterrows():
                value = pd.to_numeric(row.get(feature), errors="coerce")
                if pd.isna(value):
                    continue
                label = _assign_feature_bin(float(value), bins)
                if label is None:
                    continue
                feature_rows.append({"feature": feature, "bin_label": label, "realized_R": float(row["realized_R"])})
            if not feature_rows:
                continue
            grouped = (
                pd.DataFrame(feature_rows)
                .groupby(["feature", "bin_label"], as_index=False)
                .agg(loss_r_sum=("realized_R", "sum"), loss_trade_count=("realized_R", "size"))
            )
            for record in grouped.to_dict("records"):
                rows.append(
                    {
                        "scenario": scenario,
                        "feature": record["feature"],
                        "bin_label": record["bin_label"],
                        "loss_r_sum": record["loss_r_sum"],
                        "loss_trade_count": int(record["loss_trade_count"]),
                        "loss_share": abs(float(record["loss_r_sum"])) / total_loss,
                    }
                )
    return pd.DataFrame(rows)


def _percentile_stats(values: pd.Series) -> dict[str, Any]:
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return {"count": 0, "mean": math.nan, "median": math.nan, "p75": math.nan, "p90": math.nan, "p95": math.nan}
    return {
        "count": int(values.shape[0]),
        "mean": round(float(values.mean()), 6),
        "median": round(float(values.median()), 6),
        "p75": round(float(values.quantile(0.75)), 6),
        "p90": round(float(values.quantile(0.90)), 6),
        "p95": round(float(values.quantile(0.95)), 6),
    }


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _mann_whitney_and_effect(lhs: list[float], rhs: list[float]) -> dict[str, Any]:
    if len(lhs) == 0 or len(rhs) == 0:
        return {"p_value": math.nan, "effect_size": math.nan}
    pooled = [(float(value), 0) for value in lhs] + [(float(value), 1) for value in rhs]
    pooled.sort(key=lambda item: item[0])

    ranks = [0.0] * len(pooled)
    tie_sum = 0.0
    idx = 0
    while idx < len(pooled):
        end = idx + 1
        while end < len(pooled) and pooled[end][0] == pooled[idx][0]:
            end += 1
        avg_rank = (idx + 1 + end) / 2.0
        for rank_idx in range(idx, end):
            ranks[rank_idx] = avg_rank
        tie_size = end - idx
        if tie_size > 1:
            tie_sum += tie_size ** 3 - tie_size
        idx = end

    rank_sum_lhs = sum(rank for rank, item in zip(ranks, pooled) if item[1] == 0)
    n1 = len(lhs)
    n2 = len(rhs)
    u1 = rank_sum_lhs - (n1 * (n1 + 1) / 2.0)
    mu = n1 * n2 / 2.0
    n = n1 + n2
    if n <= 1:
        p_value = math.nan
    else:
        tie_adj = tie_sum / (n * (n - 1)) if n > 1 else 0.0
        sigma_sq = (n1 * n2 / 12.0) * ((n + 1) - tie_adj)
        if sigma_sq <= 0:
            p_value = math.nan
        else:
            sigma = math.sqrt(sigma_sq)
            correction = 0.5 if u1 > mu else -0.5 if u1 < mu else 0.0
            z = (u1 - mu - correction) / sigma
            p_value = max(0.0, min(1.0, 2.0 * (1.0 - _norm_cdf(abs(z)))))

    gt = 0
    lt = 0
    for left in lhs:
        for right in rhs:
            if left > right:
                gt += 1
            elif left < right:
                lt += 1
    denom = n1 * n2
    effect = (gt - lt) / denom if denom else math.nan
    return {"p_value": round(p_value, 6) if not math.isnan(p_value) else math.nan, "effect_size": round(effect, 6) if not math.isnan(effect) else math.nan}


def _direction_label(loser_mean: float, winner_mean: float, effect_size: float) -> str:
    if math.isnan(effect_size) or abs(effect_size) < 0.05:
        return "no_clear_difference"
    if loser_mean > winner_mean:
        return "losers_higher"
    if loser_mean < winner_mean:
        return "losers_lower"
    return "no_clear_difference"


def _scenario_family(scenario: str) -> str:
    if str(scenario).startswith("RANGE_COMPRESSION|"):
        return "RANGE_COMPRESSION"
    if str(scenario).startswith("PIVOT_HIGH|"):
        return "PIVOT_HIGH"
    if str(scenario).startswith("LONG_DONCHIAN|"):
        return "LONG_DONCHIAN"
    return "OTHER"


def _sector_bucket(symbol: str) -> str:
    sym = str(symbol).upper()
    if sym in SEMI_SYMBOLS:
        return "semis"
    if sym in SOFTWARE_INTERNET_SYMBOLS:
        return "software/internet"
    if sym in OTHER_TECH_SYMBOLS:
        return "other tech"
    return "other"


def _crowding_proxy(symbol: str) -> bool:
    return str(symbol).upper() in AI_SEMI_LEADERS


def _build_rs_percentile_lookup(symbol_feature_lookup: dict[str, dict[str, dict[str, float]]]) -> dict[str, dict[str, float]]:
    by_date: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for symbol, per_date in symbol_feature_lookup.items():
        for date_key, features in per_date.items():
            value = features.get("ret_20d_pre", math.nan)
            if math.isnan(value):
                continue
            by_date[date_key].append((symbol, float(value)))
    lookup: dict[str, dict[str, float]] = defaultdict(dict)
    for date_key, rows in by_date.items():
        sorted_rows = sorted(rows, key=lambda item: item[1])
        n = len(sorted_rows)
        for idx, (symbol, _) in enumerate(sorted_rows, start=1):
            lookup[date_key][symbol] = idx / n if n else math.nan
    return {date: dict(values) for date, values in lookup.items()}


def _build_reclustered_regime_lookup(base_dir: Path) -> dict[str, dict[str, Any]]:
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
    qld["ret_5d"] = close.pct_change(5)
    qld["ret_20d"] = close.pct_change(20)
    qld["high20"] = close.rolling(20, min_periods=20).max()
    qld["high60"] = close.rolling(60, min_periods=60).max()

    qld["close_prev"] = qld["close"].shift(1)
    for col in ("sma20", "sma50", "sma200", "std5", "std20", "ret_5d", "ret_20d", "high20", "high60"):
        qld[f"{col}_prev"] = qld[col].shift(1)
    qld["sma20_slope5_prev"] = (qld["sma20"].shift(1) - qld["sma20"].shift(6)) / qld["sma20"].shift(6)
    qld["sma50_slope5_prev"] = (qld["sma50"].shift(1) - qld["sma50"].shift(6)) / qld["sma50"].shift(6)
    qld["dd20_prev"] = qld["close_prev"] / qld["high20_prev"] - 1.0
    qld["dd60_prev"] = qld["close_prev"] / qld["high60_prev"] - 1.0

    def classify(row: pd.Series) -> str:
        close_prev = row.get("close_prev")
        sma200_prev = row.get("sma200_prev")
        if pd.isna(close_prev) or pd.isna(sma200_prev) or float(close_prev) <= float(sma200_prev):
            return "risk_off"
        ret5 = float(row.get("ret_5d_prev")) if pd.notna(row.get("ret_5d_prev")) else math.nan
        ret20 = float(row.get("ret_20d_prev")) if pd.notna(row.get("ret_20d_prev")) else math.nan
        vol_ratio = _safe_ratio(row.get("std5_prev"), row.get("std20_prev"))
        slope20 = float(row.get("sma20_slope5_prev")) if pd.notna(row.get("sma20_slope5_prev")) else math.nan
        slope50 = float(row.get("sma50_slope5_prev")) if pd.notna(row.get("sma50_slope5_prev")) else math.nan
        dist20 = _safe_ratio(close_prev, row.get("sma20_prev"))
        dist20 = dist20 - 1.0 if not math.isnan(dist20) else math.nan
        dd20 = float(row.get("dd20_prev")) if pd.notna(row.get("dd20_prev")) else math.nan
        dd60 = float(row.get("dd60_prev")) if pd.notna(row.get("dd60_prev")) else math.nan

        if (not math.isnan(ret20) and abs(ret20) < 0.03) and (not math.isnan(vol_ratio) and vol_ratio > 1.1) and (not math.isnan(slope20) and abs(slope20) < 0.01):
            return "choppy"
        if (not math.isnan(ret20) and ret20 > 0.03) and (not math.isnan(ret5) and ret5 <= 0.0) and (not math.isnan(vol_ratio) and vol_ratio >= 1.05) and (((not math.isnan(dd20)) and dd20 <= -0.03) or ((not math.isnan(dd60)) and dd60 <= -0.05)):
            return "exhaustion"
        if ((not math.isnan(dist20) and dist20 >= 0.08) or (not math.isnan(ret20) and ret20 >= 0.18)) and not ((not math.isnan(ret5) and ret5 <= 0.0) and (not math.isnan(vol_ratio) and vol_ratio >= 1.05)):
            return "extended_trend"
        if (not math.isnan(ret20) and ret20 >= 0.05) and (not math.isnan(slope20) and slope20 > 0.0) and (not math.isnan(slope50) and slope50 > 0.0) and ((math.isnan(dd20)) or dd20 > -0.04):
            return "strong_trend"
        return "early_trend"

    lookup: dict[str, dict[str, Any]] = {}
    for row in qld.itertuples(index=False):
        date_key = pd.Timestamp(row.timestamp).date().isoformat()
        row_series = pd.Series(row._asdict())
        lookup[date_key] = {
            "reclustered_regime": classify(row_series),
            "qld_ret_5d_prev": float(row_series.get("ret_5d_prev")) if pd.notna(row_series.get("ret_5d_prev")) else math.nan,
            "qld_ret_20d_prev": float(row_series.get("ret_20d_prev")) if pd.notna(row_series.get("ret_20d_prev")) else math.nan,
            "qld_vol_ratio_prev": _safe_ratio(row_series.get("std5_prev"), row_series.get("std20_prev")),
            "qld_sma20_slope5_prev": float(row_series.get("sma20_slope5_prev")) if pd.notna(row_series.get("sma20_slope5_prev")) else math.nan,
            "qld_sma50_slope5_prev": float(row_series.get("sma50_slope5_prev")) if pd.notna(row_series.get("sma50_slope5_prev")) else math.nan,
            "qld_dd20_prev": float(row_series.get("dd20_prev")) if pd.notna(row_series.get("dd20_prev")) else math.nan,
            "qld_dd60_prev": float(row_series.get("dd60_prev")) if pd.notna(row_series.get("dd60_prev")) else math.nan,
        }
    return lookup


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


def _signal_to_entry_delay_bars(signal_ts: pd.Timestamp, entry_ts: pd.Timestamp, all_timestamps: list[pd.Timestamp]) -> int:
    index_lookup = {ts: idx for idx, ts in enumerate(all_timestamps)}
    return int(index_lookup.get(entry_ts, 0) - index_lookup.get(signal_ts, 0))


def _build_trade_failure_frame(
    result: dict[str, Any],
    selection_group: str,
    frames: dict[str, pd.DataFrame],
    all_timestamps: list[pd.Timestamp],
    regime_lookup: dict[str, dict[str, Any]],
    reclustered_lookup: dict[str, dict[str, Any]],
    symbol_feature_lookup: dict[str, dict[str, dict[str, float]]],
    rs_percentile_lookup: dict[str, dict[str, float]],
) -> pd.DataFrame:
    scenario = _scenario_name(StructuralConfig(**result["config"]))
    rows: list[dict[str, Any]] = []
    for trade in result["trade_log"]:
        symbol = str(trade["symbol"])
        entry_ts = pd.Timestamp(str(trade["entry_date"]), tz="UTC")
        exit_ts = pd.Timestamp(str(trade["exit_date"]), tz="UTC")
        signal_ts = pd.Timestamp(str(trade["signal_date"]), tz="UTC")
        date_key = str(entry_ts.date())
        market_regime = regime_lookup.get(date_key, {"market_regime_base": "risk_off", "market_regime_detail": "risk_off"})
        reclustered = reclustered_lookup.get(date_key, {"reclustered_regime": "risk_off"})
        feature_row = symbol_feature_lookup.get(symbol, {}).get(date_key, {})
        rs_percentile = rs_percentile_lookup.get(date_key, {}).get(symbol, math.nan)
        entry_price = float(trade["entry_price"])
        breakout_level = float(trade["breakout_level"])
        future_1d = _future_window_metrics(frames[symbol], entry_ts, entry_price, 1)
        future_3d = _future_window_metrics(frames[symbol], entry_ts, entry_price, 3)
        future_5d = _future_window_metrics(frames[symbol], entry_ts, entry_price, 5)
        gap_over_planned = _safe_ratio(trade.get("entry_open"), trade.get("planned_entry_price"))
        gap_over_planned = gap_over_planned - 1.0 if not math.isnan(gap_over_planned) else math.nan
        rows.append(
            {
                "scenario": scenario,
                "selection_group": selection_group,
                "scenario_family": _scenario_family(scenario),
                "symbol": symbol,
                "sector_bucket": _sector_bucket(symbol),
                "crowding_proxy": _crowding_proxy(symbol),
                "entry_date": date_key,
                "exit_date": str(exit_ts.date()),
                "signal_date": str(signal_ts.date()),
                "month_bucket": exit_ts.strftime("%Y-%m"),
                "trade_label": "winner" if float(trade["realized_R"]) > 0 else "loser",
                "realized_R": float(trade["realized_R"]),
                "entry_type": _entry_type_of_trade(trade),
                "breakout_level": breakout_level,
                "entry_price": entry_price,
                "entry_open": float(trade["entry_open"]),
                "planned_entry_price": float(trade["planned_entry_price"]),
                "stop_price": float(trade["stop_price"]),
                "gap_pct": float(trade["gap_pct"]),
                "filled_at_open": bool(trade["filled_at_open"]),
                "holding_days": int(trade["holding_days"]),
                "breakout_level_source": str(trade["breakout_level_source"]),
                "market_regime_base": market_regime["market_regime_base"],
                "market_regime_detail": market_regime["market_regime_detail"],
                "reclustered_regime": reclustered["reclustered_regime"],
                "qld_ret_5d_prev": reclustered.get("qld_ret_5d_prev", math.nan),
                "qld_ret_20d_prev": reclustered.get("qld_ret_20d_prev", math.nan),
                "qld_vol_ratio_prev": reclustered.get("qld_vol_ratio_prev", math.nan),
                "qld_sma20_slope5_prev": reclustered.get("qld_sma20_slope5_prev", math.nan),
                "qld_sma50_slope5_prev": reclustered.get("qld_sma50_slope5_prev", math.nan),
                "qld_dd20_prev": reclustered.get("qld_dd20_prev", math.nan),
                "qld_dd60_prev": reclustered.get("qld_dd60_prev", math.nan),
                "breakout_strength_pct": (entry_price / breakout_level - 1.0) if breakout_level > 0 else math.nan,
                "signal_to_entry_delay_bars": _signal_to_entry_delay_bars(signal_ts, entry_ts, all_timestamps),
                "follow_through_1d_pct": future_1d["follow"],
                "follow_through_3d_pct": future_3d["follow"],
                "follow_through_5d_pct": future_5d["follow"],
                "adverse_excursion_3d_pct": future_3d["adverse"],
                "adverse_excursion_5d_pct": future_5d["adverse"],
                "post_breakout_retrace_3d_pct": future_3d["retrace"],
                "post_breakout_retrace_5d_pct": future_5d["retrace"],
                "validation_day3_next_open_r": _validation_exit_r(frames[symbol], entry_ts, entry_price, float(trade["stop_price"]), 3),
                "validation_day5_next_open_r": _validation_exit_r(frames[symbol], entry_ts, entry_price, float(trade["stop_price"]), 5),
                "rs_percentile_20d": rs_percentile,
                **{column: feature_row.get(column, math.nan) for column in ANATOMY_FEATURE_COLUMNS if column != "gap_over_planned_entry_pct"},
                "gap_over_planned_entry_pct": gap_over_planned,
            }
        )
    return pd.DataFrame(rows)


def _distribution_table(df: pd.DataFrame, features: list[str], *, subset_name: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for scenario in [*sorted(df["scenario"].unique()), "ALL"] if not df.empty else []:
        scoped = df if scenario == "ALL" else df[df["scenario"] == scenario]
        for feature in features:
            stats = _percentile_stats(scoped[feature])
            rows.append({"subset": subset_name, "scenario": scenario, "feature": feature, **stats})
    return pd.DataFrame(rows)


def _winner_loser_comparison_table(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    scopes = [*sorted(df["scenario"].unique()), "ALL"] if not df.empty else []
    for scenario in scopes:
        scoped = df if scenario == "ALL" else df[df["scenario"] == scenario]
        winners = scoped[scoped["trade_label"] == "winner"]
        losers = scoped[scoped["trade_label"] == "loser"]
        for feature in features:
            winner_values = pd.to_numeric(winners[feature], errors="coerce").dropna().tolist()
            loser_values = pd.to_numeric(losers[feature], errors="coerce").dropna().tolist()
            winner_stats = _percentile_stats(pd.Series(winner_values, dtype=float))
            loser_stats = _percentile_stats(pd.Series(loser_values, dtype=float))
            test_stats = _mann_whitney_and_effect(loser_values, winner_values)
            rows.append(
                {
                    "scenario": scenario,
                    "feature": feature,
                    "winner_count": winner_stats["count"],
                    "loser_count": loser_stats["count"],
                    "winner_mean": winner_stats["mean"],
                    "winner_median": winner_stats["median"],
                    "winner_p75": winner_stats["p75"],
                    "winner_p90": winner_stats["p90"],
                    "winner_p95": winner_stats["p95"],
                    "loser_mean": loser_stats["mean"],
                    "loser_median": loser_stats["median"],
                    "loser_p75": loser_stats["p75"],
                    "loser_p90": loser_stats["p90"],
                    "loser_p95": loser_stats["p95"],
                    "mann_whitney_p_value": test_stats["p_value"],
                    "effect_size": test_stats["effect_size"],
                    "direction_label": _direction_label(loser_stats["mean"], winner_stats["mean"], test_stats["effect_size"]),
                }
            )
    return pd.DataFrame(rows)


def _worst_decile_mask(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=bool)
    threshold = df["realized_R"].quantile(0.10)
    return df["realized_R"] <= threshold


def _worst_decile_analysis(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    losers = df[df["trade_label"] == "loser"].copy()
    if losers.empty:
        return pd.DataFrame(), False
    worst_mask = _worst_decile_mask(losers)
    worst = losers[worst_mask].copy()
    other = losers[~worst_mask].copy()
    rows: list[dict[str, Any]] = []
    total_loss = abs(float(losers["realized_R"].sum())) if float(losers["realized_R"].sum()) != 0 else 1.0
    worst_loss = abs(float(worst["realized_R"].sum())) if not worst.empty else 0.0
    rows.append(
        {
            "feature": "__overall__",
            "worst_count": int(len(worst)),
            "other_loser_count": int(len(other)),
            "worst_loss_share": worst_loss / total_loss,
            "tail_event_driven": (worst_loss / total_loss) >= 0.35,
        }
    )
    for feature in [feature for feature in WINNER_LOSER_COMPARE_FEATURES if feature != "rs_percentile_20d"] + ["realized_R"]:
        worst_values = pd.to_numeric(worst[feature], errors="coerce").dropna().tolist()
        other_values = pd.to_numeric(other[feature], errors="coerce").dropna().tolist()
        worst_stats = _percentile_stats(pd.Series(worst_values, dtype=float))
        other_stats = _percentile_stats(pd.Series(other_values, dtype=float))
        test_stats = _mann_whitney_and_effect(worst_values, other_values)
        rows.append(
            {
                "feature": feature,
                "worst_count": worst_stats["count"],
                "other_loser_count": other_stats["count"],
                "worst_mean": worst_stats["mean"],
                "worst_median": worst_stats["median"],
                "worst_p75": worst_stats["p75"],
                "worst_p90": worst_stats["p90"],
                "worst_p95": worst_stats["p95"],
                "other_mean": other_stats["mean"],
                "other_median": other_stats["median"],
                "mann_whitney_p_value": test_stats["p_value"],
                "effect_size": test_stats["effect_size"],
                "direction_label": _direction_label(worst_stats["mean"], other_stats["mean"], test_stats["effect_size"]),
            }
        )
    tail_driven = (worst_loss / total_loss) >= 0.35
    return pd.DataFrame(rows), tail_driven


def _regime_performance_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if df.empty:
        return pd.DataFrame(rows)
    for regime, scoped in df.groupby("reclustered_regime"):
        losers = scoped[scoped["trade_label"] == "loser"]
        rows.append(
            {
                "reclustered_regime": regime,
                "trade_count": int(len(scoped)),
                "win_rate": round(float((scoped["trade_label"] == "winner").mean()), 6),
                "expectancy_r": round(float(scoped["realized_R"].mean()), 6),
                "total_r": round(float(scoped["realized_R"].sum()), 6),
                "average_loss_r": round(float(losers["realized_R"].mean()), 6) if not losers.empty else math.nan,
                "loss_contribution_share": abs(float(losers["realized_R"].sum())) / abs(float(df[df["trade_label"] == "loser"]["realized_R"].sum())) if not losers.empty and float(df[df["trade_label"] == "loser"]["realized_R"].sum()) != 0 else 0.0,
            }
        )
    return pd.DataFrame(rows).sort_values(["expectancy_r", "loss_contribution_share"], ascending=[True, False]).reset_index(drop=True)


def _cross_sectional_concentration(df: pd.DataFrame, worst_mask: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    subsets = {
        "all_trades": df,
        "winners": df[df["trade_label"] == "winner"],
        "losers": df[df["trade_label"] == "loser"],
        "worst_decile": df[worst_mask] if len(worst_mask) == len(df) else df.iloc[0:0],
    }
    for subset_name, subset in subsets.items():
        total_loss = abs(float(subset[subset["realized_R"] < 0]["realized_R"].sum())) if not subset.empty and float(subset[subset["realized_R"] < 0]["realized_R"].sum()) != 0 else 1.0
        for group_col in ("sector_bucket", "symbol", "reclustered_regime", "scenario_family", "crowding_proxy", "month_bucket"):
            if group_col not in subset.columns:
                continue
            grouped = subset.groupby(group_col, as_index=False).agg(trade_count=("realized_R", "size"), total_r=("realized_R", "sum"))
            for record in grouped.to_dict("records"):
                loss_only = subset[subset[group_col] == record[group_col]]
                loss_sum = float(loss_only[loss_only["realized_R"] < 0]["realized_R"].sum()) if not loss_only.empty else 0.0
                rows.append(
                    {
                        "analysis_set": subset_name,
                        "group_type": group_col,
                        "group_value": record[group_col],
                        "trade_count": int(record["trade_count"]),
                        "total_r": round(float(record["total_r"]), 6),
                        "loss_r_sum": round(loss_sum, 6),
                        "loss_share": abs(loss_sum) / total_loss if total_loss else 0.0,
                    }
                )
    return pd.DataFrame(rows)


def _entry_timing_analysis(df: pd.DataFrame, worst_mask: pd.Series) -> pd.DataFrame:
    features = [
        "signal_to_entry_delay_bars",
        "gap_over_planned_entry_pct",
        "breakout_strength_pct",
        "ret_20d_pre",
        "dist_to_sma20_pct",
        "follow_through_1d_pct",
        "follow_through_3d_pct",
        "follow_through_5d_pct",
        "post_breakout_retrace_3d_pct",
        "post_breakout_retrace_5d_pct",
        "adverse_excursion_3d_pct",
        "adverse_excursion_5d_pct",
    ]
    comparison = _winner_loser_comparison_table(df, features)
    comparison.insert(0, "analysis_scope", "winner_vs_loser")
    worst_df = df[worst_mask] if len(worst_mask) == len(df) else df.iloc[0:0]
    other_losers = df[(df["trade_label"] == "loser") & ~worst_mask] if len(worst_mask) == len(df) else df.iloc[0:0]
    rows: list[dict[str, Any]] = []
    for feature in features:
        worst_stats = _percentile_stats(worst_df[feature]) if not worst_df.empty else _percentile_stats(pd.Series(dtype=float))
        other_stats = _percentile_stats(other_losers[feature]) if not other_losers.empty else _percentile_stats(pd.Series(dtype=float))
        test_stats = _mann_whitney_and_effect(
            pd.to_numeric(worst_df[feature], errors="coerce").dropna().tolist() if not worst_df.empty else [],
            pd.to_numeric(other_losers[feature], errors="coerce").dropna().tolist() if not other_losers.empty else [],
        )
        rows.append(
            {
                "analysis_scope": "worst_decile_vs_other_losers",
                "scenario": "ALL",
                "feature": feature,
                "winner_count": 0,
                "loser_count": worst_stats["count"],
                "winner_mean": other_stats["mean"],
                "winner_median": other_stats["median"],
                "winner_p75": other_stats["p75"],
                "winner_p90": other_stats["p90"],
                "winner_p95": other_stats["p95"],
                "loser_mean": worst_stats["mean"],
                "loser_median": worst_stats["median"],
                "loser_p75": worst_stats["p75"],
                "loser_p90": worst_stats["p90"],
                "loser_p95": worst_stats["p95"],
                "mann_whitney_p_value": test_stats["p_value"],
                "effect_size": test_stats["effect_size"],
                "direction_label": _direction_label(worst_stats["mean"], other_stats["mean"], test_stats["effect_size"]),
            }
        )
    return pd.concat([comparison, pd.DataFrame(rows)], ignore_index=True)


REGIME_STATE_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "risk_off": ("QLD below long trend or breadth weak", "low"),
    "true_early_trend": ("Trend turning up but breadth still incomplete", "cautious"),
    "rebound_chop": ("Mixed rebound with unstable breadth and correlation", "low"),
    "failed_recovery": ("Recovery attempt losing momentum", "avoid"),
    "strong_trend": ("Broad and persistent trend confirmation", "high"),
    "extended": ("Trend strong but stretched and leadership concentrated", "medium"),
    "exhaustion": ("Trend mature with slowdown or drawdown from highs", "low"),
}


def _build_universe_state_lookup(frames: dict[str, pd.DataFrame], stocks: list[str]) -> dict[str, dict[str, float]]:
    symbol_rows: list[pd.DataFrame] = []
    returns_by_symbol: dict[str, pd.Series] = {}
    for symbol in stocks:
        frame = frames[symbol].copy()
        close = pd.to_numeric(frame["close"], errors="coerce")
        ret1 = close.pct_change()
        ret20 = close.pct_change(20)
        sma20 = close.rolling(20, min_periods=20).mean()
        sma50 = close.rolling(50, min_periods=50).mean()
        sma200 = close.rolling(200, min_periods=200).mean()
        date_index = pd.to_datetime(frame["timestamp"], utc=True)
        symbol_rows.append(
            pd.DataFrame(
                {
                    "date_key": date_index.dt.date.astype(str),
                    "symbol": symbol,
                    "sector_bucket": _sector_bucket(symbol),
                    "ret20_pre": ret20.shift(1),
                    "above_sma20_pre": (close.shift(1) > sma20.shift(1)).astype(float),
                    "above_sma50_pre": (close.shift(1) > sma50.shift(1)).astype(float),
                    "above_sma200_pre": (close.shift(1) > sma200.shift(1)).astype(float),
                    "positive_20d_pre": (ret20.shift(1) > 0).astype(float),
                }
            )
        )
        returns_by_symbol[symbol] = pd.Series(ret1.values, index=date_index)

    symbol_df = pd.concat(symbol_rows, ignore_index=True) if symbol_rows else pd.DataFrame()
    if symbol_df.empty:
        return {}

    base = (
        symbol_df.groupby("date_key", as_index=False)
        .agg(
            breadth_above_sma20=("above_sma20_pre", "mean"),
            breadth_above_sma50=("above_sma50_pre", "mean"),
            breadth_above_sma200=("above_sma200_pre", "mean"),
            breadth_positive_20d=("positive_20d_pre", "mean"),
            dispersion_20d=("ret20_pre", lambda s: float(pd.to_numeric(s, errors="coerce").std(ddof=0))),
            active_symbol_count=("symbol", "nunique"),
        )
        .sort_values("date_key")
        .reset_index(drop=True)
    )

    sector_grouped = (
        symbol_df.groupby(["date_key", "sector_bucket"], as_index=False)
        .agg(sector_symbol_count=("symbol", "nunique"), sector_positive_20d=("positive_20d_pre", "sum"))
    )
    sector_lookup: dict[tuple[str, str], dict[str, float]] = {}
    for row in sector_grouped.to_dict("records"):
        sector_lookup[(str(row["date_key"]), str(row["sector_bucket"]))] = {
            "sector_symbol_count": float(row["sector_symbol_count"]),
            "sector_positive_20d": float(row["sector_positive_20d"]),
        }

    returns_df = pd.DataFrame(returns_by_symbol).sort_index()
    correlation_rows: list[dict[str, Any]] = []
    if not returns_df.empty:
        for idx in range(len(returns_df)):
            if idx < 20:
                continue
            window = returns_df.iloc[idx - 20 : idx]
            corr = window.corr()
            values: list[float] = []
            for i, lhs in enumerate(corr.columns):
                for rhs in corr.columns[i + 1 :]:
                    value = corr.loc[lhs, rhs]
                    if pd.notna(value):
                        values.append(float(value))
            mean_corr = float(sum(values) / len(values)) if values else math.nan
            date_key = pd.Timestamp(returns_df.index[idx]).date().isoformat()
            correlation_rows.append({"date_key": date_key, "mean_pairwise_corr": mean_corr})
    corr_df = pd.DataFrame(correlation_rows)
    if not corr_df.empty:
        corr_series = pd.to_numeric(corr_df["mean_pairwise_corr"], errors="coerce")
        corr_threshold = float(corr_series.quantile(0.75)) if not corr_series.dropna().empty else math.nan
        corr_df["correlation_spike"] = corr_series >= corr_threshold if not math.isnan(corr_threshold) else False
    else:
        corr_df = pd.DataFrame(columns=["date_key", "mean_pairwise_corr", "correlation_spike"])

    merged = base.merge(corr_df, on="date_key", how="left")
    lookup: dict[str, dict[str, float]] = {}
    for row in merged.to_dict("records"):
        date_key = str(row["date_key"])
        active_count = float(row.get("active_symbol_count") or 0.0) or 1.0
        sector_counts = {
            sector: sector_lookup.get((date_key, sector), {}).get("sector_symbol_count", 0.0)
            for sector in ("semis", "software/internet", "other tech", "other")
        }
        semis_share = sector_counts["semis"] / active_count
        tech_share = (sector_counts["semis"] + sector_counts["software/internet"] + sector_counts["other tech"]) / active_count
        dominance = max(sector_counts.values()) / active_count if sector_counts else 0.0
        lookup[date_key] = {
            "breadth_above_sma20": float(row.get("breadth_above_sma20") or math.nan),
            "breadth_above_sma50": float(row.get("breadth_above_sma50") or math.nan),
            "breadth_above_sma200": float(row.get("breadth_above_sma200") or math.nan),
            "breadth_positive_20d": float(row.get("breadth_positive_20d") or math.nan),
            "dispersion_20d": float(row.get("dispersion_20d") or math.nan),
            "mean_pairwise_corr": float(row.get("mean_pairwise_corr") or math.nan),
            "correlation_spike": bool(row.get("correlation_spike", False)),
            "active_symbol_count": int(active_count),
            "semis_concentration_ratio": float(semis_share),
            "tech_concentration_ratio": float(tech_share),
            "top_sector_dominance_score": float(dominance),
        }
    return lookup


def _build_regime_state_lookup(base_dir: Path, universe_state_lookup: dict[str, dict[str, float]]) -> dict[str, dict[str, Any]]:
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
    qld["ret_5d"] = close.pct_change(5)
    qld["ret_20d"] = close.pct_change(20)
    qld["high20"] = close.rolling(20, min_periods=20).max()
    qld["high60"] = close.rolling(60, min_periods=60).max()

    qld["close_prev"] = qld["close"].shift(1)
    for col in ("sma20", "sma50", "sma200", "std5", "std20", "ret_5d", "ret_20d", "high20", "high60"):
        qld[f"{col}_prev"] = qld[col].shift(1)
    qld["sma20_slope5_prev"] = (qld["sma20"].shift(1) - qld["sma20"].shift(6)) / qld["sma20"].shift(6)
    qld["sma50_slope5_prev"] = (qld["sma50"].shift(1) - qld["sma50"].shift(6)) / qld["sma50"].shift(6)
    qld["dd20_prev"] = qld["close_prev"] / qld["high20_prev"] - 1.0
    qld["dd60_prev"] = qld["close_prev"] / qld["high60_prev"] - 1.0

    def classify(row: pd.Series, state: dict[str, float]) -> str:
        close_prev = row.get("close_prev")
        sma200_prev = row.get("sma200_prev")
        breadth200 = float(state.get("breadth_above_sma200", math.nan))
        if pd.isna(close_prev) or pd.isna(sma200_prev) or float(close_prev) <= float(sma200_prev) or (not math.isnan(breadth200) and breadth200 < 0.35):
            return "risk_off"

        ret5 = float(row.get("ret_5d_prev")) if pd.notna(row.get("ret_5d_prev")) else math.nan
        ret20 = float(row.get("ret_20d_prev")) if pd.notna(row.get("ret_20d_prev")) else math.nan
        vol_ratio = _safe_ratio(row.get("std5_prev"), row.get("std20_prev"))
        slope20 = float(row.get("sma20_slope5_prev")) if pd.notna(row.get("sma20_slope5_prev")) else math.nan
        slope50 = float(row.get("sma50_slope5_prev")) if pd.notna(row.get("sma50_slope5_prev")) else math.nan
        dist20 = _safe_ratio(close_prev, row.get("sma20_prev"))
        dist20 = dist20 - 1.0 if not math.isnan(dist20) else math.nan
        dd20 = float(row.get("dd20_prev")) if pd.notna(row.get("dd20_prev")) else math.nan
        breadth20 = float(state.get("breadth_above_sma20", math.nan))
        breadth50 = float(state.get("breadth_above_sma50", math.nan))
        breadth_pos = float(state.get("breadth_positive_20d", math.nan))
        dominance = float(state.get("top_sector_dominance_score", math.nan))
        corr_spike = bool(state.get("correlation_spike", False))

        if (not math.isnan(ret20) and abs(ret20) < 0.04) and (not math.isnan(vol_ratio) and vol_ratio >= 1.05) and (not math.isnan(breadth20) and breadth20 < 0.60):
            return "rebound_chop"
        if (not math.isnan(ret20) and ret20 > 0.03) and (not math.isnan(ret5) and ret5 <= 0.0) and (((not math.isnan(dd20)) and dd20 <= -0.03) or (not math.isnan(breadth20) and breadth20 < 0.50)):
            return "failed_recovery"
        if (not math.isnan(ret20) and ret20 > 0.06) and (not math.isnan(ret5) and ret5 <= 0.0) and (not math.isnan(vol_ratio) and vol_ratio >= 1.05):
            return "exhaustion"
        if ((not math.isnan(dist20) and dist20 >= 0.08) or (not math.isnan(ret20) and ret20 >= 0.18)) and not ((not math.isnan(ret5) and ret5 <= 0.0) and (not math.isnan(vol_ratio) and vol_ratio >= 1.05)):
            return "extended"
        if (not math.isnan(ret20) and ret20 >= 0.05) and (not math.isnan(slope20) and slope20 > 0.0) and (not math.isnan(slope50) and slope50 > 0.0) and (not math.isnan(breadth50) and breadth50 >= 0.60) and not corr_spike:
            return "strong_trend"
        if (not math.isnan(ret20) and ret20 >= 0.02) and (not math.isnan(slope20) and slope20 > 0.0) and ((math.isnan(breadth20)) or breadth20 >= 0.45) and ((math.isnan(breadth50)) or breadth50 < 0.60 or (not math.isnan(dominance) and dominance >= 0.30)):
            return "true_early_trend"
        return "rebound_chop"

    lookup: dict[str, dict[str, Any]] = {}
    for row in qld.itertuples(index=False):
        date_key = pd.Timestamp(row.timestamp).date().isoformat()
        row_series = pd.Series(row._asdict())
        state = universe_state_lookup.get(date_key, {})
        label = classify(row_series, state)
        lookup[date_key] = {
            "regime_state": label,
            "qld_ret_5d_prev": float(row_series.get("ret_5d_prev")) if pd.notna(row_series.get("ret_5d_prev")) else math.nan,
            "qld_ret_20d_prev": float(row_series.get("ret_20d_prev")) if pd.notna(row_series.get("ret_20d_prev")) else math.nan,
            "qld_vol_ratio_prev": _safe_ratio(row_series.get("std5_prev"), row_series.get("std20_prev")),
            "qld_sma20_slope5_prev": float(row_series.get("sma20_slope5_prev")) if pd.notna(row_series.get("sma20_slope5_prev")) else math.nan,
            "qld_sma50_slope5_prev": float(row_series.get("sma50_slope5_prev")) if pd.notna(row_series.get("sma50_slope5_prev")) else math.nan,
            "qld_dd20_prev": float(row_series.get("dd20_prev")) if pd.notna(row_series.get("dd20_prev")) else math.nan,
            "qld_dd60_prev": float(row_series.get("dd60_prev")) if pd.notna(row_series.get("dd60_prev")) else math.nan,
            **state,
        }
    return lookup


def _validation_exit_r(frame: pd.DataFrame, entry_ts: pd.Timestamp, entry_price: float, stop_price: float, horizon: int) -> float:
    if entry_ts not in frame.index or entry_price <= 0 or stop_price >= entry_price:
        return math.nan
    try:
        loc = int(frame.index.get_loc(entry_ts))
    except TypeError:
        return math.nan
    action_loc = loc + horizon
    if action_loc >= len(frame):
        return math.nan
    exit_open = pd.to_numeric(frame.iloc[action_loc]["open"], errors="coerce")
    if pd.isna(exit_open):
        return math.nan
    initial_r = entry_price - stop_price
    if initial_r <= 0:
        return math.nan
    return float((float(exit_open) - entry_price) / initial_r)


def _apply_outcome_groups(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    bottom_cut = float(out["realized_R"].quantile(0.30))
    top_cut = float(out["realized_R"].quantile(0.70))
    out["outcome_group"] = "neutral_mid40"
    out.loc[out["realized_R"] <= bottom_cut, "outcome_group"] = "loser_bottom30"
    out.loc[out["realized_R"] >= top_cut, "outcome_group"] = "winner_top30"
    worst_cut = float(out["realized_R"].quantile(0.10))
    best_cut = float(out["realized_R"].quantile(0.90))
    out["is_worst_decile"] = out["realized_R"] <= worst_cut
    out["is_best_decile"] = out["realized_R"] >= best_cut
    out["trade_label"] = out["outcome_group"].map(
        {"winner_top30": "winner", "neutral_mid40": "neutral", "loser_bottom30": "loser"}
    ).fillna("neutral")
    return out


def _band_from_quantiles(value: float, q_low: float, q_high: float, *, lower_is_bad: bool) -> str:
    if math.isnan(value):
        return "unknown"
    if lower_is_bad:
        if value <= q_low:
            return "weak"
        if value >= q_high:
            return "strong"
        return "mixed"
    if value >= q_high:
        return "high"
    if value <= q_low:
        return "low"
    return "mid"


def _apply_post_entry_bands(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    ft3_low, ft3_high = out["follow_through_3d_pct"].quantile([0.35, 0.65]).tolist()
    retrace3_low, retrace3_high = out["post_breakout_retrace_3d_pct"].quantile([0.35, 0.65]).tolist()
    mae3_low, mae3_high = out["adverse_excursion_3d_pct"].quantile([0.35, 0.65]).tolist()
    out["ft_3d_band"] = out["follow_through_3d_pct"].apply(lambda v: _band_from_quantiles(float(v) if pd.notna(v) else math.nan, ft3_low, ft3_high, lower_is_bad=True))
    out["retrace_3d_band"] = out["post_breakout_retrace_3d_pct"].apply(lambda v: _band_from_quantiles(float(v) if pd.notna(v) else math.nan, retrace3_low, retrace3_high, lower_is_bad=False))
    out["mae_3d_band"] = out["adverse_excursion_3d_pct"].apply(lambda v: _band_from_quantiles(abs(float(v)) if pd.notna(v) else math.nan, abs(mae3_low), abs(mae3_high), lower_is_bad=False))
    return out


def _outcome_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    grouped = (
        df.groupby("outcome_group", as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            mean_realized_r=("realized_R", "mean"),
            median_realized_r=("realized_R", "median"),
            total_r=("realized_R", "sum"),
            win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
        )
        .sort_values("mean_realized_r")
        .reset_index(drop=True)
    )
    return grouped


def _regime_state_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for regime, scoped in df.groupby("regime_state"):
        desc, suit = REGIME_STATE_DESCRIPTIONS.get(regime, ("", ""))
        rows.append(
            {
                "regime": regime,
                "description": desc,
                "trade_suitability": suit,
                "trade_count": int(len(scoped)),
                "win_rate": round(float((scoped["realized_R"] > 0).mean()), 6),
                "expectancy_r": round(float(scoped["realized_R"].mean()), 6),
                "contribution_r": round(float(scoped["realized_R"].sum()), 6),
                "avg_follow_through_3d_pct": round(float(pd.to_numeric(scoped["follow_through_3d_pct"], errors="coerce").mean()), 6),
                "avg_follow_through_5d_pct": round(float(pd.to_numeric(scoped["follow_through_5d_pct"], errors="coerce").mean()), 6),
                "winner_top30_share": round(float((scoped["outcome_group"] == "winner_top30").mean()), 6),
                "loser_bottom30_share": round(float((scoped["outcome_group"] == "loser_bottom30").mean()), 6),
            }
        )
    out = pd.DataFrame(rows).sort_values(["expectancy_r", "loser_bottom30_share"], ascending=[True, False]).reset_index(drop=True)
    if not out.empty:
        best_regime = str(out.sort_values(["expectancy_r", "winner_top30_share"], ascending=[False, False]).iloc[0]["regime"])
        worst_regime = str(out.iloc[0]["regime"])
        out["regime_role"] = out["regime"].map(lambda r: "best" if r == best_regime else ("worst" if r == worst_regime else "ambiguous"))
    return out


def _regime_sector_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    matrix_sector = df["sector_bucket"].map(lambda v: "tech" if str(v) in {"software/internet", "other tech"} else v)
    scoped = df.assign(matrix_sector=matrix_sector)
    grouped = (
        scoped.groupby(["regime_state", "matrix_sector"], as_index=False)
        .agg(
            trade_count=("realized_R", "size"),
            expectancy_r=("realized_R", "mean"),
            win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())),
            total_r=("realized_R", "sum"),
        )
        .sort_values(["regime_state", "matrix_sector"])
        .reset_index(drop=True)
    )
    return grouped


def _cross_sectional_predictive_layer(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for outcome_group, scoped in df.groupby("outcome_group"):
        sector_summary = (
            scoped.groupby("sector_bucket", as_index=False)
            .agg(trade_count=("realized_R", "size"), total_r=("realized_R", "sum"), win_rate=("realized_R", lambda s: float((pd.to_numeric(s, errors="coerce") > 0).mean())))
        )
        for record in sector_summary.to_dict("records"):
            rows.append({"analysis_group": outcome_group, "metric_group": "sector_summary", **record})
        rows.append(
            {
                "analysis_group": outcome_group,
                "metric_group": "cross_section_summary",
                "sector_bucket": "ALL",
                "trade_count": int(len(scoped)),
                "total_r": round(float(scoped["realized_R"].sum()), 6),
                "win_rate": round(float((scoped["realized_R"] > 0).mean()), 6),
                "avg_rs_percentile_20d": round(float(pd.to_numeric(scoped["rs_percentile_20d"], errors="coerce").mean()), 6),
                "crowding_rate": round(float(pd.Series(scoped["crowding_proxy"]).astype(bool).mean()), 6),
                "avg_semis_concentration_ratio": round(float(pd.to_numeric(scoped["semis_concentration_ratio"], errors="coerce").mean()), 6),
                "avg_top_sector_dominance_score": round(float(pd.to_numeric(scoped["top_sector_dominance_score"], errors="coerce").mean()), 6),
                "avg_mean_pairwise_corr": round(float(pd.to_numeric(scoped["mean_pairwise_corr"], errors="coerce").mean()), 6),
            }
        )
    return pd.DataFrame(rows)


def _drawdown_proxy(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    cumulative = pd.to_numeric(series, errors="coerce").fillna(0.0).cumsum()
    running_max = cumulative.cummax()
    drawdown = cumulative - running_max
    return float(drawdown.min())


def _filtered_metrics(df: pd.DataFrame, column: str = "realized_R") -> dict[str, float]:
    if df.empty:
        return {"trade_count": 0, "expectancy_r": math.nan, "win_rate": math.nan, "total_r": 0.0, "drawdown_proxy": 0.0}
    values = pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    return {
        "trade_count": int(len(values)),
        "expectancy_r": float(values.mean()) if not values.empty else math.nan,
        "win_rate": float((values > 0).mean()) if not values.empty else math.nan,
        "total_r": float(values.sum()) if not values.empty else 0.0,
        "drawdown_proxy": _drawdown_proxy(values),
    }


def _build_post_entry_validation(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    baseline = _filtered_metrics(df)
    rules = [
        ("weak_ft_high_retrace", (df["ft_3d_band"] == "weak") & (df["retrace_3d_band"] == "high"), "exit_next_open_day3", "validation_day3_next_open_r"),
        ("weak_ft_crowded_bad_regime", (df["ft_3d_band"] == "weak") & (df["crowding_proxy"]) & (df["regime_state"].isin({"true_early_trend", "failed_recovery", "rebound_chop"})), "exit_next_open_day3", "validation_day3_next_open_r"),
        ("mixed_ft_high_mae", (df["ft_3d_band"] == "mixed") & (df["mae_3d_band"] == "high"), "reduce_next_open_day3", "validation_day3_next_open_r"),
        ("weak_ft5_or_high_retrace5", ((pd.to_numeric(df["follow_through_5d_pct"], errors="coerce") <= pd.to_numeric(df["follow_through_5d_pct"], errors="coerce").quantile(0.35)) | (pd.to_numeric(df["post_breakout_retrace_5d_pct"], errors="coerce") >= pd.to_numeric(df["post_breakout_retrace_5d_pct"], errors="coerce").quantile(0.65))), "exit_next_open_day5", "validation_day5_next_open_r"),
    ]
    rows: list[dict[str, Any]] = []
    for condition_name, mask, action, alt_col in rules:
        scoped = df.copy()
        alt_values = pd.to_numeric(scoped[alt_col], errors="coerce")
        realized = pd.to_numeric(scoped["realized_R"], errors="coerce").copy()
        triggered = mask.fillna(False)
        if action.startswith("exit"):
            realized.loc[triggered & alt_values.notna()] = alt_values.loc[triggered & alt_values.notna()]
        elif action.startswith("reduce"):
            replacement = 0.5 * realized.loc[triggered]
            replacement.loc[alt_values.loc[triggered].notna()] = 0.5 * realized.loc[triggered & alt_values.notna()] + 0.5 * alt_values.loc[triggered & alt_values.notna()]
            realized.loc[triggered] = replacement
        scoped["validation_realized_r"] = realized
        filtered = _filtered_metrics(scoped, column="validation_realized_r")
        rows.append(
            {
                "condition": condition_name,
                "action": action,
                "trigger_count": int(triggered.sum()),
                "trade_count": filtered["trade_count"],
                "expectancy_r": round(filtered["expectancy_r"], 6) if not math.isnan(filtered["expectancy_r"]) else math.nan,
                "win_rate": round(filtered["win_rate"], 6) if not math.isnan(filtered["win_rate"]) else math.nan,
                "total_r": round(filtered["total_r"], 6),
                "drawdown_proxy": round(filtered["drawdown_proxy"], 6),
                "expectancy_delta": round(filtered["expectancy_r"] - baseline["expectancy_r"], 6) if not math.isnan(filtered["expectancy_r"]) and not math.isnan(baseline["expectancy_r"]) else math.nan,
                "drawdown_delta": round(filtered["drawdown_proxy"] - baseline["drawdown_proxy"], 6),
            }
        )
    return pd.DataFrame(rows)


def _rule_robustness(mask: pd.Series, df: pd.DataFrame, baseline_expectancy: float) -> str:
    if df.empty or mask.sum() == 0:
        return "low"
    sign_hits = 0
    slices = 0
    for _, scoped in df.groupby("scenario"):
        if len(scoped) < 3:
            continue
        slices += 1
        kept = scoped[~mask.loc[scoped.index]]
        if kept.empty:
            continue
        if float(pd.to_numeric(kept["realized_R"], errors="coerce").mean()) >= baseline_expectancy:
            sign_hits += 1
    month_periods = sorted(df["entry_date"].apply(lambda s: str(s)[:7]).unique().tolist())
    for month in month_periods:
        scoped = df[df["entry_date"].astype(str).str.startswith(month)]
        if len(scoped) < 3:
            continue
        slices += 1
        kept = scoped[~mask.loc[scoped.index]]
        if kept.empty:
            continue
        if float(pd.to_numeric(kept["realized_R"], errors="coerce").mean()) >= baseline_expectancy:
            sign_hits += 1
    if slices == 0:
        return "low"
    ratio = sign_hits / slices
    if ratio >= 0.70:
        return "high"
    if ratio >= 0.50:
        return "medium"
    return "low"


def _build_rule_candidates(df: pd.DataFrame, validation_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    for column, default in {
        "dist_to_sma20_pct": 0.0,
        "semis_concentration_ratio": 0.0,
        "rs_percentile_20d": 0.5,
        "vol_expansion_ratio": 1.0,
        "breakout_strength_pct": 0.0,
        "crowding_proxy": False,
        "sector_bucket": "other",
        "regime_state": "risk_off",
    }.items():
        if column not in df.columns:
            df[column] = default
    baseline = _filtered_metrics(df)
    semis_high = float(pd.to_numeric(df["semis_concentration_ratio"], errors="coerce").quantile(0.70))
    rs_high = float(pd.to_numeric(df["rs_percentile_20d"], errors="coerce").quantile(0.70))
    dist_high = float(pd.to_numeric(df["dist_to_sma20_pct"], errors="coerce").quantile(0.70))
    rules: list[tuple[str, pd.Series, str]] = [
        (
            "block",
            (df["regime_state"].isin({"true_early_trend", "failed_recovery"}))
            & (df["sector_bucket"].isin({"semis", "software/internet"}))
            & (df["crowding_proxy"] | (pd.to_numeric(df["rs_percentile_20d"], errors="coerce") >= rs_high)),
            "if regime in {true_early_trend, failed_recovery} and sector in {semis, software/internet} and (crowding_proxy or rs_percentile_20d in high band): block",
        ),
        (
            "block",
            (df["regime_state"] == "rebound_chop")
            & (pd.to_numeric(df["vol_expansion_ratio"], errors="coerce") >= pd.to_numeric(df["vol_expansion_ratio"], errors="coerce").quantile(0.70))
            & (pd.to_numeric(df["breakout_strength_pct"], errors="coerce") <= pd.to_numeric(df["breakout_strength_pct"], errors="coerce").quantile(0.35)),
            "if regime == rebound_chop and vol_expansion_ratio in high band and breakout_strength_pct in weak band: block",
        ),
        (
            "allow",
            (df["regime_state"].isin({"strong_trend", "extended", "risk_off"}))
            & (~df["crowding_proxy"])
            & (pd.to_numeric(df["dist_to_sma20_pct"], errors="coerce") <= dist_high)
            & (pd.to_numeric(df["semis_concentration_ratio"], errors="coerce") < semis_high),
            "if regime in {strong_trend, extended, risk_off} and not crowded and entry extension band <= mid and semis concentration < high: allow",
        ),
        (
            "size",
            (df["regime_state"].isin({"true_early_trend", "extended"}))
            & ((pd.to_numeric(df["semis_concentration_ratio"], errors="coerce") >= semis_high) | df["crowding_proxy"]),
            "if regime in {true_early_trend, extended} and (semis concentration high or crowded): reduce size",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for rule_type, mask, logic in rules:
        if rule_type == "allow":
            scoped = df[mask.fillna(False)].copy()
        elif rule_type == "size":
            scoped = df.copy()
            scaled = pd.to_numeric(scoped["realized_R"], errors="coerce").copy()
            scaled.loc[mask.fillna(False)] = scaled.loc[mask.fillna(False)] * 0.5
            scoped["rule_realized_r"] = scaled
        else:
            scoped = df[~mask.fillna(False)].copy()
        metrics = _filtered_metrics(scoped, column="rule_realized_r" if "rule_realized_r" in scoped.columns else "realized_R")
        rows.append(
            {
                "rule_type": rule_type,
                "rule_logic": logic,
                "trigger_count": int(mask.fillna(False).sum()),
                "trade_count": metrics["trade_count"],
                "expectancy_r": round(metrics["expectancy_r"], 6) if not math.isnan(metrics["expectancy_r"]) else math.nan,
                "win_rate": round(metrics["win_rate"], 6) if not math.isnan(metrics["win_rate"]) else math.nan,
                "total_r": round(metrics["total_r"], 6),
                "drawdown_proxy": round(metrics["drawdown_proxy"], 6),
                "expectancy_delta": round(metrics["expectancy_r"] - baseline["expectancy_r"], 6) if not math.isnan(metrics["expectancy_r"]) and not math.isnan(baseline["expectancy_r"]) else math.nan,
                "drawdown_delta": round(metrics["drawdown_proxy"] - baseline["drawdown_proxy"], 6),
                "robustness_level": _rule_robustness(mask.fillna(False), df, baseline["expectancy_r"]),
            }
        )
    if not validation_df.empty:
        for record in validation_df.to_dict("records"):
            rows.append(
                {
                    "rule_type": "exit" if str(record["action"]).startswith("exit") else "size",
                    "rule_logic": f"if {record['condition']} then {record['action']}",
                    "trigger_count": int(record["trigger_count"]),
                    "trade_count": int(record["trade_count"]),
                    "expectancy_r": record["expectancy_r"],
                    "win_rate": record["win_rate"],
                    "total_r": record["total_r"],
                    "drawdown_proxy": record["drawdown_proxy"],
                    "expectancy_delta": record["expectancy_delta"],
                    "drawdown_delta": record["drawdown_delta"],
                    "robustness_level": "medium" if int(record["trigger_count"]) >= 5 else "low",
                }
            )
    return pd.DataFrame(rows)


def _feature_reduction(df: pd.DataFrame, comparison_df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or comparison_df.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    compare_all = comparison_df[(comparison_df["scenario"] == "ALL") & (comparison_df["analysis_scope"] == "winner_vs_loser")].copy()
    for _, row in compare_all.iterrows():
        feature = str(row["feature"])
        if feature == "signal_to_entry_delay_bars":
            continue
        scenario_effects: list[float] = []
        for scenario in sorted(df["scenario"].unique()):
            scoped = comparison_df[(comparison_df["scenario"] == scenario) & (comparison_df["feature"] == feature)]
            if scoped.empty or pd.isna(scoped.iloc[0]["effect_size"]):
                continue
            scenario_effects.append(abs(float(scoped.iloc[0]["effect_size"])))
        stability = float(sum(1 for effect in scenario_effects if effect >= 0.10) / len(scenario_effects)) if scenario_effects else 0.0
        importance = abs(float(row["effect_size"])) if pd.notna(row["effect_size"]) else 0.0
        rows.append({"feature": feature, "importance": round(importance, 6), "stability": round(stability, 6)})
    categorical_rows = [
        ("regime_state", df.groupby("regime_state")["realized_R"].mean()),
        ("sector_bucket", df.groupby("sector_bucket")["realized_R"].mean()),
        ("crowding_proxy", df.groupby("crowding_proxy")["realized_R"].mean()),
    ]
    for feature, series in categorical_rows:
        if series.empty:
            continue
        importance = float(series.max() - series.min()) if len(series) > 1 else 0.0
        stability = float((series > 0).mean()) if len(series) > 0 else 0.0
        rows.append({"feature": feature, "importance": round(abs(importance), 6), "stability": round(stability, 6)})
    out = pd.DataFrame(rows).sort_values(["importance", "stability"], ascending=[False, False]).reset_index(drop=True)
    top_features = set(out.head(5)["feature"].tolist())
    out["keep_flag"] = out["feature"].isin(top_features)
    return out


def _final_decision_system(rule_candidates_df: pd.DataFrame, feature_reduction_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    top_features = feature_reduction_df[feature_reduction_df["keep_flag"]].head(5)["feature"].tolist() if not feature_reduction_df.empty else []
    for rule_type in ("block", "allow", "size", "exit"):
        scoped = rule_candidates_df[rule_candidates_df["rule_type"] == rule_type].copy() if not rule_candidates_df.empty else pd.DataFrame()
        if scoped.empty:
            continue
        scoped = scoped.sort_values(["robustness_level", "expectancy_delta"], ascending=[False, False])
        best = scoped.iloc[0]
        rows.append(
            {
                "type": rule_type.capitalize(),
                "rule": best["rule_logic"],
                "robustness_level": best["robustness_level"],
                "expectancy_delta": best["expectancy_delta"],
                "drawdown_delta": best["drawdown_delta"],
                "key_features": ", ".join(top_features[:3]),
            }
        )
    rows.append(
        {
            "type": "System Flow",
            "rule": "Pre-entry: regime/cross-section gate -> Entry: allow/size -> Post-entry: day3/day5 validation -> Exit/Reduce next open",
            "robustness_level": "",
            "expectancy_delta": math.nan,
            "drawdown_delta": math.nan,
            "key_features": ", ".join(top_features),
        }
    )
    return pd.DataFrame(rows)


def _same_bar_comparison(
    cfg: StructuralConfig,
    *,
    base_dir: Path,
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
    stocks: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for mode in ("ALLOW_SAME_BAR_STOP", "DISABLE_ENTRY_BAR_STOP"):
        alt_cfg = StructuralConfig(**{**cfg.__dict__, "entry_bar_stop_mode": mode})
        result = run_structural_backtest(
            alt_cfg,
            base_dir,
            preloaded_frames=frames,
            preloaded_timestamps=timestamps,
            preloaded_symbols=stocks,
        )
        rows.append(
            {
                "scenario": _scenario_name(alt_cfg),
                "entry_bar_stop_mode": mode,
                "cagr_pct": result["metrics"]["cagr_pct"],
                "sharpe": result["metrics"]["sharpe"],
                "expectancy_r": result["metrics"]["expectancy_r"],
                "trade_count": result["metrics"]["trade_count"],
                "total_return_pct": result["metrics"]["total_return_pct"],
                "fill_at_open_ratio": result["diagnostics"]["fill_at_open_ratio"],
                "rejected_by_gap_over_entry_ratio_vs_triggered": result["diagnostics"]["rejected_by_gap_over_entry_ratio_vs_triggered"],
            }
        )
    return pd.DataFrame(rows)


def _run_exclusion(
    cfg: StructuralConfig,
    excluded_symbol: str,
    *,
    base_dir: Path,
    frames: dict[str, pd.DataFrame],
    timestamps: list[pd.Timestamp],
    stocks: list[str],
) -> dict[str, Any]:
    symbols = [symbol for symbol in stocks if symbol != excluded_symbol]
    result = run_structural_backtest(
        cfg,
        base_dir,
        preloaded_frames=frames,
        preloaded_timestamps=timestamps,
        preloaded_symbols=symbols,
    )
    return {
        "excluded_symbol": excluded_symbol,
        "cagr_pct": result["metrics"]["cagr_pct"],
        "sharpe": result["metrics"]["sharpe"],
        "expectancy_r": result["metrics"]["expectancy_r"],
        "trade_count": result["metrics"]["trade_count"],
        "total_return_pct": result["metrics"]["total_return_pct"],
    }


def _neighbor_rows(df: pd.DataFrame, cfg: StructuralConfig) -> pd.DataFrame:
    candidates = df[
        (df["family"] == cfg.structure_mode)
        & (df["trigger_mode_cfg"] == cfg.breakout_trigger_mode)
        & (df["entry_model_cfg"] == cfg.entry_model)
        & (df["stop_mode_cfg"] == cfg.stop_mode)
        & (df["entry_bar_stop_mode_cfg"] == cfg.entry_bar_stop_mode)
        & (df["min_avg_dollar_volume_20_cfg"] == cfg.min_avg_dollar_volume_20)
    ].copy()
    if candidates.empty:
        return candidates

    def diff_count(row: pd.Series) -> int:
        diffs = 0
        diffs += 0 if float(row["atr_multiplier_cfg"]) == float(cfg.atr_multiplier) else 1
        diffs += 0 if int(row["max_holding_days_cfg"]) == int(cfg.max_holding_days) else 1
        if cfg.structure_mode == "RANGE_COMPRESSION":
            diffs += 0 if int(row["range_lookback_cfg"]) == int(cfg.range_lookback) else 1
            diffs += 0 if math.isclose(float(row["max_range_width_pct_cfg"]), float(cfg.max_range_width_pct), rel_tol=0.0, abs_tol=1e-9) else 1
        elif cfg.structure_mode == "LONG_DONCHIAN":
            diffs += 0 if int(row["donchian_n_cfg"]) == int(cfg.donchian_n) else 1
        elif cfg.structure_mode == "PIVOT_HIGH":
            diffs += 0 if int(row["max_pivot_age_cfg"]) == int(cfg.max_pivot_age) else 1
        return diffs

    candidates["param_diff_count"] = candidates.apply(diff_count, axis=1)
    return candidates[(candidates["scenario"] != _scenario_name(cfg)) & (candidates["param_diff_count"] == 1)].copy()


def _returns_from_result(result: dict[str, Any]) -> list[float]:
    return [float(trade["realized_R"]) for trade in result["trade_log"]]


def _sample_skew(values: list[float]) -> float:
    n = len(values)
    if n < 3:
        return 0.0
    mean = statistics.fmean(values)
    m2 = statistics.fmean((x - mean) ** 2 for x in values)
    if m2 <= 0:
        return 0.0
    m3 = statistics.fmean((x - mean) ** 3 for x in values)
    return float(m3 / (m2 ** 1.5))


def _sample_kurtosis(values: list[float]) -> float:
    n = len(values)
    if n < 4:
        return 3.0
    mean = statistics.fmean(values)
    m2 = statistics.fmean((x - mean) ** 2 for x in values)
    if m2 <= 0:
        return 3.0
    m4 = statistics.fmean((x - mean) ** 4 for x in values)
    return float(m4 / (m2 ** 2))


def _sharpe_reliability(
    raw_sharpe: float,
    sample_returns: list[float],
    trial_sharpes: list[float],
    effective_trial_count: int,
) -> dict[str, Any]:
    if len(sample_returns) < 8 or effective_trial_count < 2 or len(trial_sharpes) < 2:
        return {
            "effective_trial_count": effective_trial_count,
            "raw_sharpe": raw_sharpe,
            "trial_count_adjusted_sharpe": math.nan,
            "dsr": math.nan,
            "confidence_label": "insufficient",
            "confidence_commentary": "insufficient sample or trial universe",
        }

    trial_std = statistics.stdev(trial_sharpes) if len(trial_sharpes) > 1 else 0.0
    if trial_std <= 0:
        return {
            "effective_trial_count": effective_trial_count,
            "raw_sharpe": raw_sharpe,
            "trial_count_adjusted_sharpe": raw_sharpe,
            "dsr": math.nan,
            "confidence_label": "insufficient",
            "confidence_commentary": "trial sharpe dispersion is zero",
        }

    nd = NormalDist()
    z1 = nd.inv_cdf(max(min(1.0 - 1.0 / effective_trial_count, 0.999999), 0.000001))
    z2 = nd.inv_cdf(max(min(1.0 - 1.0 / (effective_trial_count * math.e), 0.999999), 0.000001))
    sr_star = trial_std * (((1.0 - 0.5772156649) * z1) + (0.5772156649 * z2))
    adjusted_sharpe = raw_sharpe - sr_star

    skew = _sample_skew(sample_returns)
    kurt = _sample_kurtosis(sample_returns)
    denominator = 1.0 - skew * raw_sharpe + ((kurt - 1.0) / 4.0) * (raw_sharpe ** 2)
    if denominator <= 0:
        dsr = math.nan
    else:
        z = ((raw_sharpe - sr_star) * math.sqrt(max(len(sample_returns) - 1, 1))) / math.sqrt(denominator)
        dsr = nd.cdf(z)

    if math.isnan(dsr):
        label = "insufficient"
        comment = "dsr unavailable; use adjusted sharpe cautiously"
    elif dsr >= 0.95:
        label = "high"
        comment = "selection-adjusted sharpe remains strong"
    elif dsr >= 0.80:
        label = "medium"
        comment = "selection-adjusted confidence is moderate"
    else:
        label = "low"
        comment = "selection-adjusted confidence is weak"

    return {
        "effective_trial_count": effective_trial_count,
        "raw_sharpe": round(raw_sharpe, 6),
        "trial_count_adjusted_sharpe": round(adjusted_sharpe, 6),
        "dsr": round(dsr, 6) if not math.isnan(dsr) else math.nan,
        "confidence_label": label,
        "confidence_commentary": comment,
    }


def _month_start(ts: pd.Timestamp) -> pd.Timestamp:
    base = pd.Timestamp(ts).tz_convert("UTC") if pd.Timestamp(ts).tzinfo is not None else pd.Timestamp(ts, tz="UTC")
    return pd.Timestamp(year=base.year, month=base.month, day=1, tz="UTC")


def _month_end(ts: pd.Timestamp) -> pd.Timestamp:
    start = _month_start(ts)
    return (start + pd.offsets.MonthEnd(0)).tz_convert("UTC") if hasattr(start + pd.offsets.MonthEnd(0), "tz_convert") else pd.Timestamp(start + pd.offsets.MonthEnd(0), tz="UTC")


def _anchored_oos_window(latest_end: pd.Timestamp) -> OOSWindow:
    test_start = pd.Timestamp(TEST_START_DATE, tz="UTC")
    test_end = pd.Timestamp(latest_end).tz_convert("UTC") if pd.Timestamp(latest_end).tzinfo is not None else pd.Timestamp(latest_end, tz="UTC")
    train_end = pd.Timestamp(TRAIN_END_DATE, tz="UTC")
    return OOSWindow(
        name="anchored_oos",
        train_start=pd.Timestamp("1900-01-01", tz="UTC"),
        train_end=train_end,
        test_start=test_start,
        test_end=test_end,
    )


def _walk_forward_windows(earliest_ts: pd.Timestamp, latest_end: pd.Timestamp) -> list[OOSWindow]:
    windows: list[OOSWindow] = []
    earliest_month = _month_start(earliest_ts)
    latest_month = _month_start(latest_end)
    fold_idx = 0
    train_end_month = earliest_month + pd.DateOffset(months=WALK_FORWARD_MIN_TRAIN_MONTHS - 1)
    while True:
        test_start = train_end_month + pd.DateOffset(months=1)
        test_end_month = test_start + pd.DateOffset(months=TEST_MONTHS - 1)
        if test_end_month > latest_month:
            break
        windows.append(
            OOSWindow(
                name=f"walk_forward_{fold_idx:02d}",
                train_start=earliest_month,
                train_end=_month_end(train_end_month),
                test_start=_month_start(test_start),
                test_end=_month_end(test_end_month),
            )
        )
        train_end_month = train_end_month + pd.DateOffset(months=TEST_MONTHS)
        fold_idx += 1
    return windows


def _rolling_oos_windows(earliest_ts: pd.Timestamp, latest_end: pd.Timestamp) -> list[OOSWindow]:
    windows: list[OOSWindow] = []
    earliest_month = _month_start(earliest_ts)
    latest_month = _month_start(latest_end)
    fold_idx = 0
    test_start = earliest_month + pd.DateOffset(months=ROLLING_TRAIN_MONTHS)
    while True:
        test_end_month = test_start + pd.DateOffset(months=TEST_MONTHS - 1)
        if test_end_month > latest_month:
            break
        train_end_month = test_start - pd.DateOffset(months=1)
        train_start_month = test_start - pd.DateOffset(months=ROLLING_TRAIN_MONTHS)
        windows.append(
            OOSWindow(
                name=f"rolling_oos_{fold_idx:02d}",
                train_start=_month_start(train_start_month),
                train_end=_month_end(train_end_month),
                test_start=_month_start(test_start),
                test_end=_month_end(test_end_month),
            )
        )
        test_start = test_start + pd.DateOffset(months=1)
        fold_idx += 1
    return windows


def _test_result_rows(
    label: str,
    windows: list[OOSWindow],
    full_result_by_scenario: dict[str, dict[str, Any]],
    scenario_groups: dict[str, str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for window in windows:
        for scenario, result in full_result_by_scenario.items():
            metrics = _window_metrics_from_trade_subset(result["trade_log"], window.test_start, window.test_end)
            rows.append(
                {
                    "evaluation_type": label,
                    "window_name": window.name,
                    "scenario": scenario,
                    "selection_group": scenario_groups.get(scenario, ""),
                    "train_start": str(window.train_start.date()),
                    "train_end": str(window.train_end.date()),
                    "test_start": str(window.test_start.date()),
                    "test_end": str(window.test_end.date()),
                    "cagr_pct": metrics["cagr_pct"],
                    "sharpe": metrics["sharpe"],
                    "expectancy_r": metrics["expectancy_r"],
                    "trade_count": metrics["trade_count"],
                    "win_rate": metrics["win_rate"],
                    "total_return_pct": metrics["total_return_pct"],
                }
            )
    return rows


def _window_metrics_from_trade_subset(
    trade_log: list[dict[str, Any]],
    test_start: pd.Timestamp,
    test_end: pd.Timestamp,
) -> dict[str, float]:
    start = pd.Timestamp(test_start, tz="UTC") if pd.Timestamp(test_start).tzinfo is None else pd.Timestamp(test_start).tz_convert("UTC")
    end = pd.Timestamp(test_end, tz="UTC") if pd.Timestamp(test_end).tzinfo is None else pd.Timestamp(test_end).tz_convert("UTC")
    window_trades: list[dict[str, Any]] = []
    for trade in trade_log:
        entry_ts = pd.Timestamp(str(trade["entry_date"]), tz="UTC")
        exit_ts = pd.Timestamp(str(trade["exit_date"]), tz="UTC")
        if entry_ts < start or exit_ts > end:
            continue
        window_trades.append(trade)

    if not window_trades:
        return {
            "cagr_pct": 0.0,
            "sharpe": 0.0,
            "expectancy_r": 0.0,
            "trade_count": 0,
            "win_rate": 0.0,
            "total_return_pct": 0.0,
        }

    rs = [float(trade["realized_R"]) for trade in window_trades]
    trade_count = len(rs)
    total_r = float(sum(rs))
    expectancy_r = total_r / trade_count
    win_rate = sum(1 for r in rs if r > 0) / trade_count
    if trade_count >= 2:
        std_r = statistics.stdev(rs)
        sharpe = float((statistics.fmean(rs) / std_r) * math.sqrt(trade_count)) if std_r > 0 else 0.0
    else:
        sharpe = 0.0

    period_days = max((end - start).days + 1, 1)
    total_return_pct = total_r
    if period_days >= 180 and total_return_pct > -100:
        years = period_days / 365.25
        growth = max(0.0, 1.0 + total_return_pct / 100.0)
        cagr_pct = ((growth ** (1.0 / years)) - 1.0) * 100.0 if growth > 0 else -100.0
    else:
        cagr_pct = total_return_pct

    return {
        "cagr_pct": round(cagr_pct, 6),
        "sharpe": round(sharpe, 6),
        "expectancy_r": round(expectancy_r, 6),
        "trade_count": trade_count,
        "win_rate": round(win_rate, 6),
        "total_return_pct": round(total_return_pct, 6),
    }


def _oos_summary(window_df: pd.DataFrame, scenario: str) -> dict[str, Any]:
    subset = window_df[window_df["scenario"] == scenario].copy()
    if subset.empty:
        return {
            "median_return_pct": math.nan,
            "median_sharpe": math.nan,
            "median_expectancy_r": math.nan,
            "negative_majority": False,
        }
    negative_majority = int((subset["total_return_pct"] < 0).sum()) > (len(subset) / 2.0)
    return {
        "median_return_pct": round(float(subset["total_return_pct"].median()), 6),
        "median_sharpe": round(float(subset["sharpe"].median()), 6),
        "median_expectancy_r": round(float(subset["expectancy_r"].median()), 6),
        "negative_majority": bool(negative_majority),
    }


def _overfit_label(
    *,
    anchored_return_pct: float,
    anchored_expectancy_r: float,
    neighborhood: pd.DataFrame,
    max_overlap: float,
) -> tuple[str, str]:
    reasons: list[str] = []
    score = 0
    if anchored_return_pct < 0 or anchored_expectancy_r < 0:
        score += 2
        reasons.append("anchored OOS performance is negative")
    if not neighborhood.empty:
        if float(neighborhood["sharpe"].median()) < 0.85 * float(neighborhood["sharpe"].max()):
            score += 1
            reasons.append("neighboring parameters lose Sharpe")
        if float(neighborhood["cagr_pct"].median()) < 0.75 * float(neighborhood["cagr_pct"].max()):
            score += 1
            reasons.append("neighboring parameters lose CAGR")
    if max_overlap >= 0.95:
        score += 1
        reasons.append("selected alternatives overlap heavily")
    if score >= 4:
        return "high", ", ".join(reasons) if reasons else "oos and neighborhood checks are weak"
    if score >= 2:
        return "medium", ", ".join(reasons) if reasons else "some oos fragility exists"
    return "low", ", ".join(reasons) if reasons else "oos and neighborhood checks are relatively stable"


def _practicality_label(
    *,
    fill_ratio: float,
    gap_reject_ratio: float,
    same_bar_return_delta: float,
    same_bar_expectancy_delta: float,
) -> tuple[str, str]:
    reasons: list[str] = []
    score = 0
    if fill_ratio > 0.75:
        score += 2
        reasons.append("open-fill dependence is high")
    elif fill_ratio > 0.55:
        score += 1
        reasons.append("open-fill dependence is noticeable")
    if gap_reject_ratio > 0.03:
        score += 2
        reasons.append("gap rejection rate is high")
    elif gap_reject_ratio > 0.01:
        score += 1
        reasons.append("gap rejection rate is non-trivial")
    if same_bar_return_delta > 3.0 or same_bar_expectancy_delta > 0.08:
        score += 2
        reasons.append("same-bar stop assumption changes outcomes")
    elif same_bar_return_delta > 1.0 or same_bar_expectancy_delta > 0.03:
        score += 1
        reasons.append("same-bar stop assumption has some effect")
    if score >= 4:
        return "fragile", ", ".join(reasons) if reasons else "execution assumptions look fragile"
    if score >= 2:
        return "caution", ", ".join(reasons) if reasons else "execution assumptions need caution"
    return "good", ", ".join(reasons) if reasons else "execution assumptions look relatively robust"


def _concentration_label(
    *,
    top1_share: float,
    top3_share: float,
    best_symbol_cagr_delta: float,
) -> tuple[str, str]:
    reasons: list[str] = []
    score = 0
    if top1_share > 0.30 or top3_share > 0.65:
        score += 2
        reasons.append("symbol concentration is high")
    elif top1_share > 0.20 or top3_share > 0.50:
        score += 1
        reasons.append("symbol concentration is noticeable")
    if best_symbol_cagr_delta < -8.0:
        score += 2
        reasons.append("removing the top symbol hurts CAGR materially")
    elif best_symbol_cagr_delta < -3.0:
        score += 1
        reasons.append("removing the top symbol has a visible cost")
    if score >= 4:
        return "high", ", ".join(reasons) if reasons else "symbol dependence is high"
    if score >= 2:
        return "medium", ", ".join(reasons) if reasons else "some symbol dependence exists"
    return "low", ", ".join(reasons) if reasons else "symbol contribution is relatively diversified"


def _recent_6m_holds_up(anchored_result: dict[str, Any], walk_forward_summary: dict[str, Any], rolling_summary: dict[str, Any]) -> bool:
    anchored_ok = float(anchored_result["metrics"]["total_return_pct"]) > 0 and float(anchored_result["metrics"]["expectancy_r"]) > 0
    walk_ok = not walk_forward_summary["negative_majority"] and walk_forward_summary["median_sharpe"] >= 0
    rolling_ok = not rolling_summary["negative_majority"] and rolling_summary["median_sharpe"] >= 0
    return bool(anchored_ok and (walk_ok or rolling_ok))


def _report_level(level: str) -> str:
    mapping = {
        "high": "높음",
        "medium": "보통",
        "low": "낮음",
        "good": "양호",
        "caution": "주의",
        "fragile": "취약",
        "insufficient": "불충분",
    }
    return mapping.get(level, level)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task 323+ best structural breakout combo evaluation")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--ranked-input", type=str, default=str(RANKED_INPUT))
    parser.add_argument("--out-dir", type=str, default=DEFAULT_OUT_DIR)
    parser.add_argument("--candidate-pool", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args(argv)

    base_dir = Path(args.data_dir)
    ranked_input = Path(args.ranked_input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = max(1, int(args.jobs))
    candidate_pool = max(3, int(args.candidate_pool))

    stocks = [s for s in sorted(p.stem.upper() for p in base_dir.glob("*.csv")) if _asset_type(s) == "STOCK"]
    frames, timestamps = _prepare_preloaded_frames(base_dir, stocks)
    latest_end = _latest_data_end(base_dir)
    anchored_window = _anchored_oos_window(latest_end)
    train_timestamps = _slice_timestamps(timestamps, timestamps[0], anchored_window.train_end)
    recent_timestamps = _slice_timestamps(timestamps, anchored_window.test_start, anchored_window.test_end)

    ranked_input_df = _load_ranked_input(ranked_input)
    balanced_candidates_df = _balanced_rank_frame(ranked_input_df).head(candidate_pool).copy()
    cagr_candidates_df = _cagr_rank_frame(ranked_input_df).head(candidate_pool).copy()
    candidate_df = pd.concat([balanced_candidates_df, cagr_candidates_df], ignore_index=True).drop_duplicates(subset=["scenario"]).reset_index(drop=True)
    candidate_cfgs = [_config_from_scenario(scenario) for scenario in candidate_df["scenario"].tolist()]

    candidate_train_results = _run_period_reruns(candidate_cfgs, base_dir=base_dir, stocks=stocks, jobs=jobs, frames=frames, timestamps=train_timestamps)
    candidate_train_by_scenario = {_scenario_name(StructuralConfig(**result["config"])): result for result in candidate_train_results}
    train_rows = []
    for scenario, result in candidate_train_by_scenario.items():
        metrics = result["metrics"]
        train_rows.append(
            {
                "scenario": scenario,
                "cagr_pct": metrics["cagr_pct"],
                "sharpe": metrics["sharpe"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "expectancy_r": metrics["expectancy_r"],
                "trade_count": metrics["trade_count"],
                "label_rank": int(ranked_input_df.loc[ranked_input_df["scenario"] == scenario, "label_rank"].iloc[0]) if scenario in set(ranked_input_df["scenario"]) else 9,
            }
        )
    train_ranked_df = pd.DataFrame(train_rows)
    train_balanced_df = _balanced_rank_frame(train_ranked_df)
    train_cagr_df = _cagr_rank_frame(train_ranked_df)
    train_metrics_by_scenario = {row["scenario"]: row for row in train_rows}
    train_overlap_df = _trade_overlap_matrix(candidate_train_results)
    representative_by_scenario = _overlap_groups(train_overlap_df, train_metrics_by_scenario)
    selected_top3 = _select_mixed_top3(train_balanced_df, train_cagr_df, representative_by_scenario)
    selected_scenarios = [row["scenario"] for row in selected_top3]
    selection_group_map = {row["scenario"]: row["selection_group"] for row in selected_top3}
    selected_cfgs = [_config_from_scenario(scenario) for scenario in selected_scenarios]

    full_by_scenario = _period_result_by_scenario(selected_cfgs, base_dir=base_dir, stocks=stocks, jobs=jobs, frames=frames, timestamps=timestamps)
    anchored_by_scenario = _period_result_by_scenario(selected_cfgs, base_dir=base_dir, stocks=stocks, jobs=jobs, frames=frames, timestamps=recent_timestamps)

    selected_results = [full_by_scenario[scenario] for scenario in selected_scenarios]
    selected_overlap_df = _trade_overlap_matrix(selected_results)
    overlap_lookup = selected_overlap_df.set_index("scenario")
    regime_lookup = _build_market_regime_lookup(base_dir)
    symbol_feature_lookup = _build_symbol_feature_lookup(frames)
    rs_percentile_lookup = _build_rs_percentile_lookup(symbol_feature_lookup)
    reclustered_regime_lookup = _build_reclustered_regime_lookup(base_dir)

    walk_windows = _walk_forward_windows(timestamps[0], latest_end)
    rolling_windows = _rolling_oos_windows(timestamps[0], latest_end)
    walk_rows = _test_result_rows("walk_forward", walk_windows, full_by_scenario, selection_group_map)
    rolling_rows = _test_result_rows("rolling_oos", rolling_windows, full_by_scenario, selection_group_map)
    anchored_rows = []
    for scenario, result in anchored_by_scenario.items():
        metrics = result["metrics"]
        anchored_rows.append(
            {
                "evaluation_type": "anchored_oos",
                "window_name": anchored_window.name,
                "scenario": scenario,
                "selection_group": selection_group_map.get(scenario, ""),
                "train_start": str(anchored_window.train_start.date()),
                "train_end": str(anchored_window.train_end.date()),
                "test_start": str(anchored_window.test_start.date()),
                "test_end": str(anchored_window.test_end.date()),
                "cagr_pct": metrics["cagr_pct"],
                "sharpe": metrics["sharpe"],
                "expectancy_r": metrics["expectancy_r"],
                "trade_count": metrics["trade_count"],
                "win_rate": metrics["win_rate"],
                "total_return_pct": metrics["total_return_pct"],
            }
        )

    walk_df = pd.DataFrame(walk_rows)
    anchored_df = pd.DataFrame(anchored_rows)
    rolling_df = pd.DataFrame(rolling_rows)

    summary_rows: list[dict[str, Any]] = []
    contribution_rows: list[dict[str, Any]] = []
    fill_rows: list[dict[str, Any]] = []
    recent_rows: list[dict[str, Any]] = []
    exclusion_rows: list[dict[str, Any]] = []
    same_bar_rows: list[dict[str, Any]] = []
    neighborhood_rows: list[dict[str, Any]] = []
    reliability_rows: list[dict[str, Any]] = []
    recent_trade_frames: list[pd.DataFrame] = []
    failure_trade_frames: list[pd.DataFrame] = []

    trial_sharpes = [float(row["sharpe"]) for row in train_rows]
    effective_trial_count = len(candidate_cfgs) * 2

    for selected in selected_top3:
        scenario = selected["scenario"]
        selection_group = selected["selection_group"]
        full_result = full_by_scenario[scenario]
        anchored_result = anchored_by_scenario[scenario]
        cfg = StructuralConfig(**full_result["config"])
        metrics = full_result["metrics"]
        diag = full_result["diagnostics"]

        contribution_df = _symbol_contribution_df(full_result)
        contribution_rows.extend([{"scenario": scenario, **row} for row in contribution_df.to_dict("records")])

        recent_trade_df = _recent_trade_frame(anchored_result, regime_lookup, symbol_feature_lookup)
        recent_trade_frames.append(recent_trade_df)
        failure_trade_frames.append(
            _build_trade_failure_frame(
                anchored_result,
                selection_group,
                frames,
                timestamps,
                regime_lookup,
                reclustered_regime_lookup,
                symbol_feature_lookup,
                rs_percentile_lookup,
            )
        )
        anchored_metrics = anchored_result["metrics"]
        recent_rows.append(
            {
                "scenario": scenario,
                "selection_group": selection_group,
                "recent_start": str(anchored_window.test_start.date()),
                "recent_end": str(anchored_window.test_end.date()),
                "trade_count": anchored_metrics["trade_count"],
                "win_rate": anchored_metrics["win_rate"],
                "expectancy_r": anchored_metrics["expectancy_r"],
                "total_return_pct": anchored_metrics["total_return_pct"],
                "cagr_pct": anchored_metrics["cagr_pct"],
            }
        )

        same_bar_df = _same_bar_comparison(cfg, base_dir=base_dir, frames=frames, timestamps=timestamps, stocks=stocks)
        same_bar_rows.extend([{"base_scenario": scenario, **row} for row in same_bar_df.to_dict("records")])
        same_bar_disable = same_bar_df[same_bar_df["entry_bar_stop_mode"] == "DISABLE_ENTRY_BAR_STOP"].iloc[0]
        same_bar_allow = same_bar_df[same_bar_df["entry_bar_stop_mode"] == "ALLOW_SAME_BAR_STOP"].iloc[0]
        same_bar_return_delta = abs(float(same_bar_disable["total_return_pct"]) - float(same_bar_allow["total_return_pct"]))
        same_bar_expectancy_delta = abs(float(same_bar_disable["expectancy_r"]) - float(same_bar_allow["expectancy_r"]))

        best_symbol = str(contribution_df.iloc[0]["symbol"]) if not contribution_df.empty else ""
        worst_symbol = str(contribution_df.iloc[-1]["symbol"]) if not contribution_df.empty else ""
        best_exclusion = _run_exclusion(cfg, best_symbol, base_dir=base_dir, frames=frames, timestamps=timestamps, stocks=stocks)
        worst_exclusion = _run_exclusion(cfg, worst_symbol, base_dir=base_dir, frames=frames, timestamps=timestamps, stocks=stocks)
        exclusion_rows.append({"scenario": scenario, "selection_group": selection_group, "exclusion_type": "best_symbol_excluded", **best_exclusion})
        exclusion_rows.append({"scenario": scenario, "selection_group": selection_group, "exclusion_type": "worst_symbol_excluded", **worst_exclusion})

        max_overlap = 0.0
        if scenario in overlap_lookup.index:
            overlap_series = overlap_lookup.loc[scenario]
            for other, value in overlap_series.items():
                if str(other) == scenario:
                    continue
                max_overlap = max(max_overlap, float(value))

        neighbors = _neighbor_rows(ranked_input_df, cfg)
        neighborhood_rows.extend([{"scenario": scenario, **row} for row in neighbors.to_dict("records")])

        walk_summary = _oos_summary(walk_df, scenario)
        rolling_summary = _oos_summary(rolling_df, scenario)
        overfit_level, overfit_reason = _overfit_label(
            anchored_return_pct=float(anchored_metrics["total_return_pct"]),
            anchored_expectancy_r=float(anchored_metrics["expectancy_r"]),
            neighborhood=neighbors,
            max_overlap=max_overlap,
        )
        practicality_level, practicality_reason = _practicality_label(
            fill_ratio=float(diag["fill_at_open_ratio"]),
            gap_reject_ratio=float(diag["rejected_by_gap_over_entry_ratio_vs_triggered"]),
            same_bar_return_delta=same_bar_return_delta,
            same_bar_expectancy_delta=same_bar_expectancy_delta,
        )
        best_symbol_cagr_delta = float(best_exclusion["cagr_pct"]) - float(metrics["cagr_pct"])
        concentration_level, concentration_reason = _concentration_label(
            top1_share=float(diag["top1_symbol_total_R_share"]),
            top3_share=float(diag["top3_symbol_total_R_share"]),
            best_symbol_cagr_delta=best_symbol_cagr_delta,
        )
        reliability = _sharpe_reliability(float(metrics["sharpe"]), _returns_from_result(full_result), trial_sharpes, effective_trial_count)
        reliability_rows.append({"scenario": scenario, "selection_group": selection_group, **reliability})

        fill_rows.append(
            {
                "scenario": scenario,
                "selection_group": selection_group,
                "fill_at_open_ratio": diag["fill_at_open_ratio"],
                "open_gt_planned_entry_ratio": diag["open_gt_planned_entry_ratio"],
                "open_gt_actual_entry_ratio": diag["open_gt_actual_entry_ratio"],
                "rejected_by_gap_over_entry_ratio_vs_triggered": diag["rejected_by_gap_over_entry_ratio_vs_triggered"],
                "same_bar_return_delta": round(same_bar_return_delta, 6),
                "same_bar_expectancy_delta": round(same_bar_expectancy_delta, 6),
                "practicality_level": practicality_level,
                "practicality_reason": practicality_reason,
            }
        )

        summary_rows.append(
            {
                "scenario": scenario,
                "selection_group": selection_group,
                "cagr_pct": metrics["cagr_pct"],
                "sharpe": metrics["sharpe"],
                "max_drawdown_pct": metrics["max_drawdown_pct"],
                "expectancy_r": metrics["expectancy_r"],
                "trade_count": metrics["trade_count"],
                "top1_symbol_total_R_share": diag["top1_symbol_total_R_share"],
                "top3_symbol_total_R_share": diag["top3_symbol_total_R_share"],
                "anchored_oos_return_pct": anchored_metrics["total_return_pct"],
                "anchored_oos_expectancy_r": anchored_metrics["expectancy_r"],
                "anchored_oos_win_rate": anchored_metrics["win_rate"],
                "walk_forward_median_return_pct": walk_summary["median_return_pct"],
                "walk_forward_median_sharpe": walk_summary["median_sharpe"],
                "rolling_oos_median_return_pct": rolling_summary["median_return_pct"],
                "rolling_oos_median_sharpe": rolling_summary["median_sharpe"],
                "recent_6m_holds_up": _recent_6m_holds_up(anchored_result, walk_summary, rolling_summary),
                "overfit_level": overfit_level,
                "overfit_reason": overfit_reason,
                "practicality_level": practicality_level,
                "practicality_reason": practicality_reason,
                "concentration_level": concentration_level,
                "concentration_reason": concentration_reason,
                "best_symbol": best_symbol,
                "worst_symbol": worst_symbol,
                "best_symbol_excluded_cagr_delta": round(best_symbol_cagr_delta, 6),
                "worst_symbol_excluded_cagr_delta": round(float(worst_exclusion["cagr_pct"]) - float(metrics["cagr_pct"]), 6),
                "max_overlap_with_selected": round(max_overlap, 6),
                "neighbor_count": int(len(neighbors)),
                "neighbor_sharpe_median": round(float(neighbors["sharpe"].median()), 6) if not neighbors.empty else math.nan,
                "neighbor_cagr_median": round(float(neighbors["cagr_pct"].median()), 6) if not neighbors.empty else math.nan,
                "effective_trial_count": reliability["effective_trial_count"],
                "trial_count_adjusted_sharpe": reliability["trial_count_adjusted_sharpe"],
                "dsr": reliability["dsr"],
                "sharpe_confidence_label": reliability["confidence_label"],
                "sharpe_confidence_commentary": reliability["confidence_commentary"],
            }
        )

    summary_df = pd.DataFrame(summary_rows).sort_values(["selection_group", "sharpe", "cagr_pct"], ascending=[True, False, False]).reset_index(drop=True)
    contribution_out = pd.DataFrame(contribution_rows)
    fill_df = pd.DataFrame(fill_rows)
    recent_df = pd.DataFrame(recent_rows)
    exclusion_df = pd.DataFrame(exclusion_rows)
    same_bar_out = pd.DataFrame(same_bar_rows)
    neighborhood_df = pd.DataFrame(neighborhood_rows)
    reliability_df = pd.DataFrame(reliability_rows)

    all_recent_trades = pd.concat(recent_trade_frames, ignore_index=True) if recent_trade_frames else pd.DataFrame()
    failure_analysis_df = pd.concat(failure_trade_frames, ignore_index=True) if failure_trade_frames else pd.DataFrame()
    loss_trade_anatomy_df = all_recent_trades[all_recent_trades["realized_R"] < 0].copy() if not all_recent_trades.empty else pd.DataFrame()
    loss_by_month = _loss_breakdown(all_recent_trades, "month_bucket")
    loss_by_symbol = _loss_breakdown(all_recent_trades, "symbol")
    loss_by_entry_type = _loss_breakdown(all_recent_trades, "entry_type")
    loss_by_regime = _loss_breakdown(all_recent_trades, "market_regime_base")
    loss_by_regime_detail = _loss_breakdown(all_recent_trades, "market_regime_detail")
    loss_feature_summary = _feature_summary(loss_trade_anatomy_df)
    loss_feature_bins = _feature_bin_breakdown(loss_trade_anatomy_df)
    loser_distribution_df = _distribution_table(failure_analysis_df[failure_analysis_df["trade_label"] == "loser"].copy(), FAILURE_DISTRIBUTION_FEATURES, subset_name="losers") if not failure_analysis_df.empty else pd.DataFrame()
    winner_loser_df = _winner_loser_comparison_table(failure_analysis_df, WINNER_LOSER_COMPARE_FEATURES) if not failure_analysis_df.empty else pd.DataFrame()
    loser_only_df = failure_analysis_df[failure_analysis_df["trade_label"] == "loser"].copy() if not failure_analysis_df.empty else pd.DataFrame()
    if not loser_only_df.empty:
        worst_mask_losers = _worst_decile_mask(loser_only_df)
        worst_keys = set(loser_only_df.loc[worst_mask_losers, ["scenario", "symbol", "entry_date"]].astype(str).agg("|".join, axis=1).tolist())
        failure_analysis_df["is_worst_decile"] = failure_analysis_df[["scenario", "symbol", "entry_date"]].astype(str).agg("|".join, axis=1).isin(worst_keys)
        worst_decile_analysis_df, tail_event_driven = _worst_decile_analysis(failure_analysis_df)
    else:
        failure_analysis_df["is_worst_decile"] = False
        worst_decile_analysis_df, tail_event_driven = pd.DataFrame(), False
    regime_reclustered_df = failure_analysis_df[
        ["scenario", "selection_group", "symbol", "entry_date", "market_regime_base", "reclustered_regime", "qld_ret_5d_prev", "qld_ret_20d_prev", "qld_vol_ratio_prev", "qld_sma20_slope5_prev", "qld_sma50_slope5_prev", "qld_dd20_prev", "qld_dd60_prev"]
    ].copy() if not failure_analysis_df.empty else pd.DataFrame()
    regime_performance_df = _regime_performance_table(failure_analysis_df) if not failure_analysis_df.empty else pd.DataFrame()
    cross_sectional_df = _cross_sectional_concentration(failure_analysis_df, failure_analysis_df["is_worst_decile"]) if not failure_analysis_df.empty else pd.DataFrame()
    entry_timing_df = _entry_timing_analysis(failure_analysis_df, failure_analysis_df["is_worst_decile"]) if not failure_analysis_df.empty else pd.DataFrame()

    universe_state_lookup = _build_universe_state_lookup(frames, stocks)
    regime_state_lookup = _build_regime_state_lookup(base_dir, universe_state_lookup)
    if not failure_analysis_df.empty:
        state_rows = pd.DataFrame([{"entry_date": key, **value} for key, value in regime_state_lookup.items()])
        dual_map_trade_frame = failure_analysis_df.merge(state_rows, on="entry_date", how="left")
        dual_map_trade_frame["regime_state"] = dual_map_trade_frame["regime_state"].fillna("risk_off")
        dual_map_trade_frame["sector_concentration_ratio"] = pd.to_numeric(dual_map_trade_frame.get("tech_concentration_ratio"), errors="coerce")
        dual_map_trade_frame = _apply_outcome_groups(dual_map_trade_frame)
        dual_map_trade_frame = _apply_post_entry_bands(dual_map_trade_frame)
    else:
        dual_map_trade_frame = pd.DataFrame()
    outcome_summary_df = _outcome_group_summary(dual_map_trade_frame)
    regime_state_table_df = _regime_state_table(dual_map_trade_frame)
    regime_sector_matrix_df = _regime_sector_matrix(dual_map_trade_frame)
    predictive_layer_df = _cross_sectional_predictive_layer(dual_map_trade_frame)
    post_entry_validation_df = _build_post_entry_validation(dual_map_trade_frame)
    entry_timing_dual_df = _entry_timing_analysis(dual_map_trade_frame, dual_map_trade_frame["is_worst_decile"]) if not dual_map_trade_frame.empty else pd.DataFrame()
    rule_candidates_df = _build_rule_candidates(dual_map_trade_frame, post_entry_validation_df)
    feature_reduction_df = _feature_reduction(dual_map_trade_frame, entry_timing_dual_df)
    final_decision_system_df = _final_decision_system(rule_candidates_df, feature_reduction_df)

    primary = summary_df.sort_values(["selection_group", "sharpe", "max_drawdown_pct"], ascending=[True, False, True]).iloc[0]
    status = "추가 검증 1순위"
    if not bool(primary["recent_6m_holds_up"]):
        status = "추가 검증 1순위 (보류)"

    regime_filter_too_coarse = False
    regime_confidence = "낮음"
    regime_evidence = "insufficient regime clustering evidence"
    if not regime_state_table_df.empty:
        worst_state = regime_state_table_df.iloc[0]
        best_state = regime_state_table_df.sort_values(["expectancy_r", "winner_top30_share"], ascending=[False, False]).iloc[0]
        regime_filter_too_coarse = str(worst_state["regime"]) in {"true_early_trend", "failed_recovery", "rebound_chop"} and float(worst_state["loser_bottom30_share"]) >= 0.45
        regime_confidence = "보통" if regime_filter_too_coarse else "낮음"
        regime_evidence = f"worst regime `{worst_state['regime']}` loser share {float(worst_state['loser_bottom30_share']):.2f}, expectancy {float(worst_state['expectancy_r']):.3f}R; best regime `{best_state['regime']}` expectancy {float(best_state['expectancy_r']):.3f}R"

    late_chase = False
    late_confidence = "낮음"
    late_evidence = "insufficient winner vs loser timing separation"
    if not entry_timing_dual_df.empty:
        compare_all = entry_timing_dual_df[(entry_timing_dual_df["scenario"] == "ALL") & (entry_timing_dual_df["analysis_scope"] == "winner_vs_loser")].set_index("feature")
        gate_features = {"ret_20d_pre", "dist_to_sma20_pct", "gap_over_planned_entry_pct", "breakout_strength_pct"}
        follow_features = {"follow_through_3d_pct", "follow_through_5d_pct", "post_breakout_retrace_3d_pct", "post_breakout_retrace_5d_pct", "adverse_excursion_3d_pct", "adverse_excursion_5d_pct"}
        gate_hits = 0
        for feature in gate_features:
            if feature in compare_all.index:
                row = compare_all.loc[feature]
                if row["direction_label"] == "losers_higher" and pd.notna(row["effect_size"]) and abs(float(row["effect_size"])) >= 0.15:
                    gate_hits += 1
        follow_hits = 0
        for feature in follow_features:
            if feature in compare_all.index:
                row = compare_all.loc[feature]
                if feature.startswith("follow_through") and row["direction_label"] == "losers_lower" and pd.notna(row["effect_size"]) and abs(float(row["effect_size"])) >= 0.15:
                    follow_hits += 1
                if (feature.startswith("post_breakout_retrace") or feature.startswith("adverse_excursion")) and row["direction_label"] == "losers_higher" and pd.notna(row["effect_size"]) and abs(float(row["effect_size"])) >= 0.15:
                    follow_hits += 1
        late_chase = gate_hits >= 2 and follow_hits >= 2
        late_confidence = "보통" if late_chase else "낮음"
        late_evidence = f"gate hits {gate_hits}, follow-through hits {follow_hits}"

    sector_concentrated = False
    sector_confidence = "낮음"
    sector_evidence = "no dominant sector concentration"
    if not predictive_layer_df.empty:
        sector_losers = predictive_layer_df[(predictive_layer_df["analysis_group"] == "loser_bottom30") & (predictive_layer_df["metric_group"] == "sector_summary")].sort_values("total_r")
        if not sector_losers.empty:
            leader = sector_losers.iloc[0]
            sector_concentrated = str(leader["sector_bucket"]) in {"semis", "software/internet", "other tech"} and float(leader["trade_count"]) >= 4
            sector_confidence = "보통" if sector_concentrated else "낮음"
            sector_evidence = f"leading loser sector `{leader['sector_bucket']}` total R {float(leader['total_r']):.2f}, win rate {float(leader['win_rate']):.2f}"

    tail_confidence = "보통" if tail_event_driven else "낮음"
    tail_evidence = "worst-decile share unavailable"
    if not worst_decile_analysis_df.empty and "__overall__" in set(worst_decile_analysis_df["feature"]):
        tail_row = worst_decile_analysis_df[worst_decile_analysis_df["feature"] == "__overall__"].iloc[0]
        tail_evidence = f"worst decile loss share {float(tail_row['worst_loss_share']):.2f}"

    summary_hypothesis_rows = [
        {"hypothesis": "regime filter too coarse", "result": regime_filter_too_coarse, "confidence": regime_confidence, "evidence": regime_evidence},
        {"hypothesis": "breakout is late-chase", "result": late_chase, "confidence": late_confidence, "evidence": late_evidence},
        {"hypothesis": "losses driven by tail events", "result": tail_event_driven, "confidence": tail_confidence, "evidence": tail_evidence},
        {"hypothesis": "losses concentrated in specific sectors", "result": sector_concentrated, "confidence": sector_confidence, "evidence": sector_evidence},
    ]

    summary_df.to_csv(out_dir / "selected_combo_rankings.csv", index=False)
    contribution_out.to_csv(out_dir / "selected_symbol_contributions.csv", index=False)
    fill_df.to_csv(out_dir / "selected_fill_diagnostics.csv", index=False)
    recent_df.to_csv(out_dir / "selected_recent_6m_metrics.csv", index=False)
    exclusion_df.to_csv(out_dir / "selected_exclusion_impact.csv", index=False)
    selected_overlap_df.to_csv(out_dir / "selected_overlap_support.csv", index=False)
    neighborhood_df.to_csv(out_dir / "selected_neighborhood_stability.csv", index=False)
    same_bar_out.to_csv(out_dir / "selected_same_bar_comparison.csv", index=False)
    loss_by_month.to_csv(out_dir / "selected_recent_6m_loss_by_month.csv", index=False)
    loss_by_symbol.to_csv(out_dir / "selected_recent_6m_loss_by_symbol.csv", index=False)
    loss_by_entry_type.to_csv(out_dir / "selected_recent_6m_loss_by_entry_type.csv", index=False)
    loss_by_regime.to_csv(out_dir / "selected_recent_6m_loss_by_regime.csv", index=False)
    loss_trade_anatomy_df.to_csv(out_dir / "selected_recent_6m_loss_trade_anatomy.csv", index=False)
    loss_by_regime_detail.to_csv(out_dir / "selected_recent_6m_loss_by_regime_detail.csv", index=False)
    loss_feature_summary.to_csv(out_dir / "selected_recent_6m_loss_feature_summary.csv", index=False)
    loss_feature_bins.to_csv(out_dir / "selected_recent_6m_loss_feature_bins.csv", index=False)
    walk_df.to_csv(out_dir / "selected_top3_oos_walk_forward.csv", index=False)
    anchored_df.to_csv(out_dir / "selected_top3_oos_anchored.csv", index=False)
    rolling_df.to_csv(out_dir / "selected_top3_oos_rolling.csv", index=False)
    reliability_df.to_csv(out_dir / "selected_top3_sharpe_reliability.csv", index=False)
    failure_analysis_df.to_csv(out_dir / "selected_recent_6m_trade_failure_analysis.csv", index=False)
    loser_distribution_df.to_csv(out_dir / "selected_recent_6m_loser_distribution.csv", index=False)
    winner_loser_df.to_csv(out_dir / "selected_recent_6m_winner_vs_loser_comparison.csv", index=False)
    worst_decile_analysis_df.to_csv(out_dir / "selected_recent_6m_worst_decile_analysis.csv", index=False)
    regime_reclustered_df.to_csv(out_dir / "selected_recent_6m_regime_reclustered.csv", index=False)
    regime_performance_df.to_csv(out_dir / "selected_recent_6m_regime_performance.csv", index=False)
    cross_sectional_df.to_csv(out_dir / "selected_recent_6m_cross_sectional_concentration.csv", index=False)
    entry_timing_df.to_csv(out_dir / "selected_recent_6m_entry_timing_analysis.csv", index=False)
    dual_map_trade_frame.to_csv(out_dir / "selected_recent_6m_dual_map_trade_frame.csv", index=False)
    outcome_summary_df.to_csv(out_dir / "selected_recent_6m_outcome_group_summary.csv", index=False)
    regime_state_table_df.to_csv(out_dir / "selected_recent_6m_regime_state_table.csv", index=False)
    regime_sector_matrix_df.to_csv(out_dir / "selected_recent_6m_regime_sector_matrix.csv", index=False)
    predictive_layer_df.to_csv(out_dir / "selected_recent_6m_cross_sectional_predictive_layer.csv", index=False)
    post_entry_validation_df.to_csv(out_dir / "selected_recent_6m_post_entry_validation.csv", index=False)
    rule_candidates_df.to_csv(out_dir / "selected_recent_6m_rule_candidates.csv", index=False)
    feature_reduction_df.to_csv(out_dir / "selected_recent_6m_feature_reduction.csv", index=False)
    final_decision_system_df.to_csv(out_dir / "selected_recent_6m_final_decision_system.csv", index=False)

    lines = [
        "# Task 323 Production Upgrade",
        "",
        "## Executive Summary",
        f"- Evaluation end date: {latest_end.date()}",
        f"- Anchored OOS window: {anchored_window.test_start.date()} ~ {anchored_window.test_end.date()}",
        f"- Mixed top-3 count: {len(summary_df)}",
        f"- Primary status: {status}",
        f"- Primary candidate: `{primary['scenario']}`",
        "",
        "## Summary Table",
        "| Hypothesis | Result | Confidence | Key Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for row in summary_hypothesis_rows:
        lines.append(f"| {row['hypothesis']} | {row['result']} | {row['confidence']} | {row['evidence']} |")
    lines.extend(["", "## Final Rule Set", "| Type | Rule |", "| --- | --- |"])
    for row in final_decision_system_df.to_dict("records"):
        lines.append(f"| {row['type']} | {row['rule']} |")
    lines.extend(
        [
            "",
            "## System Flow",
            "| Step | Logic |",
            "| --- | --- |",
            "| Pre-entry filter | regime state + sector concentration + crowding + entry extension bands |",
            "| Entry decision | allow, block, or reduce based on rule candidate stack |",
            "| Post-entry validation | Day1~3 and Day3~5 EOD windows, execute at next trading day open |",
            "| Exit logic | weak FT plus high retrace or crowded weak-regime failure triggers exit/reduce |",
            "",
            "## Key Drivers",
            "| Category | Top Feature |",
            "| --- | --- |",
        ]
    )
    top_features = feature_reduction_df["feature"].tolist() if not feature_reduction_df.empty else []
    lines.append(f"| Regime | {next((f for f in top_features if f == 'regime_state'), top_features[0] if top_features else 'n/a')} |")
    lines.append(f"| Entry | {next((f for f in top_features if f in {'ret_20d_pre', 'dist_to_sma20_pct', 'gap_over_planned_entry_pct', 'breakout_strength_pct'}), 'n/a')} |")
    lines.append(f"| Post-entry | {next((f for f in top_features if str(f).startswith('follow_through') or str(f).startswith('post_breakout_retrace') or str(f).startswith('adverse_excursion')), 'n/a')} |")
    lines.append(f"| Cross-section | {next((f for f in top_features if f in {'sector_bucket', 'crowding_proxy', 'rs_percentile_20d'}), 'n/a')} |")
    lines.extend(
        [
            "",
            "## Failure Map",
            "| Condition | Effect |",
            "| --- | --- |",
            f"| regime | {regime_evidence} |",
            f"| sector | {sector_evidence} |",
            f"| entry | {late_evidence} |",
            f"| post-entry | {post_entry_validation_df.sort_values('expectancy_delta').iloc[0]['condition'] if not post_entry_validation_df.empty else 'n/a'} |",
            "",
            "## Success Map",
            "| Condition | Effect |",
            "| --- | --- |",
            f"| regime | best regime `{regime_state_table_df.sort_values(['expectancy_r', 'winner_top30_share'], ascending=[False, False]).iloc[0]['regime']}` supports positive expectancy |" if not regime_state_table_df.empty else "| regime | n/a |",
            f"| sector | best regime-sector combos lean on `{', '.join(regime_sector_matrix_df.sort_values(['expectancy_r', 'win_rate'], ascending=[False, False]).head(2)['matrix_sector'].astype(str).tolist())}` |" if not regime_sector_matrix_df.empty else "| sector | n/a |",
            "| entry | winners show better early continuation than losers across FT/retrace comparisons |",
            "| post-entry | hold bias when FT_3d band is strong and retrace_3d band is low/mid |",
            "",
            "## Separation Layer",
            "| Feature | Threshold | Impact |",
            "| --- | --- | --- |",
        ]
    )
    for row in feature_reduction_df.head(5).to_dict("records"):
        threshold = "upper/lower pooled band"
        if str(row["feature"]) == "follow_through_3d_pct":
            threshold = "weak/mixed/strong band"
        elif str(row["feature"]) in {"post_breakout_retrace_3d_pct", "adverse_excursion_3d_pct"}:
            threshold = "low/mid/high risk band"
        elif str(row["feature"]) == "regime_state":
            threshold = "avoid true_early_trend / failed_recovery / rebound_chop"
        elif str(row["feature"]) == "sector_bucket":
            threshold = "semis and software/internet risk bucket"
        lines.append(f"| {row['feature']} | {threshold} | importance {row['importance']:.3f}, stability {row['stability']:.3f} |")
    lines.extend(["", "## Actionable Rules", "### Block Rules"])
    for row in rule_candidates_df[rule_candidates_df["rule_type"] == "block"].sort_values(["robustness_level", "expectancy_delta"], ascending=[False, False]).head(3).to_dict("records"):
        lines.append(f"- `{row['rule_logic']}` -> expectancy delta {row['expectancy_delta']:.3f}, drawdown delta {row['drawdown_delta']:.3f}, robustness `{row['robustness_level']}`")
    lines.extend(["", "### Allow Rules"])
    for row in rule_candidates_df[rule_candidates_df["rule_type"] == "allow"].sort_values(["robustness_level", "expectancy_delta"], ascending=[False, False]).head(2).to_dict("records"):
        lines.append(f"- `{row['rule_logic']}` -> expectancy delta {row['expectancy_delta']:.3f}, robustness `{row['robustness_level']}`")
    lines.extend(["", "### Size Rules"])
    for row in rule_candidates_df[rule_candidates_df["rule_type"] == "size"].sort_values(["robustness_level", "expectancy_delta"], ascending=[False, False]).head(3).to_dict("records"):
        lines.append(f"- `{row['rule_logic']}` -> expectancy delta {row['expectancy_delta']:.3f}, drawdown delta {row['drawdown_delta']:.3f}, robustness `{row['robustness_level']}`")
    lines.extend(["", "### Exit Rules"])
    for row in rule_candidates_df[rule_candidates_df["rule_type"] == "exit"].sort_values(["robustness_level", "expectancy_delta"], ascending=[False, False]).head(3).to_dict("records"):
        lines.append(f"- `{row['rule_logic']}` -> expectancy delta {row['expectancy_delta']:.3f}, drawdown delta {row['drawdown_delta']:.3f}, robustness `{row['robustness_level']}`")
    lines.extend(
        [
            "",
            "## Pseudocode",
            "```python",
            "if regime in BAD_REGIMES:",
            "    block",
            "elif sector_concentration > high_band:",
            "    reduce_or_block",
            "elif entry_quality < acceptable_band:",
            "    skip",
            "else:",
            "    enter",
            "",
            "if ft_3d_band == \"weak\" and retrace_3d_band == \"high\":",
            "    exit_next_open",
            "elif ft_3d_band == \"mixed\":",
            "    reduce_next_open",
            "else:",
            "    hold",
            "```",
            "",
            "## Supporting Notes",
            f"- Worst month (ALL losers): `{loss_by_month[loss_by_month['scenario'] == 'ALL'].iloc[0]['month_bucket']}`" if not loss_by_month.empty else "- No recent 6M losses found.",
            f"- Largest losing symbol (ALL losers): `{loss_by_symbol[loss_by_symbol['scenario'] == 'ALL'].iloc[0]['symbol']}`" if not loss_by_symbol.empty else "",
            f"- Largest losing entry type (ALL losers): `{loss_by_entry_type[loss_by_entry_type['scenario'] == 'ALL'].iloc[0]['entry_type']}`" if not loss_by_entry_type.empty else "",
            f"- `signal_to_entry_delay_bars` is constant `{int(dual_map_trade_frame['signal_to_entry_delay_bars'].dropna().iloc[0])}` and treated as non-informative." if not dual_map_trade_frame.empty else "",
            "- This report converts current findings into implementable structural logic. It does not optimize parameters or introduce a new strategy.",
        ]
    )
    (out_dir / "task_323_best_combo_evaluation.md").write_text("\n".join([line for line in lines if line != ""]) + "\n", encoding="utf-8")
    print(f"written_dir={out_dir}")
    return 0

    primary = summary_df.sort_values(["selection_group", "sharpe", "max_drawdown_pct"], ascending=[True, False, True]).iloc[0]
    status = "추가 검증 1순위"
    if not bool(primary["recent_6m_holds_up"]):
        status = "추가 검증 1순위 (보류)"

    regime_filter_too_coarse = False
    regime_confidence = "낮음"
    regime_evidence = "insufficient regime clustering evidence"
    if not regime_performance_df.empty:
        top_bad = regime_performance_df.iloc[0]
        second_bad = regime_performance_df.iloc[1] if len(regime_performance_df) > 1 else None
        top_share = float(top_bad["loss_contribution_share"])
        second_share = float(second_bad["loss_contribution_share"]) if second_bad is not None else 0.0
        regime_filter_too_coarse = top_share >= 0.45 or (top_share + second_share) >= 0.70
        regime_confidence = "보통" if regime_filter_too_coarse else "낮음"
        regime_evidence = f"worst regime `{top_bad['reclustered_regime']}` loss share {top_share:.2f}, expectancy {float(top_bad['expectancy_r']):.3f}R"

    late_chase = False
    late_confidence = "낮음"
    late_evidence = "insufficient winner vs loser timing separation"
    if not winner_loser_df.empty:
        compare_all = winner_loser_df[winner_loser_df["scenario"] == "ALL"].set_index("feature")
        gate_features = {"ret_20d_pre", "dist_to_sma20_pct", "gap_over_planned_entry_pct", "breakout_strength_pct"}
        follow_features = {"follow_through_3d_pct", "follow_through_5d_pct", "post_breakout_retrace_3d_pct", "post_breakout_retrace_5d_pct", "adverse_excursion_3d_pct", "adverse_excursion_5d_pct"}
        gate_hits = 0
        for feature in gate_features:
            if feature in compare_all.index:
                row = compare_all.loc[feature]
                if row["direction_label"] == "losers_higher" and pd.notna(row["effect_size"]) and abs(float(row["effect_size"])) >= 0.15:
                    gate_hits += 1
        follow_hits = 0
        for feature in follow_features:
            if feature in compare_all.index:
                row = compare_all.loc[feature]
                if feature.startswith("follow_through") and row["direction_label"] == "losers_lower" and pd.notna(row["effect_size"]) and abs(float(row["effect_size"])) >= 0.15:
                    follow_hits += 1
                if (feature.startswith("post_breakout_retrace") or feature.startswith("adverse_excursion")) and row["direction_label"] == "losers_higher" and pd.notna(row["effect_size"]) and abs(float(row["effect_size"])) >= 0.15:
                    follow_hits += 1
        late_chase = gate_hits >= 2 and follow_hits >= 2
        late_confidence = "보통" if late_chase else "낮음"
        late_evidence = f"gate hits {gate_hits}, follow-through hits {follow_hits}"

    sector_concentrated = False
    sector_confidence = "낮음"
    sector_evidence = "no dominant sector concentration"
    if not cross_sectional_df.empty:
        sector_losers = cross_sectional_df[(cross_sectional_df["analysis_set"] == "losers") & (cross_sectional_df["group_type"] == "sector_bucket")].sort_values("loss_share", ascending=False)
        if not sector_losers.empty:
            leader = sector_losers.iloc[0]
            sector_concentrated = float(leader["loss_share"]) >= 0.45 and str(leader["group_value"]) in {"semis", "software/internet", "other tech"}
            sector_confidence = "보통" if sector_concentrated else "낮음"
            sector_evidence = f"leading loser sector `{leader['group_value']}` loss share {float(leader['loss_share']):.2f}"

    tail_confidence = "보통" if tail_event_driven else "낮음"
    tail_evidence = "worst-decile share unavailable"
    if not worst_decile_analysis_df.empty and "__overall__" in set(worst_decile_analysis_df["feature"]):
        tail_row = worst_decile_analysis_df[worst_decile_analysis_df["feature"] == "__overall__"].iloc[0]
        tail_evidence = f"worst decile loss share {float(tail_row['worst_loss_share']):.2f}"

    summary_hypothesis_rows = [
        {"hypothesis": "regime filter too coarse", "result": regime_filter_too_coarse, "confidence": regime_confidence, "evidence": regime_evidence},
        {"hypothesis": "breakout is late-chase", "result": late_chase, "confidence": late_confidence, "evidence": late_evidence},
        {"hypothesis": "losses driven by tail events", "result": tail_event_driven, "confidence": tail_confidence, "evidence": tail_evidence},
        {"hypothesis": "losses concentrated in specific sectors", "result": sector_concentrated, "confidence": sector_confidence, "evidence": sector_evidence},
    ]

    lines = [
        "# Task 323 Failure Map",
        "",
        "## Executive Summary",
        f"- Evaluation end date: {latest_end.date()}",
        f"- Anchored OOS window: {anchored_window.test_start.date()} ~ {anchored_window.test_end.date()}",
        f"- Mixed top-3 count: {len(summary_df)}",
        f"- Primary status: {status}",
        f"- Primary candidate: `{primary['scenario']}`",
        "",
        "## Summary Table",
        "| Hypothesis | Result | Confidence | Key Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for row in summary_hypothesis_rows:
        lines.append(f"| {row['hypothesis']} | {row['result']} | {row['confidence']} | {row['evidence']} |")

    lines.extend(
        [
            "",
            "## Failure Anatomy",
            "| Category | Key Pattern |",
            "| --- | --- |",
            f"| regime | {regime_evidence} |",
            f"| entry timing | {late_evidence} |",
            f"| volatility | refer to loser distribution and entry timing tables |",
            f"| cross-section | {sector_evidence} |",
            "",
            "## Actionable Structural Insights",
        ]
    )
    actionable_lines: list[str] = []
    if regime_filter_too_coarse and not regime_performance_df.empty:
        actionable_lines.append(f"- Disable or de-prioritize entries in `{regime_performance_df.iloc[0]['reclustered_regime']}` until that regime gate is revalidated.")
    if late_chase:
        actionable_lines.append("- Block entries that combine high pre-entry extension with weak early follow-through and fast retrace signatures.")
    if sector_concentrated:
        actionable_lines.append("- Add a cross-sectional concentration block when losses crowd into a narrow tech or semis cohort beyond normal trade share.")
    if tail_event_driven:
        actionable_lines.append("- Add tail-risk guards for the worst-loss cluster month, regime, or sector before considering deployment.")
    if not actionable_lines:
        actionable_lines.append("- No single robust block condition is confirmed yet; any new guard should be treated as a hypothesis and validated out of sample.")
    lines.extend(actionable_lines)

    lines.extend(
        [
            "",
            "## Supporting Notes",
            f"- Worst month (ALL losers): `{loss_by_month[loss_by_month['scenario'] == 'ALL'].iloc[0]['month_bucket']}`" if not loss_by_month.empty else "- No recent 6M losses found.",
            f"- Largest losing symbol (ALL losers): `{loss_by_symbol[loss_by_symbol['scenario'] == 'ALL'].iloc[0]['symbol']}`" if not loss_by_symbol.empty else "",
            f"- Largest losing entry type (ALL losers): `{loss_by_entry_type[loss_by_entry_type['scenario'] == 'ALL'].iloc[0]['entry_type']}`" if not loss_by_entry_type.empty else "",
            f"- `signal_to_entry_delay_bars` is constant `{int(failure_analysis_df['signal_to_entry_delay_bars'].dropna().iloc[0])}` and treated as non-informative." if not failure_analysis_df.empty else "",
            "- This report is for failure-condition mapping only. It does not propose new parameter optimization or new strategy variants.",
        ]
    )

    (out_dir / "task_323_best_combo_evaluation.md").write_text("\n".join([line for line in lines if line != ""]) + "\n", encoding="utf-8")
    print(f"written_dir={out_dir}")
    return 0
    loss_trade_anatomy_df = all_recent_trades[all_recent_trades["realized_R"] < 0].copy() if not all_recent_trades.empty else pd.DataFrame()
    loss_by_month = _loss_breakdown(all_recent_trades, "month_bucket")
    loss_by_symbol = _loss_breakdown(all_recent_trades, "symbol")
    loss_by_entry_type = _loss_breakdown(all_recent_trades, "entry_type")
    loss_by_regime = _loss_breakdown(all_recent_trades, "market_regime_base")
    loss_by_regime_detail = _loss_breakdown(all_recent_trades, "market_regime_detail")
    loss_feature_summary = _feature_summary(loss_trade_anatomy_df)
    loss_feature_bins = _feature_bin_breakdown(loss_trade_anatomy_df)

    summary_df.to_csv(out_dir / "selected_combo_rankings.csv", index=False)
    contribution_out.to_csv(out_dir / "selected_symbol_contributions.csv", index=False)
    fill_df.to_csv(out_dir / "selected_fill_diagnostics.csv", index=False)
    recent_df.to_csv(out_dir / "selected_recent_6m_metrics.csv", index=False)
    exclusion_df.to_csv(out_dir / "selected_exclusion_impact.csv", index=False)
    selected_overlap_df.to_csv(out_dir / "selected_overlap_support.csv", index=False)
    neighborhood_df.to_csv(out_dir / "selected_neighborhood_stability.csv", index=False)
    same_bar_out.to_csv(out_dir / "selected_same_bar_comparison.csv", index=False)
    loss_by_month.to_csv(out_dir / "selected_recent_6m_loss_by_month.csv", index=False)
    loss_by_symbol.to_csv(out_dir / "selected_recent_6m_loss_by_symbol.csv", index=False)
    loss_by_entry_type.to_csv(out_dir / "selected_recent_6m_loss_by_entry_type.csv", index=False)
    loss_by_regime.to_csv(out_dir / "selected_recent_6m_loss_by_regime.csv", index=False)
    loss_trade_anatomy_df.to_csv(out_dir / "selected_recent_6m_loss_trade_anatomy.csv", index=False)
    loss_by_regime_detail.to_csv(out_dir / "selected_recent_6m_loss_by_regime_detail.csv", index=False)
    loss_feature_summary.to_csv(out_dir / "selected_recent_6m_loss_feature_summary.csv", index=False)
    loss_feature_bins.to_csv(out_dir / "selected_recent_6m_loss_feature_bins.csv", index=False)
    walk_df.to_csv(out_dir / "selected_top3_oos_walk_forward.csv", index=False)
    anchored_df.to_csv(out_dir / "selected_top3_oos_anchored.csv", index=False)
    rolling_df.to_csv(out_dir / "selected_top3_oos_rolling.csv", index=False)
    reliability_df.to_csv(out_dir / "selected_top3_sharpe_reliability.csv", index=False)

    primary = summary_df.sort_values(["selection_group", "sharpe", "max_drawdown_pct"], ascending=[True, False, True]).iloc[0]
    status = "추가 검증 1순위"
    if not bool(primary["recent_6m_holds_up"]):
        status = "추가 검증 1순위 (보류)"

    pooled_regime_detail = loss_by_regime_detail[loss_by_regime_detail["scenario"] == "ALL"].sort_values("loss_r_sum")
    dominant_regime_detail = str(pooled_regime_detail.iloc[0]["market_regime_detail"]) if not pooled_regime_detail.empty else ""
    pooled_feature_summary = loss_feature_summary[loss_feature_summary["scenario"] == "ALL"].set_index("feature") if not loss_feature_summary.empty else pd.DataFrame()
    ret20_mean = float(pooled_feature_summary.loc["ret_20d_pre", "mean"]) if "ret_20d_pre" in pooled_feature_summary.index else math.nan
    dist20_mean = float(pooled_feature_summary.loc["dist_to_sma20_pct", "mean"]) if "dist_to_sma20_pct" in pooled_feature_summary.index else math.nan
    gap_plan_mean = float(pooled_feature_summary.loc["gap_over_planned_entry_pct", "mean"]) if "gap_over_planned_entry_pct" in pooled_feature_summary.index else math.nan
    vol_ratio_mean = float(pooled_feature_summary.loc["vol_expansion_ratio", "mean"]) if "vol_expansion_ratio" in pooled_feature_summary.index else math.nan
    supports_regime_coarse = dominant_regime_detail in {"risk_on_overextended", "risk_on_high_vol_slowdown", "risk_on_cooling"}
    supports_late_chase = (
        (not math.isnan(ret20_mean) and ret20_mean >= 0.12)
        or (not math.isnan(dist20_mean) and dist20_mean >= 0.05)
        or (not math.isnan(gap_plan_mean) and gap_plan_mean >= 0.01)
        or (not math.isnan(vol_ratio_mean) and vol_ratio_mean >= 1.25)
    )

    lines = [
        "# Task 323+ Best Structural Breakout Combo Evaluation",
        "",
        "## Executive Summary",
        f"- Evaluation end date: {latest_end.date()}",
        f"- Candidate selection train window: {timestamps[0].date()} ~ {anchored_window.train_end.date()}",
        f"- Anchored OOS window: {anchored_window.test_start.date()} ~ {anchored_window.test_end.date()}",
        f"- Mixed top-3 count: {len(summary_df)}",
        f"- Primary status: {status}",
        f"- Primary candidate: `{primary['scenario']}`",
        "",
        "## Mixed Top 3 Overview",
    ]
    for row in summary_df.itertuples(index=False):
        lines.extend(
            [
                f"### `{row.scenario}`",
                f"- Selection group: `{row.selection_group}`",
                f"- Full-period: CAGR {row.cagr_pct:.2f}%, Sharpe {row.sharpe:.3f}, MDD {row.max_drawdown_pct:.2f}%, Expectancy {row.expectancy_r:.3f}R, Trades {int(row.trade_count)}",
                f"- Anchored OOS: Return {row.anchored_oos_return_pct:.2f}%, Win rate {row.anchored_oos_win_rate:.3f}, Expectancy {row.anchored_oos_expectancy_r:.3f}R",
                f"- Overfit risk: {_report_level(row.overfit_level)} ({row.overfit_reason})",
                f"- Practicality: {_report_level(row.practicality_level)} ({row.practicality_reason})",
                f"- Symbol concentration: {_report_level(row.concentration_level)} ({row.concentration_reason})",
                f"- Sharpe reliability: DSR={row.dsr if not pd.isna(row.dsr) else 'NaN'}, adjusted Sharpe={row.trial_count_adjusted_sharpe if not pd.isna(row.trial_count_adjusted_sharpe) else 'NaN'} ({_report_level(row.sharpe_confidence_label)})",
                f"- Recent 6M hold-up: `{bool(row.recent_6m_holds_up)}`",
                "",
            ]
        )

    lines.extend(
        [
            "## 최근 6개월 손실 분해",
            f"- Worst month (ALL): `{loss_by_month[loss_by_month['scenario'] == 'ALL'].iloc[0]['month_bucket']}`" if not loss_by_month.empty else "- No recent 6M losses found.",
            f"- Largest losing symbol (ALL): `{loss_by_symbol[loss_by_symbol['scenario'] == 'ALL'].iloc[0]['symbol']}`" if not loss_by_symbol.empty else "",
            f"- Largest losing entry type (ALL): `{loss_by_entry_type[loss_by_entry_type['scenario'] == 'ALL'].iloc[0]['entry_type']}`" if not loss_by_entry_type.empty else "",
            f"- Largest losing regime base (ALL): `{loss_by_regime[loss_by_regime['scenario'] == 'ALL'].iloc[0]['market_regime_base']}`" if not loss_by_regime.empty else "",
            "",
            "## Detailed Risk-On Regime Review",
            f"- Dominant detailed regime (ALL): `{dominant_regime_detail}`" if dominant_regime_detail else "- No detailed regime concentration found.",
            f"- Hypothesis `regime filter too coarse`: `{supports_regime_coarse}`",
            "- Evidence rule: losses clustering in `risk_on_overextended`, `risk_on_high_vol_slowdown`, or `risk_on_cooling` supports the hypothesis.",
            "",
            "## Recent 6M Loss Trade Anatomy",
            f"- Pooled 20d pre-entry return mean: `{ret20_mean:.4f}`" if not math.isnan(ret20_mean) else "- Pooled 20d pre-entry return mean: `NaN`",
            f"- Pooled distance to 20DMA mean: `{dist20_mean:.4f}`" if not math.isnan(dist20_mean) else "- Pooled distance to 20DMA mean: `NaN`",
            f"- Pooled gap over planned entry mean: `{gap_plan_mean:.4f}`" if not math.isnan(gap_plan_mean) else "- Pooled gap over planned entry mean: `NaN`",
            f"- Pooled volatility expansion mean: `{vol_ratio_mean:.4f}`" if not math.isnan(vol_ratio_mean) else "- Pooled volatility expansion mean: `NaN`",
            f"- Hypothesis `breakout became late-chase in recent 6M`: `{supports_late_chase}`",
            "",
            "## OOS Revalidation",
            "- Note: anchored OOS is a corrected-engine rerun. Walk-forward and rolling OOS use corrected full-period trade-log slicing as a runtime-efficient proxy.",
        ]
    )
    for row in summary_df.itertuples(index=False):
        lines.append(
            f"- `{row.scenario}`: anchored {row.anchored_oos_return_pct:.2f}%, walk-forward median {row.walk_forward_median_return_pct:.2f}%, rolling median {row.rolling_oos_median_return_pct:.2f}%"
        )
    for scenario in selected_scenarios:
        scenario_summary = loss_feature_summary[loss_feature_summary["scenario"] == scenario].set_index("feature") if not loss_feature_summary.empty else pd.DataFrame()
        if scenario_summary.empty:
            continue
        lines.extend(
            [
                f"- `{scenario}` anatomy:",
                f"  20d pre-entry return mean `{float(scenario_summary.loc['ret_20d_pre', 'mean']):.4f}`" if "ret_20d_pre" in scenario_summary.index else "  20d pre-entry return mean `NaN`",
                f"  distance to 20DMA mean `{float(scenario_summary.loc['dist_to_sma20_pct', 'mean']):.4f}`" if "dist_to_sma20_pct" in scenario_summary.index else "  distance to 20DMA mean `NaN`",
                f"  gap over planned entry mean `{float(scenario_summary.loc['gap_over_planned_entry_pct', 'mean']):.4f}`" if "gap_over_planned_entry_pct" in scenario_summary.index else "  gap over planned entry mean `NaN`",
                f"  vol expansion mean `{float(scenario_summary.loc['vol_expansion_ratio', 'mean']):.4f}`" if "vol_expansion_ratio" in scenario_summary.index else "  vol expansion mean `NaN`",
            ]
        )
    lines.extend(
        [
            "",
            "## Sharpe Reliability",
        ]
    )
    for row in summary_df.itertuples(index=False):
        lines.append(
            f"- `{row.scenario}`: raw Sharpe {row.sharpe:.3f}, adjusted Sharpe {row.trial_count_adjusted_sharpe if not pd.isna(row.trial_count_adjusted_sharpe) else 'NaN'}, DSR {row.dsr if not pd.isna(row.dsr) else 'NaN'}, confidence {_report_level(row.sharpe_confidence_label)}"
        )
    lines.extend(
        [
            "",
            "## Final Recommendation",
            f"- Primary candidate status: {status}",
            f"- Candidate: `{primary['scenario']}`",
            "- Interpretation: this is **not** a 실전 투입 recommendation. It is the **추가 검증 1순위** candidate among the current mixed top-3 set.",
            f"- Regime-filter hypothesis supported: `{supports_regime_coarse}`",
            f"- Late-chase breakout hypothesis supported: `{supports_late_chase}`",
            "- If anchored OOS and rolling OOS remain negative, keep the candidate in observation or rejection flow rather than production deployment.",
        ]
    )

    (out_dir / "task_323_best_combo_evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written_dir={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
