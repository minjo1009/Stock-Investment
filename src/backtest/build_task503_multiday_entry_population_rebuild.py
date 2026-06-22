from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import (
    TARGET_AVG_NET,
    TARGET_COUNT_MAX,
    TARGET_COUNT_MIN,
    TARGET_ENTRY_REDUCE_MAX,
    TARGET_SAME_DAY_EXIT_MAX,
    TARGET_WIN,
    aggregate,
    failure_decomposition,
    goal_pass,
    holding_quality,
    load_daily_map,
    quality,
    run_policy_grid,
)


DEFAULT_THEME_MAP = Path("data/raw/theme_universe_10x7.csv")
DEFAULT_DAILY_DIR = Path("data/raw/us_daily_breadth_top500")
DEFAULT_INTRADAY_DIR = Path("data/raw/us_intraday")
DEFAULT_MARKET_PANEL = Path("docs/reports/task_489_broad_regime_cell_portfolio/broad_market_state_panel.csv")
DEFAULT_OUT_DIR = Path("docs/reports/task_503_multiday_entry_population_rebuild")


@dataclass(frozen=True)
class Task503Artifacts:
    entry_source_coverage_audit: pd.DataFrame
    multiday_entry_candidate_panel: pd.DataFrame
    entry_population_state_quality: pd.DataFrame
    multiday_policy_candidate_pool: pd.DataFrame
    selected_multiday_lifecycle_panel: pd.DataFrame
    selected_multiday_quality: pd.DataFrame
    selected_multiday_split_quality: pd.DataFrame
    selected_multiday_holding_quality: pd.DataFrame
    selected_multiday_failure_decomposition: pd.DataFrame
    task_503_decision: pd.DataFrame


def build_task503_multiday_entry_population_rebuild(
    *,
    theme_map_path: Path = DEFAULT_THEME_MAP,
    daily_dir: Path = DEFAULT_DAILY_DIR,
    intraday_dir: Path = DEFAULT_INTRADAY_DIR,
    market_panel_path: Path = DEFAULT_MARKET_PANEL,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task503Artifacts:
    theme_map = pd.read_csv(theme_map_path)
    theme_map["symbol"] = theme_map["symbol"].astype(str).str.upper()
    source_audit, daily_map = load_daily_map(theme_map["symbol"].tolist(), daily_dir)
    market = pd.read_csv(market_panel_path) if market_panel_path.exists() else pd.DataFrame()
    daily_features = build_daily_entry_features(theme_map, daily_map, market)
    entries = build_intraday_confirmed_entries(daily_features, intraday_dir)
    if entries.empty:
        pool, selected = pd.DataFrame(), pd.DataFrame()
    else:
        pool, selected = run_policy_grid(entries, daily_map)
    selected_quality = pd.DataFrame([aggregate(selected)])
    selected_split = quality(selected, ["split_name"])
    selected_holding = holding_quality(selected)
    selected_failure = failure_decomposition(selected)
    state_quality = entry_state_coverage(entries)
    decision = build_decision(source_audit, entries, pool, selected, selected_quality)
    artifacts = Task503Artifacts(
        source_audit,
        entries,
        state_quality,
        pool,
        selected,
        selected_quality,
        selected_split,
        selected_holding,
        selected_failure,
        decision,
    )
    write_artifacts(artifacts, out_dir)
    return artifacts


def build_daily_entry_features(theme_map: pd.DataFrame, daily_map: dict[str, pd.DataFrame], market: pd.DataFrame) -> pd.DataFrame:
    frames = []
    theme_lookup = theme_map.set_index("symbol")[["theme", "role"]].to_dict(orient="index")
    for symbol, daily in daily_map.items():
        if symbol not in theme_lookup:
            continue
        df = daily.copy()
        df["symbol"] = symbol
        df["theme_id"] = theme_lookup[symbol]["theme"]
        df["role"] = theme_lookup[symbol]["role"]
        by_close = df["close"]
        df["ret_5d"] = by_close.pct_change(5)
        df["ret_20d"] = by_close.pct_change(20)
        df["ret_60d"] = by_close.pct_change(60)
        df["ma20"] = by_close.rolling(20, min_periods=10).mean()
        df["ma50"] = by_close.rolling(50, min_periods=20).mean()
        df["high20"] = df["high"].rolling(20, min_periods=10).max()
        df["high60"] = df["high"].rolling(60, min_periods=20).max()
        df["vol20"] = df["volume"].rolling(20, min_periods=10).mean()
        for col in ["ret_5d", "ret_20d", "ret_60d", "ma20", "ma50", "high20", "high60", "vol20"]:
            df[f"{col}_prev"] = df[col].shift(1)
        df["close_prev"] = df["close"].shift(1)
        df["volume_ratio_prev"] = df["volume"].shift(1) / df["vol20_prev"].replace(0, np.nan)
        df["near_high60_prev"] = df["close_prev"] / df["high60_prev"].replace(0, np.nan)
        df["trend_stack_prev"] = (df["close_prev"].gt(df["ma20_prev"]) & df["ma20_prev"].gt(df["ma50_prev"])).astype(int)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    features = pd.concat(frames, ignore_index=True)
    theme_stats = (
        features.groupby(["trade_date", "theme_id"], dropna=False)
        .agg(
            theme_ret20_prev=("ret_20d_prev", "mean"),
            theme_breadth20_prev=("ret_20d_prev", lambda s: float((s > 0).mean())),
            theme_volume_ratio_prev=("volume_ratio_prev", "mean"),
        )
        .reset_index()
    )
    theme_stats["theme_rank_prev"] = theme_stats.groupby("trade_date")["theme_ret20_prev"].rank(ascending=False, method="min")
    features = features.merge(theme_stats, on=["trade_date", "theme_id"], how="left")
    if not market.empty and "score_date" in market.columns:
        market_keep = market[["score_date", "broad_market_score", "broad_market_stress", "breadth_20d", "market_ret_20d", "liquidity_ratio", "vol_ratio"]].copy()
        features = features.merge(market_keep, left_on="trade_date", right_on="score_date", how="left")
    features["multi_day_market_state_v4"] = features.apply(classify_market, axis=1)
    features["theme_regime_state_v4"] = features.apply(classify_theme, axis=1)
    features["symbol_multiday_setup_state"] = features.apply(classify_symbol_setup, axis=1)
    features["candidate_daily_setup_flag"] = (
        features["multi_day_market_state_v4"].isin(["persistent_broad_risk_on", "constructive_risk_on"])
        & features["theme_regime_state_v4"].isin(["persistent_theme_leader", "theme_participation", "narrow_theme_leader"])
        & features["symbol_multiday_setup_state"].isin(["trend_persistence_near_high", "volume_confirmed_reclaim", "early_acceleration"])
    ).astype(int)
    return features[features["candidate_daily_setup_flag"].eq(1)].copy()


def classify_market(row: pd.Series) -> str:
    score = _num(row, "broad_market_score")
    stress = _num(row, "broad_market_stress")
    if pd.notna(score) and score >= 4 and (pd.isna(stress) or stress <= 2):
        return "persistent_broad_risk_on"
    if pd.notna(score) and score >= 3:
        return "constructive_risk_on"
    if pd.notna(stress) and stress >= 4:
        return "weak_or_stressed"
    return "mixed_or_transition"


def classify_theme(row: pd.Series) -> str:
    rank = _num(row, "theme_rank_prev")
    ret = _num(row, "theme_ret20_prev")
    breadth = _num(row, "theme_breadth20_prev")
    volume = _num(row, "theme_volume_ratio_prev")
    if pd.notna(rank) and rank <= 2 and pd.notna(ret) and ret > 0.05 and pd.notna(breadth) and breadth >= 0.60:
        return "persistent_theme_leader"
    if pd.notna(ret) and ret > 0 and pd.notna(breadth) and breadth >= 0.55:
        return "theme_participation"
    if pd.notna(rank) and rank <= 3 and pd.notna(volume) and volume >= 1.1:
        return "narrow_theme_leader"
    return "mixed_theme"


def classify_symbol_setup(row: pd.Series) -> str:
    ret20 = _num(row, "ret_20d_prev")
    ret60 = _num(row, "ret_60d_prev")
    near_high = _num(row, "near_high60_prev")
    vol_ratio = _num(row, "volume_ratio_prev")
    trend_stack = int(_num(row, "trend_stack_prev", 0) or 0)
    ret5 = _num(row, "ret_5d_prev")
    if trend_stack and pd.notna(ret20) and ret20 > 0.05 and pd.notna(near_high) and near_high >= 0.95:
        return "trend_persistence_near_high"
    if pd.notna(ret5) and ret5 > 0.03 and pd.notna(vol_ratio) and vol_ratio >= 1.3:
        return "volume_confirmed_reclaim"
    if pd.notna(ret20) and ret20 > 0.08 and pd.notna(ret60) and ret60 > ret20:
        return "early_acceleration"
    return "weak_or_unconfirmed"


def build_intraday_confirmed_entries(daily_candidates: pd.DataFrame, intraday_dir: Path) -> pd.DataFrame:
    rows = []
    intraday_cache: dict[str, pd.DataFrame] = {}
    for symbol, symbol_candidates in daily_candidates.groupby("symbol", dropna=False):
        symbol = str(symbol).upper()
        path = intraday_dir / f"{symbol}.csv"
        if not path.exists():
            continue
        intraday_cache[symbol] = load_intraday(path)
        by_date = {date: group for date, group in intraday_cache[symbol].groupby("trade_date", dropna=False)}
        for row in symbol_candidates.to_dict(orient="records"):
            day = by_date.get(str(row["trade_date"]))
            if day is None or day.empty:
                continue
            confirmed = first_intraday_confirmation(day)
            if confirmed is None:
                continue
            out = dict(row)
            out.update(confirmed)
            out["lifecycle_id"] = f"TASK503|{symbol}|{out['entry_ts'].strftime('%Y%m%dT%H%M%SZ')}"
            out["split_name"] = split_name(out["entry_ts"])
            out["quarter"] = f"{out['entry_ts'].year}Q{((out['entry_ts'].month - 1) // 3) + 1}"
            out["inferred_lifecycle_matching_used_flag"] = 0
            out["label_used_in_assignment_flag"] = 0
            rows.append(out)
    return pd.DataFrame(rows)


def load_intraday(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [str(c).lower() for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp").reset_index(drop=True)
    df["timestamp_et"] = df["timestamp"].dt.tz_convert("America/New_York")
    df["trade_date"] = df["timestamp_et"].dt.date.astype(str)
    df["minute"] = df["timestamp_et"].dt.hour * 60 + df["timestamp_et"].dt.minute
    return df[df["minute"].between(9 * 60 + 30, 15 * 60 + 45)].copy()


def first_intraday_confirmation(day: pd.DataFrame) -> dict[str, object] | None:
    day = day.copy().reset_index(drop=True)
    day["day_high_so_far"] = day["high"].cummax()
    day["day_low_so_far"] = day["low"].cummin()
    day["range_pos_so_far"] = (day["close"] - day["day_low_so_far"]) / (day["day_high_so_far"] - day["day_low_so_far"]).replace(0, np.nan)
    day["intraday_ret_from_open"] = day["close"] / float(day.iloc[0]["open"]) - 1.0
    day["vwap_ok"] = day["close"].ge(day["vwap"]) if "vwap" in day.columns else day["close"].ge(day["open"])
    day["breakout_so_far"] = day["close"].gt(day["day_high_so_far"].shift(1))
    candidate = day[
        day["vwap_ok"].fillna(False)
        & day["range_pos_so_far"].ge(0.70)
        & day["intraday_ret_from_open"].ge(0.002)
        & (day["breakout_so_far"].fillna(False) | day["range_pos_so_far"].ge(0.85))
    ]
    if candidate.empty:
        return None
    bar = candidate.iloc[0]
    minute = int(bar["minute"])
    if minute < 10 * 60 + 30:
        timing = "opening_drive"
    elif minute < 14 * 60:
        timing = "midday_continuation"
    else:
        timing = "late_day_confirmation"
    return {
        "entry_ts": bar["timestamp"],
        "entry_price": float(bar["close"]),
        "intraday_entry_state_v4": "intraday_breakout_acceptance",
        "microstructure_state_v4": "microstructure_not_available",
        "timing_state": timing,
        "close": float(bar["close"]),
        "volume": float(bar["volume"]),
        "range_pos": float(bar["range_pos_so_far"]),
        "intraday_ret_from_open": float(bar["intraday_ret_from_open"]),
    }


def split_name(ts: pd.Timestamp) -> str:
    if ts >= pd.Timestamp("2026-01-01", tz="UTC"):
        return "recent_oos"
    if ts >= pd.Timestamp("2025-07-01", tz="UTC"):
        return "validation"
    return "train_design"


def build_decision(
    source_audit: pd.DataFrame,
    entries: pd.DataFrame,
    pool: pd.DataFrame,
    selected: pd.DataFrame,
    quality_df: pd.DataFrame,
) -> pd.DataFrame:
    metrics = quality_df.iloc[0].to_dict() if not quality_df.empty else {}
    return pd.DataFrame(
        [
            {
                "task_id": "Task503",
                "daily_source_symbol_coverage": float(source_audit["available_flag"].mean()) if not source_audit.empty else 0.0,
                "entry_candidate_count": int(len(entries)),
                "policy_candidate_count": int(len(pool)),
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "median_holding_days": metrics.get("median_holding_days", pd.NA),
                "same_day_exit_share": metrics.get("same_day_exit_share", pd.NA),
                "goal_achieved_flag": int(goal_pass(metrics)) if metrics else 0,
                "inferred_lifecycle_matching_used_flag": 0,
                "label_used_in_assignment_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def entry_state_coverage(entries: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame()
    keys = ["multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4"]
    return (
        entries.groupby(keys, dropna=False)
        .agg(entry_candidate_count=("lifecycle_id", "count"), symbol_count=("symbol", "nunique"), theme_count=("theme_id", "nunique"))
        .reset_index()
        .sort_values("entry_candidate_count", ascending=False)
    )


def _num(row: pd.Series, col: str, default: float = np.nan) -> float:
    try:
        return float(row.get(col, default))
    except (TypeError, ValueError):
        return default


def write_artifacts(artifacts: Task503Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.entry_source_coverage_audit.to_csv(out_dir / "entry_source_coverage_audit.csv", index=False)
    artifacts.multiday_entry_candidate_panel.to_csv(out_dir / "multiday_entry_candidate_panel.csv", index=False)
    artifacts.entry_population_state_quality.to_csv(out_dir / "entry_population_state_quality.csv", index=False)
    artifacts.multiday_policy_candidate_pool.to_csv(out_dir / "multiday_policy_candidate_pool.csv", index=False)
    artifacts.selected_multiday_lifecycle_panel.to_csv(out_dir / "selected_multiday_lifecycle_panel.csv", index=False)
    artifacts.selected_multiday_quality.to_csv(out_dir / "selected_multiday_quality.csv", index=False)
    artifacts.selected_multiday_split_quality.to_csv(out_dir / "selected_multiday_split_quality.csv", index=False)
    artifacts.selected_multiday_holding_quality.to_csv(out_dir / "selected_multiday_holding_quality.csv", index=False)
    artifacts.selected_multiday_failure_decomposition.to_csv(out_dir / "selected_multiday_failure_decomposition.csv", index=False)
    artifacts.task_503_decision.to_csv(out_dir / "task_503_decision.csv", index=False)
    (out_dir / "task_503_multiday_entry_population_rebuild.md").write_text(build_report(artifacts), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def build_report(artifacts: Task503Artifacts) -> str:
    d = artifacts.task_503_decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 503 - Multi-Day Entry Population Rebuild",
            "",
            "## Decision Summary",
            "",
            f"- Goal achieved: {d['goal_achieved_flag']}",
            f"- Entry candidates: {d['entry_candidate_count']}",
            f"- Count / avg net / win / entry_reduce: {d['selected_count']} / {float(d['selected_avg_net_pct']):.3f}% / {float(d['selected_win_rate']):.1%} / {float(d['selected_entry_reduce_rate']):.1%}",
            f"- Median holding days / same-day exit: {float(d['median_holding_days']):.2f} / {float(d['same_day_exit_share']):.1%}",
            "- Inferred lifecycle matching used: NO",
            "- Label used in assignment: NO",
            "",
            "## Quant Expert Report",
            "",
            "This task rebuilds the entry population from raw daily and intraday bars. Multi-day market/theme state and symbol setup are computed before the intraday confirmation bar; outcomes are generated only by the later multi-day policy simulation.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "기존 후보를 재활용하지 않고, 좋은 시장/테마와 종목의 중기 구조가 맞을 때 intraday 확인까지 받은 새 후보군을 만들었다. 이 후보군이 며칠 이상 보유해도 목표 수익/승률/손실률을 만족하는지 확인한다.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme-map", type=Path, default=DEFAULT_THEME_MAP)
    parser.add_argument("--daily-dir", type=Path, default=DEFAULT_DAILY_DIR)
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--market-panel", type=Path, default=DEFAULT_MARKET_PANEL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task503_multiday_entry_population_rebuild(
        theme_map_path=args.theme_map,
        daily_dir=args.daily_dir,
        intraday_dir=args.intraday_dir,
        market_panel_path=args.market_panel,
        out_dir=args.out_dir,
    )
    row = artifacts.task_503_decision.iloc[0]
    print(
        "[TASK503] "
        f"goal={row['goal_achieved_flag']} entries={row['entry_candidate_count']} "
        f"count={row['selected_count']} avg={float(row['selected_avg_net_pct']):.3f}%"
    )


if __name__ == "__main__":
    main()
